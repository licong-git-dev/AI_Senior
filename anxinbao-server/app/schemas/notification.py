"""
通知相关模式定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class NotificationType(str, Enum):
    """通知类型"""
    SYSTEM = 'system'  # 系统通知
    HEALTH_ALERT = "health_alert"  # 健康告警
    MEDICATION = 'medication'  # 用药提醒
    EMERGENCY = 'emergency'  # 紧急通知
    FAMILY = 'family'  # 家人消息
    DEVICE = 'device'  # 设备告警
    ACTIVITY = 'activity'  # 活动提醒
    PROMOTION = "promotion"  # 推广消息


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


class NotificationChannel(str, Enum):
    """通知渠道"""
    PUSH = 'push'  # APP推送
    SMS = 'sms'  # 短信
    EMAIL = 'email'  # 邮件
    VOICE = 'voice'  # 语音电话
    IN_APP = "in_app"  # 应用内


# ========== 通知模式 ==========

class NotificationBase(BaseSchema):
    """通知基础"""
    title: str = Field(..., max_length=100, description='标题')
    content: str = Field(..., max_length=1000, description='内容')
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = Field(None, description='附加数据')
    action_url: Optional[str] = Field(None, description="点击跳转URL")


class NotificationCreate(NotificationBase):
    """创建通知"""
    user_id: str
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.PUSH])
    scheduled_at: Optional[datetime] = None  # 定时发送


class NotificationResponse(NotificationBase, TimestampMixin):
    """通知响应"""
    id: str
    user_id: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    is_deleted: bool = False
    sent_channels: List[NotificationChannel] = []
    delivery_status: Dict[str, str] = {}  # 各渠道发送状态


class NotificationListFilter(BaseSchema):
    """通知列表过滤器"""
    notification_type: Optional[NotificationType] = None
    is_read: Optional[bool] = None
    priority: Optional[NotificationPriority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class MarkNotificationReadRequest(BaseSchema):
    """标记已读请求"""
    notification_ids: List[str] = Field(..., min_length=1)


class BatchDeleteNotificationRequest(BaseSchema):
    """批量删除通知"""
    notification_ids: List[str] = Field(..., min_length=1)


# ========== 通知偏好设置 ==========

class NotificationTypePreference(BaseSchema):
    """单个通知类型偏好"""
    enabled: bool = True
    channels: List[NotificationChannel] = [NotificationChannel.PUSH]
    quiet_hours: bool = False  # 是否遵守免打扰时间


class NotificationPreferences(BaseSchema):
    """通知偏好设置"""
    user_id: str
    global_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, description="免打扰开始时间 HH:MM")
    quiet_hours_end: Optional[str] = Field(None, description="免打扰结束时间 HH:MM")
    type_preferences: Dict[NotificationType, NotificationTypePreference] = {}


class UpdateNotificationPreferencesRequest(BaseSchema):
    """更新通知偏好"""
    global_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    type_preferences: Optional[Dict[str, NotificationTypePreference]] = None


# ========== 推送通知 ==========

class PushNotificationRequest(BaseSchema):
    """推送通知请求（管理端使用）"""
    user_ids: List[str] = Field(default=[], description="指定用户，为空则全量推送")
    user_roles: List[str] = Field(default=[], description="指定角色")
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=500)
    notification_type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class PushNotificationResult(BaseSchema):
    """推送结果"""
    total_users: int
    success_count: int
    failed_count: int
    failed_users: List[str] = []


# ========== 设备Token ==========

class DeviceTokenRegister(BaseSchema):
    """注册设备Token"""
    user_id: str
    device_token: str
    device_type: str = Field(..., description="设备类型: ios/android/web")
    device_id: Optional[str] = None
    app_version: Optional[str] = None


class DeviceTokenResponse(BaseSchema):
    """设备Token响应"""
    id: str
    user_id: str
    device_token: str
    device_type: str
    device_id: Optional[str] = None
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    created_at: datetime
