"""单元测试 · Companion Onboarding · 3 句话激活 + D1/D3/D7 (r26)"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base, User
from app.services.companion_onboarding_service import (
    ActivationScript,
    DEFAULT_ADDRESSED_AS,
    FollowUpScript,
    companion_onboarding_service,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mama_full(db):
    """字段填全的老人"""
    u = User(
        name="测试老人",
        dialect="wuhan",
        family_name="张",
        addressed_as="妈",
        closest_child_name="小军",
        favorite_tv_show="中央 1 套 19:00 新闻联播",
        health_focus="高血压",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def mama_minimal(db):
    """字段全缺的老人 → 走兜底"""
    u = User(name="测试老人", dialect="mandarin")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ===== 3 句话激活脚本 =====


class TestActivationScript:

    @pytest.mark.unit
    def test_full_fields_hit_personal(self, db, mama_full):
        s = companion_onboarding_service.generate_activation_script(db, mama_full.id)
        assert "张妈" in s.line_1
        assert "小军" in s.line_1
        assert "唠两句" in s.line_1
        # 健康关注点应嵌入第 2 句
        assert "血压" in s.line_2
        # 第 2 句应含电视节目
        assert "新闻联播" in s.line_2
        # 第 3 句必含操作权
        assert "绿色" in s.line_3
        assert "红色" in s.line_3
        # 总长度合理（30 秒 ≈ 90 字）
        assert 30 <= len(s.line_1 + s.line_2 + s.line_3) <= 250

    @pytest.mark.unit
    def test_minimal_fields_fallback_gracefully(self, db, mama_minimal):
        s = companion_onboarding_service.generate_activation_script(db, mama_minimal.id)
        # 应该用 mandarin 默认称呼"您"
        assert s.dialect == "mandarin"
        # 不应有空字段插入
        assert "{" not in s.line_1
        assert "{" not in s.line_2
        # 第 3 句结构稳定
        assert "您" in s.line_3

    @pytest.mark.unit
    def test_dialect_words_mandarin(self, db, mama_minimal):
        s = companion_onboarding_service.generate_activation_script(db, mama_minimal.id)
        # mandarin 应该用"陪您聊聊"而不是"唠两句"
        assert "唠两句" not in s.line_1

    @pytest.mark.unit
    def test_dialect_words_wuhan(self, db, mama_full):
        s = companion_onboarding_service.generate_activation_script(db, mama_full.id)
        # wuhan 应保留"唠两句"
        assert "唠两句" in s.line_1
        assert "晓得" in s.line_2  # 武汉话特征词

    @pytest.mark.unit
    def test_user_not_found_returns_fallback(self, db):
        s = companion_onboarding_service.generate_activation_script(db, 99999)
        assert isinstance(s, ActivationScript)
        assert s.line_1 and s.line_2 and s.line_3

    @pytest.mark.unit
    def test_weather_injection(self, db, mama_full):
        s = companion_onboarding_service.generate_activation_script(
            db, mama_full.id, weather_desc="阵雨",
        )
        assert "阵雨" in s.line_2

    @pytest.mark.unit
    def test_full_text_concat(self, db, mama_full):
        s = companion_onboarding_service.generate_activation_script(db, mama_full.id)
        full = s.as_full_text()
        assert s.line_1 in full
        assert s.line_2 in full
        assert s.line_3 in full


# ===== mark_onboarded 幂等 =====


class TestMarkOnboarded:

    @pytest.mark.unit
    def test_first_call_sets_timestamp(self, db, mama_full):
        assert not companion_onboarding_service.is_onboarded(db, mama_full.id)
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        assert companion_onboarding_service.is_onboarded(db, mama_full.id)

    @pytest.mark.unit
    def test_second_call_idempotent(self, db, mama_full):
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        first_at = db.query(User).get(mama_full.id).onboarded_at
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        # 不应被覆盖
        assert db.query(User).get(mama_full.id).onboarded_at == first_at


# ===== D1/D3/D7 唤回 =====


class TestFollowup:

    @pytest.mark.unit
    def test_followup_blocked_when_not_onboarded(self, db, mama_full):
        s = companion_onboarding_service.generate_followup(db, mama_full.id, 1)
        assert s is None

    @pytest.mark.unit
    def test_d1_morning_recall(self, db, mama_full):
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        s = companion_onboarding_service.generate_followup(db, mama_full.id, 1)
        assert s is not None
        assert s.day_offset == 1
        assert s.trigger_type == "morning_recall"
        assert "小军" in s.text
        assert "张妈" in s.text

    @pytest.mark.unit
    def test_d3_memory_followup_no_memory(self, db, mama_full):
        """无 EVENT/PREFERENCE 记忆时降级"""
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        s = companion_onboarding_service.generate_followup(db, mama_full.id, 3)
        assert s is not None
        assert "三天" in s.text or "认识" in s.text

    @pytest.mark.unit
    def test_d7_weekly_summary(self, db, mama_full):
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        s = companion_onboarding_service.generate_followup(db, mama_full.id, 7)
        assert s is not None
        assert "一周" in s.text
        assert "小军" in s.text

    @pytest.mark.unit
    def test_d1_idempotent(self, db, mama_full):
        """同一 day 不重复触发"""
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        s1 = companion_onboarding_service.generate_followup(db, mama_full.id, 1)
        s2 = companion_onboarding_service.generate_followup(db, mama_full.id, 1)
        assert s1 is not None
        assert s2 is None  # 已触发过

    @pytest.mark.unit
    def test_invalid_day_offset(self, db, mama_full):
        companion_onboarding_service.mark_onboarded(db, mama_full.id)
        for invalid in (0, 2, 4, 5, 6, 8, 10):
            assert companion_onboarding_service.generate_followup(
                db, mama_full.id, invalid
            ) is None
