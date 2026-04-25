"""单元测试 · 北极星指标埋点（r20 · T 选项）"""
import pytest

from app.core.north_star_metrics import (
    compute_north_star_view,
    get_local_snapshot,
    record_elder_chat,
    record_family_account_created,
    record_family_invite_accepted,
    record_memory_consolidated,
    record_points_earned,
    record_points_redeemed,
    record_proactive_acked,
    record_proactive_generated,
    reset_local_counters,
)


@pytest.fixture(autouse=True)
def reset_each_test():
    reset_local_counters()
    yield
    reset_local_counters()


class TestRecord:

    @pytest.mark.unit
    def test_record_elder_chat_with_dialect(self):
        record_elder_chat("wuhan")
        record_elder_chat("wuhan")
        record_elder_chat("mandarin")
        snap = get_local_snapshot()
        assert snap.get("elder_active_chat{dialect=wuhan}") == 2
        assert snap.get("elder_active_chat{dialect=mandarin}") == 1

    @pytest.mark.unit
    def test_record_proactive_generated_and_acked(self):
        record_proactive_generated("silence")
        record_proactive_generated("silence")
        record_proactive_generated("festival")
        record_proactive_acked("silence")
        snap = get_local_snapshot()
        assert snap["proactive_generated{trigger_name=silence}"] == 2
        assert snap["proactive_generated{trigger_name=festival}"] == 1
        assert snap["proactive_acked{trigger_name=silence}"] == 1

    @pytest.mark.unit
    def test_record_points_earned_with_amount(self):
        record_points_earned("earn_chat_message", amount=1)
        record_points_earned("earn_chat_message", amount=1)
        record_points_earned("earn_save_memory", amount=3)
        snap = get_local_snapshot()
        assert snap["points_earned{earn_type=earn_chat_message}"] == 2
        assert snap["points_earned{earn_type=earn_save_memory}"] == 3

    @pytest.mark.unit
    def test_record_family_events(self):
        record_family_account_created()
        record_family_account_created()
        record_family_invite_accepted("caretaker")
        record_family_invite_accepted("payer")
        snap = get_local_snapshot()
        assert snap["family_account_created"] == 2
        assert snap["family_invite_accepted{invited_role=caretaker}"] == 1
        assert snap["family_invite_accepted{invited_role=payer}"] == 1

    @pytest.mark.unit
    def test_record_memory_consolidated(self):
        record_memory_consolidated("fact")
        record_memory_consolidated("fact")
        record_memory_consolidated("preference")
        snap = get_local_snapshot()
        assert snap["memory_consolidated{memory_type=fact}"] == 2
        assert snap["memory_consolidated{memory_type=preference}"] == 1


class TestComputeView:

    @pytest.mark.unit
    def test_view_aggregates_correctly(self):
        record_elder_chat("wuhan")
        record_elder_chat("mandarin")
        record_proactive_generated("silence")
        record_proactive_generated("festival")
        record_proactive_acked("silence")
        record_points_earned("earn_chat_message")
        record_points_redeemed("extend_videocall_5min", cost=20)
        record_family_account_created()
        record_family_invite_accepted("caretaker")
        record_memory_consolidated("fact")

        view = compute_north_star_view()
        ns = view["north_star"]
        assert ns["elder_chat_events_total"] == 2
        assert ns["proactive_messages_generated"] == 2
        assert ns["proactive_messages_acked"] == 1
        assert ns["proactive_ack_rate"] == 0.5  # 1/2
        assert ns["companion_points_earned"] == 1
        assert ns["companion_points_redeemed"] == 20
        assert ns["family_accounts_created"] == 1
        assert ns["family_invites_accepted"] == 1
        assert ns["memories_consolidated"] == 1

    @pytest.mark.unit
    def test_ack_rate_zero_when_no_generation(self):
        record_proactive_acked("silence")  # ack 没对应的 generated
        view = compute_north_star_view()
        assert view["north_star"]["proactive_ack_rate"] == 0.0

    @pytest.mark.unit
    def test_view_includes_metadata(self):
        view = compute_north_star_view()
        assert "_note" in view
        assert "_prometheus_available" in view
        assert "north_star" in view
        assert "raw" in view


class TestFailSafe:

    @pytest.mark.unit
    def test_record_with_none_dialect_uses_default(self):
        # 不应抛
        record_elder_chat(None)
        snap = get_local_snapshot()
        assert snap["elder_active_chat{dialect=mandarin}"] == 1
