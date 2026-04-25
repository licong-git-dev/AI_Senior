"""
商业意图识别服务（r27 · Insight #13 GMV 漏斗的"识别层"）

设计依据：MONETIZATION_BEYOND_SUBSCRIPTION.md

核心：当前订阅 ¥588/年 < 单户成本 ¥800。破解路径不是再加套餐，是
**让老人"正在花的钱"有一部分流过安心宝**。

第一步不是做商城，是先做"识别老人模糊需求"的能力。攒 6 个月数据后再
拍脑袋选 SKU 上架。

实现策略（V1）:
- 模式匹配（关键词 → 分类 → 置信度）
- 不调 LLM（保证识别成本接近 0）
- 异步触发（Hermes 对话回复后 fire-and-forget 调）
- 失败静默（不影响主对话）
- 30 天自动过期（避免老人当时随口一说被永久挂账）

升级路径 V2 (r28+):
- LLM 二次确认（提高 precision）
- 接通真实 SKU 库
- 子女端"妈妈最近想要的东西"卡片
- 一键下单 → 订单回调 → 分成入账

隐私红线:
- 老人**永远看不到**自己的 commercial_intent 列表（避免被推销感）
- 仅 family.payer 可见
- 老人可一键关闭整个模块（DND 配置 + push_proactive 类似）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.database import CommercialIntent

logger = logging.getLogger(__name__)


# ===== 关键词字典 (V1: 7 一级分类 × 5-10 关键词) =====
# 每条 (keyword, category, suggested_title, confidence)
# 规则：高置信度需匹配症状性短语（"腿疼"），低置信度只命中泛词（"喝水"）

INTENT_PATTERNS: List[Tuple[str, str, str, float]] = [
    # 营养 nutrition
    ("缺钙", "nutrition", "高钙片 / 维 D", 0.8),
    ("骨头脆", "nutrition", "高钙片 / 维 D", 0.8),
    ("没胃口", "nutrition", "开胃复合维生素", 0.6),
    ("吃不下", "nutrition", "开胃复合维生素", 0.6),
    ("蛋白质", "nutrition", "老年蛋白粉", 0.7),
    ("贫血", "nutrition", "补铁食品/营养品", 0.8),
    # 镇痛/关节 pain_relief
    ("腿疼", "pain_relief", "护膝 / 关节贴", 0.85),
    ("膝盖疼", "pain_relief", "护膝 / 关节贴", 0.9),
    ("关节痛", "pain_relief", "护膝 / 氨糖", 0.85),
    ("腰疼", "pain_relief", "腰托 / 暖宝", 0.8),
    ("肩膀疼", "pain_relief", "肩颈贴", 0.8),
    # 睡眠 sleep
    ("睡不好", "sleep", "助眠枕 / 蒸汽眼罩", 0.85),
    ("失眠", "sleep", "助眠枕 / 褪黑素咨询", 0.85),
    ("半夜醒", "sleep", "助眠枕", 0.8),
    ("打鼾", "sleep", "止鼾枕", 0.7),
    # 行动 mobility
    ("走路晃", "mobility", "防滑鞋 / 助行器", 0.85),
    ("摔跤", "mobility", "防滑鞋 / 浴室扶手", 0.9),
    ("浴室滑", "mobility", "防滑垫 / 浴室扶手", 0.9),
    ("起床困难", "mobility", "床头扶手", 0.7),
    # 卫生 hygiene
    ("纸尿裤", "hygiene", "成人纸尿裤", 0.85),
    ("漏尿", "hygiene", "成人纸尿裤", 0.8),
    # 兴趣 hobby
    ("看不清字", "hobby", "大字版老花镜 / Kindle", 0.85),
    ("听不清", "hobby", "助听器", 0.9),
    ("收音机", "hobby", "老年收音机", 0.6),
    # 家电 appliance
    ("药盒", "appliance", "智能分药盒", 0.85),
    ("血压计", "appliance", "电子血压计", 0.85),
    ("血糖仪", "appliance", "血糖仪 + 试纸", 0.85),
    ("电热毯", "appliance", "老年电热毯", 0.7),
]


@dataclass
class IntentDetection:
    """识别结果（未持久化前的意图候选）"""
    category: str
    keyword: str
    suggested_title: str
    confidence: float
    source_text: str


# ===== 异常 =====


class CommercialIntentError(Exception):
    pass


class NotPayerError(CommercialIntentError):
    """非 payer 角色不能查看 / 操作 intent"""


# ===== 服务 =====


class CommercialIntentService:
    """商业意图识别（无状态；db 注入）"""

    DEFAULT_EXPIRY_DAYS = 30

    # ---- 识别 ----

    def detect_from_text(self, text: str) -> List[IntentDetection]:
        """
        从一段老人原话识别商业意图（多个）。
        优先返回置信度高的。同一关键词命中多次只算一次。
        """
        if not text or len(text) < 2:
            return []

        text_lower = text.lower()
        seen_keywords = set()
        results: List[IntentDetection] = []

        for keyword, category, title, conf in INTENT_PATTERNS:
            if keyword in seen_keywords:
                continue
            if keyword in text or keyword in text_lower:
                seen_keywords.add(keyword)
                results.append(IntentDetection(
                    category=category,
                    keyword=keyword,
                    suggested_title=title,
                    confidence=conf,
                    source_text=text[:500],
                ))

        # 按置信度倒序
        results.sort(key=lambda d: d.confidence, reverse=True)
        return results

    def record_detection(
        self,
        db: Session,
        elder_user_id: int,
        detection: IntentDetection,
        source_type: str = "chat",
        source_object_id: Optional[str] = None,
    ) -> CommercialIntent:
        """把一条识别结果落库（detected 状态）"""
        intent = CommercialIntent(
            elder_user_id=elder_user_id,
            category=detection.category,
            keyword=detection.keyword,
            source_text=detection.source_text,
            source_type=source_type,
            source_object_id=source_object_id,
            suggested_title=detection.suggested_title,
            confidence=detection.confidence,
            status="detected",
            expires_at=datetime.now() + timedelta(days=self.DEFAULT_EXPIRY_DAYS),
        )
        db.add(intent)
        db.commit()
        db.refresh(intent)
        return intent

    def detect_and_record(
        self,
        db: Session,
        elder_user_id: int,
        text: str,
        source_type: str = "chat",
        source_object_id: Optional[str] = None,
        max_records: int = 3,
    ) -> List[CommercialIntent]:
        """
        Hermes 对话后 fire-and-forget 调：
        识别 → 去重（同 keyword 30 天内已存在的不重复）→ 落库。
        """
        detections = self.detect_from_text(text)
        if not detections:
            return []

        # 去重：30 天内同 (elder, keyword) 的活跃 intent
        cutoff = datetime.now() - timedelta(days=self.DEFAULT_EXPIRY_DAYS)
        existing_keywords = {
            row.keyword for row in
            db.query(CommercialIntent)
            .filter(
                CommercialIntent.elder_user_id == elder_user_id,
                CommercialIntent.status.in_(("detected", "reviewed_by_family")),
                CommercialIntent.detected_at >= cutoff,
            )
            .all()
        }

        records: List[CommercialIntent] = []
        for d in detections[:max_records]:
            if d.keyword in existing_keywords:
                continue
            try:
                intent = self.record_detection(
                    db, elder_user_id, d, source_type, source_object_id,
                )
                records.append(intent)
            except Exception as exc:
                logger.warning(f"[intent] 持久化失败: {exc}")
        return records

    # ---- 查询（payer-only） ----

    def list_intents(
        self,
        db: Session,
        elder_user_id: int,
        viewer_user_auth_id: int,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[CommercialIntent]:
        """
        家属视角：拉某个老人的 intent 列表。
        权限：viewer 必须是该 elder 所在 family_account 的 payer。
        """
        self._require_payer_for_elder(db, elder_user_id, viewer_user_auth_id)
        q = db.query(CommercialIntent).filter(
            CommercialIntent.elder_user_id == elder_user_id,
        )
        if status:
            q = q.filter(CommercialIntent.status == status)
        return (
            q.order_by(CommercialIntent.detected_at.desc())
            .limit(max(1, min(200, limit)))
            .all()
        )

    def stats(self, db: Session, elder_user_id: int,
              viewer_user_auth_id: int) -> Dict[str, int]:
        """payer 视角：当前 active intent 的分类分布"""
        self._require_payer_for_elder(db, elder_user_id, viewer_user_auth_id)

        rows = (
            db.query(CommercialIntent)
            .filter(
                CommercialIntent.elder_user_id == elder_user_id,
                CommercialIntent.status == "detected",
            )
            .all()
        )
        by_category: Dict[str, int] = {}
        for r in rows:
            by_category[r.category] = by_category.get(r.category, 0) + 1
        return {
            "total_active": len(rows),
            "by_category": by_category,
        }

    # ---- 状态机 ----

    def mark_reviewed(
        self,
        db: Session,
        intent_id: int,
        viewer_user_auth_id: int,
    ) -> CommercialIntent:
        intent = db.query(CommercialIntent).filter(
            CommercialIntent.id == intent_id,
        ).first()
        if not intent:
            raise CommercialIntentError("intent 不存在")
        self._require_payer_for_elder(db, intent.elder_user_id, viewer_user_auth_id)
        intent.status = "reviewed_by_family"
        intent.reviewed_at = datetime.now()
        intent.reviewed_by_user_auth_id = viewer_user_auth_id
        db.commit()
        db.refresh(intent)
        return intent

    def dismiss(
        self,
        db: Session,
        intent_id: int,
        viewer_user_auth_id: int,
    ) -> CommercialIntent:
        intent = db.query(CommercialIntent).filter(
            CommercialIntent.id == intent_id,
        ).first()
        if not intent:
            raise CommercialIntentError("intent 不存在")
        self._require_payer_for_elder(db, intent.elder_user_id, viewer_user_auth_id)
        intent.status = "dismissed"
        intent.reviewed_at = datetime.now()
        intent.reviewed_by_user_auth_id = viewer_user_auth_id
        db.commit()
        db.refresh(intent)
        return intent

    # ---- 内部 ----

    def _require_payer_for_elder(
        self,
        db: Session,
        elder_user_id: int,
        viewer_user_auth_id: int,
    ) -> None:
        """
        校验 viewer 是该老人的 family payer。
        - 找老人对应的 FamilyAccount（beneficiary_user_id == elder_user_id）
        - 校验 viewer 在该账户中是 payer 角色
        """
        from app.models.database import FamilyAccount, FamilyAccountMember

        # 找承载该老人的家庭账户
        accounts = (
            db.query(FamilyAccount)
            .filter(FamilyAccount.beneficiary_user_id == elder_user_id)
            .all()
        )
        if not accounts:
            raise NotPayerError("该老人没有任何家庭账户")

        # 校验 viewer 是其中一个 payer
        for acc in accounts:
            member = (
                db.query(FamilyAccountMember)
                .filter(
                    FamilyAccountMember.family_account_id == acc.id,
                    FamilyAccountMember.user_auth_id == viewer_user_auth_id,
                    FamilyAccountMember.role == "payer",
                )
                .first()
            )
            if member:
                return

        raise NotPayerError("仅 payer 角色可访问商业意图")


# 全局单例
commercial_intent_service = CommercialIntentService()
