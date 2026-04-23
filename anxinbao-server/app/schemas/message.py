"""
消息相关模式定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class MessageType(str, Enum):
    """消息类型"""
    TEXT = 'text'  # 文本
    IMAGE = 'image'  # 图片
    VOICE = 'voice'  # 语音
    VIDEO = 'video'  # 视频
    FILE = 'file'  # 文件
    LOCATION = "location"  # 位置
    HEALTH_REPORT = "health_report"  # 健康报告
    SYSTEM = "system"  # 系统消息


class ConversationType(str, Enum):
    """会话类型"""
    PRIVATE = 'private'  # 私聊
    GROUP = 'group'  # 群聊
    SYSTEM = "system"  # 系统会话


class MessageStatus(str, Enum):
    """消息状态"""
    SENDING = "sending"
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'


# ========== 消息 ==========

class MessageBase(BaseSchema):
    """消息基础"""
    message_type: MessageType = MessageType.TEXT
    content: str = Field(..., max_length=5000)
    extra: Optional[Dict[str, Any]] = Field(None, description="附加信息")


class MessageCreate(MessageBase):
    """发送消息"""
    conversation_id: str
    sender_id: str
    reply_to_id: Optional[str] = Field(None, description="回复的消息ID")


class MessageResponse(MessageBase, TimestampMixin):
    """消息响应"""
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_avatar: Optional[str] = None
    status: MessageStatus
    reply_to: Optional['MessageResponse'] = None
    is_recalled: bool = False
    recalled_at: Optional[datetime] = None


class MessageUpdate(BaseSchema):
    """更新消息（编辑）"""
    content: str


class RecallMessageRequest(BaseSchema):
    """撤回消息"""
    message_id: str


# ========== 会话 ==========

class ConversationBase(BaseSchema):
    """会话基础"""
    conversation_type: ConversationType
    name: Optional[str] = Field(None, max_length=50)


class ConversationCreate(ConversationBase):
    """创建会话"""
    participant_ids: List[str] = Field(..., min_length=1)


class ConversationResponse(ConversationBase, TimestampMixin):
    """会话响应"""
    id: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    participant_ids: List[str]
    participants: List[Dict[str, Any]] = []  # 参与者信息
    last_message: Optional[MessageResponse] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_pinned: bool = False
    is_muted: bool = False


class ConversationListItem(BaseSchema):
    """会话列表项"""
    id: str
    conversation_type: ConversationType
    name: str
    avatar: Optional[str] = None
    last_message_content: Optional[str] = None
    last_message_type: Optional[MessageType] = None
    last_message_at: Optional[datetime] = None
    last_message_sender: Optional[str] = None
    unread_count: int = 0
    is_pinned: bool = False
    is_muted: bool = False


class ConversationSettings(BaseSchema):
    """会话设置"""
    is_pinned: bool = False
    is_muted: bool = False
    notification_enabled: bool = True


class UpdateConversationSettingsRequest(BaseSchema):
    """更新会话设置"""
    is_pinned: Optional[bool] = None
    is_muted: Optional[bool] = None
    notification_enabled: Optional[bool] = None


# ========== 语音消息 ==========

class VoiceMessageCreate(BaseSchema):
    """创建语音消息"""
    conversation_id: str
    sender_id: str
    audio_url: str
    duration_seconds: int = Field(..., ge=1, le=300)
    transcription: Optional[str] = None  # 语音转文字


class VoiceMessageResponse(BaseSchema, TimestampMixin):
    """语音消息响应"""
    id: str
    conversation_id: str
    sender_id: str
    audio_url: str
    duration_seconds: int
    transcription: Optional[str] = None
    is_played: bool = False


# ========== 图片/文件消息 ==========

class MediaMessageCreate(BaseSchema):
    """创建媒体消息"""
    conversation_id: str
    sender_id: str
    media_type: MessageType
    url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


# ========== 消息搜索 ==========

class MessageSearchRequest(BaseSchema):
    """消息搜索"""
    keyword: str = Field(..., min_length=1, max_length=100)
    conversation_id: Optional[str] = None
    message_type: Optional[MessageType] = None
    sender_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class MessageSearchResult(BaseSchema):
    """搜索结果"""
    messages: List[MessageResponse]
    total_count: int
    has_more: bool


# ========== 消息统计 ==========

class MessageStats(BaseSchema):
    """消息统计"""
    user_id: str
    period: str  # daily/weekly/monthly
    total_sent: int
    total_received: int
    by_type: Dict[str, int]
    most_active_conversation: Optional[str] = None
    most_frequent_contact: Optional[str] = None


# ========== 系统消息 ==========

class SystemMessageCreate(BaseSchema):
    """创建系统消息"""
    user_ids: List[str] = Field(default=[], description="目标用户，空为全体")
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=2000)
    message_category: str = Field(default="announcement", description='类别')
    priority: str = Field(default="normal")
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class SystemMessageResponse(BaseSchema, TimestampMixin):
    """系统消息响应"""
    id: str
    title: str
    content: str
    message_category: str
    priority: str
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
