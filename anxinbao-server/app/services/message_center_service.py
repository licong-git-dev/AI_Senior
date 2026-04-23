"""
消息中心服务
统一管理系统通知、提醒、警报等各类消息
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    SYSTEM = 'system'  # 系统通知
    EMERGENCY = 'emergency'  # 紧急警报
    HEALTH = 'health'  # 健康提醒
    REMINDER = 'reminder'  # 日常提醒
    SOCIAL = 'social'  # 社交通知
    FAMILY = 'family'  # 家庭通知
    ACTIVITY = "activity"  # 活动通知
    ACHIEVEMENT = "achievement"  # 成就通知
    PROMOTION = "promotion"  # 推广信息


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1  # 低优先级（可延迟）
    NORMAL = 2  # 普通
    HIGH = 3  # 高优先级
    URGENT = 4  # 紧急（立即推送）
    CRITICAL = 5  # 危急（强制推送+声音）


class MessageStatus(Enum):
    """消息状态"""
    UNREAD = 'unread'  # 未读
    READ = 'read'  # 已读
    ARCHIVED = 'archived'  # 已归档
    DELETED = "deleted"  # 已删除


class DeliveryChannel(Enum):
    """推送渠道"""
    IN_APP = 'in_app'  # 应用内
    PUSH = 'push'  # 推送通知
    SMS = 'sms'  # 短信
    VOICE = 'voice'  # 语音播报
    WECHAT = "wechat"  # 微信


@dataclass
class MessageAction:
    """消息操作按钮"""
    action_id: str
    label: str
    action_type: str  # link/api/dismiss
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'label': self.label,
            "action_type": self.action_type,
            'payload': self.payload
        }


@dataclass
class Message:
    """消息"""
    message_id: str
    user_id: int
    message_type: MessageType
    priority: MessagePriority
    title: str
    content: str
    summary: Optional[str] = None  # 简短摘要
    icon: Optional[str] = None
    image: Optional[str] = None
    status: MessageStatus = MessageStatus.UNREAD
    actions: List[MessageAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 来源服务
    source_id: Optional[str] = None  # 来源ID（如alert_id）
    created_at: datetime = field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    voice_content: Optional[str] = None  # 语音播报内容

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            'priority': self.priority.value,
            "priority_name": self._get_priority_name(),
            'title': self.title,
            'content': self.content,
            'summary': self.summary or self.content[:50],
            'icon': self.icon or self._get_default_icon(),
            'image': self.image,
            'status': self.status.value,
            'is_read': self.status != MessageStatus.UNREAD,
            'actions': [a.to_dict() for a in self.actions],
            'source': self.source,
            'created_at': self.created_at.isoformat(),
            'time_ago': self._format_time_ago(),
            'is_expired': self.expires_at and datetime.now() > self.expires_at
        }

    def _get_priority_name(self) -> str:
        names = {
            MessagePriority.LOW: '低',
            MessagePriority.NORMAL: '普通',
            MessagePriority.HIGH: '重要',
            MessagePriority.URGENT: '紧急',
            MessagePriority.CRITICAL: '危急'
        }
        return names.get(self.priority, '未知')

    def _get_default_icon(self) -> str:
        icons = {
            MessageType.SYSTEM: 'info',
            MessageType.EMERGENCY: 'warning',
            MessageType.HEALTH: 'heart',
            MessageType.REMINDER: 'bell',
            MessageType.SOCIAL: 'users',
            MessageType.FAMILY: 'home',
            MessageType.ACTIVITY: 'calendar',
            MessageType.ACHIEVEMENT: 'trophy',
            MessageType.PROMOTION: 'gift'
        }
        return icons.get(self.message_type, 'message')

    def _format_time_ago(self) -> str:
        delta = datetime.now() - self.created_at
        if delta.days > 7:
            return self.created_at.strftime('%m月%d日')
        elif delta.days > 0:
            return f'{delta.days}天前'
        elif delta.seconds >= 3600:
            return f'{delta.seconds // 3600}小时前'
        elif delta.seconds >= 60:
            return f'{delta.seconds // 60}分钟前'
        else:
            return "刚刚"


@dataclass
class MessagePreference:
    """消息偏好设置"""
    user_id: int
    enabled_types: Dict[str, bool] = field(default_factory=dict)
    channels: Dict[str, bool] = field(default_factory=dict)
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None
    voice_enabled: bool = True
    voice_speed: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled_types": self.enabled_types,
            'channels': self.channels,
            "quiet_hours": {
                'start': self.quiet_hours_start,
                'end': self.quiet_hours_end
            } if self.quiet_hours_start is not None else None,
            "voice_enabled": self.voice_enabled,
            "voice_speed": self.voice_speed
        }


# ==================== 消息中心服务 ====================

class MessageCenterService:
    """消息中心服务"""

    def __init__(self):
        self.messages: Dict[str, Message] = {}
        self.user_messages: Dict[int, List[str]] = {}  # user_id -> message_ids
        self.preferences: Dict[int, MessagePreference] = {}
        self.delivery_handlers: Dict[DeliveryChannel, callable] = {}
        self._message_counter = 0

    def _generate_message_id(self, user_id: int) -> str:
        """生成消息ID"""
        self._message_counter += 1
        return f"msg_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._message_counter}"

    def create_message(
        self,
        user_id: int,
        message_type: MessageType,
        title: str,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        summary: Optional[str] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        actions: Optional[List[MessageAction]] = None,
        metadata: Optional[Dict] = None,
        source: str = '',
        source_id: Optional[str] = None,
        voice_content: Optional[str] = None,
        expires_in_hours: Optional[int] = None
    ) -> Message:
        """创建消息"""
        message_id = self._generate_message_id(user_id)

        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        message = Message(
            message_id=message_id,
            user_id=user_id,
            message_type=message_type,
            priority=priority,
            title=title,
            content=content,
            summary=summary,
            icon=icon,
            image=image,
            actions=actions or [],
            metadata=metadata or {},
            source=source,
            source_id=source_id,
            voice_content=voice_content,
            expires_at=expires_at
        )

        self.messages[message_id] = message

        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        self.user_messages[user_id].insert(0, message_id)  # 新消息在前

        # 限制每用户最多保存1000条消息
        if len(self.user_messages[user_id]) > 1000:
            old_ids = self.user_messages[user_id][1000:]
            self.user_messages[user_id] = self.user_messages[user_id][:1000]
            for old_id in old_ids:
                if old_id in self.messages:
                    del self.messages[old_id]

        logger.info(f"创建消息: {message_id} for user {user_id}")
        return message

    async def send_message(
        self,
        user_id: int,
        message_type: MessageType,
        title: str,
        content: str,
        channels: Optional[List[DeliveryChannel]] = None,
        **kwargs
    ) -> Message:
        """发送消息（创建+推送）"""
        message = self.create_message(
            user_id=user_id,
            message_type=message_type,
            title=title,
            content=content,
            **kwargs
        )

        # 检查用户偏好
        pref = self.get_preference(user_id)
        if not self._should_deliver(pref, message_type):
            logger.info(f'用户 {user_id} 已禁用 {message_type.value} 类型消息')
            return message

        # 检查免打扰时间
        if self._in_quiet_hours(pref) and message.priority.value < MessagePriority.URGENT.value:
            logger.info(f"用户 {user_id} 处于免打扰时间")
            return message

        # 推送消息
        channels = channels or [DeliveryChannel.IN_APP, DeliveryChannel.PUSH]
        await self._deliver_message(message, channels, pref)

        return message

    async def _deliver_message(
        self,
        message: Message,
        channels: List[DeliveryChannel],
        preference: MessagePreference
    ):
        """推送消息到各渠道"""
        for channel in channels:
            # 检查渠道是否启用
            if not preference.channels.get(channel.value, True):
                continue

            handler = self.delivery_handlers.get(channel)
            if handler:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f'消息推送失败 [{channel.value}]: {e}')
            else:
                logger.debug(f"渠道 {channel.value} 未配置处理器")

        # 语音播报
        if preference.voice_enabled and message.voice_content:
            if message.priority.value >= MessagePriority.HIGH.value:
                await self._voice_announce(message, preference)

    async def _voice_announce(self, message: Message, preference: MessagePreference):
        """语音播报消息"""
        content = message.voice_content or message.title
        logger.info(f"语音播报: {content}")
        # TODO: 调用TTS服务
        # await tts_service.speak(content, speed=preference.voice_speed)

    def _should_deliver(self, preference: MessagePreference, message_type: MessageType) -> bool:
        """检查是否应该推送该类型消息"""
        return preference.enabled_types.get(message_type.value, True)

    def _in_quiet_hours(self, preference: MessagePreference) -> bool:
        """检查是否在免打扰时间"""
        if preference.quiet_hours_start is None:
            return False

        current_hour = datetime.now().hour
        start = preference.quiet_hours_start
        end = preference.quiet_hours_end or 7

        if start < end:
            return start <= current_hour < end
        else:  # 跨午夜
            return current_hour >= start or current_hour < end

    def register_delivery_handler(self, channel: DeliveryChannel, handler: callable):
        """注册推送处理器"""
        self.delivery_handlers[channel] = handler

    # ==================== 消息查询 ====================

    def get_message(self, message_id: str) -> Optional[Message]:
        """获取消息"""
        return self.messages.get(message_id)

    def get_user_messages(
        self,
        user_id: int,
        message_type: Optional[MessageType] = None,
        status: Optional[MessageStatus] = None,
        priority: Optional[MessagePriority] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """获取用户消息列表"""
        message_ids = self.user_messages.get(user_id, [])
        messages = []

        for mid in message_ids:
            msg = self.messages.get(mid)
            if not msg:
                continue
            if msg.status == MessageStatus.DELETED:
                continue
            if message_type and msg.message_type != message_type:
                continue
            if status and msg.status != status:
                continue
            if priority and msg.priority != priority:
                continue
            # 过滤已过期消息
            if msg.expires_at and datetime.now() > msg.expires_at:
                continue
            messages.append(msg)

        return messages[offset:offset + limit]

    def get_unread_messages(self, user_id: int, limit: int = 50) -> List[Message]:
        """获取未读消息"""
        return self.get_user_messages(
            user_id, status=MessageStatus.UNREAD, limit=limit
        )

    def get_unread_count(self, user_id: int) -> Dict[str, int]:
        """获取未读消息数量统计"""
        messages = self.get_user_messages(user_id, status=MessageStatus.UNREAD, limit=1000)

        count_by_type = {}
        for msg in messages:
            type_key = msg.message_type.value
            count_by_type[type_key] = count_by_type.get(type_key, 0) + 1

        return {
            'total': len(messages),
            'by_type': count_by_type
        }

    def get_important_messages(self, user_id: int, limit: int = 20) -> List[Message]:
        """获取重要消息（高优先级+未读）"""
        messages = self.get_user_messages(user_id, status=MessageStatus.UNREAD, limit=100)
        important = [m for m in messages if m.priority.value >= MessagePriority.HIGH.value]
        return important[:limit]

    # ==================== 消息操作 ====================

    def mark_as_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        message = self.messages.get(message_id)
        if not message:
            return False

        message.status = MessageStatus.READ
        message.read_at = datetime.now()
        return True

    def mark_all_as_read(self, user_id: int, message_type: Optional[MessageType] = None) -> int:
        """标记所有消息为已读"""
        messages = self.get_user_messages(user_id, message_type=message_type, status=MessageStatus.UNREAD, limit=1000)
        count = 0
        for msg in messages:
            msg.status = MessageStatus.READ
            msg.read_at = datetime.now()
            count += 1
        return count

    def archive_message(self, message_id: str) -> bool:
        """归档消息"""
        message = self.messages.get(message_id)
        if not message:
            return False

        message.status = MessageStatus.ARCHIVED
        return True

    def delete_message(self, message_id: str, user_id: int) -> bool:
        """删除消息"""
        message = self.messages.get(message_id)
        if not message or message.user_id != user_id:
            return False

        message.status = MessageStatus.DELETED
        return True

    def clear_messages(
        self,
        user_id: int,
        message_type: Optional[MessageType] = None,
        before_date: Optional[datetime] = None
    ) -> int:
        """清理消息"""
        messages = self.get_user_messages(user_id, message_type=message_type, limit=10000)
        count = 0

        for msg in messages:
            if before_date and msg.created_at >= before_date:
                continue
            msg.status = MessageStatus.DELETED
            count += 1

        return count

    # ==================== 偏好设置 ====================

    def get_preference(self, user_id: int) -> MessagePreference:
        """获取用户消息偏好"""
        if user_id not in self.preferences:
            # 默认偏好
            self.preferences[user_id] = MessagePreference(
                user_id=user_id,
                enabled_types={t.value: True for t in MessageType},
                channels={c.value: True for c in DeliveryChannel},
                voice_enabled=True,
                voice_speed=1.0
            )
        return self.preferences[user_id]

    def update_preference(
        self,
        user_id: int,
        enabled_types: Optional[Dict[str, bool]] = None,
        channels: Optional[Dict[str, bool]] = None,
        quiet_hours_start: Optional[int] = None,
        quiet_hours_end: Optional[int] = None,
        voice_enabled: Optional[bool] = None,
        voice_speed: Optional[float] = None
    ) -> MessagePreference:
        """更新消息偏好"""
        pref = self.get_preference(user_id)

        if enabled_types:
            pref.enabled_types.update(enabled_types)
        if channels:
            pref.channels.update(channels)
        if quiet_hours_start is not None:
            pref.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            pref.quiet_hours_end = quiet_hours_end
        if voice_enabled is not None:
            pref.voice_enabled = voice_enabled
        if voice_speed is not None:
            pref.voice_speed = voice_speed

        return pref


# ==================== 消息模板服务 ====================

class MessageTemplateService:
    """消息模板服务"""

    # 预定义模板
    TEMPLATES = {
        # 紧急类
        'sos_alert': {
            'type': MessageType.EMERGENCY,
            'priority': MessagePriority.CRITICAL,
            'title': '紧急求助',
            "content": "{user_name}发出紧急求助！",
            "voice": "紧急情况，{user_name}正在求助，请立即查看。",
            'icon': 'sos'
        },
        'fall_alert': {
            'type': MessageType.EMERGENCY,
            'priority': MessagePriority.CRITICAL,
            'title': '跌倒警报',
            "content": "检测到{user_name}可能跌倒",
            "voice": "警报，检测到{user_name}可能发生跌倒，请立即确认。",
            'icon': "fall"
        },

        # 健康类
        "health_abnormal": {
            'type': MessageType.HEALTH,
            'priority': MessagePriority.HIGH,
            'title': '健康指标异常',
            "content": "{user_name}的{metric}异常：{value}",
            "voice": "健康提醒，{user_name}的{metric}数值异常，请注意。",
            'icon': "heart"
        },
        "medication_reminder": {
            'type': MessageType.REMINDER,
            'priority': MessagePriority.NORMAL,
            'title': '服药提醒',
            "content": "该吃{medicine}了",
            "voice": "服药提醒，现在该服用{medicine}了。",
            'icon': "pill"
        },

        # 社交类
        "new_friend_request": {
            'type': MessageType.SOCIAL,
            'priority': MessagePriority.NORMAL,
            'title': '新的好友请求',
            "content": "{requester_name}想添加您为好友",
            'icon': 'user-plus'
        },
        'post_liked': {
            'type': MessageType.SOCIAL,
            'priority': MessagePriority.LOW,
            'title': '收到点赞',
            "content": "{user_name}赞了您的动态",
            'icon': "thumbs-up"
        },
        "new_comment": {
            'type': MessageType.SOCIAL,
            'priority': MessagePriority.NORMAL,
            'title': '新评论',
            "content": "{user_name}评论了您的动态：{comment}",
            'icon': "message"
        },

        # 家庭类
        "family_binding_request": {
            'type': MessageType.FAMILY,
            'priority': MessagePriority.HIGH,
            'title': '家庭绑定请求',
            "content": "{requester_name}邀请您加入家庭组",
            "voice": "{requester_name}邀请您加入家庭组，请查看。",
            'icon': "home"
        },
        "guardian_reminder": {
            'type': MessageType.FAMILY,
            'priority': MessagePriority.NORMAL,
            'title': "来自{guardian_name}的提醒",
            'content': '{message}',
            "voice": "{guardian_name}提醒您：{message}",
            'icon': "bell"
        },

        # 活动类
        "activity_reminder": {
            'type': MessageType.ACTIVITY,
            'priority': MessagePriority.NORMAL,
            'title': '活动提醒',
            "content": "您报名的活动「{activity_name}」即将开始",
            "voice": "活动提醒，您报名的{activity_name}即将开始。",
            'icon': "calendar"
        },

        # 成就类
        "checkin_streak": {
            'type': MessageType.ACHIEVEMENT,
            'priority': MessagePriority.LOW,
            'title': '打卡成就',
            "content": "恭喜！您已连续打卡{days}天",
            'icon': "trophy"
        },
        "game_achievement": {
            'type': MessageType.ACHIEVEMENT,
            'priority': MessagePriority.LOW,
            'title': '游戏成就',
            "content": "恭喜获得成就：{achievement_name}",
            'icon': "star"
        },

        # 系统类
        "system_update": {
            'type': MessageType.SYSTEM,
            'priority': MessagePriority.NORMAL,
            'title': '系统更新',
            'content': '{message}',
            'icon': "info"
        },
        "device_offline": {
            'type': MessageType.SYSTEM,
            'priority': MessagePriority.HIGH,
            'title': '设备离线',
            "content": "{device_name}已离线，请检查设备状态",
            "voice": "提醒，{device_name}已离线，请检查。",
            'icon': "wifi-off"
        }
    }

    def __init__(self, message_service: MessageCenterService):
        self.message_service = message_service

    async def send_from_template(
        self,
        user_id: int,
        template_name: str,
        params: Dict[str, Any],
        actions: Optional[List[MessageAction]] = None,
        metadata: Optional[Dict] = None,
        channels: Optional[List[DeliveryChannel]] = None
    ) -> Optional[Message]:
        """使用模板发送消息"""
        template = self.TEMPLATES.get(template_name)
        if not template:
            logger.warning(f'消息模板不存在: {template_name}')
            return None

        # 填充模板
        title = template['title'].format(**params)
        content = template['content'].format(**params)
        voice_content = None
        if 'voice' in template:
            voice_content = template['voice'].format(**params)

        return await self.message_service.send_message(
            user_id=user_id,
            message_type=template['type'],
            title=title,
            content=content,
            priority=template['priority'],
            icon=template.get("icon"),
            voice_content=voice_content,
            actions=actions,
            metadata=metadata,
            source=template_name,
            channels=channels
        )


# 全局服务实例
message_center = MessageCenterService()
message_template = MessageTemplateService(message_center)
