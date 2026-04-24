"""
SafetyAgent · 24/7 安全守护（无 LLM，规则引擎）

Phase 4 完整体职责：
- 监听 SOS 触发（关键词 / 长按按钮 / 跌倒事件）
- 监控长时间无交互（4h 静默 → 警告；8h 静默 → 通知家属）
- 监控位置异常（如老人深夜出门未回）
- 异常时立即向 Hermes 上报 critical 级，触发紧急通知链

当前骨架：返回 info；填充时接入 emergency_service。
"""
from __future__ import annotations

from typing import Any, Dict

from app.services.agents.base import AgentReport, BaseAgent


class SafetyAgent(BaseAgent):
    name = "safety"

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        # Phase 4 实施时填充：监听 emergency_service.alerts + 计算静默时长
        return AgentReport(
            agent_name=self.name,
            severity="info",
            summary="无安全事件",
        )
