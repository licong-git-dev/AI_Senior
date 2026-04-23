"""
情感记忆系统 Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ==================== 枚举类型 ====================

class MemoryType(str, Enum):
    """记忆类型"""
    FAMILY = "family"
    EVENT = 'event'
    PREFERENCE = 'preference'
    HEALTH = 'health'
    EMOTION = 'emotion'
    STORY = 'story'


class DateType(str, Enum):
    """重要日期类型"""
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    MEMORIAL = "memorial"
    CUSTOM = 'custom'


class StoryCateogry(str, Enum):
    """人生故事类别"""
    CHILDHOOD = "childhood"
    YOUTH = 'youth'
    CAREER = 'career'
    FAMILY = 'family'
    TRAVEL = 'travel'
    CUSTOM = 'custom'


class AIPersona(str, Enum):
    """AI人设类型"""
    CARING_COMPANION = "caring_companion"
    HEALTH_ADVISOR = "health_advisor"
    CHEERFUL_FRIEND = "cheerful_friend"


class CommunicationStyle(str, Enum):
    """沟通风格"""
    FORMAL = "formal"
    CASUAL = 'casual'
    CARING = 'caring'


# ==================== 用户画像 ====================

class FamilyMemberInfo(BaseModel):
    """家庭成员信息"""
    name: str
    relation: str
    nickname: Optional[str] = None
    birthday: Optional[str] = None
    notes: Optional[str] = None


class UserProfileCreate(BaseModel):
    """创建用户画像"""
    user_id: int
    nickname: Optional[str] = None
    birth_date: Optional[date] = None
    hometown: Optional[str] = None
    current_city: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """更新用户画像"""
    nickname: Optional[str] = None
    birth_date: Optional[date] = None
    zodiac: Optional[str] = None
    constellation: Optional[str] = None
    hometown: Optional[str] = None
    current_city: Optional[str] = None

    # 家庭信息
    family_info: Optional[Dict[str, Any]] = None

    # 兴趣爱好
    hobbies: Optional[List[str]] = None
    favorite_music: Optional[List[str]] = None
    favorite_foods: Optional[List[str]] = None
    disliked_foods: Optional[List[str]] = None

    # 健康相关
    chronic_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None

    # 性格特点
    personality_traits: Optional[List[str]] = None
    communication_style: Optional[CommunicationStyle] = None
    preferred_topics: Optional[List[str]] = None

    # AI对话风格
    ai_persona: Optional[AIPersona] = None
    response_speed: Optional[str] = None
    verbosity: Optional[str] = None


class UserProfileResponse(BaseModel):
    """用户画像响应"""
    id: int
    user_id: int
    nickname: Optional[str]
    birth_date: Optional[datetime]
    zodiac: Optional[str]
    constellation: Optional[str]
    hometown: Optional[str]
    current_city: Optional[str]

    family_info: Optional[Dict[str, Any]]
    hobbies: Optional[List[str]]
    favorite_music: Optional[List[str]]
    favorite_foods: Optional[List[str]]
    disliked_foods: Optional[List[str]]

    chronic_conditions: Optional[List[str]]
    allergies: Optional[List[str]]
    dietary_restrictions: Optional[List[str]]

    personality_traits: Optional[List[str]]
    communication_style: Optional[str]
    preferred_topics: Optional[List[str]]

    ai_persona: str
    response_speed: str
    verbosity: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 用户记忆 ====================

class UserMemoryCreate(BaseModel):
    """创建用户记忆"""
    user_id: int
    memory_type: MemoryType
    category: Optional[str] = None
    key: str = Field(..., max_length=100)
    value: str
    context: Optional[str] = None
    source_conversation_id: Optional[int] = None
    importance: int = Field(default=5, ge=1, le=10)
    confidence: float = Field(default=0.8, ge=0, le=1)


class UserMemoryUpdate(BaseModel):
    """更新用户记忆"""
    value: Optional[str] = None
    context: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=10)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class UserMemoryResponse(BaseModel):
    """用户记忆响应"""
    id: int
    user_id: int
    memory_type: str
    category: Optional[str]
    key: str
    value: str
    context: Optional[str]
    source_conversation_id: Optional[int]
    importance: int
    confidence: float
    last_referenced_at: Optional[datetime]
    reference_count: int
    is_verified: bool
    is_active: bool
    extracted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractMemoryRequest(BaseModel):
    """从对话中提取记忆请求"""
    user_id: int
    conversation_id: int
    conversation_content: str


class ExtractMemoryResponse(BaseModel):
    """提取记忆响应"""
    extracted_memories: List[UserMemoryResponse]
    total_extracted: int


class RetrieveMemoryRequest(BaseModel):
    """检索记忆请求"""
    user_id: int
    memory_types: Optional[List[MemoryType]] = None
    keywords: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=50)


class RetrieveMemoryResponse(BaseModel):
    """检索记忆响应"""
    memories: List[UserMemoryResponse]
    total: int


# ==================== 重要日期 ====================

class ImportantDateCreate(BaseModel):
    """创建重要日期"""
    user_id: int
    date_type: DateType
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    is_lunar: bool = False
    year: Optional[int] = None
    reminder_days_before: int = Field(default=1, ge=0, le=30)
    reminder_enabled: bool = True
    related_person: Optional[str] = None


class ImportantDateUpdate(BaseModel):
    """更新重要日期"""
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    is_lunar: Optional[bool] = None
    year: Optional[int] = None
    reminder_days_before: Optional[int] = Field(None, ge=0, le=30)
    reminder_enabled: Optional[bool] = None
    related_person: Optional[str] = None
    is_active: Optional[bool] = None


class ImportantDateResponse(BaseModel):
    """重要日期响应"""
    id: int
    user_id: int
    date_type: str
    title: str
    description: Optional[str]
    month: int
    day: int
    is_lunar: bool
    year: Optional[int]
    reminder_days_before: int
    reminder_enabled: bool
    related_person: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpcomingDatesResponse(BaseModel):
    """即将到来的重要日期"""
    dates: List[ImportantDateResponse]
    today_dates: List[ImportantDateResponse]


# ==================== 人生故事 ====================

class LifeStoryCreate(BaseModel):
    """创建人生故事"""
    user_id: int
    title: Optional[str] = Field(None, max_length=200)
    content: str
    category: Optional[StoryCateogry] = None
    era: Optional[str] = None
    location: Optional[str] = None
    related_people: Optional[List[str]] = None
    audio_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    emotion_tags: Optional[List[str]] = None
    source: str = "conversation"
    recorded_at: Optional[datetime] = None


class LifeStoryUpdate(BaseModel):
    """更新人生故事"""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    category: Optional[StoryCateogry] = None
    era: Optional[str] = None
    location: Optional[str] = None
    related_people: Optional[List[str]] = None
    audio_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    emotion_tags: Optional[List[str]] = None


class LifeStoryResponse(BaseModel):
    """人生故事响应"""
    id: int
    user_id: int
    title: Optional[str]
    content: str
    category: Optional[str]
    era: Optional[str]
    location: Optional[str]
    related_people: Optional[List[str]]
    audio_url: Optional[str]
    photo_urls: Optional[List[str]]
    emotion_tags: Optional[List[str]]
    source: str
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 对话个性化 ====================

class PersonalizationContext(BaseModel):
    """对话个性化上下文"""
    user_profile: Optional[UserProfileResponse] = None
    relevant_memories: List[UserMemoryResponse] = []
    upcoming_dates: List[ImportantDateResponse] = []
    recent_interactions: int = 0
    last_interaction_time: Optional[datetime] = None


class GeneratePersonalizedResponseRequest(BaseModel):
    """生成个性化回复请求"""
    user_id: int
    user_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class GeneratePersonalizedResponseResponse(BaseModel):
    """生成个性化回复响应"""
    response: str
    personalization_elements: List[str]  # 使用了哪些个性化元素
    memories_referenced: List[str]  # 引用了哪些记忆
    new_memories_extracted: List[Dict[str, Any]]  # 新提取的记忆
