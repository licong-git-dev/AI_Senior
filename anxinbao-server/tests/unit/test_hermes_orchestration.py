"""
单元测试 · Phase 4 第 3 轮 (U-R3) · Hermes 协调与短路逻辑

聚焦点：
- critical 双路径短路（safety / health）
- agent reports 真正注入 PersonaContext
- 长时间静默时的克制措辞（不假报警）
"""
import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

import pytest

from app.services.agents.base import AgentReport
from app.services.agents.hermes import Hermes
from app.services.persona import (
    ANXINBAO_PERSONA,
    PersonaContext,
    build_system_prompt,
)


def _fake_report(name, severity="info", summary="ok", details=None):
    return AgentReport(
        agent_name=name,
        severity=severity,
        summary=summary,
        details=details or {},
    )


class TestPersonaContextInjection:

    @pytest.mark.unit
    def test_schedule_critical_in_prompt(self):
        ctx = PersonaContext(
            elder_name="张妈妈",
            schedule_critical=["1 次用药已过期未服"],
        )
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "🚨" in prompt
        assert "用药已过期未服" in prompt

    @pytest.mark.unit
    def test_schedule_today_todo_in_prompt(self):
        ctx = PersonaContext(
            elder_name="张妈妈",
            schedule_today_todo=["3 个重要日期临近"],
        )
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "📋" in prompt
        assert "重要日期临近" in prompt

    @pytest.mark.unit
    def test_special_mode_in_prompt(self):
        ctx = PersonaContext(
            elder_name="张妈妈",
            safety_special_mode="bereavement",
        )
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "特殊模式" in prompt
        assert "bereavement" in prompt

    @pytest.mark.unit
    def test_no_extra_when_fields_empty(self):
        """所有 U-R3 字段为 None 时，不应污染 prompt（向后兼容）"""
        ctx = PersonaContext(elder_name="张妈妈")
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "🚨" not in prompt
        assert "📋" not in prompt
        assert "特殊模式" not in prompt

    @pytest.mark.unit
    def test_memory_health_note_in_prompt(self):
        ctx = PersonaContext(
            elder_name="张妈妈",
            memory_health_note="缺关系类记忆",
        )
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "缺关系类记忆" in prompt


class TestCriticalShortCircuit:

    @pytest.mark.unit
    def test_safety_critical_emergency_event_no_llm(self, monkeypatch):
        """safety critical（真实紧急事件）→ 短路不调 LLM"""
        h = Hermes()

        # 5 agent 都用 fake；safety 设 critical（非 silence 而是真事件）
        async def fake_eval(self, user_id, ctx):
            if self.name == "safety":
                return _fake_report("safety", "critical",
                                     "进行中的紧急事件: fall_detected",
                                     details={"alert_id": "x", "type": "fall"})
            return _fake_report(self.name)

        monkeypatch.setattr(
            "app.services.agents.base.BaseAgent.safe_evaluate", fake_eval
        )
        # qwen 应当不被调用
        monkeypatch.setattr(
            "app.services.qwen_service.qwen_service.chat_async",
            lambda *a, **kw: (_ for _ in ()).throw(AssertionError("LLM 不应被调用"))
        )

        rsp = asyncio.run(h.chat(user_id=1, user_message="?", elder_name="妈"))
        assert "紧急" in rsp.text or "察觉到紧急" in rsp.text
        assert rsp.fallback is False  # 短路不算 fallback

    @pytest.mark.unit
    def test_safety_critical_long_silence_uses_gentle_text(self, monkeypatch):
        """safety critical（25h 静默）→ 用关切语，不假说"已通知" """
        h = Hermes()

        async def fake_eval(self, user_id, ctx):
            if self.name == "safety":
                return _fake_report(
                    "safety", "critical",
                    "老人已 26h 没互动",
                    details={"hours_silent": 26, "last_seen": "x"},
                )
            return _fake_report(self.name)

        monkeypatch.setattr(
            "app.services.agents.base.BaseAgent.safe_evaluate", fake_eval
        )

        rsp = asyncio.run(h.chat(user_id=1, user_message="?", elder_name="妈"))
        # 不应包含"已通知"等假报警措辞
        assert "已通知" not in rsp.text
        assert "通知您家人" not in rsp.text
        # 应含关切意味
        assert any(kw in rsp.text for kw in ["陪", "好不好", "还好吗"])

    @pytest.mark.unit
    def test_health_critical_short_circuit(self, monkeypatch):
        """health critical → 短路用预设健康关切语"""
        h = Hermes()

        async def fake_eval(self, user_id, ctx):
            if self.name == "health":
                return _fake_report(
                    "health", "critical",
                    "血压急剧偏高：185/115 mmHg（极高）",
                )
            return _fake_report(self.name)

        monkeypatch.setattr(
            "app.services.agents.base.BaseAgent.safe_evaluate", fake_eval
        )
        # qwen 不应被调用
        monkeypatch.setattr(
            "app.services.qwen_service.qwen_service.chat_async",
            lambda *a, **kw: (_ for _ in ()).throw(AssertionError("LLM 不应被调用"))
        )

        rsp = asyncio.run(h.chat(user_id=1, user_message="?", elder_name="妈"))
        # 必须包含关切 + 引导联系医生 / 家人
        assert "医生" in rsp.text or "家人" in rsp.text
        assert "185" in rsp.text  # 体现具体数字（来自 agent summary）
        assert rsp.fallback is False


class TestAgentSignalIntegration:

    @pytest.mark.unit
    def test_hermes_passes_all_5_agent_signals_to_persona(self, monkeypatch):
        """5 个 agent 的关键 details 都应传到 PersonaContext"""
        h = Hermes()

        async def fake_eval(self, user_id, ctx):
            if self.name == "memory":
                return _fake_report("memory", "info", "x", details={
                    "recent_mood": "happy",
                    "memory_health": {"note": "缺关系类记忆"},
                })
            if self.name == "schedule":
                return _fake_report("schedule", "info", "x", details={
                    "today_todo": ["1 次用药即将到点"],
                    "critical_alerts": ["1 次过期未服"],
                })
            if self.name == "safety":
                return _fake_report("safety", "info", "x", details={
                    "mode": "bereavement",  # 注意此处不是 critical 故不会短路
                })
            return _fake_report(self.name, "info", "ok")

        monkeypatch.setattr(
            "app.services.agents.base.BaseAgent.safe_evaluate", fake_eval
        )

        captured: dict = {}

        async def fake_qwen(*args, **kwargs):
            captured["system_prompt"] = kwargs.get("system_prompt", "")
            return "好咯，我陪着您"

        monkeypatch.setattr(
            "app.services.qwen_service.qwen_service.chat_async", fake_qwen
        )

        asyncio.run(h.chat(user_id=1, user_message="今天好闷", elder_name="张妈妈"))

        prompt = captured.get("system_prompt", "")
        # 5 个关键信号都应在 prompt 中
        assert "happy" in prompt  # mood
        assert "缺关系类记忆" in prompt  # memory health note
        assert "用药即将到点" in prompt  # schedule todo
        assert "过期未服" in prompt  # schedule critical
        assert "bereavement" in prompt  # safety special mode
