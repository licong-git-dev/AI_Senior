"""
测试配置和共享Fixture
提供测试所需的数据库、客户端、模拟数据等
"""
import os
import sys
import pytest
from typing import Generator, Dict, Any
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import json

# 设置测试环境变量（必须在导入app之前）
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32chars!"
os.environ["DASHSCOPE_API_KEY"] = "test-api-key"
os.environ["REDIS_URL"] = ""  # 禁用Redis，使用内存存储

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Base, User, FamilyMember, Conversation, HealthNotification
from app.models.database import UserAuth, DeviceAuth, RefreshToken, AuditLog
from app.core.config import get_settings


# ==================== 数据库Fixtures ====================

@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎（会话级别，整个测试会话共用）"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    # 清理
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """创建测试数据库会话（每个测试函数独立）"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # 清理所有表数据
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def override_get_db(db_session):
    """覆盖数据库依赖"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


# ==================== 应用Fixtures ====================

@pytest.fixture
def app(override_get_db):
    """创建测试应用实例"""
    from main import app as fastapi_app
    from app.models.database import get_db
    from app.core.deps import get_db as get_db_deps

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_db_deps] = override_get_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> TestClient:
    """同步测试客户端"""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncClient:
    """异步测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ==================== 测试数据Fixtures ====================

@pytest.fixture
def sample_user(db_session) -> User:
    """创建测试用户（老人）"""
    user = User(
        name="测试老人",
        device_id="test-device-001",
        dialect="mandarin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user_auth(db_session, sample_user) -> UserAuth:
    """创建测试用户认证"""
    from app.core.security import get_password_hash

    user_auth = UserAuth(
        username="13800138000",
        password_hash=get_password_hash("Test123456"),
        role="elder",
        user_id=sample_user.id,
        is_active=True
    )
    db_session.add(user_auth)
    db_session.commit()
    db_session.refresh(user_auth)
    return user_auth


@pytest.fixture
def sample_family_member(db_session, sample_user) -> FamilyMember:
    """创建测试家属"""
    family = FamilyMember(
        user_id=sample_user.id,
        name="测试子女",
        phone="13900139000",
        openid="test_openid_001",
        is_primary=True
    )
    db_session.add(family)
    db_session.commit()
    db_session.refresh(family)
    return family


@pytest.fixture
def sample_family_auth(db_session, sample_family_member) -> UserAuth:
    """创建测试家属认证"""
    from app.core.security import get_password_hash

    family_auth = UserAuth(
        username="13900139000",
        password_hash=get_password_hash("Test123456"),
        role="family",
        family_id=sample_family_member.id,
        is_active=True
    )
    db_session.add(family_auth)
    db_session.commit()
    db_session.refresh(family_auth)
    return family_auth


@pytest.fixture
def sample_device_auth(db_session, sample_user) -> DeviceAuth:
    """创建测试设备认证"""
    from app.core.security import get_password_hash

    device = DeviceAuth(
        device_id="speaker-test-001",
        device_secret=get_password_hash("device-secret-123"),
        device_type="speaker",
        user_id=sample_user.id,
        is_active=True
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def sample_conversation(db_session, sample_user) -> Conversation:
    """创建测试对话记录"""
    conversation = Conversation(
        user_id=sample_user.id,
        session_id="session-test-001",
        role="user",
        content="我今天感觉有点头晕",
        risk_score=3.0,
        category="health"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


@pytest.fixture
def sample_health_notification(db_session, sample_user) -> HealthNotification:
    """创建测试健康通知"""
    notification = HealthNotification(
        user_id=sample_user.id,
        conversation_summary="老人表示头晕不适",
        risk_score=7.0,
        risk_reason="头晕症状，建议关注",
        is_read=False,
        is_handled=False
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


# ==================== 认证Fixtures ====================

@pytest.fixture
def auth_headers(sample_user_auth) -> Dict[str, str]:
    """生成老人端认证头"""
    from app.core.security import create_tokens

    tokens = create_tokens(
        user_id=str(sample_user_auth.id),
        role=sample_user_auth.role
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def family_auth_headers(sample_family_auth) -> Dict[str, str]:
    """生成家属端认证头"""
    from app.core.security import create_tokens

    tokens = create_tokens(
        user_id=str(sample_family_auth.id),
        role=sample_family_auth.role
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def admin_auth_headers() -> Dict[str, str]:
    """生成管理员认证头"""
    from app.core.security import create_tokens

    tokens = create_tokens(
        user_id="admin-001",
        role="admin"
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def device_auth_headers(sample_device_auth) -> Dict[str, str]:
    """生成设备端认证头"""
    from app.core.security import create_tokens

    tokens = create_tokens(
        user_id=str(sample_device_auth.id),
        role='device'
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def device_auth_headers(sample_device_auth) -> Dict[str, str]:
    """生成设备认证头"""
    from app.core.security import create_tokens

    tokens = create_tokens(
        user_id=str(sample_device_auth.id),
        role="device",
        device_id=sample_device_auth.device_id
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_qwen_service():
    """模拟通义千问AI服务"""
    with patch('app.services.qwen_service.Generation') as mock_gen:
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''没事的，头晕很常见，可能是休息不好。多喝点温水，坐下来休息一会儿。

```json
{"risk_score": 3, "risk_reason": "轻微头晕，无需过度担心", "need_notify": false, "category": "health", "emotion": {"type": "neutral", "intensity": 2, "keywords": ["头晕"]}, "topics": ["健康"]}
```'''

        mock_gen.call.return_value = mock_response
        yield mock_gen


@pytest.fixture
def mock_qwen_high_risk():
    """模拟高风险AI响应"""
    with patch('app.services.qwen_service.Generation') as mock_gen:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''别担心，让孩子带您去检查一下比较放心。现在先坐下来休息，不要乱走动。

```json
{"risk_score": 8, "risk_reason": "胸闷症状，建议就医", "need_notify": true, "category": "health", "emotion": {"type": "anxious", "intensity": 4, "keywords": ["胸闷", "难受"]}, "topics": ["健康", "紧急"]}
```'''

        mock_gen.call.return_value = mock_response
        yield mock_gen


@pytest.fixture
def mock_iflytek_tts():
    """模拟科大讯飞TTS服务"""
    with patch('app.services.xfyun_service.XfyunTTS') as mock_tts:
        mock_instance = Mock()
        mock_instance.synthesize.return_value = b"fake_audio_data"
        mock_tts.return_value = mock_instance
        yield mock_tts


@pytest.fixture
def mock_iflytek_asr():
    """模拟科大讯飞ASR服务"""
    with patch('app.services.xfyun_service.XfyunASR') as mock_asr:
        mock_instance = Mock()
        mock_instance.recognize.return_value = "我今天感觉还不错"
        mock_asr.return_value = mock_instance
        yield mock_asr


@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    with patch('app.core.cache.get_redis_client') as mock:
        mock.return_value = None  # 使用内存存储
        yield mock


# ==================== 辅助函数 ====================

@pytest.fixture
def create_user(db_session):
    """用户工厂函数"""
    def _create_user(name: str = "测试用户", device_id: str = None, dialect: str = "mandarin") -> User:
        if device_id is None:
            import uuid
            device_id = f"device-{uuid.uuid4().hex[:8]}"

        user = User(name=name, device_id=device_id, dialect=dialect)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user


@pytest.fixture
def create_conversation(db_session):
    """对话工厂函数"""
    def _create_conversation(
        user_id: int,
        role: str = "user",
        content: str = "测试消息",
        risk_score: float = 1.0,
        category: str = "chat"
    ) -> Conversation:
        import uuid
        conv = Conversation(
            user_id=user_id,
            session_id=f"session-{uuid.uuid4().hex[:8]}",
            role=role,
            content=content,
            risk_score=risk_score,
            category=category
        )
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)
        return conv
    return _create_conversation


# ==================== 测试数据常量 ====================

TEST_USER_DATA = {
    "name": "测试老人",
    "device_id": "test-device-001",
    "dialect": "mandarin"
}

TEST_AUTH_DATA = {
    "username": "13800138000",
    "password": "Test123456"
}

TEST_FAMILY_DATA = {
    "name": "测试子女",
    "phone": "13900139000"
}

TEST_CHAT_MESSAGE = {
    "message": "我今天感觉有点头晕",
    "session_id": "test-session-001"
}

TEST_HEALTH_MESSAGES = {
    "low_risk": "今天天气真好，我出去散步了",
    "medium_risk": "我最近睡眠不太好，总是醒",
    "high_risk": "我胸口闷得慌，有点喘不上气"
}
