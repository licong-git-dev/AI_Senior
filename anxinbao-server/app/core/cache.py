"""
Redis缓存和会话管理模块
提供会话存储、缓存、令牌黑名单等功能
"""
import json
from typing import Optional, Any, Dict, List
from datetime import timedelta
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis客户端实例
_redis_client = None


def get_redis_client():
    """获取Redis客户端（懒加载）"""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    if not settings.redis_url:
        logger.warning("Redis URL未配置，使用内存存储")
        return None

    try:
        import redis
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        # 测试连接
        _redis_client.ping()
        logger.info("Redis连接成功")
        return _redis_client
    except ImportError:
        logger.warning("Redis库未安装，使用内存存储")
        return None
    except Exception as e:
        logger.error(f"Redis连接失败: {e}，使用内存存储")
        return None


class SessionStore:
    """
    会话存储管理器
    支持Redis（生产）和内存（开发）两种模式
    """

    # 内存存储（fallback）
    _memory_store: Dict[str, Dict] = {}

    def __init__(self, prefix: str = "session"):
        self.prefix = prefix
        self.redis = get_redis_client()

    def _key(self, session_id: str) -> str:
        """生成完整的Redis键"""
        return f"{self.prefix}:{session_id}"

    async def get(self, session_id: str) -> Optional[Dict]:
        """获取会话数据"""
        if self.redis:
            try:
                data = self.redis.get(self._key(session_id))
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return self._memory_store.get(session_id)
        else:
            return self._memory_store.get(session_id)

    async def set(
        self,
        session_id: str,
        data: Dict,
        expire: int = 3600  # 默认1小时过期
    ) -> bool:
        """设置会话数据"""
        if self.redis:
            try:
                self.redis.setex(
                    self._key(session_id),
                    expire,
                    json.dumps(data, ensure_ascii=False)
                )
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                self._memory_store[session_id] = data
                return True
        else:
            self._memory_store[session_id] = data
            return True

    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        if self.redis:
            try:
                self.redis.delete(self._key(session_id))
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                self._memory_store.pop(session_id, None)
                return True
        else:
            self._memory_store.pop(session_id, None)
            return True

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        if self.redis:
            try:
                return bool(self.redis.exists(self._key(session_id)))
            except Exception as e:
                logger.error(f"Redis exists error: {e}")
                return session_id in self._memory_store
        else:
            return session_id in self._memory_store

    async def extend(self, session_id: str, expire: int = 3600) -> bool:
        """延长会话过期时间"""
        if self.redis:
            try:
                self.redis.expire(self._key(session_id), expire)
                return True
            except Exception as e:
                logger.error(f"Redis extend error: {e}")
                return False
        return True  # 内存存储不支持过期


class ConversationStore:
    """
    对话历史存储管理器
    用于存储用户的对话上下文
    """

    _memory_store: Dict[str, List[Dict]] = {}

    def __init__(self, max_history: int = 20):
        self.prefix = "conv"
        self.redis = get_redis_client()
        self.max_history = max_history

    def _key(self, user_id: str, session_id: str) -> str:
        return f"{self.prefix}:{user_id}:{session_id}"

    async def get_history(self, user_id: str, session_id: str) -> List[Dict]:
        """获取对话历史"""
        key = self._key(user_id, session_id)

        if self.redis:
            try:
                data = self.redis.lrange(key, 0, -1)
                return [json.loads(item) for item in data]
            except Exception as e:
                logger.error(f"Redis lrange error: {e}")
                return self._memory_store.get(key, [])
        else:
            return self._memory_store.get(key, [])

    async def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加消息到对话历史"""
        key = self._key(user_id, session_id)
        message = {
            "role": role,
            "content": content,
            **(metadata or {})
        }

        if self.redis:
            try:
                self.redis.rpush(key, json.dumps(message, ensure_ascii=False))
                # 保持最大历史记录数
                self.redis.ltrim(key, -self.max_history, -1)
                # 设置过期时间（24小时）
                self.redis.expire(key, 86400)
                return True
            except Exception as e:
                logger.error(f"Redis rpush error: {e}")
                if key not in self._memory_store:
                    self._memory_store[key] = []
                self._memory_store[key].append(message)
                self._memory_store[key] = self._memory_store[key][-self.max_history:]
                return True
        else:
            if key not in self._memory_store:
                self._memory_store[key] = []
            self._memory_store[key].append(message)
            self._memory_store[key] = self._memory_store[key][-self.max_history:]
            return True

    async def clear_history(self, user_id: str, session_id: str) -> bool:
        """清除对话历史"""
        key = self._key(user_id, session_id)

        if self.redis:
            try:
                self.redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                self._memory_store.pop(key, None)
                return True
        else:
            self._memory_store.pop(key, None)
            return True


class CacheStore:
    """
    通用缓存存储
    用于缓存热点数据（如用户信息、配置等）
    """

    _memory_cache: Dict[str, Any] = {}

    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix
        self.redis = get_redis_client()

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self.redis:
            try:
                data = self.redis.get(self._key(key))
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")
                return self._memory_cache.get(key)
        else:
            return self._memory_cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 300  # 默认5分钟
    ) -> bool:
        """设置缓存"""
        if self.redis:
            try:
                self.redis.setex(
                    self._key(key),
                    expire,
                    json.dumps(value, ensure_ascii=False)
                )
                return True
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
                self._memory_cache[key] = value
                return True
        else:
            self._memory_cache[key] = value
            return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self.redis:
            try:
                self.redis.delete(self._key(key))
                return True
            except Exception as e:
                logger.error(f"Redis cache delete error: {e}")
                self._memory_cache.pop(key, None)
                return True
        else:
            self._memory_cache.pop(key, None)
            return True

    async def invalidate_pattern(self, pattern: str) -> int:
        """按模式批量删除缓存"""
        if self.redis:
            try:
                keys = self.redis.keys(f"{self.prefix}:{pattern}")
                if keys:
                    return self.redis.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Redis invalidate error: {e}")
                return 0
        else:
            # 内存存储的简单模式匹配
            count = 0
            to_delete = [k for k in self._memory_cache if pattern.replace("*", "") in k]
            for k in to_delete:
                self._memory_cache.pop(k, None)
                count += 1
            return count


class TokenBlacklist:
    """
    令牌黑名单
    用于存储已撤销的JWT令牌
    """

    _blacklist: set = set()

    def __init__(self):
        self.prefix = "token_blacklist"
        self.redis = get_redis_client()

    async def add(self, token_hash: str, expire: int = 86400 * 7) -> bool:
        """添加令牌到黑名单"""
        if self.redis:
            try:
                self.redis.setex(f"{self.prefix}:{token_hash}", expire, "1")
                return True
            except Exception as e:
                logger.error(f"Redis blacklist add error: {e}")
                self._blacklist.add(token_hash)
                return True
        else:
            self._blacklist.add(token_hash)
            return True

    async def is_blacklisted(self, token_hash: str) -> bool:
        """检查令牌是否在黑名单中"""
        if self.redis:
            try:
                return bool(self.redis.exists(f"{self.prefix}:{token_hash}"))
            except Exception as e:
                logger.error(f"Redis blacklist check error: {e}")
                return token_hash in self._blacklist
        else:
            return token_hash in self._blacklist


# 全局实例
session_store = SessionStore()
conversation_store = ConversationStore()
cache_store = CacheStore()
token_blacklist = TokenBlacklist()
