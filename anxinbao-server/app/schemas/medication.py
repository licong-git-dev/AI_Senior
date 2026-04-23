"""
用药提醒相关模式定义
"""
from datetime import datetime, date, time
from typing import Optional, List
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin


class MedicationFrequency(str, Enum):
    """服药频率"""
    ONCE_DAILY = 'once_daily'  # 每日一次
    TWICE_DAILY = "twice_daily"  # 每日两次
    THREE_TIMES_DAILY = "three_times_daily"  # 每日三次
    FOUR_TIMES_DAILY = "four_times_daily"  # 每日四次
    AS_NEEDED = 'as_needed'  # 按需服用
    WEEKLY = 'weekly'  # 每周
    CUSTOM = 'custom'  # 自定义


class MedicationStatus(str, Enum):
    """服药状态"""
    PENDING = 'pending'  # 待服用
    TAKEN = 'taken'  # 已服用
    MISSED = 'missed'  # 漏服
    SKIPPED = 'skipped'  # 跳过


class MedicationType(str, Enum):
    """药物类型"""
    TABLET = 'tablet'  # 片剂
    CAPSULE = 'capsule'  # 胶囊
    LIQUID = 'liquid'  # 液体
    INJECTION = 'injection'  # 注射
    TOPICAL = 'topical'  # 外用
    INHALER = 'inhaler'  # 吸入剂
    PATCH = 'patch'  # 贴剂
    OTHER = 'other'  # 其他


# ========== 药物信息 ==========

class MedicationBase(BaseSchema):
    """药物基础信息"""
    name: str = Field(..., max_length=100, description='药物名称')
    dosage: str = Field(..., max_length=50, description="剂量，如'1片'")
    medication_type: MedicationType = Field(default=MedicationType.TABLET)
    frequency: MedicationFrequency = Field(default=MedicationFrequency.ONCE_DAILY)
    times: List[str] = Field(..., description='服药时间，如["08:00", "20:00"]')
    notes: Optional[str] = Field(None, max_length=500, description='备注')
    instructions: Optional[str] = Field(None, description='服用说明')
    side_effects: Optional[str] = Field(None, description='副作用提示')

    @field_validator('times')
    @classmethod
    def validate_times(cls, v):
        import re
        time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
        for t in v:
            if not time_pattern.match(t):
                raise ValueError(f'时间格式错误: {t}，应为 HH:MM')
        return sorted(v)


class MedicationCreate(MedicationBase):
    """创建用药计划"""
    user_id: str
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    prescriber: Optional[str] = Field(None, description='开药医生')
    pharmacy: Optional[str] = Field(None, description='购药药店')
    quantity: Optional[int] = Field(None, ge=0, description='库存数量')


class MedicationUpdate(BaseSchema):
    """更新用药计划"""
    dosage: Optional[str] = None
    frequency: Optional[MedicationFrequency] = None
    times: Optional[List[str]] = None
    notes: Optional[str] = None
    instructions: Optional[str] = None
    end_date: Optional[date] = None
    quantity: Optional[int] = None
    is_active: Optional[bool] = None


class MedicationResponse(MedicationBase, TimestampMixin):
    """用药计划响应"""
    id: str
    user_id: str
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = True
    prescriber: Optional[str] = None
    pharmacy: Optional[str] = None
    quantity: Optional[int] = None
    low_stock_alert: bool = False


# ========== 服药记录 ==========

class MedicationRecordCreate(BaseSchema):
    """创建服药记录"""
    medication_id: str
    user_id: str
    scheduled_time: datetime
    status: MedicationStatus = MedicationStatus.PENDING
    notes: Optional[str] = None


class MedicationRecordUpdate(BaseSchema):
    """更新服药记录"""
    status: MedicationStatus
    taken_time: Optional[datetime] = None
    notes: Optional[str] = None


class MedicationRecordResponse(BaseSchema, TimestampMixin):
    """服药记录响应"""
    id: str
    medication_id: str
    medication_name: str
    user_id: str
    scheduled_time: datetime
    taken_time: Optional[datetime] = None
    status: MedicationStatus
    notes: Optional[str] = None


class TakeMedicationRequest(BaseSchema):
    """记录服药请求"""
    notes: Optional[str] = None
    taken_time: Optional[datetime] = None  # 默认当前时间


class SkipMedicationRequest(BaseSchema):
    """跳过服药请求"""
    reason: str = Field(..., max_length=200, description='跳过原因')


# ========== 今日服药计划 ==========

class TodayMedicationItem(BaseSchema):
    """今日服药项"""
    medication_id: str
    medication_name: str
    dosage: str
    medication_type: MedicationType
    scheduled_time: str
    status: MedicationStatus
    record_id: Optional[str] = None
    notes: Optional[str] = None
    instructions: Optional[str] = None


class TodayMedicationSchedule(BaseSchema):
    """今日服药计划"""
    user_id: str
    date: date
    schedule: List[TodayMedicationItem]
    total_count: int
    taken_count: int
    missed_count: int
    pending_count: int

    @property
    def completion_rate(self) -> float:
        if self.total_count == 0:
            return 100.0
        return round(self.taken_count / self.total_count * 100, 1)


# ========== 用药统计 ==========

class MedicationStats(BaseSchema):
    """用药统计"""
    user_id: str
    period: str  # daily/weekly/monthly
    start_date: date
    end_date: date
    total_scheduled: int
    total_taken: int
    total_missed: int
    total_skipped: int
    compliance_rate: float = Field(ge=0, le=100)
    medications: List[dict]  # 各药物统计


# ========== 药物提醒设置 ==========

class MedicationReminderSettings(BaseSchema):
    """用药提醒设置"""
    user_id: str
    enabled: bool = True
    advance_minutes: int = Field(default=15, ge=0, le=60, description='提前提醒分钟数')
    reminder_methods: List[str] = Field(default=['push', 'voice'], description='提醒方式')
    snooze_minutes: int = Field(default=10, ge=5, le=30, description='稍后提醒间隔')
    max_reminders: int = Field(default=3, ge=1, le=5, description='最大提醒次数')
    quiet_hours_start: Optional[str] = None  # 免打扰开始时间
    quiet_hours_end: Optional[str] = None  # 免打扰结束时间


class UpdateReminderSettingsRequest(BaseSchema):
    """更新提醒设置"""
    enabled: Optional[bool] = None
    advance_minutes: Optional[int] = None
    reminder_methods: Optional[List[str]] = None
    snooze_minutes: Optional[int] = None
    max_reminders: Optional[int] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
