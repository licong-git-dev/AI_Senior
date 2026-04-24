"""单元测试 · Companion 情境触发器（Phase 2）"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.companion_triggers import (
    ALL_TRIGGERS,
    FamilyAbsenceTrigger,
    FestivalTrigger,
    HealthAnomalyTrigger,
    MemorialTrigger,
    SilenceTrigger,
    TriggerEvaluation,
    WeatherTrigger,
    evaluate_all,
)


class TestSilenceTrigger:

    @pytest.mark.unit
    def test_silence_fires_after_threshold(self):
        t = SilenceTrigger()
        ctx = {
            "now": datetime(2026, 4, 24, 14, 0),
            "last_activity_at": datetime(2026, 4, 24, 9, 0),  # 5h 前
        }
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is True
        assert "5.0h" in ev.reason or "5h" in ev.reason

    @pytest.mark.unit
    def test_silence_does_not_fire_recent(self):
        t = SilenceTrigger()
        ctx = {
            "now": datetime(2026, 4, 24, 14, 0),
            "last_activity_at": datetime(2026, 4, 24, 13, 30),  # 0.5h 前
        }
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is False

    @pytest.mark.unit
    def test_silence_first_time_user(self):
        """首次使用（last_activity=None）应触发引导"""
        t = SilenceTrigger()
        ctx = {"now": datetime.now(), "last_activity_at": None}
        # 这里会去查 DB；我们假设 DB 也无记录 → 应 fired=True
        # 通过 monkeypatch SessionLocal 来隔离
        with patch("app.models.database.SessionLocal") as mock_session:
            mock_session.return_value.query.return_value.filter.return_value.\
                order_by.return_value.first.return_value = None
            mock_session.return_value.close.return_value = None
            ev = t.evaluate(user_id=999, context={"now": datetime.now()})
            assert ev.fired is True


class TestFestivalTrigger:

    @pytest.mark.unit
    def test_festival_within_window(self):
        t = FestivalTrigger()
        # 2026-09-25 是中秋
        ctx = {"now": datetime(2026, 9, 24, 10, 0)}  # 距中秋 1 天
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is True
        assert "中秋" in ev.reason

    @pytest.mark.unit
    def test_chongyang_high_priority(self):
        """重阳节（老人节）应有更高优先级"""
        t = FestivalTrigger()
        ctx = {"now": datetime(2026, 10, 17, 10, 0)}
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is True
        assert "重阳" in ev.reason
        assert ev.priority >= 7

    @pytest.mark.unit
    def test_festival_outside_window(self):
        t = FestivalTrigger()
        ctx = {"now": datetime(2026, 7, 15, 10, 0)}  # 远离任何节日
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is False


class TestWeatherTrigger:

    @pytest.mark.unit
    def test_weather_no_data(self):
        t = WeatherTrigger()
        ev = t.evaluate(user_id=1, context={})
        assert ev.fired is False

    @pytest.mark.unit
    def test_weather_temp_drop(self):
        t = WeatherTrigger()
        ctx = {"weather_forecast": {"temp_drop": 10}}
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is True
        assert "10°C" in ev.reason or "10" in ev.reason

    @pytest.mark.unit
    def test_weather_heat_wave(self):
        t = WeatherTrigger()
        ctx = {"weather_forecast": {"heat_wave": True}}
        ev = t.evaluate(user_id=1, context=ctx)
        assert ev.fired is True
        assert "高温" in ev.reason


class TestEvaluateAll:

    @pytest.mark.unit
    def test_all_triggers_safe_evaluate(self):
        """无 context 时所有 trigger 都不应抛异常"""
        results = evaluate_all(user_id=12345, context={})
        assert isinstance(results, list)
        # 每个结果都应是 TriggerEvaluation
        for r in results:
            assert isinstance(r, TriggerEvaluation)

    @pytest.mark.unit
    def test_results_sorted_by_priority(self):
        """fired 的 trigger 应按优先级降序排列"""
        # 制造场景：中秋 + 天气剧变（两个都 fired）
        results = evaluate_all(user_id=1, context={
            "now": datetime(2026, 9, 24, 10, 0),
            "weather_forecast": {"heat_wave": True},
        })
        # 至少 1 个 fired
        priorities = [r.priority for r in results]
        assert priorities == sorted(priorities, reverse=True)

    @pytest.mark.unit
    def test_all_triggers_registered(self):
        """6 个核心 trigger 都应注册"""
        names = {t.name for t in ALL_TRIGGERS}
        assert "silence" in names
        assert "health_anomaly" in names
        assert "family_absence" in names
        assert "festival" in names
        assert "memorial" in names
        assert "weather" in names

    @pytest.mark.unit
    def test_safe_evaluate_swallows_exception(self):
        """trigger 内部抛异常 → safe_evaluate 返回 fired=False，不外抛"""
        class BoomTrigger(SilenceTrigger):
            name = "boom"
            def evaluate(self, user_id, context):
                raise RuntimeError("intentional")
        t = BoomTrigger()
        ev = t.safe_evaluate(user_id=1, context={})
        assert ev.fired is False
        assert "异常" in ev.reason
