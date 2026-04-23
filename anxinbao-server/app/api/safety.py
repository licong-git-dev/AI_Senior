"""
安全守护API
提供跌倒检测、行为监测、GPS定位与安全区域等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.safety_service import (
    safety_service,
    FallSeverity,
    FallStatus,
    BehaviorType,
    AnomalyLevel
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/safety", tags=["安全守护"])


# ==================== 请求模型 ====================

class SensorDataRequest(BaseModel):
    """传感器数据请求"""
    acceleration: Dict[str, float] = Field(..., description="加速度 {x, y, z}")
    gyroscope: Dict[str, float] = Field(..., description="陀螺仪 {x, y, z}")
    orientation: Dict[str, float] = Field(default_factory=dict, description="方向 {pitch, roll, yaw}")


class ConfirmFallRequest(BaseModel):
    """确认跌倒请求"""
    is_real: bool = Field(..., description='是否真实跌倒')
    notes: Optional[str] = Field(None, description="备注")


class SetBehaviorPatternRequest(BaseModel):
    """设置行为模式请求"""
    behavior_type: str = Field(..., description='行为类型')
    usual_time: str = Field(..., description='通常时间 HH:MM')
    usual_duration: int = Field(..., description='通常持续时间(分钟)')
    frequency: str = Field("daily", description="频率: daily/weekly")
    tolerance_minutes: int = Field(60, description="容差(分钟)")


class LogActivityRequest(BaseModel):
    """记录活动请求"""
    behavior_type: str = Field(..., description='行为类型')
    started_at: datetime = Field(default_factory=datetime.now, description='开始时间')
    duration_minutes: Optional[int] = Field(None, description="持续时间(分钟)")


class AddSafeZoneRequest(BaseModel):
    """添加安全区域请求"""
    name: str = Field(..., max_length=50, description='区域名称')
    latitude: float = Field(..., description='纬度')
    longitude: float = Field(..., description='经度')
    radius_meters: int = Field(500, ge=50, le=5000, description='半径(米)')
    is_home: bool = Field(False, description="是否为家")


class UpdateLocationRequest(BaseModel):
    """更新位置请求"""
    latitude: float = Field(..., description='纬度')
    longitude: float = Field(..., description='经度')
    accuracy: float = Field(10, description='精度(米)')
    address: Optional[str] = Field(None, description="地址")


# ==================== 跌倒检测API ====================

@router.post("/fall/detect")
async def detect_fall(
    request: SensorDataRequest,
    location: Optional[str] = Query(None, description="位置描述"),
    current_user: dict = Depends(get_current_user)
):
    """
    跌倒检测

    分析传感器数据判断是否发生跌倒
    """
    user_id = int(current_user['sub'])

    event = safety_service.fall_detection.analyze_sensor_data(
        user_id,
        request.acceleration,
        request.gyroscope,
        request.orientation
    )

    if event:
        return {
            "fall_detected": True,
            'event': event.to_dict(),
            'message': "检测到可能的跌倒，请确认是否需要帮助",
            "confirmation_required": True,
            "confirmation_timeout": 60
        }

    return {
        "fall_detected": False,
        'message': "未检测到异常"
    }


@router.post("/fall/events/{event_id}/confirm")
async def confirm_fall_event(
    event_id: str,
    request: ConfirmFallRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    确认跌倒事件

    用户或监护人确认是否真实跌倒
    """
    success = safety_service.fall_detection.confirm_fall(
        event_id,
        request.is_real,
        request.notes
    )

    if not success:
        raise HTTPException(status_code=404, detail='事件不存在')

    return {
        'success': True,
        'event_id': event_id,
        'is_real': request.is_real,
        'message': '确认已记录' if request.is_real else "已标记为误报"
    }


