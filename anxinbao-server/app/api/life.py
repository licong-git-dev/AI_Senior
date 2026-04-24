"""
生活服务API
提供天气、新闻、便民服务、本地生活等接口
"""
from functools import wraps
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.life_service import (
    life_service,
    LifeServiceNotImplemented,
    WeatherType,
    AirQuality,
    NewsCategory,
    ServiceType,
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/life", tags=["生活服务"])


def _life_route(handler):
    """
    生活服务路由装饰器：把 LifeServiceNotImplemented 翻译为 HTTP 501，
    给前端可读的"未实现"提示，避免在生产环境返回 random 假数据。
    """
    @wraps(handler)
    async def wrapper(*args, **kwargs):
        try:
            return await handler(*args, **kwargs)
        except LifeServiceNotImplemented as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={
                    "code": "feature_not_implemented",
                    "message": str(e),
                    "fallback": (
                        "前端建议改用 wttr.in / 高德天气 / 心知天气 等真实数据源；"
                        " 后端接入真实数据后本端点会自动恢复。"
                    ),
                },
            )
    return wrapper


# ==================== 天气API ====================

@router.get("/weather/current")
@_life_route
async def get_current_weather(
    city: str = Query('北京', description="城市名称")
):
    """
    获取当前天气

    包含温度、空气质量、出行建议等
    """
    weather = life_service.weather.get_weather(city)

    return {
        'weather': weather.to_dict(),
        'message': f"为您查询到{city}的天气"
    }


@router.get("/weather/forecast")
@_life_route
async def get_weather_forecast(
    city: str = Query('北京', description='城市名称'),
    days: int = Query(7, ge=1, le=15, description="预报天数")
):
    """
    获取天气预报
    """
    forecasts = life_service.weather.get_forecast(city, days)

    return {
        'city': city,
        'forecasts': [f.to_dict() for f in forecasts],
        'count': len(forecasts)
    }


@router.get("/weather/advice")
@_life_route
async def get_elderly_weather_advice(
    city: str = Query('北京', description="城市名称")
):
    """
    获取老年人出行建议

    根据天气情况提供专门针对老年人的建议
    """
    weather = life_service.weather.get_weather(city)
    advice = life_service.weather.get_elderly_advice(weather)

    return {
        'city': city,
        'weather': weather.to_dict(),
        'advice': advice
    }


# ==================== 新闻API ====================

