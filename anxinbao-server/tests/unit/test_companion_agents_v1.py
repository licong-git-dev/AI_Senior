"""单元测试 · Phase 4 第 1 轮 · HealthAgent / SocialAgent / SafetyAgent V1"""
import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import (
    AuditLog,
    Base,
    Conversation,
    FamilyMember,
    HealthRecord,
    User,
    UserAuth,
)
from app.services.agents.health_agent import HealthAgent, THRESHOLDS
from app.services.agents.safety_agent import SafetyAgent
from app.services.agents.social_agent import SocialAgent


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    # 关键：让 agent 内部 import 的 SessionLocal 用同一个 engine
    import app.models.database as dbmod
    original = dbmod.SessionLocal
    dbmod.SessionLocal = SessionLocal

    yield SessionLocal()
    dbmod.SessionLocal = original
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mama(db):
    u = User(name="妈妈", dialect="wuhan")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _add_bp(db, user_id, sys, dia, days_ago=0):
    db.add(HealthRecord(
        user_id=user_id,
        record_type="blood_pressure",
        value_primary=sys,
        value_secondary=dia,
        measured_at=datetime.now() - timedelta(days=days_ago),
    ))
    db.commit()


class TestHealthAgentV1:

    @pytest.mark.unit
    def test_no_data_returns_info(self, db, mama):
        agent = HealthAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert "无健康数据" in rpt.summary
        assert rpt.details["records_count"] == 0

    @pytest.mark.unit
    def test_normal_bp_no_anomaly(self, db, mama):
        for d in range(0, 4):
            _add_bp(db, mama.id, sys=120, dia=80, days_ago=d)
        agent = HealthAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert "正常" in rpt.summary

    @pytest.mark.unit
    def test_continuous_high_bp_warning(self, db, mama):
        # 4 次连续偏高
        for d in range(0, 4):
            _add_bp(db, mama.id, sys=145, dia=92, days_ago=d)
        agent = HealthAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "warning"
        assert "偏高" in rpt.summary
        assert any("医生" in s for s in rpt.suggested_actions)

    @pytest.mark.unit
    def test_extreme_bp_critical(self, db, mama):
        _add_bp(db, mama.id, sys=185, dia=115, days_ago=0)
        _add_bp(db, mama.id, sys=130, dia=85, days_ago=1)
        _add_bp(db, mama.id, sys=128, dia=82, days_ago=2)
        agent = HealthAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "critical"
        assert "急剧偏高" in rpt.summary or "极高" in rpt.summary


class TestSocialAgentV1:

    @pytest.mark.unit
    def test_no_family_returns_info(self, db, mama):
        agent = SocialAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert "尚未绑定家属" in rpt.summary
        assert any("邀请" in s for s in rpt.suggested_actions)

    @pytest.mark.unit
    def test_active_family_returns_info(self, db, mama):
        # 添加家属 + 对应 UserAuth + 最近 audit
        fm = FamilyMember(user_id=mama.id, name="小军", phone="13800001000", is_primary=True)
        db.add(fm)
        ua = UserAuth(username="13800001000", password_hash="x", role="family")
        db.add(ua)
        db.commit()
        db.add(AuditLog(
            user_id=str(ua.id),
            action="login",
            created_at=datetime.now() - timedelta(hours=2),
        ))
        db.commit()

        agent = SocialAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert rpt.details["active_recent"] == 1
        assert rpt.details["silent_critical"] == 0

    @pytest.mark.unit
    def test_silent_family_warns(self, db, mama):
        # 家属 30+ 天没活动
        fm = FamilyMember(user_id=mama.id, name="小军", phone="13800001000", is_primary=True)
        db.add(fm)
        ua = UserAuth(username="13800001000", password_hash="x", role="family")
        db.add(ua)
        db.commit()
        # 没加 audit log → 视为长期静默
        agent = SocialAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "warning"
        assert rpt.details["silent_critical"] == 1


class TestSafetyAgentV1:

    @pytest.mark.unit
    def test_no_conversations_first_time(self, db, mama):
        agent = SafetyAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert "首次" in rpt.summary or "尚无" in rpt.summary

    @pytest.mark.unit
    def test_recent_chat_returns_info(self, db, mama):
        db.add(Conversation(
            user_id=mama.id,
            session_id="s1",
            role="user",
            content="今天天气真好",
            created_at=datetime.now() - timedelta(minutes=30),
        ))
        db.commit()

        agent = SafetyAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert "活跃" in rpt.summary

    @pytest.mark.unit
    def test_silent_5h_warning(self, db, mama):
        db.add(Conversation(
            user_id=mama.id,
            session_id="s1",
            role="user",
            content="x",
            created_at=datetime.now() - timedelta(hours=5),
        ))
        db.commit()

        agent = SafetyAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "warning"

    @pytest.mark.unit
    def test_silent_25h_critical(self, db, mama):
        db.add(Conversation(
            user_id=mama.id,
            session_id="s1",
            role="user",
            content="x",
            created_at=datetime.now() - timedelta(hours=25),
        ))
        db.commit()

        agent = SafetyAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "critical"
        assert "没互动" in rpt.summary

    @pytest.mark.unit
    def test_safe_evaluate_swallows_exceptions(self, db, mama):
        """异常应被 safe_evaluate 兜底"""
        class BoomAgent(SafetyAgent):
            async def evaluate(self, user_id, context):
                raise RuntimeError("boom")

        agent = BoomAgent()
        rpt = asyncio.run(agent.safe_evaluate(mama.id, {}))
        assert rpt.severity == "error"
        assert "异常" in rpt.summary
