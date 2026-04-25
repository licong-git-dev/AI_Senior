"""
MemoryAgent V1 · 长期记忆管理 · Phase 4 第 2 轮（U-R2）

职责（V1 实施）：
- 输出记忆健康度（总条数、各类分布、最久未更新的事实）
- 心境聚合（最近 7 天 mood 类记忆的多数派 + 强度趋势）
- 给 Hermes 提供 details: recent_mood / fact_density / mood_trend
- 暴露"老人讲过的话题热度"（话题权重）

设计原则:
- 只读，不写（写入由 MemoryConsolidator 在对话后异步处理）
- mood 聚合不只看最新一条，看最近 N 条多数派 + 趋势
- 不暴露具体记忆内容给 Hermes（内容隐私），只给聚合标签
- DB 异常返 error，不抛
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.services.agents.base import AgentReport, BaseAgent
from app.services.memory_engine import (
    MemoryEngine,
    MemoryRecord,
    MemoryType,
    get_memory_engine,
)

logger = logging.getLogger(__name__)


# ===== 心境分类关键词（中英双语 + 武汉话）=====

MOOD_KEYWORDS: Dict[str, List[str]] = {
    "happy": ["happy", "高兴", "开心", "乐", "舒畅", "蛮好", "舒服", "笑"],
    "lonely": ["lonely", "孤独", "寂寞", "想伢", "想孩子", "一个人"],
    "sad": ["sad", "难过", "伤心", "哭", "委屈", "心酸"],
    "anxious": ["anxious", "焦虑", "急", "慌", "担心", "怕"],
    "tired": ["tired", "累", "疲", "困", "没劲", "没精神"],
    "angry": ["angry", "气", "烦", "火大", "讨厌", "受不了"],
    "neutral": ["neutral", "还行", "一般", "凑合"],
}


def _classify_mood(content: str) -> str:
    """从一条记忆 content 推测心境类别"""
    text = (content or "").lower()
    for mood, kws in MOOD_KEYWORDS.items():
        if any(kw in text or kw in content for kw in kws):
            return mood
    return "neutral"


class MemoryAgent(BaseAgent):
    name = "memory"

    LOOKBACK_DAYS_FOR_MOOD = 7
    MOOD_SAMPLE_SIZE = 10  # 取最近 N 条 mood 类做多数派

    def __init__(self):
        super().__init__()
        self._engine: Optional[MemoryEngine] = None

    @property
    def engine(self) -> MemoryEngine:
        if self._engine is None:
            self._engine = get_memory_engine()
        return self._engine

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        try:
            stats = self.engine.stats(user_id)
        except Exception as exc:
            logger.exception(f"MemoryAgent stats 失败: {exc}")
            return AgentReport(
                self.name, severity="error",
                summary=f"记忆统计失败: {type(exc).__name__}",
            )

        total = stats.get("total", 0)
        by_type = stats.get("by_type", {})

        # 1) 心境聚合
        mood_info = self._analyze_mood(user_id)

        # 2) 记忆健康度
        health = self._memory_health(by_type, total)

        # 3) 决定 severity
        # - 持续负面心境 (sad/anxious/lonely 占多数) → warning
        # - 否则 info
        severity = "info"
        if mood_info["dominant"] in ("sad", "anxious", "lonely") and mood_info["sample_size"] >= 3:
            severity = "warning"

        # 4) 拼摘要
        summary_parts = [
            f"记忆 {total} 条",
            f"心境 {mood_info['dominant']}",
        ]
        if health["needs_attention"]:
            summary_parts.append(health["note"])
        summary = " · ".join(summary_parts)

        return AgentReport(
            self.name,
            severity=severity,
            summary=summary,
            details={
                "stats": stats,
                "recent_mood": mood_info["dominant"],
                "mood_distribution": mood_info["distribution"],
                "mood_sample_size": mood_info["sample_size"],
                "memory_health": health,
            },
        )

    # ===== 内部 =====

    def _analyze_mood(self, user_id: int) -> Dict[str, Any]:
        """
        最近 N 条 mood 类的多数派 + 分布。
        sample_size < 2 时返 neutral 不做强判断。
        """
        try:
            moods = self.engine.recall(
                user_id=user_id,
                types=[MemoryType.MOOD],
                top_k=self.MOOD_SAMPLE_SIZE,
            )
        except Exception:
            moods = []

        if not moods:
            return {
                "dominant": "neutral",
                "distribution": {},
                "sample_size": 0,
            }

        # 7 天内的为主要样本（旧的权重低）
        cutoff = datetime.now() - timedelta(days=self.LOOKBACK_DAYS_FOR_MOOD)
        cutoff_str = cutoff.isoformat()
        recent = [m for m in moods if (m.created_at or "") >= cutoff_str]
        sample = recent if recent else moods  # 7天内没数据则用 top-k

        classes = [_classify_mood(m.content) for m in sample]
        dist = dict(Counter(classes))

        # dominant: 多数派；并列时优先选负面（产品决定：宁可关心多一点）
        rank = {"sad": 5, "anxious": 4, "lonely": 3, "tired": 2, "angry": 2, "happy": 1, "neutral": 0}
        sorted_classes = sorted(
            dist.items(),
            key=lambda kv: (kv[1], rank.get(kv[0], 0)),
            reverse=True,
        )
        dominant = sorted_classes[0][0] if sorted_classes else "neutral"

        return {
            "dominant": dominant,
            "distribution": dist,
            "sample_size": len(sample),
        }

    def _memory_health(self, by_type: Dict[str, int], total: int) -> Dict[str, Any]:
        """
        简单的"记忆健康度"指标：
        - 太少 (<3): cold-start 中
        - 事实/偏好/关系任一为 0 + 总量已不少: 提醒做记忆补全
        - 大体均衡: 健康
        """
        if total < 3:
            return {"status": "cold_start", "needs_attention": False, "note": ""}

        fact = by_type.get("fact", 0)
        pref = by_type.get("preference", 0)
        rel = by_type.get("relation", 0)
        if total >= 10 and (fact == 0 or pref == 0 or rel == 0):
            missing = []
            if fact == 0: missing.append("事实")
            if pref == 0: missing.append("偏好")
            if rel == 0: missing.append("关系")
            return {
                "status": "needs_completion",
                "needs_attention": True,
                "note": f"缺{'/'.join(missing)}类记忆",
            }
        return {"status": "healthy", "needs_attention": False, "note": ""}
