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

        # ===== U-R3 加强：critical 双路径短路 =====
        # 路径 A: SafetyAgent critical → 紧急安抚语 + 不调 LLM（避免幻觉给出错误指引）
        # 路径 B: HealthAgent critical → 健康关切语 + 标记 fallback（让客户端知道走的是预设响应）
        critical_safety = next(
            (r for r in agent_reports
             if r.agent_name == "safety" and r.severity == "critical"),
            None,
        )
        if critical_safety:
            logger.error(f"Hermes critical safety: {critical_safety.summary}")
            return HermesResponse(
                text=self._safety_critical_text(elder_name, dialect, critical_safety),
                used_memories=[],
                agent_reports=list(agent_reports),
                fallback=False,
            )

        critical_health = next(
            (r for r in agent_reports
             if r.agent_name == "health" and r.severity == "critical"),
            None,
        )
        if critical_health:
            logger.warning(f"Hermes critical health: {critical_health.summary}")
            return HermesResponse(
                text=self._health_critical_text(elder_name, dialect, critical_health),
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

        # 3) 构造 PersonaContext + system prompt（U-R3：注入全部 5 agent 信号）
        reports_list = list(agent_reports)
        schedule_details = self._find_details(reports_list, "schedule")
        safety_details = self._find_details(reports_list, "safety")
        memory_details = self._find_details(reports_list, "memory")

        ctx = PersonaContext(
            elder_name=elder_name,
            elder_dialect=dialect,
            elder_mood_recent=self._extract_mood(reports_list),
            health_status=self._extract_health(reports_list),
            family_status=self._extract_social(reports_list),
            last_chat_summary=self._format_memories_summary(memories),
            time_of_day=time_of_day,
            # U-R3 新增字段（去 None 防误用）
            schedule_today_todo=(schedule_details or {}).get("today_todo") or None,
            schedule_critical=(schedule_details or {}).get("critical_alerts") or None,
            safety_special_mode=(safety_details or {}).get("mode"),
            memory_health_note=((memory_details or {}).get("memory_health") or {}).get("note") or None,
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

    @staticmethod
    def _safety_critical_text(elder_name: str, dialect: str,
                               report: AgentReport) -> str:
        """SafetyAgent critical 短路时的紧急安抚语（不调 LLM 防幻觉）"""
        # 尽量明确告知"已通知家人"，但**不假报警**——若 details 显示是静默而非真 SOS，
        # 措辞要克制
        details = report.details or {}
        if "hours_silent" in details:
            # 仅是长时间没说话；用关切语，不假说"已通知"
            if dialect == "wuhan":
                return f"{elder_name}，蛮久没听到您声音咯，您现在好不好？我陪着您。"
            return f"{elder_name}，好久没和我说话了，您现在还好吗？我在这里。"
        # 真实紧急事件
        if dialect == "wuhan":
            return f"{elder_name}，我察觉到紧急情况嘞，家里人那边我已经在通知。您莫怕，我陪您。"
        return f"{elder_name}，我察觉到紧急情况，已经在通知您家人。您先深呼吸，我陪着您。"

    @staticmethod
    def _health_critical_text(elder_name: str, dialect: str,
                               report: AgentReport) -> str:
        """HealthAgent critical 短路时的健康关切语（不调 LLM 防医疗建议幻觉）"""
        if dialect == "wuhan":
            return (
                f"{elder_name}，您家最近的指标我看了，{report.summary}。"
                f"莫慌，建议您赶紧打个电话给医生，或者让伢们陪您去看一下。我守着您。"
            )
        return (
            f"{elder_name}，最近的检查指标显示：{report.summary}。"
            f"建议尽快联系您的医生或家人，我会一直陪着您。"
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

    @staticmethod
    def _find_details(reports: List[AgentReport], agent_name: str) -> Optional[Dict[str, Any]]:
        """从 reports 找指定 agent 的 details 字典"""
        for r in reports:
            if r.agent_name == agent_name:
                return r.details or {}
        return None


# 全局单例
hermes = Hermes()
