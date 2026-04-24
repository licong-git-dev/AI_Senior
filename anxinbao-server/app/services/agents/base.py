"""
Agent 基类（被所有专业 agent 继承）

设计原则：
- 每个 agent 只暴露 evaluate() / observe() / report() 三个生命周期方法
- 失败必须返回 AgentReport(severity='error') 而不是抛异常
- agent 之间不直接通信，只通过 Hermes 协调
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentReport:
    """专业 agent 向 Hermes 汇报的统一结构"""
    agent_name: str
    severity: str = "info"  # info / warning / error / critical
    summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    suggested_actions: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseAgent(ABC):
    """所有 agent 的基类"""

    name: str = "base"

    def __init__(self):
        self.last_run_at: Optional[str] = None

    @abstractmethod
    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        """
        核心评估方法 —— Hermes 调用此方法获取本 agent 对当前情境的判断。
        返回 AgentReport，永不抛异常（异常应内部捕获并返回 severity='error'）。
        """
        ...

    async def safe_evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        """带异常兜底的 evaluate；Hermes 应当优先调用此方法"""
        try:
            report = await self.evaluate(user_id, context)
            self.last_run_at = datetime.now().isoformat()
            return report
        except Exception as exc:
            logger.exception(f"agent {self.name} evaluate 异常: {exc}")
            return AgentReport(
                agent_name=self.name,
                severity="error",
                summary=f"agent 异常: {type(exc).__name__}",
                details={"error": str(exc)},
            )