@router.post("/fall/events/{event_id}/emergency")
async def trigger_fall_emergency(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    触发紧急求助

    发送紧急求助通知给紧急联系人
    """
    result = safety_service.fall_detection.trigger_emergency(event_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/fall/events/{event_id}/handle")
async def mark_fall_handled(
    event_id: str,
    notes: Optional[str] = Query(None, description="处理备注"),
    current_user: dict = Depends(get_current_user)
):
    """
    标记跌倒事件已处理
    """
    success = safety_service.fall_detection.mark_handled(event_id, notes)

    if not success:
        raise HTTPException(status_code=404, detail='事件不存在')

    return {
        'success': True,
        'event_id': event_id,
        'message': "事件已标记为已处理"
    }


@router.get("/fall/events")
async def get_fall_events(
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取跌倒事件列表
    """
    user_id = int(current_user['sub'])

    status_filter = None
    if status:
        try:
            status_filter = FallStatus(status)
        except ValueError:
            pass

    events = safety_service.fall_detection.get_user_events(user_id, status_filter, limit)

    return {
        'events': [e.to_dict() for e in events],
        'count': len(events)
    }


@router.get("/fall/statistics")
async def get_fall_statistics(current_user: dict = Depends(get_current_user)):
    """
    获取跌倒统计数据
    """
    user_id = int(current_user['sub'])

    stats = safety_service.fall_detection.get_statistics(user_id)
    return stats


# ==================== 行为监测API ====================

@router.post("/behavior/patterns")
async def set_behavior_pattern(
    request: SetBehaviorPatternRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    设置行为模式

    定义正常的行为习惯，用于检测异常
    """
    user_id = int(current_user['sub'])

    try:
        behavior_type = BehaviorType(request.behavior_type)
    except ValueError:
        valid_types = [t.value for t in BehaviorType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的行为类型，可选: {valid_types}"
        )

    pattern = safety_service.behavior_monitor.set_behavior_pattern(
        user_id,
        behavior_type,
        request.usual_time,
        request.usual_duration,
        request.frequency,
        request.tolerance_minutes
    )

    return {
        'success': True,
        'pattern': pattern.to_dict(),
        'message': "行为模式已设置"
    }


@router.get("/behavior/patterns")
async def get_behavior_patterns(current_user: dict = Depends(get_current_user)):
    """
    获取行为模式列表
    """
    user_id = int(current_user['sub'])

    patterns = safety_service.behavior_monitor.get_user_patterns(user_id)

    return {
        'patterns': [p.to_dict() for p in patterns],
        'count': len(patterns)
    }


@router.post("/behavior/activities")
async def log_activity(
    request: LogActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    记录活动

    记录日常活动并检测是否异常
    """
    user_id = int(current_user['sub'])

    try:
        behavior_type = BehaviorType(request.behavior_type)
    except ValueError:
        valid_types = [t.value for t in BehaviorType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的行为类型，可选: {valid_types}"
        )

    anomaly = safety_service.behavior_monitor.log_activity(
        user_id,
        behavior_type,
        request.started_at,
        request.duration_minutes
    )

    result = {
        "success": True,
        "activity_logged": True,
        "has_anomaly": anomaly is not None
    }

    if anomaly:
        result['anomaly'] = anomaly.to_dict()

    return result


@router.get("/behavior/anomalies")
async def get_behavior_anomalies(
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取行为异常列表
    """
    user_id = int(current_user['sub'])

    anomalies = safety_service.behavior_monitor.get_user_anomalies(user_id, resolved, limit)

    return {
        'anomalies': [a.to_dict() for a in anomalies],
        'count': len(anomalies)
    }


@router.post("/behavior/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: str,
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    解决行为异常
    """
    success = safety_service.behavior_monitor.resolve_anomaly(anomaly_id, notes)

    if not success:
        raise HTTPException(status_code=404, detail='异常记录不存在')

    return {
        'success': True,
        'anomaly_id': anomaly_id,
        'message': "异常已标记为已解决"
    }


@router.get("/behavior/check-inactivity")
async def check_inactivity(
    hours: int = Query(12, ge=1, le=48, description="检查时间范围(小时)"),
    current_user: dict = Depends(get_current_user)
):
    """
    检查长时间无活动
    """
    user_id = int(current_user['sub'])

    anomaly = safety_service.behavior_monitor.check_inactivity(user_id, hours)

    if anomaly:
        return {
            'inactive': True,
            'anomaly': anomaly.to_dict(),
            'message': f"检测到超过{hours}小时无活动"
        }

    return {
        'inactive': False,
        'message': "活动正常"
    }


# ==================== GPS定位与安全区域API ====================

@router.post("/location/zones")
async def add_safe_zone(
    request: AddSafeZoneRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加安全区域

    设置家、常去地点等安全区域
    """
    user_id = int(current_user['sub'])

    zone = safety_service.location.add_safe_zone(
        user_id,
        request.name,
        request.latitude,
        request.longitude,
        request.radius_meters,
        request.is_home
    )

    return {
        'success': True,
        'zone': zone.to_dict(),
        'message': f"安全区域 {request.name} 添加成功"
    }


@router.get("/location/zones")
async def get_safe_zones(current_user: dict = Depends(get_current_user)):
    """
    获取安全区域列表
    """
    user_id = int(current_user['sub'])

    zones = safety_service.location.get_user_zones(user_id)

    return {
        'zones': [z.to_dict() for z in zones],
        'count': len(zones)
    }


@router.delete("/location/zones/{zone_id}")
async def remove_safe_zone(
    zone_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    移除安全区域
    """
    user_id = int(current_user['sub'])

    success = safety_service.location.remove_safe_zone(zone_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='安全区域不存在')

    return {
        'success': True,
        'message': "安全区域已移除"
    }


@router.post("/location/update")
async def update_location(
    request: UpdateLocationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新位置

    上报当前位置，检测是否在安全区域内
    """
    user_id = int(current_user['sub'])

    record, alert = safety_service.location.update_location(
        user_id,
        request.latitude,
        request.longitude,
        request.accuracy,
        request.address
    )

    result = {
        'success': True,
        'location': record.to_dict(),
        "in_safe_zone": record.in_safe_zone,
        'has_alert': alert is not None
    }

    if alert:
        result['alert'] = alert.to_dict()
        if alert.alert_type == 'exit':
            result['message'] = '已离开安全区域'
        else:
            result['message'] = "已进入安全区域"

    return result


@router.get("/location/current")
async def get_current_location(current_user: dict = Depends(get_current_user)):
    """
    获取当前位置

    获取最后上报的位置
    """
    user_id = int(current_user['sub'])

    location = safety_service.location.get_last_location(user_id)

    if not location:
        return {'has_location': False, 'message': "暂无位置信息"}

    return {
        "has_location": True,
        'location': location.to_dict()
    }


@router.get("/location/history")
async def get_location_history(
    hours: int = Query(24, ge=1, le=168, description="时间范围(小时)"),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """
    获取位置历史
    """
    user_id = int(current_user['sub'])

    history = safety_service.location.get_location_history(user_id, hours, limit)

    return {
        'history': [h.to_dict() for h in history],
        'count': len(history)
    }


@router.get("/location/alerts")
async def get_zone_alerts(
    acknowledged: Optional[bool] = Query(None, description="是否已确认"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取区域警报列表
    """
    user_id = int(current_user['sub'])

    alerts = safety_service.location.get_user_alerts(user_id, acknowledged, limit)

    return {
        'alerts': [a.to_dict() for a in alerts],
        'count': len(alerts)
    }


@router.post("/location/alerts/{alert_id}/acknowledge")
async def acknowledge_zone_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    确认区域警报
    """
    user_id = int(current_user['sub'])

    success = safety_service.location.acknowledge_alert(alert_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='警报不存在')

    return {
        'success': True,
        'alert_id': alert_id,
        'message': '警报已确认'
    }


# ==================== 安全仪表板API ====================

@router.get("/dashboard")
async def get_safety_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取安全守护仪表板

    综合展示各项安全数据
    """
    user_id = int(current_user['sub'])

    # 跌倒统计
    fall_stats = safety_service.fall_detection.get_statistics(user_id)

    # 最近跌倒事件
    recent_falls = safety_service.fall_detection.get_user_events(user_id, limit=3)

    # 未解决的行为异常
    unresolved_anomalies = safety_service.behavior_monitor.get_user_anomalies(
        user_id, resolved=False, limit=5
    )

    # 当前位置
    current_location = safety_service.location.get_last_location(user_id)

    # 未确认的区域警报
    pending_alerts = safety_service.location.get_user_alerts(
        user_id, acknowledged=False, limit=5
    )

    # 安全区域
    safe_zones = safety_service.location.get_user_zones(user_id)

    return {
        "fall_detection": {
            'statistics': fall_stats,
            "recent_events": [e.to_dict() for e in recent_falls]
        },
        "behavior_monitor": {
            "unresolved_anomalies": [a.to_dict() for a in unresolved_anomalies],
            "anomaly_count": len(unresolved_anomalies)
        },
        'location': {
            'current': current_location.to_dict() if current_location else None,
            "in_safe_zone": current_location.in_safe_zone if current_location else None,
            "pending_alerts": [a.to_dict() for a in pending_alerts],
            "safe_zones_count": len(safe_zones)
        },
        'overall_status': "safe" if not pending_alerts and not unresolved_anomalies else "attention_needed"
    }
