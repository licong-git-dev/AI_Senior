"""单元测试 · ProactiveEngagement（DND/quota/cooldown 守护）"""
import os
import tempfile
from datetime import datetime

import pytest

from app.services.proactive_engagement import (
    ProactiveMessage,
    ProactiveStore,
    _is_in_dnd,
)


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db", prefix="proactive_test_")
    os.close(fd)
    yield ProactiveStore(db_path=path)
    try:
        os.unlink(path)
    except OSError:
        pass


class TestProactiveStoreCRUD:

    @pytest.mark.unit
    def test_save_and_list(self, store):
        msg = ProactiveMessage(
            user_id=1, trigger_name="silence", text="嘿，您家在忙啥",
            priority=5, reason="3h 无活动",
        )
        new_id = store.save_message(msg)
        assert new_id > 0
        items = store.list_inbox(user_id=1)
        assert len(items) == 1
        assert items[0].text == "嘿，您家在忙啥"

    @pytest.mark.unit
    def test_user_isolation(self, store):
        store.save_message(ProactiveMessage(user_id=1, trigger_name="t", text="a", priority=5))
        store.save_message(ProactiveMessage(user_id=2, trigger_name="t", text="b", priority=5))
        assert len(store.list_inbox(1)) == 1
        assert len(store.list_inbox(2)) == 1
        assert store.list_inbox(1)[0].text == "a"

    @pytest.mark.unit
    def test_mark_delivered(self, store):
        store.save_message(ProactiveMessage(user_id=1, trigger_name="t", text="a", priority=5))
        items = store.list_inbox(1)
        assert items[0].delivered is False
        ok = store.mark_delivered(items[0].id, user_id=1)
        assert ok is True
        # 跨 user 不应能改
        ok = store.mark_delivered(items[0].id, user_id=2)
        assert ok is False

    @pytest.mark.unit
    def test_only_undelivered_filter(self, store):
        store.save_message(ProactiveMessage(user_id=1, trigger_name="t", text="a", priority=5))
        store.save_message(ProactiveMessage(user_id=1, trigger_name="t", text="b", priority=5))
        items = store.list_inbox(1)
        store.mark_delivered(items[0].id, user_id=1)
        undelivered = store.list_inbox(1, only_undelivered=True)
        assert len(undelivered) == 1


class TestDNDConfig:

    @pytest.mark.unit
    def test_default_dnd_config(self, store):
        cfg = store.get_dnd(user_id=999)
        assert cfg["dnd_start"] == "22:00"
        assert cfg["dnd_end"] == "07:00"
        assert cfg["daily_quota"] == 4
        assert cfg["enabled"]

    @pytest.mark.unit
    def test_upsert_dnd(self, store):
        cfg = store.upsert_dnd(user_id=1, dnd_start="21:00", daily_quota=2)
        assert cfg["dnd_start"] == "21:00"
        assert cfg["daily_quota"] == 2
        # 二次 upsert 部分字段
        cfg2 = store.upsert_dnd(user_id=1, dnd_end="06:00")
        assert cfg2["dnd_start"] == "21:00"  # 保留
        assert cfg2["dnd_end"] == "06:00"


class TestIsInDND:

    @pytest.mark.unit
    def test_within_overnight_dnd(self):
        # 23:30 在 22:00-07:00 区间内
        assert _is_in_dnd(datetime(2026, 1, 1, 23, 30), "22:00", "07:00") is True

    @pytest.mark.unit
    def test_morning_within_overnight_dnd(self):
        # 06:00 也在 22:00-07:00 区间内
        assert _is_in_dnd(datetime(2026, 1, 1, 6, 0), "22:00", "07:00") is True

    @pytest.mark.unit
    def test_outside_overnight_dnd(self):
        # 14:00 不在 22:00-07:00 区间
        assert _is_in_dnd(datetime(2026, 1, 1, 14, 0), "22:00", "07:00") is False

    @pytest.mark.unit
    def test_same_day_dnd(self):
        # 14:00-16:00 标准区间
        assert _is_in_dnd(datetime(2026, 1, 1, 15, 0), "14:00", "16:00") is True
        assert _is_in_dnd(datetime(2026, 1, 1, 17, 0), "14:00", "16:00") is False


class TestCooldown:

    @pytest.mark.unit
    def test_no_cooldown_initially(self, store):
        assert store.in_cooldown(user_id=1, trigger_name="silence", hours=4) is False

    @pytest.mark.unit
    def test_cooldown_active_after_record(self, store):
        store.record_cooldown(user_id=1, trigger_name="silence")
        assert store.in_cooldown(user_id=1, trigger_name="silence", hours=4) is True
        # 不同 trigger 不受影响
        assert store.in_cooldown(user_id=1, trigger_name="festival", hours=4) is False


class TestQuotaCount:

    @pytest.mark.unit
    def test_count_today(self, store):
        for _ in range(3):
            store.save_message(ProactiveMessage(
                user_id=1, trigger_name="silence", text="x", priority=5,
            ))
        assert store.count_today(user_id=1) == 3
        # 不同用户隔离
        assert store.count_today(user_id=2) == 0
