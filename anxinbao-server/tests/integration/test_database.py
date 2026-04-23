"""
数据库集成测试
测试数据库操作、事务、关联关系等
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.database import (
    User, FamilyMember, Conversation, HealthNotification,
    UserAuth, DeviceAuth, RefreshToken, AuditLog
)


class TestUserOperations:
    """用户数据操作测试"""

    @pytest.mark.integration
    def test_create_user(self, db_session: Session):
        """测试创建用户"""
        user = User(
            name="集成测试用户",
            device_id="integration-device-001",
            dialect="mandarin"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.created_at is not None

    @pytest.mark.integration
    def test_user_with_family_members(self, db_session: Session, create_user):
        """测试用户与家属关联"""
        user = create_user(name="有家属的老人")

        family1 = FamilyMember(
            user_id=user.id,
            name="大儿子",
            phone="13800001111",
            is_primary=True
        )
        family2 = FamilyMember(
            user_id=user.id,
            name="小女儿",
            phone="13800002222",
            is_primary=False
        )

        db_session.add_all([family1, family2])
        db_session.commit()

        # 刷新用户对象
        db_session.refresh(user)

        assert len(user.family_members) == 2
        assert any(f.is_primary for f in user.family_members)

    @pytest.mark.integration
    def test_user_with_conversations(self, db_session: Session, sample_user):
        """测试用户与对话关联"""
        # 添加多条对话
        for i in range(5):
            conv = Conversation(
                user_id=sample_user.id,
                session_id="session-integration-001",
                role="user" if i % 2 == 0 else "assistant",
                content=f"测试消息{i}",
                risk_score=1.0,
                category="chat"
            )
            db_session.add(conv)

        db_session.commit()
        db_session.refresh(sample_user)

        assert len(sample_user.conversations) == 5

    @pytest.mark.integration
    def test_cascade_delete_user(self, db_session: Session, create_user):
        """测试级联删除用户"""
        user = create_user(name="待删除用户")

        # 添加关联数据
        family = FamilyMember(user_id=user.id, name="家属", phone="13800003333")
        conv = Conversation(
            user_id=user.id,
            session_id="delete-test",
            role="user",
            content="测试",
            risk_score=1.0,
            category="chat"
        )

        db_session.add_all([family, conv])
        db_session.commit()

        user_id = user.id

        # 删除用户（注意：需要先删除外键约束的记录）
        db_session.query(Conversation).filter(Conversation.user_id == user_id).delete()
        db_session.query(FamilyMember).filter(FamilyMember.user_id == user_id).delete()
        db_session.delete(user)
        db_session.commit()

        # 验证删除
        assert db_session.query(User).filter(User.id == user_id).first() is None


class TestAuthOperations:
    """认证数据操作测试"""

    @pytest.mark.integration
    def test_create_user_auth(self, db_session: Session, sample_user):
        """测试创建用户认证"""
        from app.core.security import get_password_hash

        auth = UserAuth(
            username="auth_test_user",
            password_hash=get_password_hash("TestPassword123"),
            role="elder",
            user_id=sample_user.id,
            is_active=True
        )

        db_session.add(auth)
        db_session.commit()

        assert auth.id is not None
        assert auth.created_at is not None

    @pytest.mark.integration
    def test_create_device_auth(self, db_session: Session, sample_user):
        """测试创建设备认证"""
        from app.core.security import get_password_hash

        device = DeviceAuth(
            device_id="integration-speaker-001",
            device_secret=get_password_hash("device-secret"),
            device_type="speaker",
            user_id=sample_user.id,
            is_active=True
        )

        db_session.add(device)
        db_session.commit()

        assert device.id is not None
        db_session.refresh(device)
        assert device.user is not None

    @pytest.mark.integration
    def test_refresh_token_lifecycle(self, db_session: Session, sample_user_auth):
        """测试刷新令牌生命周期"""
        import hashlib

        token_hash = hashlib.sha256("test_refresh_token".encode()).hexdigest()

        token = RefreshToken(
            token_hash=token_hash,
            user_auth_id=sample_user_auth.id,
            expires_at=datetime.now() + timedelta(days=7),
            is_revoked=False
        )

        db_session.add(token)
        db_session.commit()

        # 验证创建
        assert token.id is not None

        # 撤销令牌
        token.is_revoked = True
        db_session.commit()

        # 验证撤销
        db_session.refresh(token)
        assert token.is_revoked is True

    @pytest.mark.integration
    def test_audit_log_creation(self, db_session: Session):
        """测试审计日志创建"""
        log = AuditLog(
            user_id="test-user-001",
            action="login",
            resource="auth",
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0",
            details='{"method": "password"}',
            status="success"
        )

        db_session.add(log)
        db_session.commit()

        assert log.id is not None
        assert log.created_at is not None


class TestConversationOperations:
    """对话数据操作测试"""

    @pytest.mark.integration
    def test_create_conversation_chain(self, db_session: Session, sample_user):
        """测试创建对话链"""
        session_id = "chain-session-001"
        messages = [
            ("user", "你好"),
            ("assistant", "您好！有什么可以帮您的？"),
            ("user", "我今天有点头晕"),
            ("assistant", "别担心，头晕很常见。您最近睡眠怎么样？"),
        ]

        for role, content in messages:
            conv = Conversation(
                user_id=sample_user.id,
                session_id=session_id,
                role=role,
                content=content,
                risk_score=1.0 if role == "user" else 0.0,
                category="chat"
            )
            db_session.add(conv)

        db_session.commit()

        # 查询对话链
        conversations = db_session.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(Conversation.created_at).all()

        assert len(conversations) == 4
        assert conversations[0].role == "user"
        assert conversations[-1].role == "assistant"

    @pytest.mark.integration
    def test_high_risk_conversation_query(self, db_session: Session, sample_user):
        """测试高风险对话查询"""
        # 创建不同风险等级的对话
        risk_levels = [1, 2, 5, 7, 9]

        for i, risk in enumerate(risk_levels):
            conv = Conversation(
                user_id=sample_user.id,
                session_id=f"risk-test-{i}",
                role="user",
                content=f"风险等级{risk}的消息",
                risk_score=risk,
                category="health"
            )
            db_session.add(conv)

        db_session.commit()

        # 查询高风险对话（>=7）
        high_risk = db_session.query(Conversation).filter(
            Conversation.user_id == sample_user.id,
            Conversation.risk_score >= 7
        ).all()

        assert len(high_risk) == 2


class TestHealthNotificationOperations:
    """健康通知操作测试"""

    @pytest.mark.integration
    def test_create_health_notification(self, db_session: Session, sample_user):
        """测试创建健康通知"""
        notification = HealthNotification(
            user_id=sample_user.id,
            conversation_summary="老人表示胸闷不适",
            risk_score=8.0,
            risk_reason="胸闷症状，建议及时就医",
            is_read=False,
            is_handled=False
        )

        db_session.add(notification)
        db_session.commit()

        assert notification.id is not None

    @pytest.mark.integration
    def test_mark_notification_as_read(self, db_session: Session, sample_health_notification):
        """测试标记通知已读"""
        sample_health_notification.is_read = True
        db_session.commit()

        db_session.refresh(sample_health_notification)
        assert sample_health_notification.is_read is True

    @pytest.mark.integration
    def test_query_unread_notifications(self, db_session: Session, sample_user):
        """测试查询未读通知"""
        # 创建已读和未读通知
        for i in range(5):
            notification = HealthNotification(
                user_id=sample_user.id,
                conversation_summary=f"通知{i}",
                risk_score=5.0,
                risk_reason="测试",
                is_read=(i % 2 == 0),  # 偶数已读
                is_handled=False
            )
            db_session.add(notification)

        db_session.commit()

        # 查询未读
        unread = db_session.query(HealthNotification).filter(
            HealthNotification.user_id == sample_user.id,
            HealthNotification.is_read == False
        ).all()

        assert len(unread) == 2


class TestQueryPerformance:
    """查询性能测试"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_bulk_conversation_insert(self, db_session: Session, sample_user):
        """测试批量插入对话"""
        import time

        conversations = []
        for i in range(1000):
            conv = Conversation(
                user_id=sample_user.id,
                session_id=f"bulk-session-{i // 100}",
                role="user" if i % 2 == 0 else "assistant",
                content=f"批量测试消息{i}",
                risk_score=1.0,
                category="chat"
            )
            conversations.append(conv)

        start = time.time()
        db_session.add_all(conversations)
        db_session.commit()
        duration = time.time() - start

        # 批量插入1000条应该在合理时间内
        assert duration < 10  # 10秒以内

    @pytest.mark.integration
    def test_indexed_query_performance(self, db_session: Session, sample_user, create_conversation):
        """测试索引查询性能"""
        import time

        # 创建一些对话
        for i in range(100):
            create_conversation(
                user_id=sample_user.id,
                content=f"性能测试消息{i}"
            )

        # 测试按user_id查询（有索引）
        start = time.time()
        result = db_session.query(Conversation).filter(
            Conversation.user_id == sample_user.id
        ).all()
        duration = time.time() - start

        assert len(result) >= 100
        assert duration < 1  # 应该很快
