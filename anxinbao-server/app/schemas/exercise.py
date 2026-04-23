"""
运动相关模式定义
"""
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class ExerciseType(str, Enum):
    """运动类型"""
    WALKING = 'walking'  # 步行
    RUNNING = 'running'  # 跑步
    CYCLING = 'cycling'  # 骑行
    SWIMMING = 'swimming'  # 游泳
    TAI_CHI = 'tai_chi'  # 太极
    YOGA = 'yoga'  # 瑜伽
    STRETCHING = 'stretching'  # 拉伸
    STRENGTH = "strength"  # 力量训练
    REHABILITATION = "rehabilitation"  # 康复训练
    DANCE = 'dance'  # 舞蹈
    OTHER = "other"  # 其他


class ExerciseIntensity(str, Enum):
    """运动强度"""
    LIGHT = 'light'  # 轻度
    MODERATE = 'moderate'  # 中度
    VIGOROUS = "vigorous"  # 高强度


class ExerciseStatus(str, Enum):
    """运动状态"""
    SCHEDULED = 'scheduled'  # 已计划
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = 'completed'  # 已完成
    SKIPPED = 'skipped'  # 已跳过
    CANCELLED = "cancelled"  # 已取消


# ========== 运动记录 ==========

class ExerciseRecordBase(BaseSchema):
    """运动记录基础"""
    exercise_type: ExerciseType
    intensity: ExerciseIntensity = ExerciseIntensity.MODERATE
    duration_minutes: int = Field(..., ge=1, le=480, description="持续时间(分钟)")
    notes: Optional[str] = Field(None, max_length=500)


class ExerciseRecordCreate(ExerciseRecordBase):
    """创建运动记录"""
    user_id: str
    started_at: datetime
    calories_burned: Optional[int] = Field(None, ge=0)
    steps: Optional[int] = Field(None, ge=0)
    distance_meters: Optional[int] = Field(None, ge=0)
    heart_rate_avg: Optional[int] = Field(None, ge=30, le=250)
    heart_rate_max: Optional[int] = Field(None, ge=30, le=250)


class ExerciseRecordResponse(ExerciseRecordBase, TimestampMixin):
    """运动记录响应"""
    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: ExerciseStatus
    calories_burned: Optional[int] = None
    steps: Optional[int] = None
    distance_meters: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    source: str = Field(default='manual', description="数据来源")


class ExerciseRecordUpdate(BaseSchema):
    """更新运动记录"""
    duration_minutes: Optional[int] = None
    intensity: Optional[ExerciseIntensity] = None
    calories_burned: Optional[int] = None
    steps: Optional[int] = None
    distance_meters: Optional[int] = None
    notes: Optional[str] = None


# ========== 运动计划 ==========

class ExercisePlanBase(BaseSchema):
    """运动计划基础"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    exercise_type: ExerciseType
    target_duration_minutes: int = Field(..., ge=5, le=120)
    intensity: ExerciseIntensity = ExerciseIntensity.MODERATE
    schedule_days: List[int] = Field(..., description='周几执行 1-7')
    schedule_time: str = Field(..., description="执行时间 HH:MM")


class ExercisePlanCreate(ExercisePlanBase):
    """创建运动计划"""
    user_id: str
    start_date: date
    end_date: Optional[date] = None
    reminder_enabled: bool = True
    reminder_minutes_before: int = Field(default=15)


class ExercisePlanResponse(ExercisePlanBase, TimestampMixin):
    """运动计划响应"""
    id: str
    user_id: str
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = True
    reminder_enabled: bool = True
    total_sessions: int = 0
    completed_sessions: int = 0
    completion_rate: float = 0


class ExercisePlanUpdate(BaseSchema):
    """更新运动计划"""
    name: Optional[str] = None
    target_duration_minutes: Optional[int] = None
    intensity: Optional[ExerciseIntensity] = None
    schedule_days: Optional[List[int]] = None
    schedule_time: Optional[str] = None
    is_active: Optional[bool] = None
    reminder_enabled: Optional[bool] = None


# ========== 康复训练 ==========

class RehabilitationType(str, Enum):
    """康复类型"""
    POST_SURGERY = "post_surgery"  # 术后康复
    STROKE = 'stroke'  # 中风康复
    JOINT = 'joint'  # 关节康复
    BALANCE = 'balance'  # 平衡训练
    COGNITIVE = "cognitive"  # 认知康复
    RESPIRATORY = "respiratory"  # 呼吸康复


class RehabilitationExercise(BaseSchema):
    """康复训练项目"""
    id: str
    name: str
    description: str
    rehabilitation_type: RehabilitationType
    duration_minutes: int
    difficulty_level: int = Field(ge=1, le=5)
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    instructions: List[str] = []
    precautions: List[str] = []


class RehabilitationPlanCreate(BaseSchema):
    """创建康复计划"""
    user_id: str
    name: str
    rehabilitation_type: RehabilitationType
    exercises: List[str] = Field(..., description="训练项目ID列表")
    frequency_per_week: int = Field(ge=1, le=7)
    duration_weeks: int = Field(ge=1, le=52)
    doctor_name: Optional[str] = None
    doctor_notes: Optional[str] = None


class RehabilitationPlanResponse(BaseSchema, TimestampMixin):
    """康复计划响应"""
    id: str
    user_id: str
    name: str
    rehabilitation_type: RehabilitationType
    exercises: List[RehabilitationExercise]
    frequency_per_week: int
    duration_weeks: int
    current_week: int
    progress_percentage: float
    doctor_name: Optional[str] = None
    doctor_notes: Optional[str] = None
    is_active: bool = True


class RehabilitationProgressRecord(BaseSchema, TimestampMixin):
    """康复进度记录"""
    id: str
    plan_id: str
    exercise_id: str
    completed_at: datetime
    duration_minutes: int
    pain_level: Optional[int] = Field(None, ge=0, le=10)
    difficulty_feedback: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


# ========== 今日运动 ==========

class TodayExerciseItem(BaseSchema):
    """今日运动项"""
    plan_id: str
    plan_name: str
    exercise_type: ExerciseType
    scheduled_time: str
    target_duration_minutes: int
    status: ExerciseStatus
    record_id: Optional[str] = None
    actual_duration_minutes: Optional[int] = None


class TodayExerciseSummary(BaseSchema):
    """今日运动摘要"""
    user_id: str
    date: date
    scheduled_count: int
    completed_count: int
    total_duration_minutes: int
    total_calories: int
    total_steps: int
    items: List[TodayExerciseItem]


# ========== 运动统计 ==========

class ExerciseStats(BaseSchema):
    """运动统计"""
    user_id: str
    period: str  # daily/weekly/monthly
    start_date: date
    end_date: date
    total_sessions: int
    total_duration_minutes: int
    total_calories: int
    total_steps: int
    total_distance_meters: int
    by_type: Dict[str, int]
    by_intensity: Dict[str, int]
    daily_average_duration: float
    streak_days: int = 0  # 连续运动天数


class ExerciseGoal(BaseSchema):
    """运动目标"""
    user_id: str
    goal_type: str = Field(description="目标类型: steps/duration/calories/sessions")
    target_value: int
    current_value: int
    period: str = Field(description="周期: daily/weekly/monthly")
    start_date: date
    end_date: date
    is_achieved: bool = False


class ExerciseGoalCreate(BaseSchema):
    """创建运动目标"""
    user_id: str
    goal_type: str
    target_value: int
    period: str


class ExerciseGoalUpdate(BaseSchema):
    """更新运动目标"""
    target_value: Optional[int] = None
    is_active: Optional[bool] = None
