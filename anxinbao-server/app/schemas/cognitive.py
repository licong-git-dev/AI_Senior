"""
认知训练模块 Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class GameType(str, Enum):
    """游戏类型"""
    MEMORY = "memory"
    ATTENTION = 'attention'
    CALCULATION = "calculation"
    LANGUAGE = "language"
    SPATIAL = 'spatial'


class SessionStatus(str, Enum):
    """游戏会话状态"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = 'abandoned'


class AssessmentType(str, Enum):
    """评估类型"""
    MMSE = "mmse"
    MOCA = 'moca'
    CUSTOM = 'custom'
    DAILY = 'daily'


class CognitiveLevel(str, Enum):
    """认知水平"""
    NORMAL = "normal"
    MILD_DECLINE = "mild_decline"
    MODERATE_DECLINE = "moderate_decline"
    SEVERE_DECLINE = "severe_decline"


class Trend(str, Enum):
    """趋势"""
    IMPROVING = "improving"
    STABLE = 'stable'
    DECLINING = 'declining'


# ==================== 认知游戏 ====================

class CognitiveGameCreate(BaseModel):
    """创建认知游戏"""
    name: str = Field(..., max_length=100)
    game_type: GameType
    difficulty_levels: int = Field(default=3, ge=1, le=10)
    description: Optional[str] = None
    instructions: Optional[str] = None
    benefits: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    icon_url: Optional[str] = None


