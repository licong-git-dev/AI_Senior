"""单元测试 · FamilyAccount 服务（r18）"""
import os
import tempfile
from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import (
    Base,
    FamilyAccount,
    FamilyAccountInvite,
    FamilyAccountMember,
    User,
    UserAuth,
)
from app.services.family_account_service import (
    CannotRemoveLastPayerError,
    FamilyAccountError,
    InsufficientPermissionError,
    InviteExpiredOrUsedError,
    NotAMemberError,
    family_account_service,
)


@pytest.fixture
def db():
    """每个测试一个独立内存 SQLite"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def alice_auth(db):
    """老大 alice"""
    ua = UserAuth(username="13800001000", password_hash="x", role="family")
    db.add(ua)
    db.commit()
    db.refresh(ua)
    return ua


@pytest.fixture
def bob_auth(db):
    """老二 bob"""
    ua = UserAuth(username="13800002000", password_hash="x", role="family")
    db.add(ua)
    db.commit()
    db.refresh(ua)
    return ua


@pytest.fixture
def carol_auth(db):
    """局外人 carol（用于测试越权）"""
    ua = UserAuth(username="13800003000", password_hash="x", role="family")
    db.add(ua)
    db.commit()
    db.refresh(ua)
    return ua


@pytest.fixture
def mama(db):
    """妈妈这位老人"""
    u = User(name="妈妈", dialect="wuhan")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


class TestCreate:
    @pytest.mark.unit
    def test_create_account_makes_creator_payer(self, db, alice_auth, mama):
        acc = family_account_service.create_account(
            db, alice_auth.id, "妈妈的家庭", beneficiary_user_id=mama.id
        )
        assert acc.id is not None
        assert acc.primary_payer_user_auth_id == alice_auth.id
        assert acc.beneficiary_user_id == mama.id

        member = family_account_service.get_member(db, acc.id, alice_auth.id)
        assert member is not None
        assert member.role == "payer"
        assert member.permission_level == 5


class TestInvite:
    @pytest.mark.unit
    def test_payer_can_invite(self, db, alice_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id)
        assert len(inv.invite_code) == 6
        assert inv.invited_role == "caretaker"
        assert inv.expires_at > inv.created_at

    @pytest.mark.unit
    def test_non_payer_cannot_invite(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        # bob 不是成员
        with pytest.raises(NotAMemberError):
            family_account_service.create_invite(db, acc.id, bob_auth.id)

    @pytest.mark.unit
    def test_accept_invite_adds_member(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        m = family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)
        assert m.user_auth_id == bob_auth.id
        assert m.role == "caretaker"

        # 邀请已被消费
        db.refresh(inv)
        assert inv.used_at is not None
        assert inv.used_by_user_auth_id == bob_auth.id

    @pytest.mark.unit
    def test_invite_cannot_be_used_twice(self, db, alice_auth, bob_auth, carol_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)
        # carol 试图复用
        with pytest.raises(InviteExpiredOrUsedError):
            family_account_service.accept_invite(db, inv.invite_code, carol_auth.id)

    @pytest.mark.unit
    def test_invite_self_rejected(self, db, alice_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id)
        with pytest.raises(FamilyAccountError, match="自己"):
            family_account_service.accept_invite(db, inv.invite_code, alice_auth.id)

    @pytest.mark.unit
    def test_expired_invite_rejected(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        # 手工置过期
        from datetime import datetime
        inv.expires_at = datetime.now() - timedelta(seconds=10)
        db.commit()
        with pytest.raises(InviteExpiredOrUsedError):
            family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)


class TestPayerTransfer:
    @pytest.mark.unit
    def test_transfer_promotes_new_demotes_old(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)

        new_acc = family_account_service.transfer_payer(db, acc.id, alice_auth.id, bob_auth.id)
        assert new_acc.primary_payer_user_auth_id == bob_auth.id

        alice_m = family_account_service.get_member(db, acc.id, alice_auth.id)
        bob_m = family_account_service.get_member(db, acc.id, bob_auth.id)
        assert bob_m.role == "payer"
        assert alice_m.role == "caretaker"  # 被降级，但仍可访问

    @pytest.mark.unit
    def test_cannot_transfer_to_non_member(self, db, alice_auth, carol_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        with pytest.raises(FamilyAccountError, match="不是该家庭账户成员"):
            family_account_service.transfer_payer(db, acc.id, alice_auth.id, carol_auth.id)

    @pytest.mark.unit
    def test_only_payer_can_transfer(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)
        # bob (caretaker) 试图转 payer 给自己
        with pytest.raises(InsufficientPermissionError):
            family_account_service.transfer_payer(db, acc.id, bob_auth.id, bob_auth.id)


class TestLeave:
    @pytest.mark.unit
    def test_caretaker_can_leave(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)
        family_account_service.leave_account(db, acc.id, bob_auth.id)
        assert family_account_service.get_member(db, acc.id, bob_auth.id) is None

    @pytest.mark.unit
    def test_last_payer_cannot_leave(self, db, alice_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        with pytest.raises(CannotRemoveLastPayerError):
            family_account_service.leave_account(db, acc.id, alice_auth.id)

    @pytest.mark.unit
    def test_payer_can_leave_after_transfer(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)
        family_account_service.transfer_payer(db, acc.id, alice_auth.id, bob_auth.id)
        # alice 现在是 caretaker，可以退会
        family_account_service.leave_account(db, acc.id, alice_auth.id)
        assert family_account_service.get_member(db, acc.id, alice_auth.id) is None


class TestListAndIsolation:
    @pytest.mark.unit
    def test_list_my_accounts_includes_only_membership(self, db, alice_auth, bob_auth, mama):
        acc1 = family_account_service.create_account(db, alice_auth.id, "妈妈家", mama.id)
        # bob 创建另一个账户（如岳父母）
        acc2 = family_account_service.create_account(db, bob_auth.id, "岳父母家")

        alice_list = family_account_service.list_my_accounts(db, alice_auth.id)
        bob_list = family_account_service.list_my_accounts(db, bob_auth.id)

        assert {a.id for a in alice_list} == {acc1.id}
        assert {a.id for a in bob_list} == {acc2.id}

    @pytest.mark.unit
    def test_list_members_requires_membership(self, db, alice_auth, carol_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        # carol 不是成员，不能查
        with pytest.raises(NotAMemberError):
            family_account_service.list_members(db, acc.id, carol_auth.id)

    @pytest.mark.unit
    def test_list_members_marks_self(self, db, alice_auth, bob_auth, mama):
        acc = family_account_service.create_account(db, alice_auth.id, "家", mama.id)
        inv = family_account_service.create_invite(db, acc.id, alice_auth.id, "caretaker")
        family_account_service.accept_invite(db, inv.invite_code, bob_auth.id)

        members_view_alice = family_account_service.list_members(db, acc.id, alice_auth.id)
        # 找出 alice 自己那一行
        alice_row = next(m for m in members_view_alice if m.user_auth_id == alice_auth.id)
        bob_row = next(m for m in members_view_alice if m.user_auth_id == bob_auth.id)
        assert alice_row.is_self is True
        assert bob_row.is_self is False
