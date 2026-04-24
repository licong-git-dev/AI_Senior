"""单元测试 · Phase 3 工具调用安全网关（confirm_token 二次确认 + 消费 + 过期）"""
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from app.services.proactive_engagement import ProactiveStore


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db", prefix="safegate_test_")
    os.close(fd)
    yield ProactiveStore(db_path=path)
    try:
        os.unlink(path)
    except OSError:
        pass


class TestPendingConfirmations:

    @pytest.mark.unit
    def test_create_and_fetch(self, store):
        cid = store.create_confirmation(
            user_id=1,
            tool_name="video_call_family",
            params={"family_member_id": "fam_123"},
            safety_level="medium",
        )
        assert cid.startswith("conf_")
        pending = store.get_confirmation(cid, user_id=1)
        assert pending is not None
        assert pending["tool_name"] == "video_call_family"
        assert pending["params"]["family_member_id"] == "fam_123"
        assert pending["safety_level"] == "medium"

    @pytest.mark.unit
    def test_cross_user_cannot_fetch(self, store):
        cid = store.create_confirmation(
            user_id=1, tool_name="t", params={}, safety_level="medium",
        )
        # 用户 2 不能拿到用户 1 的 confirm
        assert store.get_confirmation(cid, user_id=2) is None

    @pytest.mark.unit
    def test_consume_single_use(self, store):
        cid = store.create_confirmation(
            user_id=1, tool_name="t", params={}, safety_level="medium",
        )
        # 第一次消费成功
        assert store.consume_confirmation(cid, user_id=1) is True
        # 第二次消费失败（已消费）
        assert store.consume_confirmation(cid, user_id=1) is False
        # 消费后 get 也应失败
        assert store.get_confirmation(cid, user_id=1) is None

    @pytest.mark.unit
    def test_cross_user_cannot_consume(self, store):
        cid = store.create_confirmation(
            user_id=1, tool_name="t", params={}, safety_level="critical",
        )
        # 用户 2 不能消费
        assert store.consume_confirmation(cid, user_id=2) is False
        # 用户 1 自己能消费
        assert store.consume_confirmation(cid, user_id=1) is True

    @pytest.mark.unit
    def test_expired_confirmation(self, store):
        """ttl 过期后 get 应返回 None"""
        # ttl=0 应立刻过期
        cid = store.create_confirmation(
            user_id=1, tool_name="t", params={}, safety_level="medium",
            ttl_seconds=0,
        )
        # 给一点时间让过期判断生效
        import time
        time.sleep(0.01)
        assert store.get_confirmation(cid, user_id=1) is None

    @pytest.mark.unit
    def test_list_pending(self, store):
        store.create_confirmation(user_id=1, tool_name="a", params={}, safety_level="medium")
        store.create_confirmation(user_id=1, tool_name="b", params={}, safety_level="critical")
        store.create_confirmation(user_id=2, tool_name="c", params={}, safety_level="medium")

        items_1 = store.list_pending_confirmations(user_id=1)
        items_2 = store.list_pending_confirmations(user_id=2)
        assert len(items_1) == 2
        assert len(items_2) == 1
        names_1 = {x["tool_name"] for x in items_1}
        assert names_1 == {"a", "b"}


class TestPushProactiveConfig:

    @pytest.mark.unit
    def test_default_push_enabled(self, store):
        cfg = store.get_dnd(user_id=1)
        # 新老人默认启用推送
        assert bool(cfg.get("push_proactive", True)) is True

    @pytest.mark.unit
    def test_upsert_push_proactive(self, store):
        cfg = store.upsert_dnd(user_id=1, push_proactive=False)
        assert int(cfg["push_proactive"]) == 0
        # 再次 upsert 其他字段不应覆盖 push_proactive
        cfg2 = store.upsert_dnd(user_id=1, dnd_start="20:00")
        assert int(cfg2["push_proactive"]) == 0
