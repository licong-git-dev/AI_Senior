"""单元测试 · companion_tools（工具池注册 + 安全分级 + 调度）"""
import pytest

from app.services.companion_tools import (
    SafetyLevel,
    dispatch,
    list_tools,
    requires_confirmation,
    safety_level,
)


class TestToolRegistry:

    @pytest.mark.unit
    def test_tools_registered(self):
        tools = list_tools()
        names = {t["name"] for t in tools}
        # Phase 1 必须有的 5 个 LOW 级 + 关键 CRITICAL
        assert "log_medication_taken" in names
        assert "log_meal" in names
        assert "log_mood" in names
        assert "save_memory" in names
        assert "query_health_trend" in names
        assert "trigger_sos" in names

    @pytest.mark.unit
    def test_tool_has_input_schema(self):
        for t in list_tools():
            assert "input_schema" in t
            assert t["input_schema"].get("type") == "object"

    @pytest.mark.unit
    def test_tool_has_safety_level(self):
        for t in list_tools():
            assert t["safety_level"] in {"low", "medium", "high", "critical"}


class TestSafetyLevelDistribution:
    """关键安全：高敏感工具必须标记为 HIGH/CRITICAL"""

    @pytest.mark.unit
    def test_sos_is_critical(self):
        assert safety_level("trigger_sos") == "critical"

    @pytest.mark.unit
    def test_health_advice_is_high(self):
        """健康建议必须 HIGH —— 强制走规则引擎，不能 LLM 直答"""
        assert safety_level("request_health_advice") == "high"

    @pytest.mark.unit
    def test_video_call_requires_confirmation(self):
        """视频通话涉资源，应 medium 触发确认"""
        assert requires_confirmation("video_call_family") is True

    @pytest.mark.unit
    def test_log_mood_low(self):
        """log_mood 是低敏感记录，可直接执行"""
        assert safety_level("log_mood") == "low"
        assert requires_confirmation("log_mood") is False


class TestDispatch:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self):
        result = await dispatch("nonexistent_tool", user_id=1, params={})
        assert result["ok"] is False
        assert "unknown tool" in result["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_dispatch_save_memory(self, monkeypatch):
        """save_memory 工具应当真把数据写入记忆引擎"""
        # 用临时 DB 隔离
        import os, tempfile
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        monkeypatch.setenv("COMPANION_MEMORY_DB", path)
        # 重置全局单例使其用新 DB
        import app.services.memory_engine as me
        me._engine = None

        result = await dispatch(
            "save_memory",
            user_id=999,
            params={
                "type": "fact",
                "content": "测试事实",
                "keywords": ["测试"],
            },
        )
        assert result["ok"] is True
        assert "memory_id" in result["result"]

        os.unlink(path)
