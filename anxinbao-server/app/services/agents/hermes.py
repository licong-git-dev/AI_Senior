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


def _infer_time_of_day() -> str:
    """根据当前时间推断 time_of_day（与 dialect_companion 周期对齐）"""
    from datetime import datetime as _dt
    h = _dt.now().hour
    if 5 <= h < 11:
        return "morning"
    if 11 <= h < 18:
        return "afternoon"
    if 18 <= h < 22:
        return "evening"
    return "night"

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
        老人发来一条消息，Hermes 给出回应（Phase 1 真实链路）。

        流程:
          1) 并行收集所有 agent 的 report（含 MemoryAgent 的 mood 聚合）
          2) 召回相关长期记忆（top-K=8，含关键词命中 + 时间衰减）
          3) 构造 PersonaContext + AnxinbaoPersona system_prompt（≤800 token）
          4) 调用 LLM 生成回复
          5) 触发 MemoryConsolidator（fire-and-forget，不阻塞）

        异常时降级：
          - LLM 失败 → 兜底语 + fallback=True
          - 记忆引擎失败 → 跳过召回，对话继续（warning 日志）
          - Agent 失败 → 各 agent 内部已有 safe_evaluate 兜底
        """
        time_of_day = _infer_time_of_day()

        # 1) 并行收集 agent reports（asyncio.gather 比串行快 5x）
        import asyncio
        ctx_for_agents = {"user_message": user_message, "time_of_day": time_of_day}
        agent_reports: List[AgentReport] = await asyncio.gather(
            self.health.safe_evaluate(user_id, ctx_for_agents),
            self.social.safe_evaluate(user_id, ctx_for_agents),
            self.memory.safe_evaluate(user_id, ctx_for_agents),
            self.safety.safe_evaluate(user_id, ctx_for_agents),
            self.schedule.safe_evaluate(user_id, ctx_for_agents),
        )

        # 安全 agent critical → 短路返回（绕开 LLM）
        critical_safety = next(
            (r for r in agent_reports if r.agent_name == "safety" and r.severity == "critical"),
            None,
        )
        if critical_safety:
            logger.error(f"Hermes 检测到 critical safety event: {critical_safety.summary}")
            return HermesResponse(
                text=f"{elder_name}，我察觉到紧急情况，已经通知您家人了。您先深呼吸，我陪着您。",
                used_memories=[],
                agent_reports=list(agent_reports),
                fallback=False,
            )

        # 2) 召回长期记忆（容错：失败不影响对话）
        memories = []
        try:
            memories = self.memory_engine.recall(
                user_id=user_id,
                query=user_message,
                top_k=8,
            )
        except Exception as exc:
            logger.warning(f"Hermes 召回记忆失败: {exc}（对话继续）")

        # 3) 构造 PersonaContext + system prompt
        ctx = PersonaContext(
            elder_name=elder_name,
            elder_dialect=dialect,
            elder_mood_recent=self._extract_mood(list(agent_reports)),
            health_status=self._extract_health(list(agent_reports)),
            family_status=self._extract_social(list(agent_reports)),
            last_chat_summary=self._format_memories_summary(memories),
            time_of_day=time_of_day,
        )
        system_prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)

        # 4) 调用 LLM（当前用 qwen_service，Phase 3 升级为 function calling）
        text = ""
        fallback = False
        try:
            from app.services.qwen_service import qwen_service
            text = await qwen_service.chat_async(
                user_id=str(user_id),
                message=user_message,
                system_prompt=system_prompt,
            )
            if not text or not text.strip():
                fallback = True
                text = self._fallback_text(elder_name, dialect)
        except Exception as exc:
            logger.exception(f"Hermes.chat 调用 qwen_service 失败: {exc}")
            fallback = True
            text = self._fallback_text(elder_name, dialect)

        # 5) 触发 MemoryConsolidator（fire-and-forget，不阻塞返回）
        try:
            from app.services.memory_consolidator import schedule_consolidation
            schedule_consolidation(user_id, user_message)
        except Exception as exc:
            logger.warning(f"Hermes 触发 MemoryConsolidator 失败: {exc}（对话继续）")

        return HermesResponse(
            text=text,
            tool_calls=[],  # Phase 3 接入 function calling
            used_memories=[m.id for m in memories if m.id is not None],
            agent_reports=list(agent_reports),
            fallback=fallback,
        )

    @staticmethod
    def _fallback_text(elder_name: str, dialect: str) -> str:
        """LLM 异常时的兜底语，按方言选词"""
        if dialect == "wuhan":
            return f"{elder_name}，我刚才走神了一下，您再跟我说一遍好不？"
        return f"{elder_name}，我刚才有点没听清，您再说一次好吗？"

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
