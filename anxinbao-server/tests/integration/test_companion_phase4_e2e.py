"""
Phase 4 端到端集成测试（U-R3 完结）

完整链路：
  老人发消息
  → 5 agent 并行评估真实 DB
  → critical 短路 / 否则继续
  → 召回长期记忆
  → PersonaContext 注入 system prompt
  → mock LLM 返回回复
  → MemoryConsolidator 异步触发

不启动 uvicorn，全部用 in-process TestClient + 临时 SQLite。
"""
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
    AuditLog,
    Base,
    Conversation,
    FamilyMember,
    HealthRecord,
    Medication,
    MedicationRecord,
    User,
    UserAuth,
)
from app.services.agents.hermes import Hermes
from app.services.memory_engine import (
    MemoryEngine,
    MemoryRecord,
    MemoryType,
    MemoryVisibility,
)


# ===== Fixtures =====


@pytest.fixture
def db():
    """临时 SQLite + monkeypatch SessionLocal 让所有 agent 都用它"""
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
    fd, path = tempfile.mkstemp(suffix=".db", prefix="phase4_e2e_")
    os.close(fd)
    eng = MemoryEngine(db_path=path)
    import app.services.memory_engine as me
    original = me._engine
    me._engine = eng
    yield eng
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


@pytest.fixture
def mock_llm(monkeypatch):
    """捕获 LLM 调用并记录 system_prompt"""
    captured = {}

    async def fake_qwen(*args, **kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt", "")
        captured["message"] = kwargs.get("message", "") or (args[1] if len(args) > 1 else "")
        return "嗯，您讲，我陪您。"

    monkeypatch.setattr(
        "app.services.qwen_service.qwen_service.chat_async", fake_qwen
    )
    return captured


@pytest.fixture
def mock_consolidator(monkeypatch):
    """禁用真实 consolidator 避免触发 LLM"""
    called = {"n": 0}

    def fake_schedule(user_id, message):
        called["n"] += 1

    monkeypatch.setattr(
        "app.services.memory_consolidator.schedule_consolidation", fake_schedule
    )
    return called


# ===== E2E 场景 =====


class TestPhase4Happy:

    @pytest.mark.integration
    def test_normal_chat_full_flow(
        self, db, mama, isolated_memory_engine, mock_llm, mock_consolidator,
    ):
        """正常对话：5 agent → memory recall → LLM → consolidator"""
        # 准备：先写一些 mood / event 让 agent 有数据
        isolated_memory_engine.save(MemoryRecord(
            user_id=mama.id, type=MemoryType.MOOD,
            content="今天蛮开心，跟孙子玩",
            visibility=MemoryVisibility.SELF_ONLY,
        ))

        h = Hermes()
        rsp = asyncio.run(h.chat(
            user_id=mama.id,
            user_message="今天天气好，想出门走走",
            elder_name="妈妈",
            dialect="wuhan",
        ))

        # 1) agent 全 5 个都汇报了
        assert len(rsp.agent_reports) == 5
        names = {r.agent_name for r in rsp.agent_reports}
        assert names == {"health", "social", "memory", "safety", "schedule"}

        # 2) LLM 被调用
        assert mock_llm.get("system_prompt"), "LLM 应被调用"

        # 3) consolidator 被触发
        assert mock_consolidator["n"] == 1

        # 4) 回复非空 + fallback=False
        assert rsp.text
        assert rsp.fallback is False


class TestPhase4CriticalShortCircuit:

    @pytest.mark.integration
    def test_health_critical_skips_llm(
        self, db, mama, isolated_memory_engine, mock_llm, mock_consolidator,
    ):
        """高血压极端值 → HealthAgent critical → 短路不调 LLM"""
        # 写 BP 185/115（critical 阈值）
        db.add(HealthRecord(
            user_id=mama.id,
            record_type="blood_pressure",
            value_primary=185,
            value_secondary=115,
            measured_at=datetime.now(),
        ))
        # 至少 3 条样本（阈值要求）
        for d in (1, 2):
            db.add(HealthRecord(
                user_id=mama.id,
                record_type="blood_pressure",
                value_primary=130,
                value_secondary=85,
                measured_at=datetime.now() - timedelta(days=d),
            ))
        db.commit()

        h = Hermes()
        rsp = asyncio.run(h.chat(
            user_id=mama.id,
            user_message="头有点晕",
            elder_name="妈妈",
            dialect="wuhan",
        ))

        # LLM 不应被调用（短路）
        assert "system_prompt" not in mock_llm
        # 回复必含医生/家人引导
        assert "医生" in rsp.text or "家人" in rsp.text
        # consolidator 短路时不触发
        assert mock_consolidator["n"] == 0

    @pytest.mark.integration
    def test_long_silence_gentle_text(
        self, db, mama, isolated_memory_engine, mock_llm, mock_consolidator,
    ):
        """26h 静默 → SafetyAgent critical → 关切语，不假说已通知"""
        # 上一条对话 26h 前
        db.add(Conversation(
            user_id=mama.id,
            session_id="s1",
            role="user",
            content="x",
            created_at=datetime.now() - timedelta(hours=26),
        ))
        db.commit()

        h = Hermes()
        rsp = asyncio.run(h.chat(
            user_id=mama.id,
            user_message="?",
            elder_name="妈妈",
            dialect="wuhan",
        ))
        assert "已通知" not in rsp.text
        assert any(kw in rsp.text for kw in ["陪", "好不好", "还好吗"])
        # LLM 短路
        assert "system_prompt" not in mock_llm


class TestPhase4PersonaInjection:

    @pytest.mark.integration
    def test_overdue_medication_appears_in_prompt(
        self, db, mama, isolated_memory_engine, mock_llm, mock_consolidator,
    ):
        """用药超时 → ScheduleAgent → 注入 prompt"""
        med = Medication(user_id=mama.id, name="降压药", dosage="1 片",
                          frequency="daily", status="active")
        db.add(med)
        db.commit()
        db.add(MedicationRecord(
            user_id=mama.id,
            medication_id=med.id,
            scheduled_time=datetime.now() - timedelta(minutes=90),
            status="pending",
        ))
        db.commit()

        h = Hermes()
        rsp = asyncio.run(h.chat(
            user_id=mama.id,
            user_message="今天该做啥",
            elder_name="妈妈",
            dialect="wuhan",
        ))

        prompt = mock_llm.get("system_prompt", "")
        # ScheduleAgent critical 应进 prompt
        assert "🚨" in prompt
        assert "用药" in prompt
