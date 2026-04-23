"""
紧急服务相关模式定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class EmergencyType(str, Enum):
    """紧急情况类型"""
    FALL = 'fall'  # 跌倒
    HEALTH_CRISIS = "health_crisis"  # 健康危机
    DISTRESS = 'distress'  # 求助
    FIRE = 'fire'  # 火灾
    INTRUSION = 'intrusion'  # 入侵
    GAS_LEAK = 'gas_leak'  # 燃气泄漏
    OTHER = "other"  # 其他


class EmergencyStatus(str, Enum):
    """紧急情况状态"""
    TRIGGERED = 'triggered'  # 已触发
    NOTIFYING = 'notifying'  # 通知中
    RESPONDING = 'responding'  # 响应中
    RESOLVED = "resolved"  # 已解决
    FALSE_ALARM = "false_alarm"  # 误报
    CANCELLED = "cancelled"  # 已取消


class EmergencySeverity(str, Enum):
    """紧急程度"""
    LOW = "low"
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


# ========== 紧急事件 ==========

class EmergencyAlertCreate(BaseSchema):
    """创建紧急告警"""
    user_id: str
    emergency_type: EmergencyType
    severity: EmergencySeverity = EmergencySeverity.HIGH
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = Field(None, description='位置信息')
    trigger_source: str = Field(default="manual", description="触发来源: manual/device/fall_detection")
    device_id: Optional[str] = None


class EmergencyAlertResponse(BaseSchema, TimestampMixin):
    """紧急告警响应"""
    id: str
    user_id: str
    user_name: str
    user_phone: str
    emergency_type: EmergencyType
    severity: EmergencySeverity
    status: EmergencyStatus
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    trigger_source: str
    device_id: Optional[str] = None
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    notified_contacts: List[str] = []
    response_time_seconds: Optional[int] = None


class EmergencyAlertUpdate(BaseSchema):
    """更新紧急告警"""
    status: Optional[EmergencyStatus] = None
    resolution_notes: Optional[str] = None


class ResolveEmergencyRequest(BaseSchema):
    """解决紧急情况请求"""
    resolved_by: str
    resolution_notes: Optional[str] = None
    is_false_alarm: bool = False


class CancelEmergencyRequest(BaseSchema):
    """取消紧急情况请求"""
    cancel_reason: str = Field(..., max_length=200)


# ========== 紧急联系人 ==========

class EmergencyContactBase(BaseSchema):
    """紧急联系人基础"""
    name: str = Field(..., max_length=50)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    relationship: str = Field(..., max_length=20)
    is_primary: bool = False
    notify_order: int = Field(default=1, ge=1, le=10, description="通知顺序")


class EmergencyContactCreate(EmergencyContactBase):
    """创建紧急联系人"""
    user_id: str


class EmergencyContactResponse(EmergencyContactBase, TimestampMixin):
    """紧急联系人响应"""
    id: str
    user_id: str
    notification_enabled: bool = True
    last_notified_at: Optional[datetime] = None


class EmergencyContactUpdate(BaseSchema):
    """更新紧急联系人"""
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    is_primary: Optional[bool] = None
    notify_order: Optional[int] = None
    notification_enabled: Optional[bool] = None


# ========== 紧急服务设置 ==========

class EmergencySettings(BaseSchema):
    """紧急服务设置"""
    user_id: str
    sos_enabled: bool = True
    fall_detection_enabled: bool = True
    auto_call_emergency_services: bool = False
    countdown_seconds: int = Field(default=30, ge=10, le=120, description='确认倒计时秒数')
    notification_methods: List[str] = Field(default=['push', 'sms', 'call'])
    emergency_services_phone: str = Field(default='120', description='急救电话')
    police_phone: str = Field(default='110')
    fire_phone: str = Field(default="119")


class UpdateEmergencySettingsRequest(BaseSchema):
    """更新紧急服务设置"""
    sos_enabled: Optional[bool] = None
    fall_detection_enabled: Optional[bool] = None
    auto_call_emergency_services: Optional[bool] = None
    countdown_seconds: Optional[int] = None
    notification_methods: Optional[List[str]] = None


# ========== 通知记录 ==========

class EmergencyNotificationRecord(BaseSchema, TimestampMixin):
    """紧急通知记录"""
    id: str
    emergency_id: str
    contact_id: str
    contact_name: str
    contact_phone: str
    notification_method: str  # sms/call/push
    status: str  # sent/delivered/failed/answered
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ========== 位置信息 ==========

class LocationInfo(BaseSchema):
    """位置信息"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0, description="精度(米)")
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class UpdateLocationRequest(BaseSchema):
    """更新位置请求"""
    user_id: str
    location: LocationInfo


# ========== 统计 ==========

class EmergencyStats(BaseSchema):
    """紧急事件统计"""
    period: str  # daily/weekly/monthly
    total_events: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    average_response_time_seconds: Optional[float] = None
    false_alarm_rate: float = 0
