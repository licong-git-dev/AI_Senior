"""
实时天气服务（M · 接入 wttr.in）

设计目标：
- 让 WeatherTrigger 真用上实时数据（替代 context 注入的占位）
- 不引入新依赖（用项目已有的 httpx）
- 内存缓存（1h TTL），避免对 wttr.in 频繁请求
- 失败容错：网络挂了/wttr.in 抽风 → 返回 None，让 trigger 静默跳过
- 仅返回 trigger 关心的关键信号（temp_drop / heavy_rain / heat_wave）

wttr.in 使用 JSON 格式（?format=j1），免费、无需 key、有限流。
官方推荐每个客户端 1 次/分钟以内。我们 1h 缓存远低于此。

升级路径：
- 量大后切换到付费天气 API（如和风、心知）只需替换 _fetch_raw_forecast()
- 无需改 WeatherTrigger 代码
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ===== 配置 =====
WTTR_BASE_URL = "https://wttr.in"
DEFAULT_CITY = "Wuhan"
CACHE_TTL_SECONDS = 3600  # 1h
HTTP_TIMEOUT_SECONDS = 5.0


@dataclass
class WeatherForecast:
    """trigger 关心的核心信号 + 原始数据"""
    city: str
    today_temp_max: int
    today_temp_min: int
    tomorrow_temp_max: int
    tomorrow_temp_min: int
    tomorrow_weather_desc: str
    temp_drop: int = 0           # 次日比今日 max 降几度
    heavy_rain: bool = False
    heat_wave: bool = False       # 次日 temp_max ≥ 35
    fetched_at: float = 0.0       # epoch

    def to_trigger_context(self) -> Dict[str, any]:
        """转为 WeatherTrigger 期待的 dict 格式"""
        return {
            "temp_drop": self.temp_drop,
            "heavy_rain": self.heavy_rain,
            "heat_wave": self.heat_wave,
            "tomorrow_temp_max": self.tomorrow_temp_max,
            "tomorrow_temp_min": self.tomorrow_temp_min,
            "city": self.city,
        }


# ===== 缓存 =====

_CACHE: Dict[str, WeatherForecast] = {}
_CACHE_LOCK = threading.Lock()


def _cache_get(city: str) -> Optional[WeatherForecast]:
    with _CACHE_LOCK:
        item = _CACHE.get(city)
        if not item:
            return None
        if time.time() - item.fetched_at > CACHE_TTL_SECONDS:
            return None
        return item


def _cache_set(city: str, forecast: WeatherForecast) -> None:
    with _CACHE_LOCK:
        _CACHE[city] = forecast


def _cache_clear() -> None:
    """供测试使用"""
    with _CACHE_LOCK:
        _CACHE.clear()


# ===== 主入口 =====


async def get_forecast(city: str = DEFAULT_CITY) -> Optional[WeatherForecast]:
    """
    获取天气预报；带缓存 + 失败兜底。

    返回 None 当：
    - 网络异常 / wttr.in 不可达
    - 响应格式异常
    - 解析失败

    None 时调用方应当静默跳过（不要假报警）。
    """
    cached = _cache_get(city)
    if cached is not None:
        return cached

    try:
        raw = await _fetch_raw_forecast(city)
    except Exception as exc:
        logger.warning(f"[weather] {city} 拉取失败: {exc}")
        return None

    if not raw:
        return None

    try:
        parsed = _parse_wttr_response(city, raw)
    except Exception as exc:
        logger.warning(f"[weather] {city} 解析失败: {exc}")
        return None

    _cache_set(city, parsed)
    return parsed


# ===== HTTP 调用 =====


async def _fetch_raw_forecast(city: str) -> Optional[dict]:
    """从 wttr.in 拿原始 JSON"""
    try:
        import httpx
    except ImportError:
        logger.error("[weather] httpx 未安装")
        return None

    url = f"{WTTR_BASE_URL}/{city}?format=j1&lang=zh"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            logger.warning(f"[weather] wttr.in {city} 返回 {resp.status_code}")
            return None
        return resp.json()


# ===== 解析 =====


def _parse_wttr_response(city: str, raw: dict) -> WeatherForecast:
    """
    解析 wttr.in j1 格式：
    raw['weather'] = [
        {'date': '2026-04-24', 'maxtempC': '30', 'mintempC': '18', 'hourly': [...]},
        {'date': '2026-04-25', 'maxtempC': '20', 'mintempC': '12', 'hourly': [...]},
        {'date': '2026-04-26', ...}
    ]
    """
    days = raw.get("weather") or []
    if len(days) < 2:
        raise ValueError("wttr.in 返回的预报不足 2 天")

    today = days[0]
    tomorrow = days[1]

    today_max = int(today.get("maxtempC", 0))
    today_min = int(today.get("mintempC", 0))
    tomorrow_max = int(tomorrow.get("maxtempC", 0))
    tomorrow_min = int(tomorrow.get("mintempC", 0))

    # 明日天气描述（取中午时段）
    desc = ""
    hourly = tomorrow.get("hourly") or []
    if hourly:
        # 取索引接近中午的（hourly 是 8 个时段，每 3h）
        mid = hourly[len(hourly) // 2] if len(hourly) >= 4 else hourly[0]
        lang_zh = mid.get("lang_zh") or [{}]
        desc = (lang_zh[0].get("value") or mid.get("weatherDesc", [{}])[0].get("value", ""))

    # ===== 关键信号 =====
    temp_drop = max(0, today_max - tomorrow_max)
    heavy_rain = any(
        kw in desc.lower() or kw in desc
        for kw in ("暴雨", "大雨", "thunderstorm", "heavy rain")
    )
    heat_wave = tomorrow_max >= 35

    return WeatherForecast(
        city=city,
        today_temp_max=today_max,
        today_temp_min=today_min,
        tomorrow_temp_max=tomorrow_max,
        tomorrow_temp_min=tomorrow_min,
        tomorrow_weather_desc=desc,
        temp_drop=temp_drop,
        heavy_rain=heavy_rain,
        heat_wave=heat_wave,
        fetched_at=time.time(),
    )


# ===== 同步包装（供 trigger 调用，trigger 是同步的）=====


def get_forecast_sync(city: str = DEFAULT_CITY) -> Optional[WeatherForecast]:
    """
    供同步代码（如 WeatherTrigger.evaluate）调用的包装。
    在已有 event loop 时不应直接调（应改用异步路径），但 trigger 是
    cron job 触发的同步函数，自己起 loop。

    若已有运行中的 loop（如在 async 端点中误调），返回 None 避免死锁。
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.warning("[weather] 在已运行的 loop 中调 sync 包装，跳过")
            return None
    except RuntimeError:
        pass  # 无 loop，正常路径

    try:
        return asyncio.run(get_forecast(city))
    except Exception as exc:
        logger.warning(f"[weather] sync 调用异常: {exc}")
        return None
