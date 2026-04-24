"""
Hermes 协调者（数字生命的"对外脸面"）

职责：
1. 唯一与老人对话的 agent（其他 agent 都是"幕后专家"）
2. 拉取所有专业 agent 的 report，整合为对话上下文
3. 调用 PersonaConfig + MemoryEngine 构造 system prompt
4. 决定是否调用工具（function calling）
5. 异常时降级到现有 qwen_service.chat（保底体验）

Phase 4 完成时本类会负责所有对话；当前是骨架，主要演示 API 形态。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.agents.base import AgentReport, BaseAgent
from app.services.agents.health_agent import HealthAgent
from app.services.agents.memory_agent import MemoryAgent
from app.services.agents.safety_agent import SafetyAgent
from app.services.agents.schedule_agent import ScheduleAgent
from app.services.agents.social_agent import SocialAgent
from app.services.memory_engine import MemoryEngine, MemoryType, get_memory_engine
from app.services.persona import (
    ANXINBAO_PERSONA,
    PersonaContext,
    build_system_prompt,
)

logger = logging.getLogger(__name__)


@dataclass
class HermesResponse:
    """Hermes 一次对话的输出"""
    text: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    used_memories: List[int] = field(default_factory=list)  # 召回了哪些 memory.id
    agent_reports: List[AgentReport] = field(default_factory=list)
    fallback: bool = False  # 是否降级到了 qwen_service


class Hermes:
    """协调者"""

    def __init__(self):
        self.health = HealthAgent()
        self.social = SocialAgent()
        self.memory = MemoryAgent()
        self.safety = SafetyAgent()
        self.schedule = ScheduleAgent()
        self._memory_engine: Optional[MemoryEngine] = None

    @property
    def memory_engine(self) -> MemoryEngine:
        if self._memory_engine is None:
            self._memory_engine = get_memory_engine()
        return self._memory_engine

    async def chat(
        self,
        user_id: int,
        user_message: str,
        elder_name: str = "您",
        dialect: str = "wuhan",
    ) -> HermesResponse:
        """
        老人发来一条消息，Hermes 给出回应。

        当前实现是骨架：调用所有 agent → 召回记忆 → 构造 prompt →
        降级到 qwen_service。Phase 4 完成时会替换为完整 LLM + 工具调用循环。
        """
        # 1) 收集所有 agent 的 report
        ctx_for_agents = {"user_message": user_message}
        agent_reports: List[AgentReport] = []
        for agent in (self.health, self.social, self.memory, self.safety, self.schedule):
            agent_reports.append(await agent.safe_evaluate(user_id, ctx_for_agents))

        # 2) 召回相关长期记忆
        memories = self.memory_engine.recall(
            user_id=user_id,
            query=user_message,
            top_k=8,
        )

        # 3) 构造 PersonaContext
        ctx = PersonaContext(
            elder_name=elder_name,
            elder_dialect=dialect,
            elder_mood_recent=self._extract_mood(agent_reports),
            health_status=self._extract_health(agent_reports),
            family_status=self._extract_social(agent_reports),
            last_chat_summary=self._format_memories_summary(memories),
        )
        system_prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)

        # 4) 调用 LLM —— 当前骨架降级到现有 qwen_service.chat_async
        try:
            from app.services.qwen_service import qwen_service
            text = await qwen_service.chat_async(
                user_id=str(user_id),
                message=user_message,
                system_prompt=system_prompt,
            )
            fallback = True  # 当前还是用旧 qwen 接口，标记为 fallback
        except Exception as exc:
            logger.exception(f"Hermes.chat 调用 qwen_service 失败: {exc}")
            text = "唉，我现在脑子有点转不过来，您再说一遍好不？"
            fallback = True

        return HermesResponse(
            text=text,
            tool_calls=[],  # Phase 3 接入 function calling
            used_memories=[m.id for m in memories if m.id is not None],
            agent_reports=agent_reports,
            fallback=fallback,
        )

    # ===== 辅助 =====

    @staticmethod
    def _extract_mood(reports: List[AgentReport]) -> Optional[str]:
        for r in reports:
            if r.agent_name == "memory" and "recent_mood" in r.details:
                return r.details["recent_mood"]
        return None

    @staticmethod
    def _extract_health(reports: List[AgentReport]) -> Optional[str]:
        for r in reports:
            if r.agent_name == "health":
                return r.summary or None
        return None

    @staticmethod
    def _extract_social(reports: List[AgentReport]) -> Optional[str]:
        for r in reports:
            if r.agent_name == "social":
                return r.summary or None
        return None

    @staticmethod
    def _format_memories_summary(memories) -> Optional[str]:
        if not memories:
            return None
        # 拼前 3 条作为"上次聊到"的提示
        items = [f"「{m.content[:40]}」" for m in memories[:3]]
        return "; ".join(items)


# 全局单例
hermes = Hermes()
