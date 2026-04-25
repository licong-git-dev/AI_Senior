"""单元测试 · Phase 4 第 2 轮 (U-R2) · MemoryAgent V1 + ScheduleAgent V1"""
import asyncio
import os
import tempfile
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.database as dbmod
from app.models.database import (
    Base,
    ExerciseRecord,
    Medication,
    MedicationRecord,
    User,
)
from app.services.agents.memory_agent import MemoryAgent, _classify_mood
from app.services.agents.schedule_agent import ScheduleAgent
from app.services.memory_engine import (
    MemoryEngine,
    MemoryRecord,
    MemoryType,
    MemoryVisibility,
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
    original = dbmod.SessionLocal
    dbmod.SessionLocal = SessionLocal
    yield SessionLocal()
    dbmod.SessionLocal = original
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def isolated_memory_engine(monkeypatch):
    """每个测试独立 SQLite 隔离的 MemoryEngine"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="memengine_test_")
    os.close(fd)
    engine = MemoryEngine(db_path=path)

    import app.services.memory_engine as me
    original = me._engine
    me._engine = engine
    yield engine
    me._engine = original
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def mama(db):
    u = User(name="妈妈", dialect="wuhan")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ===== MemoryAgent =====


class TestMoodClassifier:

    @pytest.mark.unit
    def test_happy(self):
        assert _classify_mood("今天蛮开心，跟孙子玩") == "happy"

    @pytest.mark.unit
    def test_lonely(self):
        assert _classify_mood("一个人在家好寂寞") == "lonely"

    @pytest.mark.unit
    def test_sad(self):
        assert _classify_mood("难过想哭") == "sad"

    @pytest.mark.unit
    def test_anxious(self):
        assert _classify_mood("有点担心血压") == "anxious"

    @pytest.mark.unit
    def test_neutral_default(self):
        assert _classify_mood("今天天气怎么样") == "neutral"


class TestMemoryAgentV1:

    @pytest.mark.unit
    def test_cold_start(self, mama, isolated_memory_engine):
        """无记忆 → cold_start，severity=info"""
        agent = MemoryAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert rpt.details["recent_mood"] == "neutral"
        assert rpt.details["memory_health"]["status"] == "cold_start"

    @pytest.mark.unit
    def test_dominant_mood_lonely_warning(self, mama, isolated_memory_engine):
        """连续多条 lonely → warning"""
        for content in ["一个人想伢", "好寂寞", "想孩子了"]:
            isolated_memory_engine.save(MemoryRecord(
                user_id=mama.id, type=MemoryType.MOOD,
                content=content, visibility=MemoryVisibility.SELF_ONLY,
            ))
        agent = MemoryAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "warning"
        assert rpt.details["recent_mood"] == "lonely"
        assert rpt.details["mood_sample_size"] == 3

    @pytest.mark.unit
    def test_dominant_mood_happy_info(self, mama, isolated_memory_engine):
        """连续高兴 → info"""
        for content in ["今天蛮开心", "跟孙子笑了", "舒服多了"]:
            isolated_memory_engine.save(MemoryRecord(
                user_id=mama.id, type=MemoryType.MOOD,
                content=content, visibility=MemoryVisibility.SELF_ONLY,
            ))
        agent = MemoryAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert rpt.details["recent_mood"] == "happy"

    @pytest.mark.unit
    def test_health_needs_completion(self, mama, isolated_memory_engine):
        """总量≥10 但缺事实/偏好/关系类 → needs_completion 标志"""
        for i in range(11):
            isolated_memory_engine.save(MemoryRecord(
                user_id=mama.id, type=MemoryType.MOOD,
                content=f"心情记录 {i}", visibility=MemoryVisibility.SELF_ONLY,
            ))
        agent = MemoryAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.details["memory_health"]["status"] == "needs_completion"
        assert rpt.details["memory_health"]["needs_attention"] is True

    @pytest.mark.unit
    def test_privacy_no_content_in_details(self, mama, isolated_memory_engine):
        """details 不应直接暴露记忆原文"""
        secret = "我对老伴非常生气他骂我"
        isolated_memory_engine.save(MemoryRecord(
            user_id=mama.id, type=MemoryType.MOOD,
            content=secret, visibility=MemoryVisibility.SELF_ONLY,
        ))
        agent = MemoryAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        # details 任何字段都不应包含原文
        details_str = str(rpt.details)
        assert secret not in details_str


# ===== ScheduleAgent =====


def _add_med_record(db, user_id, status, scheduled_offset_min):
    """offset_min: 相对 now 的偏移（负数=过去，正数=未来）"""
    med = Medication(user_id=user_id, name="测试药", dosage="1 片",
                      frequency="daily", status="active")
    db.add(med)
    db.commit()
    rec = MedicationRecord(
        user_id=user_id,
        medication_id=med.id,
        scheduled_time=datetime.now() + timedelta(minutes=scheduled_offset_min),
        status=status,
    )
    db.add(rec)
    db.commit()


class TestScheduleAgentV1:

    @pytest.mark.unit
    def test_no_data_returns_info(self, mama):
        """无 medication / exercise / 临近事件 → info '无紧迫日程'"""
        agent = ScheduleAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert "无紧迫日程" in rpt.summary

    @pytest.mark.unit
    def test_overdue_medication_warning(self, db, mama):
        """超时 60+ 分钟未服 → warning"""
        _add_med_record(db, mama.id, "pending", scheduled_offset_min=-90)
        agent = ScheduleAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "warning"
        assert "过期未服" in rpt.summary or "过期" in rpt.summary
        assert rpt.details["medication"]["overdue_count"] >= 1

    @pytest.mark.unit
    def test_upcoming_medication_in_todo(self, db, mama):
        """30 分钟内的服药 → today_todo（info 级）"""
        _add_med_record(db, mama.id, "pending", scheduled_offset_min=15)
        agent = ScheduleAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert rpt.severity == "info"
        assert rpt.details["medication"]["upcoming_count"] == 1
        assert any("即将到点" in a for a in rpt.details["today_todo"])

    @pytest.mark.unit
    def test_long_inactive_exercise_soft_reminder(self, db, mama):
        """5 天没运动 → soft_reminders 含运动提示"""
        ex = ExerciseRecord(
            user_id=mama.id,
            exercise_type="walk",
            duration_minutes=30,
            created_at=datetime.now() - timedelta(days=5),
        )
        db.add(ex)
        db.commit()
        agent = ScheduleAgent()
        rpt = asyncio.run(agent.evaluate(mama.id, {}))
        assert any("没运动" in r for r in rpt.details["soft_reminders"])

    @pytest.mark.unit
    def test_safe_evaluate_swallows(self, mama):
        """异常应被 base.safe_evaluate 兜底"""
        class BoomSchedule(ScheduleAgent):
            async def evaluate(self, user_id, context):
                raise RuntimeError("boom")

        rpt = asyncio.run(BoomSchedule().safe_evaluate(mama.id, {}))
        assert rpt.severity == "error"
