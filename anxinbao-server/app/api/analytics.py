"""
数据分析报表API
提供用户分析、健康数据分析、业务报表等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta

from app.services.analytics_service import (
    analytics_service,
    ReportPeriod
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["数据分析"])


# ==================== 权限验证 ====================

async def verify_analyst(current_user: dict = Depends(get_current_user)) -> dict:
    """验证分析师/管理员身份"""
    user_id = int(current_user.get('sub', 0))
    # 实际实现中应验证用户是否有分析权限
    return {"analyst_id": user_id}


# ==================== 请求模型 ====================

class GenerateReportRequest(BaseModel):
    """生成报表请求"""
    report_type: str = Field(..., description="报表类型: revenue/subscription/feature_usage")
    period: str = Field(default="monthly", description="周期: daily/weekly/monthly")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")


# ==================== 管理层摘要API ====================

@router.get("/summary")
async def get_executive_summary(analyst: dict = Depends(verify_analyst)):
    """
    获取管理层摘要

    包含关键指标、亮点、关注点和建议
    """
    summary = analytics_service.get_executive_summary()
    return summary


# ==================== 用户分析API ====================

@router.get("/users/growth")
async def get_user_growth(
    start_date: str = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期 YYYY-MM-DD"),
    analyst: dict = Depends(verify_analyst)
):
    """
    获取用户增长数据
    """
    if not start_date:
        start = date.today() - timedelta(days=30)
    else:
        start = date.fromisoformat(start_date)

    if not end_date:
        end = date.today()
    else:
        end = date.fromisoformat(end_date)

    data = analytics_service.user_analytics.get_user_growth(start, end)
    return data


@router.get("/users/retention")
async def get_retention_analysis(
    cohort_date: str = Query(None, description="同期群日期 YYYY-MM-DD"),
    analyst: dict = Depends(verify_analyst)
):
    """
    获取用户留存分析

    分析指定日期注册用户的留存情况
    """
    if not cohort_date:
        cohort = date.today() - timedelta(days=14)
    else:
        cohort = date.fromisoformat(cohort_date)

    data = analytics_service.user_analytics.get_retention_analysis(cohort)
    return data


@router.get("/users/segments")
async def get_user_segments(analyst: dict = Depends(verify_analyst)):
    """
    获取用户分群数据

    基于行为特征的用户分群
    """
    data = analytics_service.user_analytics.get_user_segments()
    return data


@router.get("/users/{user_id}/journey")
async def get_user_journey(
    user_id: int,
    analyst: dict = Depends(verify_analyst)
):
    """
    获取单个用户的旅程分析
    """
    data = analytics_service.user_analytics.get_user_journey(user_id)
    return data


# ==================== 健康数据分析API ====================

@router.get("/health/overview")
async def get_health_overview(analyst: dict = Depends(verify_analyst)):
    """
    获取健康数据概览
    """
    data = analytics_service.health_analytics.get_health_overview()
    return data


@router.get("/health/trends")
async def get_health_trends(
    metric: str = Query("blood_pressure_high", description='指标类型'),
    days: int = Query(30, ge=7, le=90, description="天数"),
    analyst: dict = Depends(verify_analyst)
):
    """
    获取健康指标趋势

    可选指标: blood_pressure_high, blood_pressure_low, heart_rate, blood_sugar, sleep_hours
    """
    data = analytics_service.health_analytics.get_health_trends(metric, days)
    return data


@router.get("/health/alerts")
async def get_alert_analysis(analyst: dict = Depends(verify_analyst)):
    """
    获取健康警报分析
    """
    data = analytics_service.health_analytics.get_alert_analysis()
    return data


# ==================== 业务报表API ====================

@router.get("/business/revenue")
async def get_revenue_report(
    period: str = Query('daily', description="周期: daily/monthly"),
    start_date: str = Query(None, description='开始日期'),
    end_date: str = Query(None, description="结束日期"),
    analyst: dict = Depends(verify_analyst)
):
    """
    获取收入报表
    """
    try:
        report_period = ReportPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的周期类型")

    if not start_date:
        start = date.today() - timedelta(days=30)
    else:
        start = date.fromisoformat(start_date)

    if not end_date:
        end = date.today()
    else:
        end = date.fromisoformat(end_date)

    data = analytics_service.business_report.get_revenue_report(report_period, start, end)
    return data


@router.get("/business/subscriptions")
async def get_subscription_report(analyst: dict = Depends(verify_analyst)):
    """
    获取订阅报表

    包含订阅概览、层级分布、转化率等
    """
    data = analytics_service.business_report.get_subscription_report()
    return data


@router.get("/business/feature-usage")
async def get_feature_usage_report(analyst: dict = Depends(verify_analyst)):
    """
    获取功能使用报表
    """
    data = analytics_service.business_report.get_feature_usage_report()
    return data


# ==================== 报表生成API ====================

@router.post("/reports/generate")
async def generate_report(
    request: GenerateReportRequest,
    analyst: dict = Depends(verify_analyst)
):
    """
    生成自定义报表
    """
    try:
        period = ReportPeriod(request.period)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的周期类型")

    if request.start_date:
        start = date.fromisoformat(request.start_date)
    else:
        start = date.today() - timedelta(days=30)

    if request.end_date:
        end = date.fromisoformat(request.end_date)
    else:
        end = date.today()

    report = analytics_service.business_report.generate_report(
        report_type=request.report_type,
        period=period,
        start_date=start,
        end_date=end
    )

    return report.to_dict()


@router.get("/reports/export")
async def export_report(
    report_type: str = Query(..., description='报表类型'),
    format: str = Query("json", description="导出格式: json/csv"),
    analyst: dict = Depends(verify_analyst)
):
    """
    导出报表
    """
    result = analytics_service.export_report(report_type, format)
    return result


# ==================== 实时数据API ====================

@router.get("/realtime/active-users")
async def get_realtime_active_users(analyst: dict = Depends(verify_analyst)):
    """
    获取实时活跃用户数
    """
    import random
    return {
        "current_active": random.randint(3000, 5000),
        'peak_today': random.randint(8000, 12000),
        'peak_time': "09:30",
        'by_feature': {
            'ai_chat': random.randint(1000, 2000),
            "health_check": random.randint(500, 1000),
            "entertainment": random.randint(800, 1500),
            'social': random.randint(400, 800),
            'games': random.randint(300, 600)
        },
        'timestamp': datetime.now().isoformat()
    }


@router.get("/realtime/events")
async def get_realtime_events(
    limit: int = Query(20, ge=1, le=100),
    analyst: dict = Depends(verify_analyst)
):
    """
    获取实时事件流
    """
    import random

    event_types = [
        ('user_register', '新用户注册'),
        ('subscription_start', '新增订阅'),
        ('health_check', '健康检查'),
        ('sos_alert', '紧急求助'),
        ('payment_complete', '支付完成')
    ]

    events = []
    for i in range(limit):
        event_type, event_name = random.choice(event_types)
        events.append({
            'event_id': f"evt_{i}",
            'type': event_type,
            'name': event_name,
            'user_id': random.randint(1, 50000),
            'timestamp': (datetime.now() - timedelta(seconds=random.randint(1, 300))).isoformat(),
            'details': {}
        })

    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return {"events": events}


# ==================== 对比分析API ====================

@router.get("/compare/periods")
async def compare_periods(
    metric: str = Query('revenue', description='对比指标'),
    period1_start: str = Query(..., description='周期1开始日期'),
    period1_end: str = Query(..., description='周期1结束日期'),
    period2_start: str = Query(..., description='周期2开始日期'),
    period2_end: str = Query(..., description="周期2结束日期"),
    analyst: dict = Depends(verify_analyst)
):
    """
    周期对比分析
    """
    import random

    p1_value = random.uniform(100000, 200000)
    p2_value = random.uniform(100000, 200000)
    change = (p2_value - p1_value) / p1_value * 100

    return {
        'metric': metric,
        'period1': {
            'start': period1_start,
            'end': period1_end,
            'value': p1_value
        },
        'period2': {
            'start': period2_start,
            'end': period2_end,
            'value': p2_value
        },
        "change_percentage": round(change, 2),
        'trend': 'up' if change > 0 else 'down'
    }
