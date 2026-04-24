"""
SocialAgent · 家庭关系与社交（轻量 LLM 或规则）

Phase 4 完整体职责：
- 维护家庭关系图谱（哪些家属、谁主要联系人、上次互动时间）
- 节日 / 纪念日提醒（中秋将至、老伴忌日等）
- 子女缺席检测（"小军 1 周未联系，要不主动提一下？"）
- 社区社交提醒（"楼下张娭毑有阵子没串门了"）

当前骨架：返回静态 info report。
"""
from __future__ import annotations

from typing import Any, Dict

from app.services.agents.base import AgentReport, BaseAgent


class SocialAgent(BaseAgent):
    name = "social"

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        # Phase 4 实施时填充：调用 family_service + memory_engine 中的 relation 类记忆
        return AgentReport(
            agent_name=self.name,
            severity="info",
            summary="社交状态待接入（Phase 4）",
        )