class CognitiveGameUpdate(BaseModel):
    """更新认知游戏"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    instructions: Optional[str] = None
    benefits: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None


class CognitiveGameResponse(BaseModel):
    """认知游戏响应"""
    id: int
    name: str
    game_type: str
    difficulty_levels: int
    description: Optional[str]
    instructions: Optional[str]
    benefits: Optional[str]
    config: Optional[Dict[str, Any]]
    icon_url: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CognitiveGameBrief(BaseModel):
    """认知游戏简要"""
    id: int
    name: str
    game_type: str
    difficulty_levels: int
    icon_url: Optional[str]

    class Config:
        from_attributes = True


# ==================== 游戏会话 ====================

class StartGameSessionRequest(BaseModel):
    """开始游戏会话请求"""
    user_id: int
    game_id: int
    difficulty: int = Field(default=1, ge=1, le=10)


class StartGameSessionResponse(BaseModel):
    """开始游戏会话响应"""
    session_id: int
    game: CognitiveGameBrief
    difficulty: int
    game_data: Dict[str, Any]  # 游戏数据（题目等）


class SubmitGameAnswerRequest(BaseModel):
    """提交游戏答案请求"""
    session_id: int
    answer: Any  # 答案内容
    time_taken_seconds: Optional[int] = None


class SubmitGameAnswerResponse(BaseModel):
    """提交游戏答案响应"""
    is_correct: bool
    correct_answer: Any
    current_score: int
    feedback: Optional[str]
    next_question: Optional[Dict[str, Any]]


class EndGameSessionRequest(BaseModel):
    """结束游戏会话请求"""
    session_id: int
    abandon: bool = False


class GameSessionResponse(BaseModel):
    """游戏会话响应"""
    id: int
    user_id: int
    game_id: int
    difficulty: int
    score: int
    max_score: Optional[int]
    accuracy: Optional[float]
    completion_time_seconds: Optional[int]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class GameSessionDetailResponse(BaseModel):
    """游戏会话详情响应"""
    session: GameSessionResponse
    game: CognitiveGameBrief
    game_data: Optional[Dict[str, Any]]
    performance_analysis: Optional[Dict[str, Any]]


# ==================== 认知评估 ====================

class StartAssessmentRequest(BaseModel):
    """开始认知评估请求"""
    user_id: int
    assessment_type: AssessmentType


class StartAssessmentResponse(BaseModel):
    """开始认知评估响应"""
    assessment_id: int
    assessment_type: str
    total_questions: int
    questions: List[Dict[str, Any]]  # 评估题目


class SubmitAssessmentRequest(BaseModel):
    """提交认知评估请求"""
    assessment_id: int
    answers: List[Dict[str, Any]]  # [{'question_id': 1, 'answer': 'xxx'}]


class CognitiveAssessmentResponse(BaseModel):
    """认知评估响应"""
    id: int
    user_id: int
    assessment_type: str
    assessment_date: datetime
    dimension_scores: Optional[Dict[str, Any]]
    total_score: int
    max_score: int
    percentile: Optional[float]
    cognitive_level: Optional[str]
    trend: Optional[str]
    analysis: Optional[str]
    recommendations: Optional[List[str]]
    notified_family: bool
    notification_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentResultResponse(BaseModel):
    """评估结果响应"""
    assessment: CognitiveAssessmentResponse
    comparison_with_previous: Optional[Dict[str, Any]]
    detailed_analysis: Dict[str, Any]
    personalized_recommendations: List[str]
    suggested_training_plan: Optional[Dict[str, Any]]


# ==================== 训练计划 ====================

class TrainingPlanGameConfig(BaseModel):
    """训练计划游戏配置"""
    game_id: int
    difficulty: int = Field(default=1, ge=1, le=10)
    repetitions: int = Field(default=3, ge=1, le=10)


class CognitiveTrainingPlanCreate(BaseModel):
    """创建认知训练计划"""
    user_id: int
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    target_dimensions: Optional[List[str]] = None
    weekly_sessions: int = Field(default=3, ge=1, le=7)
    session_duration_minutes: int = Field(default=15, ge=5, le=60)
    games_config: Optional[List[TrainingPlanGameConfig]] = None
    schedule_days: Optional[List[int]] = None
    schedule_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    start_date: datetime
    end_date: Optional[datetime] = None
    reminder_enabled: bool = True


class CognitiveTrainingPlanUpdate(BaseModel):
    """更新认知训练计划"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    target_dimensions: Optional[List[str]] = None
    weekly_sessions: Optional[int] = Field(None, ge=1, le=7)
    session_duration_minutes: Optional[int] = Field(None, ge=5, le=60)
    games_config: Optional[List[TrainingPlanGameConfig]] = None
    schedule_days: Optional[List[int]] = None
    schedule_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_date: Optional[datetime] = None
    reminder_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class CognitiveTrainingPlanResponse(BaseModel):
    """认知训练计划响应"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    target_dimensions: Optional[List[str]]
    weekly_sessions: int
    session_duration_minutes: int
    games_config: Optional[List[Dict[str, Any]]]
    schedule_days: Optional[List[int]]
    schedule_time: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    reminder_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 统计与报告 ====================

class CognitiveStatsRequest(BaseModel):
    """认知统计请求"""
    user_id: int
    days: int = Field(default=30, ge=7, le=365)


class DimensionStats(BaseModel):
    """维度统计"""
    dimension: str
    average_score: float
    trend: str
    sessions_count: int


class CognitiveStatsResponse(BaseModel):
    """认知统计响应"""
    user_id: int
    period_days: int
    total_sessions: int
    total_time_minutes: int
    average_score: float
    best_dimension: str
    weakest_dimension: str
    dimension_stats: List[DimensionStats]
    recent_assessments: List[CognitiveAssessmentResponse]
    overall_trend: str
    streak_days: int  # 连续训练天数


class GenerateTrainingReportRequest(BaseModel):
    """生成训练报告请求"""
    user_id: int
    period_days: int = Field(default=30, ge=7, le=365)


class TrainingReportResponse(BaseModel):
    """训练报告响应"""
    user_id: int
    report_period: str
    summary: str
    total_sessions: int
    total_time_minutes: int
    completion_rate: float
    performance_by_dimension: Dict[str, Dict[str, Any]]
    progress_chart_data: List[Dict[str, Any]]
    achievements: List[str]
    recommendations: List[str]
    generated_at: datetime


# ==================== 推荐与建议 ====================

class GetRecommendedGamesRequest(BaseModel):
    """获取推荐游戏请求"""
    user_id: int
    limit: int = Field(default=5, ge=1, le=10)


class RecommendedGame(BaseModel):
    """推荐游戏"""
    game: CognitiveGameBrief
    recommended_difficulty: int
    reason: str
    expected_benefit: str


class GetRecommendedGamesResponse(BaseModel):
    """获取推荐游戏响应"""
    recommended_games: List[RecommendedGame]
    daily_goal_completed: bool
    next_scheduled_session: Optional[datetime]
