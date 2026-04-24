"""
HealthAgent · 健康监控（无 LLM，规则引擎）

Phase 4 完整体职责：
- 监控老人健康数据流（血压/心率/血糖/睡眠）
- 检测异常趋势（连续 3 天血压偏高、心率昼夜倒置等）
- 向 Hermes 汇报健康状况摘要 + 建议（不直接给医疗结论）

当前骨架：调用 health_evaluator 拿基础评估并汇总。
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.services.agents.base import AgentReport, BaseAgent

logger = logging.getLogger(__name__)


class HealthAgent(BaseAgent):
    name = "health"

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        # Phase 4 实施时填充：调用 health_evaluator + 趋势分析
        try:
            from app.services.health_evaluator import health_evaluator
            # 占位调用：尝试拿一次评估，失败则返回 info
            try:
                summary = "健康状况待评估"
                if hasattr(health_evaluator, "get_user_summary"):
                    res = health_evaluator.get_user_summary(user_id)
                    if res:
                        summary = str(res)[:120]
                return AgentReport(
                    agent_name=self.name,
                    severity="info",
                    summary=summary,
                )
            except Exception:
                pass
        except ImportError:
            pass

        return AgentReport(
            agent_name=self.name,
            severity="info",
            summary="健康监控待接入（Phase 4）",
        )