@router.get("/news")
async def get_news_list(
    category: Optional[str] = Query(None, description="分类"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    获取新闻列表
    """
    cat_filter = None
    if category:
        try:
            cat_filter = NewsCategory(category)
        except ValueError:
            pass

    news = life_service.news.get_news_list(cat_filter, limit)

    return {
        'news': [n.to_dict() for n in news],
        'count': len(news),
        'categories': [c.value for c in NewsCategory]
    }


@router.get("/news/briefing")
async def get_daily_briefing():
    """
    获取每日简报

    精选头条、健康、养老相关新闻
    """
    briefing = life_service.news.get_daily_briefing()
    return briefing


@router.get("/news/{news_id}")
async def get_news_detail(news_id: str):
    """
    获取新闻详情
    """
    news = life_service.news.get_news_detail(news_id)
    if not news:
        raise HTTPException(status_code=404, detail='新闻不存在')

    return {"news": news.to_dict()}


# ==================== 便民服务API ====================

@router.get("/convenience")
async def get_convenience_services(
    service_type: Optional[str] = Query(None, description="服务类型")
):
    """
    获取便民服务列表
    """
    type_filter = None
    if service_type:
        try:
            type_filter = ServiceType(service_type)
        except ValueError:
            pass

    services = life_service.convenience.get_services(type_filter)

    return {
        'services': [s.to_dict() for s in services],
        'count': len(services),
        "service_types": [t.value for t in ServiceType]
    }


@router.get("/convenience/emergency")
async def get_emergency_phones():
    """
    获取紧急电话

    110、120、119等重要电话
    """
    phones = life_service.convenience.get_emergency_phones()
    return {
        "emergency_phones": phones,
        'tip': "紧急情况请直接拨打以上电话"
    }


@router.get("/convenience/search")
async def search_convenience_services(
    q: str = Query(..., min_length=1, description="搜索关键词")
):
    """
    搜索便民服务
    """
    results = life_service.convenience.search_services(q)
    return {
        'results': [s.to_dict() for s in results],
        'count': len(results),
        'query': q
    }


# ==================== 本地生活API ====================

@router.get("/local/nearby")
async def get_nearby_places(
    category: Optional[str] = Query(None, description="分类: 公园/医疗/超市等"),
    max_distance: float = Query(5.0, description='最大距离(公里)'),
    elderly_friendly: bool = Query(True, description="仅显示适老化场所")
):
    """
    获取附近场所
    """
    places = life_service.local.get_nearby_places(
        category, max_distance, elderly_friendly
    )

    return {
        'places': [p.to_dict() for p in places],
        'count': len(places)
    }


@router.get("/local/recommendations")
async def get_local_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """
    获取本地生活推荐

    包括周边公园、服务、活动等
    """
    user_id = int(current_user['sub'])

    recommendations = life_service.local.get_recommendations()
    return recommendations


@router.get("/local/search")
async def search_local_places(
    q: str = Query(..., min_length=1, description="搜索关键词")
):
    """
    搜索本地场所
    """
    results = life_service.local.search_places(q)
    return {
        'results': [p.to_dict() for p in results],
        'count': len(results),
        'query': q
    }


# ==================== 综合生活服务API ====================

@router.get("/dashboard")
async def get_life_dashboard(
    city: str = Query('北京', description="城市"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取生活服务仪表板

    整合天气、新闻、推荐等信息
    """
    user_id = int(current_user['sub'])

    # 获取天气
    weather = life_service.weather.get_weather(city)
    advice = life_service.weather.get_elderly_advice(weather)

    # 获取新闻简报
    briefing = life_service.news.get_daily_briefing()

    # 获取本地推荐
    local_rec = life_service.local.get_recommendations()

    # 获取紧急电话
    emergency = life_service.convenience.get_emergency_phones()

    return {
        'weather': {
            'current': weather.to_dict(),
            'advice': advice
        },
        'news': {
            'greeting': briefing['greeting'],
            'headlines': briefing['headlines'][:3]
        },
        'local': {
            'parks': local_rec['parks'][:2],
            'activities': local_rec['activities'][:2]
        },
        'emergency': emergency,
        "tips": weather.tips
    }


@router.get("/morning-report")
async def get_morning_report(
    city: str = Query('北京', description="城市"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取早间报告

    适合早上播报的综合信息
    """
    user_id = int(current_user['sub'])

    weather = life_service.weather.get_weather(city)
    advice = life_service.weather.get_elderly_advice(weather)
    briefing = life_service.news.get_daily_briefing()

    # 生成语音播报文本
    report_text = f"""
    早上好！今天是{briefing['date']}。

    首先为您播报天气：今天{city}{weather._get_weather_text()}，
    气温{weather.temp_low}到{weather.temp_high}度，
    {weather.wind_direction}{weather.wind_level}级。

    出行建议：{advice['clothing_advice']}
    {advice["exercise_advice"]}

    接下来是新闻简报：
    """

    for i, news in enumerate(briefing['headlines'][:3], 1):
        # 注意：避免在 f-string 内嵌套同款引号，PEP 701 仅 3.12+ 支持。
        # 旧 Python（3.10/3.11）会抛 SyntaxError。
        title = news["title"]
        report_text += f"\n第{i}条：{title}"

    return {
        'date': briefing['date'],
        "weather_summary": f"{weather._get_weather_text()}，{weather.temp_low}~{weather.temp_high}°C",
        'advice': advice,
        'headlines': briefing['headlines'][:3],
        "report_text": report_text.strip(),
        "audio_available": True
    }
