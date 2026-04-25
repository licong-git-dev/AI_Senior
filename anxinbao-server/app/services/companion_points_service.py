"""
陪伴值养成系统服务（r19 · S 选项 · Insight #3）

设计原则：
- **不可逆沉没成本** —— 老人攒了陪伴值就舍不得换平台
- **正反馈即时**  —— 说话 +1 当场可见，不要"次日结算"那种延迟
- **每日上限**     —— 防止刷分（防 D7 之后失去意义）
- **流水不可改**   —— PointsLedger 仅 append-only，便于审计与争议处理
- **懒创建账户**   —— 老人首次产生互动时才建 CompanionPoints 行

行为分值（earn 类）：
| 行为 | 分值 | 每日上限 |
|---|---|---|
| 一句对话 | +1 | 30 |
| 当日首次签到 | +5 | 1 |
| 教 AI 一个事实（save_memory） | +3 | 10 |
| 接受触发器问候 | +2 | 6 |
| 生日当天额外 | +50 | 1 |

兑换池（spend 类）：
| 物品 | 价格 | 备注 |
|---|---|---|
| 视频通话延长 5 分钟 | 20 | 在通话中实时消耗 |
| 生日彩蛋（AI 唱生日歌 + 视频卡片） | 50 | 仅生日当天可换 |
| 解锁一段人生故事整理为文字稿 | 30 | 由 LIFE_STORY 记忆类型驱动 |
| 个性化 AI 语调升级 | 100 | 一次性永久 |
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.database import CompanionPoints, PointsLedger

logger = logging.getLogger(__name__)


# ===== 业务常量（白名单 + 限频，集中维护）=====


# (delta, daily_limit) — daily_limit=None 表示不限
EARN_RULES: Dict[str, Tuple[int, Optional[int]]] = {
    "earn_chat_message": (1, 30),
    "earn_daily_signin": (5, 1),
    "earn_save_memory": (3, 10),
    "earn_proactive_ack": (2, 6),
    "earn_birthday_bonus": (50, 1),
}


# 兑换价目（spend 必须正数；service 内部转负）
REDEMPTION_CATALOG: Dict[str, Dict[str, any]] = {
    "extend_videocall_5min": {
        "cost": 20,
        "title": "视频通话延长 5 分钟",
        "description": "下次和孙辈视频时自动多 5 分钟",
        "ledger_type": "spend_extend_videocall",
    },
    "birthday_egg": {
        "cost": 50,
        "title": "生日彩蛋",
        "description": "AI 用方言唱生日歌 + 子女合成贺卡",
        "ledger_type": "spend_birthday_egg",
        "constraint": "birthday_only",  # 仅生日当天可换
    },
    "unlock_life_story": {
        "cost": 30,
        "title": "整理人生故事为文字稿",
        "description": "AI 把您讲过的一段往事整理成可分享的文字+音频",
        "ledger_type": "spend_unlock_story",
    },
    "premium_voice": {
        "cost": 100,
        "title": "个性化 AI 语调",
        "description": "永久升级 AI 说话方式（更贴近您本人节奏）",
        "ledger_type": "spend_premium_voice",
        "permanent": True,
    },
}


# ===== 异常 =====


class PointsError(Exception):
    pass


class InsufficientBalanceError(PointsError):
    pass


class DailyLimitExceededError(PointsError):
    pass


class UnknownRedemptionError(PointsError):
    pass


class RedemptionConstraintViolatedError(PointsError):
    pass


# ===== 服务 =====


class CompanionPointsService:
    """陪伴值服务（无状态；db 注入）"""

    # ---- 账户 ----

    def get_or_create(self, db: Session, user_id: int) -> CompanionPoints:
        """懒创建账户。首次互动时调用。"""
        row = (
            db.query(CompanionPoints)
            .filter(CompanionPoints.user_id == user_id)
            .first()
        )
        if row:
            return row
        row = CompanionPoints(user_id=user_id, balance=0)
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info(f"[points] 为 user={user_id} 创建陪伴值账户")
        return row

    def get_balance(self, db: Session, user_id: int) -> int:
        row = self.get_or_create(db, user_id)
        return row.balance

    # ---- 进账 ----

    def earn(
        self,
        db: Session,
        user_id: int,
        type_: str,
        related_object_type: Optional[str] = None,
        related_object_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> PointsLedger:
        """
        进账。如果命中 daily_limit 则抛 DailyLimitExceededError。

        约定：service 调用方应当 try/except 该异常并**安静吞掉**
        （限频本身就是用户感知不到的体验细节）。
        """
        if type_ not in EARN_RULES:
            raise PointsError(f"未知 earn 类型: {type_}")

        delta, daily_limit = EARN_RULES[type_]
        if delta <= 0:
            raise PointsError(f"earn 类型 delta 必须 >0: {type_}={delta}")

        # 限频
        if daily_limit is not None:
            today_count = self._count_today(db, user_id, type_)
            if today_count >= daily_limit:
                raise DailyLimitExceededError(
                    f"{type_} 今日已达上限 {daily_limit}，跳过"
                )

        return self._record(db, user_id, delta, type_, note, related_object_type, related_object_id)

    # ---- 消耗 ----

    def redeem(
        self,
        db: Session,
        user_id: int,
        item_key: str,
        context: Optional[dict] = None,
    ) -> PointsLedger:
        """
        兑换。失败抛 InsufficientBalanceError / UnknownRedemptionError /
        RedemptionConstraintViolatedError。
        """
        item = REDEMPTION_CATALOG.get(item_key)
        if not item:
            raise UnknownRedemptionError(f"兑换码不存在: {item_key}")

        # 约束检查（如生日彩蛋仅生日当天）
        constraint = item.get("constraint")
        if constraint == "birthday_only":
            if not (context and context.get("is_birthday_today")):
                raise RedemptionConstraintViolatedError(
                    f"{item['title']} 仅生日当天可兑换"
                )

        # 余额检查
        cost = int(item["cost"])
        balance = self.get_balance(db, user_id)
        if balance < cost:
            raise InsufficientBalanceError(
                f"余额不足：当前 {balance}，需要 {cost}"
            )

        return self._record(
            db, user_id, -cost,
            type_=item["ledger_type"],
            note=item["title"],
            related_object_type="redemption",
            related_object_id=item_key,
        )

    # ---- 流水 ----

    def list_ledger(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
    ) -> List[PointsLedger]:
        return (
            db.query(PointsLedger)
            .filter(PointsLedger.user_id == user_id)
            .order_by(PointsLedger.created_at.desc())
            .limit(max(1, min(200, limit)))
            .all()
        )

    # ---- 签到（streak）----

    def daily_signin(self, db: Session, user_id: int) -> Tuple[bool, int]:
        """
        每天首次互动调用一次。返回 (是否真签到, 当前 streak_days)。

        逻辑:
        - 今天没签到过 → 加分 + streak +1（如昨天有签到则连续，否则归 1）
        - 今天已签到过 → 不加分，仅返回当前 streak
        """
        row = self.get_or_create(db, user_id)
        now = datetime.now()
        today = now.date()

        if row.last_streak_check_at and row.last_streak_check_at.date() == today:
            return False, row.streak_days

        # 判断连续
        if row.last_streak_check_at and (today - row.last_streak_check_at.date()).days == 1:
            row.streak_days += 1
        else:
            row.streak_days = 1
        row.last_streak_check_at = now
        db.commit()

        # 加签到分（如已达限就吞）
        try:
            self.earn(db, user_id, "earn_daily_signin", note=f"streak={row.streak_days}")
        except DailyLimitExceededError:
            pass

        return True, row.streak_days

    # ---- 内部 ----

    def _record(
        self,
        db: Session,
        user_id: int,
        delta: int,
        type_: str,
        note: Optional[str],
        related_object_type: Optional[str],
        related_object_id: Optional[str],
    ) -> PointsLedger:
        row = self.get_or_create(db, user_id)
        new_balance = row.balance + delta
        if new_balance < 0:
            # 安全网：理论上 redeem 已校验，这里防并发
            raise InsufficientBalanceError(f"扣减后余额会变负: {row.balance} + {delta}")

        row.balance = new_balance
        if delta > 0:
            row.lifetime_earned += delta
            row.last_earned_at = datetime.now()
        else:
            row.lifetime_spent += -delta

        ledger = PointsLedger(
            user_id=user_id,
            delta=delta,
            type=type_,
            note=note,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            balance_after=new_balance,
        )
        db.add(ledger)
        db.commit()
        db.refresh(ledger)
        return ledger

    def _count_today(self, db: Session, user_id: int, type_: str) -> int:
        """统计今天这个类型已出现几次（限频用）"""
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        return (
            db.query(PointsLedger)
            .filter(
                PointsLedger.user_id == user_id,
                PointsLedger.type == type_,
                PointsLedger.created_at >= today_start,
            )
            .count()
        )

    # ---- 安全的进账 helper（吞限频/未知类型，不影响主流程）----

    def safe_earn(self, db: Session, user_id: int, type_: str, **kwargs) -> Optional[PointsLedger]:
        """供 chat / proactive 等热路径调用：限频/异常都安静吞，不影响业务。"""
        try:
            return self.earn(db, user_id, type_, **kwargs)
        except DailyLimitExceededError:
            return None
        except Exception as exc:
            logger.warning(f"[points] safe_earn 异常: {exc}")
            return None


# 全局单例
companion_points_service = CompanionPointsService()
