"""
安心宝 - 通知存储服务
支持Redis缓存和数据库持久化
"""
import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import asyncio
from enum import Enum

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationType(str, Enum):
    """通知类型"""
    SYSTEM = "system"
    HEALTH_ALERT = "health_alert"
    MEDICATION = "medication"
    EMERGENCY = 'emergency'
    FAMILY = 'family'
    DEVICE = 'device'
    ACTIVITY = 'activity'
    PROMOTION = 'promotion'


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


class NotificationStatus(str, Enum):
    """通知状态"""
    PENDING = "pending"
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'


class Notification:
    """通知模型"""
    def __init__(
        self,
        id: str,
        user_id: str,
        title: str,
        content: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.notification_type = notification_type
        self.priority = priority
        self.data = data or {}
        self.action_url = action_url
        self.created_at = created_at or datetime.now()
        self.expires_at = expires_at
        self.status = NotificationStatus.PENDING
        self.is_read = False
        self.read_at: Optional[datetime] = None
        self.is_deleted = False
        self.sent_channels: List[str] = []
        self.delivery_results: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            "notification_type": self.notification_type.value if isinstance(self.notification_type, Enum) else self.notification_type,
            'priority': self.priority.value if isinstance(self.priority, Enum) else self.priority,
            'data': self.data,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status.value if isinstance(self.status, Enum) else self.status,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_deleted': self.is_deleted,
            "sent_channels": self.sent_channels,
            "delivery_results": self.delivery_results
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        notification = cls(
            id=data['id'],
            user_id=data['user_id'],
            title=data['title'],
            content=data['content'],
            notification_type=NotificationType(data["notification_type"]) if data.get("notification_type") else NotificationType.SYSTEM,
            priority=NotificationPriority(data.get('priority', 'normal')),
            data=data.get('data', {}),
            action_url=data.get('action_url'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )
        notification.status = NotificationStatus(data.get('status', 'pending'))
        notification.is_read = data.get('is_read', False)
        notification.read_at = datetime.fromisoformat(data['read_at']) if data.get('read_at') else None
        notification.is_deleted = data.get('is_deleted', False)
        notification.sent_channels = data.get("sent_channels", [])
        notification.delivery_results = data.get("delivery_results", {})
        return notification


class BaseNotificationStore:
    """通知存储基类"""

    async def save(self, notification: Notification) -> bool:
        raise NotImplementedError

    async def get(self, notification_id: str) -> Optional[Notification]:
        raise NotImplementedError

    async def get_by_user(
        self,
        user_id: str,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        raise NotImplementedError

    async def mark_as_read(self, notification_id: str) -> bool:
        raise NotImplementedError

    async def mark_many_as_read(self, notification_ids: List[str]) -> int:
        raise NotImplementedError

    async def delete(self, notification_id: str) -> bool:
        raise NotImplementedError

    async def delete_many(self, notification_ids: List[str]) -> int:
        raise NotImplementedError

    async def get_unread_count(self, user_id: str) -> int:
        raise NotImplementedError

    async def cleanup_expired(self) -> int:
        raise NotImplementedError


class InMemoryNotificationStore(BaseNotificationStore):
    """内存通知存储（开发/测试用）"""

    def __init__(self):
        self._notifications: Dict[str, Notification] = {}
        self._user_index: Dict[str, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def save(self, notification: Notification) -> bool:
        async with self._lock:
            self._notifications[notification.id] = notification
            if notification.id not in self._user_index[notification.user_id]:
                self._user_index[notification.user_id].insert(0, notification.id)
            logger.debug(f"通知已保存: {notification.id}")
            return True

    async def get(self, notification_id: str) -> Optional[Notification]:
        return self._notifications.get(notification_id)

    async def get_by_user(
        self,
        user_id: str,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        notification_ids = self._user_index.get(user_id, [])
        result = []

        for nid in notification_ids:
            notification = self._notifications.get(nid)
            if not notification or notification.is_deleted:
                continue

            # 过滤类型
            if notification_type and notification.notification_type != notification_type:
                continue

            # 过滤已读状态
            if is_read is not None and notification.is_read != is_read:
                continue

            result.append(notification)

        # 按创建时间倒序排序
        result.sort(key=lambda x: x.created_at, reverse=True)

        # 分页
        return result[offset:offset + limit]

    async def mark_as_read(self, notification_id: str) -> bool:
        notification = self._notifications.get(notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.now()
            notification.status = NotificationStatus.READ
            return True
        return False

    async def mark_many_as_read(self, notification_ids: List[str]) -> int:
        count = 0
        for nid in notification_ids:
            if await self.mark_as_read(nid):
                count += 1
        return count

    async def delete(self, notification_id: str) -> bool:
        notification = self._notifications.get(notification_id)
        if notification:
            notification.is_deleted = True
            return True
        return False

    async def delete_many(self, notification_ids: List[str]) -> int:
        count = 0
        for nid in notification_ids:
            if await self.delete(nid):
                count += 1
        return count

    async def get_unread_count(self, user_id: str) -> int:
        notification_ids = self._user_index.get(user_id, [])
        count = 0
        for nid in notification_ids:
            notification = self._notifications.get(nid)
            if notification and not notification.is_read and not notification.is_deleted:
                count += 1
        return count

    async def cleanup_expired(self) -> int:
        now = datetime.now()
        expired_ids = []

        for nid, notification in self._notifications.items():
            if notification.expires_at and notification.expires_at < now:
                expired_ids.append(nid)

        for nid in expired_ids:
            del self._notifications[nid]
            for user_ids in self._user_index.values():
                if nid in user_ids:
                    user_ids.remove(nid)

        return len(expired_ids)


class RedisNotificationStore(BaseNotificationStore):
    """Redis通知存储"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self._redis = None
        self._key_prefix = "anxinbao:notification:"
        self._user_key_prefix = "anxinbao:user_notifications:"
        self._unread_count_prefix = "anxinbao:unread_count:"

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            except ImportError:
                logger.warning("redis.asyncio 不可用，降级到内存存储")
                return None
            except Exception as e:
                logger.error(f'Redis连接失败: {e}')
                return None
        return self._redis

    async def save(self, notification: Notification) -> bool:
        redis = await self._get_redis()
        if not redis:
            return False

        try:
            key = f'{self._key_prefix}{notification.id}'
            user_key = f'{self._user_key_prefix}{notification.user_id}'
            unread_key = f'{self._unread_count_prefix}{notification.user_id}'

            # 保存通知数据
            await redis.set(key, json.dumps(notification.to_dict()))

            # 设置过期时间（30天）
            await redis.expire(key, 30 * 24 * 3600)

            # 添加到用户通知列表
            await redis.lpush(user_key, notification.id)
            await redis.ltrim(user_key, 0, 999)  # 保留最近1000条

            # 更新未读数
            if not notification.is_read:
                await redis.incr(unread_key)

            logger.debug(f'通知已保存到Redis: {notification.id}')
            return True

        except Exception as e:
            logger.error(f'Redis保存通知失败: {e}')
            return False

    async def get(self, notification_id: str) -> Optional[Notification]:
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            key = f'{self._key_prefix}{notification_id}'
            data = await redis.get(key)
            if data:
                return Notification.from_dict(json.loads(data))
            return None
        except Exception as e:
            logger.error(f'Redis获取通知失败: {e}')
            return None

    async def get_by_user(
        self,
        user_id: str,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        redis = await self._get_redis()
        if not redis:
            return []

        try:
            user_key = f'{self._user_key_prefix}{user_id}'

            # 获取用户通知ID列表
            notification_ids = await redis.lrange(user_key, 0, -1)

            result = []
            for nid in notification_ids:
                notification = await self.get(nid)
                if not notification or notification.is_deleted:
                    continue

                if notification_type and notification.notification_type != notification_type:
                    continue

                if is_read is not None and notification.is_read != is_read:
                    continue

                result.append(notification)

            # 分页
            return result[offset:offset + limit]

        except Exception as e:
            logger.error(f'Redis获取用户通知列表失败: {e}')
            return []

    async def mark_as_read(self, notification_id: str) -> bool:
        redis = await self._get_redis()
        if not redis:
            return False

        try:
            notification = await self.get(notification_id)
            if not notification or notification.is_read:
                return False

            notification.is_read = True
            notification.read_at = datetime.now()
            notification.status = NotificationStatus.READ

            key = f'{self._key_prefix}{notification_id}'
            await redis.set(key, json.dumps(notification.to_dict()))

            # 减少未读数
            unread_key = f'{self._unread_count_prefix}{notification.user_id}'
            await redis.decr(unread_key)

            return True

        except Exception as e:
            logger.error(f'Redis标记已读失败: {e}')
            return False

    async def mark_many_as_read(self, notification_ids: List[str]) -> int:
        count = 0
        for nid in notification_ids:
            if await self.mark_as_read(nid):
                count += 1
        return count

    async def delete(self, notification_id: str) -> bool:
        redis = await self._get_redis()
        if not redis:
            return False

        try:
            notification = await self.get(notification_id)
            if not notification:
                return False

            notification.is_deleted = True
            key = f'{self._key_prefix}{notification_id}'
            await redis.set(key, json.dumps(notification.to_dict()))

            # 如果未读，减少未读数
            if not notification.is_read:
                unread_key = f'{self._unread_count_prefix}{notification.user_id}'
                await redis.decr(unread_key)

            return True

        except Exception as e:
            logger.error(f'Redis删除通知失败: {e}')
            return False

    async def delete_many(self, notification_ids: List[str]) -> int:
        count = 0
        for nid in notification_ids:
            if await self.delete(nid):
                count += 1
        return count

    async def get_unread_count(self, user_id: str) -> int:
        redis = await self._get_redis()
        if not redis:
            return 0

        try:
            unread_key = f'{self._unread_count_prefix}{user_id}'
            count = await redis.get(unread_key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Redis获取未读数失败: {e}")
            return 0

    async def cleanup_expired(self) -> int:
        # Redis自动处理过期，这里返回0
        return 0


class NotificationStoreService:
    """通知存储服务"""

    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis and getattr(settings, 'redis_url', None)

        if self.use_redis:
            self._store = RedisNotificationStore()
            self._fallback_store = InMemoryNotificationStore()
        else:
            self._store = InMemoryNotificationStore()
            self._fallback_store = None

    async def create_notification(
        self,
        user_id: str,
        title: str,
        content: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        expires_in_days: int = 30
    ) -> Optional[Notification]:
        """创建通知"""
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            priority=priority,
            data=data,
            action_url=action_url,
            expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None
        )

        success = await self._store.save(notification)
        if not success and self._fallback_store:
            success = await self._fallback_store.save(notification)

        return notification if success else None

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """获取通知"""
        notification = await self._store.get(notification_id)
        if not notification and self._fallback_store:
            notification = await self._fallback_store.get(notification_id)
        return notification

    async def get_user_notifications(
        self,
        user_id: str,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """获取用户通知列表"""
        notifications = await self._store.get_by_user(
            user_id, notification_type, is_read, limit, offset
        )
        if not notifications and self._fallback_store:
            notifications = await self._fallback_store.get_by_user(
                user_id, notification_type, is_read, limit, offset
            )
        return notifications

    async def mark_as_read(self, notification_id: str) -> bool:
        """标记通知为已读"""
        success = await self._store.mark_as_read(notification_id)
        if not success and self._fallback_store:
            success = await self._fallback_store.mark_as_read(notification_id)
        return success

    async def mark_all_as_read(self, user_id: str) -> int:
        """标记所有通知为已读"""
        notifications = await self.get_user_notifications(user_id, is_read=False, limit=1000)
        notification_ids = [n.id for n in notifications]
        return await self._store.mark_many_as_read(notification_ids)

    async def delete_notification(self, notification_id: str) -> bool:
        """删除通知"""
        success = await self._store.delete(notification_id)
        if not success and self._fallback_store:
            success = await self._fallback_store.delete(notification_id)
        return success

    async def delete_notifications(self, notification_ids: List[str]) -> int:
        """批量删除通知"""
        return await self._store.delete_many(notification_ids)

    async def get_unread_count(self, user_id: str) -> int:
        """获取未读通知数"""
        count = await self._store.get_unread_count(user_id)
        if count == 0 and self._fallback_store:
            count = await self._fallback_store.get_unread_count(user_id)
        return count

    async def cleanup(self) -> int:
        """清理过期通知"""
        return await self._store.cleanup_expired()

    # ========== 便捷方法 ==========

    async def create_health_alert(
        self,
        user_id: str,
        alert_title: str,
        alert_content: str,
        severity: str = "high",
        health_data: Optional[Dict] = None
    ) -> Optional[Notification]:
        """创建健康告警通知"""
        priority = NotificationPriority.URGENT if severity == 'critical' else NotificationPriority.HIGH
        return await self.create_notification(
            user_id=user_id,
            title=alert_title,
            content=alert_content,
            notification_type=NotificationType.HEALTH_ALERT,
            priority=priority,
            data={'severity': severity, "health_data": health_data}
        )

    async def create_medication_reminder(
        self,
        user_id: str,
        medication_name: str,
        dosage: str,
        scheduled_time: str
    ) -> Optional[Notification]:
        """创建用药提醒通知"""
        return await self.create_notification(
            user_id=user_id,
            title="用药提醒",
            content=f"请记得服用 {medication_name} ({dosage})，计划时间: {scheduled_time}",
            notification_type=NotificationType.MEDICATION,
            priority=NotificationPriority.HIGH,
            data={
                "medication_name": medication_name,
                'dosage': dosage,
                "scheduled_time": scheduled_time
            }
        )

    async def create_emergency_notification(
        self,
        user_id: str,
        emergency_type: str,
        description: str,
        location: Optional[Dict] = None
    ) -> Optional[Notification]:
        """创建紧急通知"""
        return await self.create_notification(
            user_id=user_id,
            title=f"紧急情况: {emergency_type}",
            content=description,
            notification_type=NotificationType.EMERGENCY,
            priority=NotificationPriority.URGENT,
            data={
                "emergency_type": emergency_type,
                'location': location
            }
        )

    async def create_family_message(
        self,
        user_id: str,
        from_name: str,
        message_preview: str
    ) -> Optional[Notification]:
        """创建家人消息通知"""
        return await self.create_notification(
            user_id=user_id,
            title=f"来自{from_name}的消息",
            content=message_preview,
            notification_type=NotificationType.FAMILY,
            priority=NotificationPriority.NORMAL,
            data={"from_name": from_name}
        )

    async def create_device_alert(
        self,
        user_id: str,
        device_name: str,
        alert_reason: str
    ) -> Optional[Notification]:
        """创建设备告警通知"""
        return await self.create_notification(
            user_id=user_id,
            title=f"设备告警: {device_name}",
            content=alert_reason,
            notification_type=NotificationType.DEVICE,
            priority=NotificationPriority.HIGH,
            data={
                "device_name": device_name,
                "alert_reason": alert_reason
            }
        )


# 全局通知存储服务实例
notification_store = NotificationStoreService()
