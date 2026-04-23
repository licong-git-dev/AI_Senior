"""
健康数据相关模式定义
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin


class HealthRecordType(str, Enum):
    """健康记录类型"""
    BLOOD_PRESSURE = "blood_pressure"  # 血压
    HEART_RATE = "heart_rate"  # 心率
    BLOOD_SUGAR = "blood_sugar"  # 血糖
    BLOOD_OXYGEN = "blood_oxygen"  # 血氧
    TEMPERATURE = "temperature"  # 体温
    WEIGHT = 'weight'  # 体重
    SLEEP = 'sleep'  # 睡眠
    STEPS = "steps"  # 步数


class HealthDataSource(str, Enum):
    """数据来源"""
    MANUAL = 'manual'  # 手动输入
    DEVICE = 'device'  # 设备采集
    IMPORT = "import"  # 导入


class HealthAlertLevel(str, Enum):
    """健康告警级别"""
    NORMAL = "normal"
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


# ========== 血压 ==========

class BloodPressureValue(BaseSchema):
    """血压值"""
    systolic: int = Field(..., ge=60, le=300, description='收缩压(高压)')
    diastolic: int = Field(..., ge=30, le=200, description='舒张压(低压)')
    pulse: Optional[int] = Field(None, ge=30, le=250, description="脉搏")

    @property
    def level(self) -> HealthAlertLevel:
        if self.systolic >= 180 or self.diastolic >= 120:
            return HealthAlertLevel.CRITICAL
        elif self.systolic >= 140 or self.diastolic >= 90:
            return HealthAlertLevel.HIGH
        elif self.systolic >= 130 or self.diastolic >= 85:
            return HealthAlertLevel.MEDIUM
        elif self.systolic < 90 or self.diastolic < 60:
            return HealthAlertLevel.LOW
        return HealthAlertLevel.NORMAL


class BloodPressureRecord(BaseSchema, TimestampMixin):
    """血压记录"""
    id: str
    user_id: str
    value: BloodPressureValue
    source: HealthDataSource = HealthDataSource.MANUAL
    device_id: Optional[str] = None
    notes: Optional[str] = None
    measured_at: datetime


# ========== 心率 ==========

class HeartRateValue(BaseSchema):
    """心率值"""
    bpm: int = Field(..., ge=30, le=250, description='每分钟心跳次数')
    is_resting: bool = Field(default=True, description="是否静息心率")

    @property
    def level(self) -> HealthAlertLevel:
        if self.bpm > 150 or self.bpm < 40:
            return HealthAlertLevel.CRITICAL
        elif self.bpm > 120 or self.bpm < 50:
            return HealthAlertLevel.HIGH
        elif self.bpm > 100:
            return HealthAlertLevel.MEDIUM
        return HealthAlertLevel.NORMAL


# ========== 血糖 ==========

class BloodSugarValue(BaseSchema):
    """血糖值"""
    value: float = Field(..., ge=0, le=50, description='血糖值 mmol/L')
    is_fasting: bool = Field(default=True, description="是否空腹血糖")

    @property
    def level(self) -> HealthAlertLevel:
        if self.is_fasting:
            if self.value >= 11.1 or self.value < 3.0:
                return HealthAlertLevel.CRITICAL
            elif self.value >= 7.0:
                return HealthAlertLevel.HIGH
            elif self.value >= 6.1:
                return HealthAlertLevel.MEDIUM
        else:
            if self.value >= 16.7 or self.value < 3.0:
                return HealthAlertLevel.CRITICAL
            elif self.value >= 11.1:
                return HealthAlertLevel.HIGH
            elif self.value >= 7.8:
                return HealthAlertLevel.MEDIUM
        return HealthAlertLevel.NORMAL


# ========== 血氧 ==========

class BloodOxygenValue(BaseSchema):
    """血氧值"""
    spo2: int = Field(..., ge=50, le=100, description="血氧饱和度 %")

    @property
    def level(self) -> HealthAlertLevel:
        if self.spo2 < 90:
            return HealthAlertLevel.CRITICAL
        elif self.spo2 < 94:
            return HealthAlertLevel.HIGH
        elif self.spo2 < 96:
            return HealthAlertLevel.MEDIUM
        return HealthAlertLevel.NORMAL


# ========== 体温 ==========

class TemperatureValue(BaseSchema):
    """体温值"""
    celsius: float = Field(..., ge=30, le=45, description='体温 °C')
    measurement_site: str = Field(default="oral", description="测量部位: oral/armpit/ear/forehead")

    @property
    def level(self) -> HealthAlertLevel:
        if self.celsius >= 39.5 or self.celsius < 35.0:
            return HealthAlertLevel.CRITICAL
        elif self.celsius >= 38.5:
            return HealthAlertLevel.HIGH
        elif self.celsius >= 37.5:
            return HealthAlertLevel.MEDIUM
        return HealthAlertLevel.NORMAL


# ========== 睡眠 ==========

class SleepValue(BaseSchema):
    """睡眠数据"""
    total_minutes: int = Field(..., ge=0, le=1440, description='总睡眠时长(分钟)')
    deep_sleep_minutes: Optional[int] = Field(None, ge=0, description='深睡时长')
    light_sleep_minutes: Optional[int] = Field(None, ge=0, description='浅睡时长')
    rem_minutes: Optional[int] = Field(None, ge=0, description='REM睡眠时长')
    awake_times: int = Field(default=0, ge=0, description='夜醒次数')
    sleep_quality_score: Optional[int] = Field(None, ge=0, le=100, description="睡眠质量评分")


# ========== 步数 ==========

class StepsValue(BaseSchema):
    """步数数据"""
    count: int = Field(..., ge=0, description='步数')
    distance_meters: Optional[int] = Field(None, ge=0, description='距离(米)')
    calories: Optional[int] = Field(None, ge=0, description="消耗卡路里")


# ========== 通用健康记录 ==========

class HealthRecordCreate(BaseSchema):
    """创建健康记录请求"""
    user_id: str
    record_type: HealthRecordType
    value: Dict[str, Any]
    source: HealthDataSource = HealthDataSource.MANUAL
    device_id: Optional[str] = None
    notes: Optional[str] = None
    measured_at: Optional[datetime] = None


class HealthRecordUpdate(BaseSchema):
    """更新健康记录"""
    value: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class HealthRecordResponse(BaseSchema, TimestampMixin):
    """健康记录响应"""
    id: str
    user_id: str
    record_type: HealthRecordType
    value: Dict[str, Any]
    unit: str
    source: HealthDataSource
    device_id: Optional[str] = None
    notes: Optional[str] = None
    measured_at: datetime
    alert_level: HealthAlertLevel = HealthAlertLevel.NORMAL


class HealthRecordFilter(BaseSchema):
    """健康记录过滤器"""
    record_type: Optional[HealthRecordType] = None
    source: Optional[HealthDataSource] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    alert_level: Optional[HealthAlertLevel] = None


# ========== 健康趋势 ==========

class HealthTrendPoint(BaseSchema):
    """健康趋势数据点"""
    date: date
    values: List[Dict[str, Any]]
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class HealthTrendResponse(BaseSchema):
    """健康趋势响应"""
    user_id: str
    record_type: HealthRecordType
    period_days: int
    trend: List[HealthTrendPoint]
    overall_trend: str = Field(description="趋势: improving/stable/declining")


# ========== 健康报告 ==========

class HealthReportSummary(BaseSchema):
    """健康报告摘要"""
    record_type: HealthRecordType
    record_count: int
    latest_value: Optional[Dict[str, Any]] = None
    average_value: Optional[Dict[str, Any]] = None
    alert_count: int = 0
    trend: str = "stable"


class HealthReportResponse(BaseSchema):
    """健康报告响应"""
    user_id: str
    report_type: str = Field(description="报告类型: daily/weekly/monthly")
    start_date: date
    end_date: date
    summaries: List[HealthReportSummary]
    overall_score: int = Field(ge=0, le=100, description='综合健康评分')
    recommendations: List[str] = Field(default=[], description="健康建议")
    generated_at: datetime


# ========== 健康告警 ==========

class HealthAlertCreate(BaseSchema):
    """创建健康告警"""
    user_id: str
    alert_type: str
    level: HealthAlertLevel
    title: str
    content: str
    record_id: Optional[str] = None
    record_type: Optional[HealthRecordType] = None
    value: Optional[Dict[str, Any]] = None


class HealthAlertResponse(BaseSchema, TimestampMixin):
    """健康告警响应"""
    id: str
    user_id: str
    alert_type: str
    level: HealthAlertLevel
    title: str
    content: str
    is_read: bool = False
    is_handled: bool = False
    handled_at: Optional[datetime] = None
    handled_by: Optional[str] = None
    handle_notes: Optional[str] = None


class HandleAlertRequest(BaseSchema):
    """处理告警请求"""
    handled_by: str
    handle_notes: Optional[str] = None
