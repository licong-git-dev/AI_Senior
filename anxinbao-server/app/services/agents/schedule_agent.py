"""
ScheduleAgent · 用药 / 服务 / 出行规划

Phase 4 完整体职责：
- 监控待处理的用药提醒（30 分钟内即将服药）
- 计划中的社区服务订单（明天 9:00 上门保洁）
- 出行规划（明天阴天，改后天去公园）
- 主动提醒 Hermes "30 分钟后该吃药了，可以提一下"

当前骨架：占位。
"""
from __future__ import annotations

from typing import Any, Dict

from app.services.agents.base import AgentReport, BaseAgent


class ScheduleAgent(BaseAgent):
    name = "schedule"

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        return AgentReport(
            agent_name=self.name,
            severity="info",
            summary="无紧迫日程",
        )
