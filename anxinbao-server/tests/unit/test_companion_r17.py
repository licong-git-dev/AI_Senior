"""r17 单测 · LifeMomentTrigger + LIFE_STORY 记忆类型 + special_mode"""
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from app.services.companion_triggers import LifeMomentTrigger
from app.services.memory_engine import (
    MemoryEngine,
    MemoryRecord,
    MemoryType,
    MemoryVisibility,
)
from app.services.proactive_engagement import ProactiveStore


# ============ LIFE_STORY 记忆类型 ============


@pytest.fixture
def engine():
    fd, path = tempfile.mkstemp(suffix=".db", prefix="r17_mem_")
    os.close(fd)
    yield MemoryEngine(db_path=path)
    try:
        os.unlink(path)
    except OSError:
        pass


class TestLifeStoryMemoryType:

    @pytest.mark.unit
    def test_life_story_enum_exists(self):
        assert MemoryType.LIFE_STORY.value == "life_story"

    @pytest.mark.unit
    def test_life_story_not_in_default_recall(self, engine):
        """LIFE_STORY 不参与对话召回，避免老人讲过的话被反复喂回去"""
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.LIFE_STORY,
            content="我年轻时的故事：追到了您爷爷",
            keywords=["爷爷"],
        ))
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.FACT,
            content="爷爷是军人", keywords=["爷爷"],
        ))
        # 普通召回不应返回 LIFE_STORY
        items = engine.recall(user_id=1, query="爷爷")
        assert len(items) == 1
        assert items[0].type == MemoryType.FACT

    @pytest.mark.unit
    def test_life_story_explicit_recall(self, engine):
        """显式传 types=[LIFE_STORY] 时才能召回"""
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.LIFE_STORY,
            content="人生故事 A",
        ))
        # 显式指定
        items = engine.recall(user_id=1, types=[MemoryType.LIFE_STORY])
        assert len(items) == 1


# ============ LifeMomentTrigger ============


class TestLifeMomentTrigger:

    @pytest.mark.unit
    def test_no_events_no_fire(self, engine, monkeypatch):
        """没有 EVENT 记忆时，trigger 不 fired"""
        monkeypatch.setattr(
            "app.services.memory_engine._engine",
            engine,
            raising=False,
        )
        # 用 mock：让 trigger 读的 engine 就是 fixture engine
        from app.services import memory_engine as me
        original = me._engine
        me._engine = engine
        try:
            trigger = LifeMomentTrigger()
            ev = trigger.evaluate(user_id=999, context={"now": datetime.now()})
            assert ev.fired is False
        finally:
            me._engine = original

    @pytest.mark.unit
    def test_birthday_today_fires_priority_9(self, engine):
        """老人本人生日当天应 fired，优先级 9（突破 DND）"""
        now = datetime(2026, 4, 24, 10, 0)
        birthday_today = datetime(1955, 4, 24)  # 71 岁生日今天
        engine.save(MemoryRecord(
            user_id=1,
            type=MemoryType.EVENT,
            content="我生日",
            occurred_at=birthday_today.isoformat(),
        ))
        # 绑定全局单例
        from app.services import memory_engine as me
        original = me._engine
        me._engine = engine
        try:
            trigger = LifeMomentTrigger()
            ev = trigger.evaluate(user_id=1, context={"now": now})
            assert ev.fired is True
            assert ev.priority == 9  # 自己生日最高
            assert "+0d" in ev.reason or "-0d" in ev.reason
        finally:
            me._engine = original

    @pytest.mark.unit
    def test_grandchild_birthday_priority_7(self, engine):
        now = datetime(2026, 4, 24, 10, 0)
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.EVENT,
            content="孙子生日",
            occurred_at=datetime(2012, 4, 24).isoformat(),
        ))
        from app.services import memory_engine as me
        original = me._engine
        me._engine = engine
        try:
            trigger = LifeMomentTrigger()
            ev = trigger.evaluate(user_id=1, context={"now": now})
            assert ev.fired is True
            assert ev.priority == 7
        finally:
            me._engine = original

    @pytest.mark.unit
    def test_event_far_away_no_fire(self, engine):
        """事件距今 >3 天 → 不 fired"""
        now = datetime(2026, 4, 24)
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.EVENT,
            content="我生日",
            occurred_at=datetime(1955, 8, 15).isoformat(),  # 4 个月后
        ))
        from app.services import memory_engine as me
        original = me._engine
        me._engine = engine
        try:
            trigger = LifeMomentTrigger()
            ev = trigger.evaluate(user_id=1, context={"now": now})
            assert ev.fired is False
        finally:
            me._engine = original


# ============ Special Mode（crisis/bereavement/hospital）============


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db", prefix="r17_proa_")
    os.close(fd)
    yield ProactiveStore(db_path=path)
    try:
        os.unlink(path)
    except OSError:
        pass


class TestSpecialMode:

    @pytest.mark.unit
    def test_default_special_mode_is_none(self, store):
        cfg = store.get_dnd(user_id=1)
        assert cfg.get("special_mode") in (None, "normal")

    @pytest.mark.unit
    def test_set_bereavement_mode(self, store):
        cfg = store.upsert_dnd(user_id=1, special_mode="bereavement")
        assert cfg["special_mode"] == "bereavement"
        assert cfg["special_mode_started_at"] is not None

    @pytest.mark.unit
    def test_set_crisis_mode(self, store):
        cfg = store.upsert_dnd(user_id=1, special_mode="crisis")
        assert cfg["special_mode"] == "crisis"

    @pytest.mark.unit
    def test_mode_transitions_preserve_other_fields(self, store):
        """切换 special_mode 时，DND 时段等不应被覆盖"""
        store.upsert_dnd(user_id=1, dnd_start="23:00")
        cfg = store.upsert_dnd(user_id=1, special_mode="hospital")
        assert cfg["dnd_start"] == "23:00"
        assert cfg["special_mode"] == "hospital"

    @pytest.mark.unit
    def test_mode_revert_to_normal(self, store):
        store.upsert_dnd(user_id=1, special_mode="bereavement")
        cfg = store.upsert_dnd(user_id=1, special_mode="normal")
        assert cfg["special_mode"] == "normal"
