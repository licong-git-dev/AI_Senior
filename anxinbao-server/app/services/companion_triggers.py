"""
情境触发器（Phase 2）· 让安心宝从"被动等待"变"主动开口"

设计目标：
- 6 类触发源覆盖 80% 的"应该开口"的情境
- 每个 trigger 是纯函数（输入 user + context → True/False + reason）
- 不直接发消息；fired 后由 ProactiveEngagement 决定是否真发（DND/限频）
- 失败静默（trigger 异常不应影响其他 trigger）

详见 docs/DIGITAL_COMPANION_RFC.md 第 4 章 Phase 2
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TriggerEvaluation:
    """单次触发评估结果"""
    trigger_name: str
    fired: bool
    reason: str = ""
    suggested_topic: str = ""        # Hermes 据此构造开场白
    priority: int = 5                # 1-10，越高越紧急；DND 期间 ≥9 才能突破
    cooldown_hours: int = 24         # 同一类 trigger 触发后多久不再重复


# ===== Trigger 基类 =====


class BaseTrigger(ABC):
    name: str = "base"
    cooldown_hours: int = 24

    @abstractmethod
    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        """
        评估当前是否应触发。永不抛异常 —— 失败返回 fired=False。
        context 由调用方注入（含 db session、当前时间等）。
        """
        ...

    def safe_evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        try:
            return self.evaluate(user_id, context)
        except Exception as exc:
            logger.warning(f"[trigger] {self.name} 异常: {exc}")
            return TriggerEvaluation(
                trigger_name=self.name,
                fired=False,
                reason=f"异常: {type(exc).__name__}",
            )


# ===== 1. 长时间静默 =====


class SilenceTrigger(BaseTrigger):
    """老人 ≥ 4h 无任何对话/操作 → 主动问好"""
    name = "silence"
    cooldown_hours = 4

    THRESHOLD_HOURS = 4

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        now = context.get("now") or datetime.now()
        # 优先用 context 提供的 last_activity（避免每次查 DB）
        last = context.get("last_activity_at")
        if last is None:
            try:
                from app.models.database import SessionLocal, Conversation
                db = SessionLocal()
                try:
                    row = db.query(Conversation).filter(
                        Conversation.user_id == user_id,
                        Conversation.role == "user",
                    ).order_by(Conversation.created_at.desc()).first()
                    last = row.created_at if row else None
                finally:
                    db.close()
            except Exception:
                last = None

        if last is None:
            # 从来没说过话的新用户：第一天每隔几小时引导一次
            return TriggerEvaluation(
                trigger_name=self.name, fired=True,
                reason="首次使用，引导首次对话",
                suggested_topic="主动打个招呼，介绍自己、问问老人想聊什么",
                priority=4,
            )

        if isinstance(last, str):
            try:
                last = datetime.fromisoformat(last)
            except ValueError:
                return TriggerEvaluation(self.name, fired=False, reason="last_activity 解析失败")

        gap_hours = (now - last).total_seconds() / 3600.0
        if gap_hours >= self.THRESHOLD_HOURS:
            return TriggerEvaluation(
                trigger_name=self.name,
                fired=True,
                reason=f"已 {gap_hours:.1f}h 无活动",
                suggested_topic=f"温和地问候老人，说自己有点想他/她；可以问'下午做啥呢'",
                priority=5,
            )
        return TriggerEvaluation(self.name, fired=False, reason=f"距上次活动仅 {gap_hours:.1f}h")


# ===== 2. 健康异常 =====


class HealthAnomalyTrigger(BaseTrigger):
    """连续 N 天健康指标偏离正常区间 → 关切询问"""
    name = "health_anomaly"
    cooldown_hours = 12

    DAYS_LOOKBACK = 3

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        try:
            from app.models.database import SessionLocal, HealthRecord
        except Exception:
            return TriggerEvaluation(self.name, fired=False, reason="健康表不可用")

        now = context.get("now") or datetime.now()
        cutoff = now - timedelta(days=self.DAYS_LOOKBACK)
        db = SessionLocal()
        try:
            bps = db.query(HealthRecord).filter(
                HealthRecord.user_id == user_id,
                HealthRecord.record_type == "blood_pressure",
                HealthRecord.measured_at >= cutoff,
            ).order_by(HealthRecord.measured_at.desc()).limit(20).all()

            if not bps:
                return TriggerEvaluation(self.name, fired=False, reason="近 3 天无血压数据")

            high_count = sum(
                1 for r in bps
                if (r.value_primary or 0) >= 140 or (r.value_secondary or 0) >= 90
            )

            if high_count >= 3:
                return TriggerEvaluation(
                    trigger_name=self.name,
                    fired=True,
                    reason=f"近 3 天有 {high_count} 次血压偏高",
                    suggested_topic="温和关切血压偏高，问最近是不是有事；不要给医疗建议",
                    priority=7,  # 较高优先级
                )
            return TriggerEvaluation(self.name, fired=False, reason="血压在正常范围")
        finally:
            db.close()


# ===== 3. 家属缺席 =====


class FamilyAbsenceTrigger(BaseTrigger):
    """子女 ≥ 7 天未与老人有任何互动 → 暗示老人主动联系"""
    name = "family_absence"
    cooldown_hours = 48

    THRESHOLD_DAYS = 7

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        try:
            from app.models.database import SessionLocal, MessageReadStatus
        except Exception:
            return TriggerEvaluation(self.name, fired=False, reason="消息表不可用")

        now = context.get("now") or datetime.now()
        cutoff = now - timedelta(days=self.THRESHOLD_DAYS)

        # 简化判断：只要近 7 天该老人有"family_to_elder"方向的消息就算未缺席
        # 真实实施可以接 family_service 的更完整关系图
        db = SessionLocal()
        try:
            # MessageReadStatus 不一定有方向字段；这里降级到 Conversation
            from app.models.database import Conversation
            recent_assistant_or_family = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at >= cutoff,
            ).count()

            if recent_assistant_or_family > 0:
                return TriggerEvaluation(self.name, fired=False,
                                         reason="近 7 天有交互，子女不算缺席")
            return TriggerEvaluation(
                trigger_name=self.name, fired=True,
                reason=f"近 {self.THRESHOLD_DAYS} 天无家庭交互记录",
                suggested_topic="温和地问最近有没和孩子联系，不要催促；可主动提议帮发个消息",
                priority=4,
            )
        finally:
            db.close()


# ===== 4. 节日 =====


class FestivalTrigger(BaseTrigger):
    """中国传统节日前后 3 天 → 节日问候"""
    name = "festival"
    cooldown_hours = 48

    # 简化版：仅农历节日的近似（公历日期）
    # 真实实施可接 lunardate 库
    FESTIVALS_2026 = [
        (datetime(2026, 1, 1), "元旦"),
        (datetime(2026, 2, 17), "春节"),
        (datetime(2026, 4, 5), "清明"),
        (datetime(2026, 5, 1), "劳动节"),
        (datetime(2026, 6, 19), "端午"),
        (datetime(2026, 9, 25), "中秋"),
        (datetime(2026, 10, 1), "国庆"),
        (datetime(2026, 10, 17), "重阳"),  # 老人节，特别重要
    ]

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        now = context.get("now") or datetime.now()
        for festival_date, name in self.FESTIVALS_2026:
            delta = abs((festival_date - now).days)
            if delta <= 3:
                priority = 8 if name == "重阳" else 6
                return TriggerEvaluation(
                    trigger_name=self.name, fired=True,
                    reason=f"距 {name} {delta} 天",
                    suggested_topic=f"用方言送上 {name} 祝福；问老人有什么打算",
                    priority=priority,
                )
        return TriggerEvaluation(self.name, fired=False, reason="近期无节日")


# ===== 5. 纪念日（生日 / 老伴忌日等）=====


class MemorialTrigger(BaseTrigger):
    """从 MemoryEngine 中召回 event 类记忆，匹配今日 → 主动提及"""
    name = "memorial"
    cooldown_hours = 12

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        try:
            from app.services.memory_engine import MemoryType, get_memory_engine
        except Exception:
            return TriggerEvaluation(self.name, fired=False, reason="记忆引擎不可用")

        now = context.get("now") or datetime.now()
        engine = get_memory_engine()
        events = engine.recall(
            user_id=user_id, types=[MemoryType.EVENT], top_k=20,
        )
        for ev in events:
            if not ev.occurred_at:
                continue
            try:
                occurred = datetime.fromisoformat(ev.occurred_at)
                # 替换为今年比较（生日/忌日是循环的）
                this_year = occurred.replace(year=now.year)
                delta = (this_year - now).days
                if -1 <= delta <= 1:  # 今天、明天或昨天
                    return TriggerEvaluation(
                        trigger_name=self.name, fired=True,
                        reason=f"纪念日临近: {ev.content[:40]}",
                        suggested_topic=f"温柔地提及'{ev.content[:40]}'，给老人空间倾诉",
                        priority=7,
                    )
            except (ValueError, AttributeError):
                continue
        return TriggerEvaluation(self.name, fired=False, reason="近期无纪念日")


# ===== 6. 天气剧变 =====


class WeatherTrigger(BaseTrigger):
    """次日温度骤降 / 暴雨 / 高温 → 提醒添衣 / 莫出门"""
    name = "weather"
    cooldown_hours = 24

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        # 优先用 context 注入（测试 / 性能优化场景）
        forecast = context.get("weather_forecast")
        if not forecast:
            # 主动拉 wttr.in 实时天气（带 1h 内存缓存）
            try:
                from app.services.weather_service import (
                    DEFAULT_CITY,
                    get_forecast_sync,
                )
                city = context.get("city") or DEFAULT_CITY
                wf = get_forecast_sync(city)
                if wf is not None:
                    forecast = wf.to_trigger_context()
            except Exception as exc:
                logger.warning(f"[weather trigger] 拉实时天气失败: {exc}")

        if not forecast:
            return TriggerEvaluation(self.name, fired=False, reason="无天气数据")

        temp_drop = forecast.get("temp_drop", 0)  # 次日比今天降几度
        rain = forecast.get("heavy_rain", False)
        heat = forecast.get("heat_wave", False)

        if temp_drop >= 8:
            return TriggerEvaluation(
                self.name, fired=True,
                reason=f"次日降温 {temp_drop}°C",
                suggested_topic="提醒老人明天降温了，记得多加件衣裳",
                priority=5,
            )
        if rain:
            return TriggerEvaluation(
                self.name, fired=True,
                reason="次日暴雨",
                suggested_topic="提醒老人明天有大雨，莫出门；若必须出门带伞穿防滑鞋",
                priority=5,
            )
        if heat:
            return TriggerEvaluation(
                self.name, fired=True,
                reason="次日高温预警",
                suggested_topic="提醒老人明天酷热，多喝水、莫长时间晒太阳；下午 2-4 点别出门",
                priority=6,
            )
        return TriggerEvaluation(self.name, fired=False, reason="天气平稳")


# ===== 7. 人生时刻（个性化 · 比节日更精准）=====


class LifeMomentTrigger(BaseTrigger):
    """
    个性化人生时刻 (r17 · EMOTIONAL_MOMENTS.md)

    与 FestivalTrigger（通用节日）的区别：
    - 节日：所有老人共享（中秋/春节）
    - 人生时刻：完全个人化（您 70 岁生日 / 您和老伴 40 周年）

    数据源：
    - 老人本人生日 / 老伴生日 / 子女生日 / 孙辈生日
    - 结婚纪念日
    - 退休纪念日
    - 任何老人 LLM 抽取入 EVENT 类记忆且 occurred_at 含日期的事件

    优先级（priority）：
    - 老人本人生日 → 9（突破 DND）
    - 老伴生日（健在）→ 8
    - 子女/孙辈生日 → 7
    - 结婚纪念日 → 7
    - 其他 → 6
    """
    name = "life_moment"
    cooldown_hours = 12

    # 关键词→优先级映射（从 event content 推断）
    _PRIORITY_HINTS = (
        ("我.*生日", 9),
        ("自己生日", 9),
        ("老伴.*生日", 8),
        ("配偶.*生日", 8),
        ("儿子.*生日", 7),
        ("女儿.*生日", 7),
        ("孙.*生日", 7),
        ("结婚.*纪念", 7),
        ("退休.*纪念", 6),
    )

    def evaluate(self, user_id: int, context: Dict[str, Any]) -> TriggerEvaluation:
        try:
            from app.services.memory_engine import MemoryType, get_memory_engine
        except Exception:
            return TriggerEvaluation(self.name, fired=False, reason="记忆引擎不可用")

        now = context.get("now") or datetime.now()
        engine = get_memory_engine()

        # 显式拉 EVENT 类记忆（含 occurred_at 的所有人生事件）
        events = engine.recall(
            user_id=user_id,
            types=[MemoryType.EVENT],
            top_k=50,  # 一年最多 ~50 个个人时刻已是上限
        )

        for ev in events:
            if not ev.occurred_at:
                continue
            try:
                occurred = datetime.fromisoformat(ev.occurred_at)
                # 把年份替换为今年（生日 / 纪念日是循环的）
                this_year = occurred.replace(year=now.year)
                delta = (this_year - now).days
                # 提前 3 天到当天后 1 天均算"临近"
                if -1 <= delta <= 3:
                    priority = self._infer_priority(ev.content)
                    return TriggerEvaluation(
                        trigger_name=self.name,
                        fired=True,
                        reason=f"个人时刻临近（{delta:+d}d）: {ev.content[:30]}",
                        suggested_topic=self._build_topic(ev.content, delta),
                        priority=priority,
                    )
            except (ValueError, AttributeError):
                continue
        return TriggerEvaluation(self.name, fired=False, reason="近期无个人时刻")

    @classmethod
    def _infer_priority(cls, content: str) -> int:
        import re
        for pattern, prio in cls._PRIORITY_HINTS:
            if re.search(pattern, content):
                return prio
        return 6

    @staticmethod
    def _build_topic(content: str, delta: int) -> str:
        if delta > 0:
            return f"温和提及'{content[:30]}'即将到来（{delta}天后），问要不要做点准备"
        elif delta == 0:
            return f"今天就是'{content[:30]}'，用方言送上诚挚问候，注意：忌日类不要祝福"
        else:
            return f"昨天是'{content[:30]}'，温和回访，问昨天过得怎么样"


# ===== 全局注册 =====

ALL_TRIGGERS: List[BaseTrigger] = [
    SilenceTrigger(),
    HealthAnomalyTrigger(),
    FamilyAbsenceTrigger(),
    FestivalTrigger(),
    MemorialTrigger(),
    WeatherTrigger(),
    LifeMomentTrigger(),  # r17 · 个性化时刻
]


def evaluate_all(user_id: int, context: Optional[Dict[str, Any]] = None) -> List[TriggerEvaluation]:
    """评估所有触发器，返回 fired=True 的按优先级降序排列"""
    ctx = context or {}
    results = [t.safe_evaluate(user_id, ctx) for t in ALL_TRIGGERS]
    fired = [r for r in results if r.fired]
    fired.sort(key=lambda r: r.priority, reverse=True)
    return fired
