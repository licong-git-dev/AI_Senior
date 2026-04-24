"""单元测试 · Anxinbao Persona（Phase 1 数字生命陪伴）"""
import pytest

from app.services.persona import (
    ANXINBAO_PERSONA,
    PersonaConfig,
    PersonaContext,
    build_system_prompt,
    get_persona_summary,
)


class TestPersonaConfig:
    """PersonaConfig 不可变性 + 关键字段"""

    @pytest.mark.unit
    def test_persona_is_frozen(self):
        """frozen dataclass：杜绝运行时被 prompt injection 改写"""
        with pytest.raises(Exception):  # FrozenInstanceError
            ANXINBAO_PERSONA.warmth = 0.1  # type: ignore

    @pytest.mark.unit
    def test_persona_critical_fields(self):
        """关键不变量：名字 / 方言 / 性格 必须在合理范围"""
        assert ANXINBAO_PERSONA.name == "安心宝"
        assert ANXINBAO_PERSONA.accent == "wuhan"
        assert 0 <= ANXINBAO_PERSONA.warmth <= 1
        assert ANXINBAO_PERSONA.patience >= 0.9  # 老人需要极高耐心

    @pytest.mark.unit
    def test_must_not_say_includes_ai_disclosure(self):
        """禁忌库必须含 '我是 AI' —— 否则破坏沉浸感"""
        joined = " ".join(ANXINBAO_PERSONA.must_not_say)
        assert "AI" in joined or "机器人" in joined

    @pytest.mark.unit
    def test_must_not_say_blocks_commercial_push(self):
        """禁忌库必须禁止主动推销"""
        joined = " ".join(ANXINBAO_PERSONA.must_not_say)
        assert "订阅" in joined or "升级" in joined or "付费" in joined

    @pytest.mark.unit
    def test_taboos_includes_family_negativity(self):
        """禁谈话题必须含'对家庭成员的负面评价'"""
        joined = " ".join(ANXINBAO_PERSONA.taboos)
        assert "负面" in joined or "评价" in joined


class TestSystemPromptBuild:
    """system prompt 构造正确性 + 体积"""

    @pytest.mark.unit
    def test_prompt_under_token_budget(self):
        """system prompt 不应超过 1500 字符（≈ 800 token）"""
        ctx = PersonaContext(elder_name="张妈妈")
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert len(prompt) < 1500, f"prompt 太长: {len(prompt)} chars"

    @pytest.mark.unit
    def test_prompt_includes_persona_name(self):
        ctx = PersonaContext()
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "安心宝" in prompt

    @pytest.mark.unit
    def test_prompt_includes_dialect(self):
        ctx = PersonaContext(elder_dialect="wuhan")
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "wuhan" in prompt or "武汉" in prompt or "方言" in prompt

    @pytest.mark.unit
    def test_prompt_includes_elder_name(self):
        ctx = PersonaContext(elder_name="李婆婆")
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "李婆婆" in prompt

    @pytest.mark.unit
    def test_prompt_includes_must_not_say(self):
        """system prompt 必须把 must_not_say 注入 LLM 视野"""
        ctx = PersonaContext()
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        # 至少一条禁语应进 prompt
        any_present = any(rule in prompt for rule in ANXINBAO_PERSONA.must_not_say)
        assert any_present

    @pytest.mark.unit
    def test_prompt_with_mood_context(self):
        ctx = PersonaContext(elder_mood_recent="lonely")
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert "lonely" in prompt

    @pytest.mark.unit
    def test_prompt_handles_empty_context(self):
        """所有 ctx 字段 None 时仍能构造（不抛异常）"""
        ctx = PersonaContext()
        prompt = build_system_prompt(ANXINBAO_PERSONA, ctx)
        assert len(prompt) > 100


class TestPersonaSummary:
    @pytest.mark.unit
    def test_summary_structure(self):
        s = get_persona_summary()
        assert "name" in s
        assert "personality" in s
        assert "catchphrases" in s
        assert "taboos" in s
        assert s["personality"]["warmth"] == ANXINBAO_PERSONA.warmth
