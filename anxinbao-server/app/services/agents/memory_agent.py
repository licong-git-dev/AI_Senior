"""
MemoryAgent · 长期记忆管理

Phase 4 完整体职责：
- 每天凌晨"睡眠"做记忆整合（合并相似事实、归档过期心境）
- 从对话中抽取新事实/偏好/关系并入库（与 Hermes 协作，不阻塞实时对话）
- 暴露最近心境趋势给 Hermes（用于 PersonaContext.elder_mood_recent）

当前骨架：包装 memory_engine 提供基本统计 + 占位心境聚合。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.services.agents.base import AgentReport, BaseAgent
from app.services.memory_engine import (
    MemoryEngine,
    MemoryType,
    get_memory_engine,
)

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    name = "memory"

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
            recent_moods = self.engine.recall(
                user_id=user_id,
                types=[MemoryType.MOOD],
                top_k=5,
            )
            mood_summary = "neutral"
            if recent_moods:
                last = recent_moods[0]
                if "happy" in last.content.lower() or "高兴" in last.content:
                    mood_summary = "happy"
                elif "lonely" in last.content.lower() or "孤独" in last.content or "想伢" in last.content:
                    mood_summary = "lonely"
                elif "sad" in last.content.lower() or "难过" in last.content:
                    mood_summary = "sad"
                elif "anxious" in last.content.lower() or "焦虑" in last.content or "急" in last.content:
                    mood_summary = "anxious"

            return AgentReport(
                agent_name=self.name,
                severity="info",
                summary=f"记忆 {stats['total']} 条，最近心境 {mood_summary}",
                details={"stats": stats, "recent_mood": mood_summary},
            )
        except Exception as exc:
            logger.exception(f"MemoryAgent evaluate 异常: {exc}")
            return AgentReport(
                agent_name=self.name,
                severity="error",
                summary=f"记忆评估异常: {type(exc).__name__}",
            )
