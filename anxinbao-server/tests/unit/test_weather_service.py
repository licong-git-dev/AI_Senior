"""单元测试 · weather_service（wttr.in 解析 + 缓存 + 兜底）"""
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.services.weather_service import (
    WeatherForecast,
    _cache_clear,
    _cache_get,
    _cache_set,
    _parse_wttr_response,
    get_forecast,
)


@pytest.fixture(autouse=True)
def clean_cache():
    _cache_clear()
    yield
    _cache_clear()


_FAKE_WTTR_NORMAL = {
    "weather": [
        {"date": "2026-04-24", "maxtempC": "28", "mintempC": "18", "hourly": []},
        {
            "date": "2026-04-25",
            "maxtempC": "20",
            "mintempC": "12",
            "hourly": [
                {"lang_zh": [{"value": "晴"}], "weatherDesc": [{"value": "Sunny"}]},
                {"lang_zh": [{"value": "晴"}], "weatherDesc": [{"value": "Sunny"}]},
                {"lang_zh": [{"value": "晴"}], "weatherDesc": [{"value": "Sunny"}]},
                {"lang_zh": [{"value": "晴"}], "weatherDesc": [{"value": "Sunny"}]},
            ],
        },
        {"date": "2026-04-26", "maxtempC": "21", "mintempC": "13", "hourly": []},
    ]
}

_FAKE_WTTR_HEAT = {
    "weather": [
        {"date": "2026-07-30", "maxtempC": "32", "mintempC": "26", "hourly": []},
        {
            "date": "2026-07-31",
            "maxtempC": "37",
            "mintempC": "29",
            "hourly": [{"lang_zh": [{"value": "晴"}]}] * 4,
        },
        {"date": "2026-08-01", "maxtempC": "38", "mintempC": "30", "hourly": []},
    ]
}

_FAKE_WTTR_RAIN = {
    "weather": [
        {"date": "2026-06-10", "maxtempC": "27", "mintempC": "22", "hourly": []},
        {
            "date": "2026-06-11",
            "maxtempC": "23",
            "mintempC": "20",
            "hourly": [
                {"lang_zh": [{"value": "暴雨"}], "weatherDesc": [{"value": "Heavy rain"}]}
            ] * 4,
        },
        {"date": "2026-06-12", "maxtempC": "25", "mintempC": "20", "hourly": []},
    ]
}


class TestParseWttrResponse:

    @pytest.mark.unit
    def test_parse_normal_temp_drop(self):
        forecast = _parse_wttr_response("Wuhan", _FAKE_WTTR_NORMAL)
        assert forecast.city == "Wuhan"
        assert forecast.today_temp_max == 28
        assert forecast.tomorrow_temp_max == 20
        assert forecast.temp_drop == 8  # 28-20
        assert forecast.heavy_rain is False
        assert forecast.heat_wave is False

    @pytest.mark.unit
    def test_parse_heat_wave(self):
        forecast = _parse_wttr_response("Wuhan", _FAKE_WTTR_HEAT)
        assert forecast.heat_wave is True  # 37 >= 35
        assert forecast.temp_drop == 0  # 32 → 37 不算降

    @pytest.mark.unit
    def test_parse_heavy_rain(self):
        forecast = _parse_wttr_response("Wuhan", _FAKE_WTTR_RAIN)
        assert forecast.heavy_rain is True

    @pytest.mark.unit
    def test_parse_insufficient_data_raises(self):
        with pytest.raises(ValueError):
            _parse_wttr_response("Wuhan", {"weather": [{"maxtempC": "20"}]})


class TestCache:

    @pytest.mark.unit
    def test_cache_hit(self):
        forecast = WeatherForecast(
            city="Wuhan", today_temp_max=20, today_temp_min=10,
            tomorrow_temp_max=22, tomorrow_temp_min=12,
            tomorrow_weather_desc="晴", fetched_at=time.time(),
        )
        _cache_set("Wuhan", forecast)
        cached = _cache_get("Wuhan")
        assert cached is not None
        assert cached.tomorrow_temp_max == 22

    @pytest.mark.unit
    def test_cache_expires(self):
        old_forecast = WeatherForecast(
            city="Wuhan", today_temp_max=20, today_temp_min=10,
            tomorrow_temp_max=22, tomorrow_temp_min=12,
            tomorrow_weather_desc="",
            fetched_at=time.time() - 7200,  # 2h 前，超 TTL
        )
        _cache_set("Wuhan", old_forecast)
        assert _cache_get("Wuhan") is None  # 应已过期


class TestGetForecast:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_forecast_success(self):
        with patch("app.services.weather_service._fetch_raw_forecast",
                   new=AsyncMock(return_value=_FAKE_WTTR_NORMAL)):
            forecast = await get_forecast("Wuhan")
            assert forecast is not None
            assert forecast.city == "Wuhan"
            assert forecast.temp_drop == 8

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_forecast_uses_cache(self):
        """两次调 get_forecast，第二次应命中缓存（_fetch_raw_forecast 不被再调）"""
        call_count = {"n": 0}

        async def fake_fetch(city):
            call_count["n"] += 1
            return _FAKE_WTTR_NORMAL

        with patch("app.services.weather_service._fetch_raw_forecast", new=fake_fetch):
            await get_forecast("Wuhan")
            await get_forecast("Wuhan")
            assert call_count["n"] == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_forecast_network_failure(self):
        """网络异常 → 返回 None，不应抛"""
        with patch("app.services.weather_service._fetch_raw_forecast",
                   new=AsyncMock(side_effect=RuntimeError("network down"))):
            forecast = await get_forecast("Wuhan")
            assert forecast is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_forecast_bad_response(self):
        """wttr.in 返回奇怪结构 → 返回 None，不应抛"""
        with patch("app.services.weather_service._fetch_raw_forecast",
                   new=AsyncMock(return_value={"weather": []})):
            forecast = await get_forecast("Wuhan")
            assert forecast is None
