"""
主动交互系统 Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class GreetingType(str, Enum):
    """问候类型"""
    MORNING = "morning"
    AFTERNOON = 'afternoon'
    EVENING = 'evening'
    HEALTH_CHECK = "health_check"
    CARE = "care"


class ReminderType(str, Enum):
    """提醒类型"""
    WATER = "water"
    STAND_UP = 'stand_up'
    EXERCISE = 'exercise'
    REST = 'rest'
    MEDICATION = 'medication'
    CUSTOM = 'custom'


class TriggerType(str, Enum):
    """触发类型"""
    TIME_BASED = "time_based"
    INTERVAL = 'interval'
    BEHAVIOR_BASED = "behavior_based"


class PatternType(str, Enum):
    """行为模式类型"""
    WAKE_TIME = "wake_time"
    SLEEP_TIME = 'sleep_time'
    MEAL_TIME = 'meal_time'
    ACTIVITY_PEAK = "activity_peak"
    INACTIVE_PERIOD = "inactive_period"


class InteractionType(str, Enum):
    """主动交互类型"""
    GREETING = "greeting"
    REMINDER = 'reminder'
    CARE_INQUIRY = "care_inquiry"
    HEALTH_CHECK = "health_check"


class ResponseType(str, Enum):
    """用户回应类型"""
    POSITIVE = "positive"
    NEUTRAL = 'neutral'
    NEGATIVE = 'negative'
    NO_RESPONSE = "no_response"


# ==================== 主动问候 ====================

class ProactiveGreetingCreate(BaseModel):
    """创建主动问候配置"""
    user_id: int
    greeting_type: GreetingType
    schedule_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description='时间格式 HH:MM')
    schedule_days: List[int] = Field(default=[1, 2, 3, 4, 5, 6, 7], description="周几，1-7")
    greeting_template: Optional[str] = None
    include_weather: bool = True
    include_health_tip: bool = True
    include_medication_reminder: bool = True


class ProactiveGreetingUpdate(BaseModel):
    """更新主动问候配置"""
    schedule_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    schedule_days: Optional[List[int]] = None
    greeting_template: Optional[str] = None
    include_weather: Optional[bool] = None
    include_health_tip: Optional[bool] = None
    include_medication_reminder: Optional[bool] = None
    is_enabled: Optional[bool] = None


class ProactiveGreetingResponse(BaseModel):
    """主动问候配置响应"""
    id: int
    user_id: int
    greeting_type: str
    schedule_time: str
    schedule_days: List[int]
    greeting_template: Optional[str]
    include_weather: bool
    include_health_tip: bool
    include_medication_reminder: bool
    is_enabled: bool
    last_triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 主动提醒 ====================

class ProactiveReminderCreate(BaseModel):
    """创建主动提醒"""
    user_id: int
    reminder_type: ReminderType
    title: str = Field(..., max_length=100)
    content: Optional[str] = None
    trigger_type: TriggerType
    schedule_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    interval_minutes: Optional[int] = Field(None, ge=15, le=480)
    behavior_trigger: Optional[str] = None
    min_interval_minutes: int = Field(default=60, ge=15)
    quiet_during_sleep: bool = True
    skip_if_interacted: bool = True


class ProactiveReminderUpdate(BaseModel):
    """更新主动提醒"""
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = None
    schedule_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    interval_minutes: Optional[int] = Field(None, ge=15, le=480)
    min_interval_minutes: Optional[int] = Field(None, ge=15)
    quiet_during_sleep: Optional[bool] = None
    skip_if_interacted: Optional[bool] = None
    is_enabled: Optional[bool] = None


class ProactiveReminderResponse(BaseModel):
    """主动提醒响应"""
    id: int
    user_id: int
    reminder_type: str
    title: str
    content: Optional[str]
    trigger_type: str
    schedule_time: Optional[str]
    interval_minutes: Optional[int]
    behavior_trigger: Optional[str]
    min_interval_minutes: int
    quiet_during_sleep: bool
    skip_if_interacted: bool
    is_enabled: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 用户行为模式 ====================

class BehaviorPatternCreate(BaseModel):
    """创建行为模式记录"""
    user_id: int
    pattern_type: PatternType
    pattern_value: str
    confidence: float = Field(default=0.5, ge=0, le=1)


class BehaviorPatternResponse(BaseModel):
    """行为模式响应"""
    id: int
    user_id: int
    pattern_type: str
    pattern_value: str
    confidence: float
    sample_count: int
    last_occurrence: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 主动交互日志 ====================

class ProactiveInteractionLogCreate(BaseModel):
    """创建主动交互日志"""
    user_id: int
    interaction_type: InteractionType
    trigger_source: Optional[str] = None
    content: Optional[str] = None


class ProactiveInteractionLogResponse(BaseModel):
    """主动交互日志响应"""
    id: int
    user_id: int
    interaction_type: str
    trigger_source: Optional[str]
    content: Optional[str]
    user_response: Optional[str]
    response_type: Optional[str]
    triggered_at: datetime
    responded_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateInteractionResponse(BaseModel):
    """更新交互回应"""
    user_response: str
    response_type: ResponseType


# ==================== 触发主动交互请求 ====================

class TriggerGreetingRequest(BaseModel):
    """触发主动问候请求"""
    user_id: int
    greeting_type: Optional[GreetingType] = None
    custom_message: Optional[str] = None


class TriggerGreetingResponse(BaseModel):
    """触发主动问候响应"""
    success: bool
    interaction_id: int
    greeting_content: str
    includes: dict  # {'weather': "...", 'health_tip': '...', 'medication': '...'}


class TriggerReminderRequest(BaseModel):
    """触发主动提醒请求"""
    user_id: int
    reminder_id: Optional[int] = None
    reminder_type: Optional[ReminderType] = None
    custom_content: Optional[str] = None


class TriggerReminderResponse(BaseModel):
    """触发主动提醒响应"""
    success: bool
    interaction_id: int
    reminder_content: str


# ==================== 智能问候生成 ====================

class GenerateGreetingRequest(BaseModel):
    """生成智能问候请求"""
    user_id: int
    context: Optional[dict] = None  # 上下文信息


class GenerateGreetingResponse(BaseModel):
    """生成智能问候响应"""
    greeting: str
    components: dict  # 各组成部分
    personalization_applied: List[str]  # 使用的个性化元素
