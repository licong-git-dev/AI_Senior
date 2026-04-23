"""
缓存模块单元测试
测试Redis缓存、会话存储、对话历史等功能
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import json

from app.core.cache import (
    SessionStore,
    ConversationStore,
    CacheStore,
    TokenBlacklist,
)


class TestSessionStore:
    """会话存储测试"""

    @pytest.fixture
    def session_store(self):
        """创建会话存储实例（使用内存模式）"""
        with patch('app.core.cache.get_redis_client') as mock:
            mock.return_value = None
            store = SessionStore()
            # 清理内存存储
            store._memory_store.clear()
            yield store

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_and_get_session(self, session_store):
        """测试设置和获取会话"""
        session_id = "test-session-001"
        data = {"user_id": "123", "role": "elder"}

        result = await session_store.set(session_id, data)
        assert result is True

        retrieved = await session_store.get(session_id)
        assert retrieved == data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_store):
        """测试获取不存在的会话"""
        result = await session_store.get("nonexistent-session")
        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_session(self, session_store):
        """测试删除会话"""
        session_id = "test-session-002"
        data = {"user_id": "456"}

        await session_store.set(session_id, data)
        result = await session_store.delete(session_id)
        assert result is True

        retrieved = await session_store.get(session_id)
        assert retrieved is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exists_session(self, session_store):
        """测试检查会话存在"""
        session_id = "test-session-003"
        data = {"user_id": "789"}

        assert await session_store.exists(session_id) is False

        await session_store.set(session_id, data)
        assert await session_store.exists(session_id) is True


class TestConversationStore:
    """对话历史存储测试"""

    @pytest.fixture
    def conv_store(self):
        """创建对话存储实例"""
        with patch('app.core.cache.get_redis_client') as mock:
            mock.return_value = None
            store = ConversationStore(max_history=10)
            store._memory_store.clear()
            yield store

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_and_get_message(self, conv_store):
        """测试添加和获取消息"""
        user_id = "user-001"
        session_id = "session-001"

        await conv_store.add_message(user_id, session_id, "user", "你好")
        await conv_store.add_message(user_id, session_id, "assistant", "您好！有什么可以帮您的？")

        history = await conv_store.get_history(user_id, session_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "你好"
        assert history[1]["role"] == "assistant"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_max_history_limit(self, conv_store):
        """测试最大历史记录限制"""
        user_id = "user-002"
        session_id = "session-002"

        # 添加15条消息（超过max_history=10）
        for i in range(15):
            await conv_store.add_message(user_id, session_id, "user", f"消息{i}")

        history = await conv_store.get_history(user_id, session_id)
        assert len(history) == 10  # 只保留最近10条
        assert history[0]["content"] == "消息5"  # 第一条应该是消息5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_clear_history(self, conv_store):
        """测试清除历史"""
        user_id = "user-003"
        session_id = "session-003"

        await conv_store.add_message(user_id, session_id, "user", "测试消息")
        await conv_store.clear_history(user_id, session_id)

        history = await conv_store.get_history(user_id, session_id)
        assert len(history) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_message_with_metadata(self, conv_store):
        """测试添加带元数据的消息"""
        user_id = "user-004"
        session_id = "session-004"

        await conv_store.add_message(
            user_id, session_id, "user", "我头晕",
            metadata={"risk_score": 3, "emotion": "anxious"}
        )

        history = await conv_store.get_history(user_id, session_id)
        assert len(history) == 1
        assert history[0]["risk_score"] == 3
        assert history[0]["emotion"] == "anxious"


class TestCacheStore:
    """通用缓存测试"""

    @pytest.fixture
    def cache_store(self):
        """创建缓存存储实例"""
        with patch('app.core.cache.get_redis_client') as mock:
            mock.return_value = None
            store = CacheStore()
            store._memory_cache.clear()
            yield store

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_and_get_cache(self, cache_store):
        """测试设置和获取缓存"""
        key = "user:profile:123"
        value = {"name": "测试用户", "age": 70}

        result = await cache_store.set(key, value)
        assert result is True

        retrieved = await cache_store.get(key)
        assert retrieved == value

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_nonexistent_cache(self, cache_store):
        """测试获取不存在的缓存"""
        result = await cache_store.get("nonexistent-key")
        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_store):
        """测试删除缓存"""
        key = "temp:data"
        await cache_store.set(key, {"data": "test"})

        result = await cache_store.delete(key)
        assert result is True

        retrieved = await cache_store.get(key)
        assert retrieved is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_store):
        """测试模式匹配删除"""
        await cache_store.set("user:1", {"id": 1})
        await cache_store.set("user:2", {"id": 2})
        await cache_store.set("config:app", {"setting": True})

        count = await cache_store.invalidate_pattern("user*")
        assert count == 2

        # 验证user开头的都被删除
        assert await cache_store.get("user:1") is None
        assert await cache_store.get("user:2") is None
        # config没有被删除
        assert await cache_store.get("config:app") is not None


class TestTokenBlacklist:
    """令牌黑名单测试"""

    @pytest.fixture
    def blacklist(self):
        """创建黑名单实例"""
        with patch('app.core.cache.get_redis_client') as mock:
            mock.return_value = None
            bl = TokenBlacklist()
            bl._blacklist.clear()
            yield bl

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_to_blacklist(self, blacklist):
        """测试添加到黑名单"""
        token_hash = "abc123def456"
        result = await blacklist.add(token_hash)
        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_blacklisted(self, blacklist):
        """测试检查是否在黑名单"""
        token_hash = "xyz789"

        # 未添加时
        assert await blacklist.is_blacklisted(token_hash) is False

        # 添加后
        await blacklist.add(token_hash)
        assert await blacklist.is_blacklisted(token_hash) is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_tokens(self, blacklist):
        """测试多个令牌"""
        tokens = ["token1", "token2", "token3"]

        for token in tokens:
            await blacklist.add(token)

        for token in tokens:
            assert await blacklist.is_blacklisted(token) is True

        assert await blacklist.is_blacklisted("token4") is False


class TestRedisIntegration:
    """Redis集成测试（当Redis可用时）"""

    @pytest.fixture
    def redis_session_store(self):
        """创建使用Redis的会话存储"""
        # 创建mock Redis客户端
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = False

        with patch('app.core.cache.get_redis_client') as mock:
            mock.return_value = mock_redis
            store = SessionStore()
            yield store, mock_redis

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redis_set_called(self, redis_session_store):
        """测试Redis set方法被调用"""
        store, mock_redis = redis_session_store
        session_id = "redis-test-001"
        data = {"test": "data"}

        await store.set(session_id, data, expire=3600)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "session:redis-test-001" in str(call_args)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redis_get_called(self, redis_session_store):
        """测试Redis get方法被调用"""
        store, mock_redis = redis_session_store
        session_id = "redis-test-002"

        # 设置返回值
        mock_redis.get.return_value = json.dumps({"test": "data"})

        result = await store.get(session_id)

        mock_redis.get.assert_called_once_with("session:redis-test-002")
        assert result == {"test": "data"}
