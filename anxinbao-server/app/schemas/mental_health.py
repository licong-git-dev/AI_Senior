"""
心理健康相关模式定义
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class MoodType(str, Enum):
    """心情类型"""
    HAPPY = 'happy'  # 开心
    CALM = 'calm'  # 平静
    NEUTRAL = 'neutral'  # 一般
    TIRED = 'tired'  # 疲惫
    ANXIOUS = 'anxious'  # 焦虑
    SAD = 'sad'  # 难过
    ANGRY = 'angry'  # 生气
    LONELY = "lonely"  # 孤独


class AssessmentType(str, Enum):
    """评估类型"""
    PHQ9 = 'phq9'  # 抑郁筛查
    GAD7 = 'gad7'  # 焦虑筛查
    LONELINESS = "loneliness"  # 孤独感评估
    SLEEP_QUALITY = "sleep_quality"  # 睡眠质量
    LIFE_SATISFACTION = "life_satisfaction"  # 生活满意度
    COGNITIVE = "cognitive"  # 认知评估


class SeverityLevel(str, Enum):
    """严重程度"""
    MINIMAL = 'minimal'  # 极轻
    MILD = 'mild'  # 轻度
    MODERATE = "moderate"  # 中度
    MODERATELY_SEVERE = "moderately_severe"  # 中重度
    SEVERE = "severe"  # 重度


# ========== 心情记录 ==========

class MoodRecordBase(BaseSchema):
    """心情记录基础"""
    mood_type: MoodType
    intensity: int = Field(ge=1, le=10, description='强度 1-10')
    notes: Optional[str] = Field(None, max_length=500)
    triggers: List[str] = Field(default=[], description='触发因素')
    activities: List[str] = Field(default=[], description="相关活动")


class MoodRecordCreate(MoodRecordBase):
    """创建心情记录"""
    user_id: str
    recorded_at: Optional[datetime] = None


class MoodRecordResponse(MoodRecordBase, TimestampMixin):
    """心情记录响应"""
    id: str
    user_id: str
    recorded_at: datetime


class MoodRecordUpdate(BaseSchema):
    """更新心情记录"""
    mood_type: Optional[MoodType] = None
    intensity: Optional[int] = None
    notes: Optional[str] = None
    triggers: Optional[List[str]] = None
    activities: Optional[List[str]] = None


# ========== 心情趋势 ==========

class MoodTrendPoint(BaseSchema):
    """心情趋势数据点"""
    date: date
    average_intensity: float
    dominant_mood: MoodType
    record_count: int


class MoodTrendResponse(BaseSchema):
    """心情趋势响应"""
    user_id: str
    period_days: int
    trend: List[MoodTrendPoint]
    overall_trend: str = Field(description="整体趋势: improving/stable/declining")
    most_common_mood: MoodType
    average_intensity: float


# ========== 心理评估 ==========

class AssessmentQuestion(BaseSchema):
    """评估问题"""
    id: str
    text: str
    options: List[Dict[str, Any]]  # {value: int, label: str}


class AssessmentTemplate(BaseSchema):
    """评估模板"""
    id: str
    assessment_type: AssessmentType
    name: str
    description: str
    questions: List[AssessmentQuestion]
    max_score: int
    scoring_interpretation: Dict[str, str]  # 分数区间对应解释


class AssessmentSubmission(BaseSchema):
    """评估提交"""
    user_id: str
    assessment_type: AssessmentType
    answers: List[Dict[str, int]]  # {question_id: str, answer: int}


class AssessmentResult(BaseSchema, TimestampMixin):
    """评估结果"""
    id: str
    user_id: str
    assessment_type: AssessmentType
    total_score: int
    max_score: int
    severity_level: SeverityLevel
    interpretation: str
    recommendations: List[str]
    answers: List[Dict[str, Any]]
    completed_at: datetime


class AssessmentHistory(BaseSchema):
    """评估历史"""
    user_id: str
    assessment_type: AssessmentType
    results: List[AssessmentResult]
    trend: str = Field(description="趋势: improving/stable/worsening")


# ========== 睡眠记录 ==========

class SleepQuality(str, Enum):
    """睡眠质量"""
    VERY_POOR = "very_poor"
    POOR = 'poor'
    FAIR = 'fair'
    GOOD = 'good'
    EXCELLENT = 'excellent'


class SleepRecordBase(BaseSchema):
    """睡眠记录基础"""
    bedtime: datetime
    wake_time: datetime
    quality: SleepQuality
    deep_sleep_minutes: Optional[int] = Field(None, ge=0)
    light_sleep_minutes: Optional[int] = Field(None, ge=0)
    rem_minutes: Optional[int] = Field(None, ge=0)
    awake_times: int = Field(default=0, ge=0)
    notes: Optional[str] = None


class SleepRecordCreate(SleepRecordBase):
    """创建睡眠记录"""
    user_id: str


class SleepRecordResponse(SleepRecordBase, TimestampMixin):
    """睡眠记录响应"""
    id: str
    user_id: str
    total_sleep_minutes: int
    sleep_efficiency: float = Field(ge=0, le=100, description="睡眠效率%")


class SleepRecordUpdate(BaseSchema):
    """更新睡眠记录"""
    bedtime: Optional[datetime] = None
    wake_time: Optional[datetime] = None
    quality: Optional[SleepQuality] = None
    awake_times: Optional[int] = None
    notes: Optional[str] = None


class SleepStats(BaseSchema):
    """睡眠统计"""
    user_id: str
    period: str
    average_duration_minutes: float
    average_quality_score: float
    average_efficiency: float
    by_quality: Dict[str, int]
    trend: List[Dict[str, Any]]


# ========== 社交互动 ==========

class SocialInteractionType(str, Enum):
    """社交类型"""
    FAMILY_CALL = "family_call"  # 家人通话
    FRIEND_CHAT = "friend_chat"  # 朋友聊天
    COMMUNITY_ACTIVITY = "community_activity"  # 社区活动
    ONLINE_SOCIAL = "online_social"  # 线上社交
    VISIT = "visit"  # 探访


class SocialInteractionRecord(BaseSchema, TimestampMixin):
    """社交互动记录"""
    id: str
    user_id: str
    interaction_type: SocialInteractionType
    duration_minutes: Optional[int] = None
    participants: List[str] = []
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class SocialInteractionCreate(BaseSchema):
    """创建社交互动记录"""
    user_id: str
    interaction_type: SocialInteractionType
    duration_minutes: Optional[int] = None
    participants: List[str] = []
    satisfaction_score: Optional[int] = None
    notes: Optional[str] = None


class SocialStats(BaseSchema):
    """社交统计"""
    user_id: str
    period: str
    total_interactions: int
    by_type: Dict[str, int]
    total_duration_minutes: int
    average_satisfaction: float
    isolation_risk: str = Field(description="孤独风险: low/medium/high")


# ========== 放松练习 ==========

class RelaxationType(str, Enum):
    """放松类型"""
    BREATHING = 'breathing'  # 呼吸练习
    MEDITATION = "meditation"  # 冥想
    MUSCLE_RELAXATION = "muscle_relaxation"  # 肌肉放松
    MINDFULNESS = "mindfulness"  # 正念
    GUIDED_IMAGERY = "guided_imagery"  # 引导想象


class RelaxationExercise(BaseSchema):
    """放松练习"""
    id: str
    name: str
    relaxation_type: RelaxationType
    duration_minutes: int
    difficulty_level: int = Field(ge=1, le=5)
    description: str
    instructions: List[str]
    audio_url: Optional[str] = None
    video_url: Optional[str] = None


class RelaxationSessionRecord(BaseSchema, TimestampMixin):
    """放松练习记录"""
    id: str
    user_id: str
    exercise_id: str
    exercise_name: str
    relaxation_type: RelaxationType
    duration_minutes: int
    completed: bool
    effectiveness_score: Optional[int] = Field(None, ge=1, le=5)
    mood_before: Optional[MoodType] = None
    mood_after: Optional[MoodType] = None


class RelaxationSessionCreate(BaseSchema):
    """创建放松练习记录"""
    user_id: str
    exercise_id: str
    duration_minutes: int
    completed: bool = True
    effectiveness_score: Optional[int] = None
    mood_before: Optional[MoodType] = None
    mood_after: Optional[MoodType] = None


# ========== 心理健康评分 ==========

class MentalHealthScore(BaseSchema):
    """心理健康评分"""
    user_id: str
    date: date
    overall_score: int = Field(ge=0, le=100)
    mood_score: int = Field(ge=0, le=100)
    sleep_score: int = Field(ge=0, le=100)
    social_score: int = Field(ge=0, le=100)
    anxiety_score: int = Field(ge=0, le=100, description='越低越好')
    depression_score: int = Field(ge=0, le=100, description="越低越好")
    status: str = Field(description="状态: excellent/good/fair/needs_attention/concerning")
    recommendations: List[str] = []


class MentalHealthTrend(BaseSchema):
    """心理健康趋势"""
    user_id: str
    period_days: int
    scores: List[MentalHealthScore]
    overall_trend: str
    improvement_areas: List[str]
    concern_areas: List[str]


# ========== 心理健康建议 ==========

class MentalHealthTip(BaseSchema):
    """心理健康建议"""
    id: str
    category: str
    title: str
    content: str
    priority: int = Field(ge=1, le=5)
    related_areas: List[str] = []


class DailyMentalHealthSummary(BaseSchema):
    """每日心理健康摘要"""
    user_id: str
    date: date
    mood_records: List[MoodRecordResponse]
    sleep_record: Optional[SleepRecordResponse] = None
    social_interactions: List[SocialInteractionRecord]
    relaxation_sessions: List[RelaxationSessionRecord]
    overall_assessment: str
    tips: List[MentalHealthTip]
