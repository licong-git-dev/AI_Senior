"""
家庭账户服务（r18 · 解耦付费者≠使用者悖论）

设计依据：PRODUCT_INSIGHTS.md Insight #1

核心能力：
1. 创建家庭账户（注册流程末尾自动建 solo 账户，或子女主动建）
2. 邀请其他成员（生成 6 位邀请码，7 天过期）
3. 接受邀请（被邀请人输入邀请码加入）
4. 角色管理（payer ↔ caretaker ↔ observer 升降级）
5. 主付费人转让（如老大要让老二接管订阅）
6. 受益老人变更（如父母重组，谁的"妈"是这个账户的受益人）
7. 退会（永久离开家庭）
8. 查询（成员列表 + 当前角色 + 权限矩阵）

权限矩阵：
                    | payer | caretaker | observer
账单/支付            | ✅    | ❌        | ❌
邀请新成员           | ✅    | ❌        | ❌
查看完整日报         | ✅    | ✅        | ❌
查看安心指数（聚合）  | ✅    | ✅        | ✅
设置 DND/触发器      | ✅    | ✅        | ❌
触发 SOS（代老人）   | ✅    | ✅        | ❌
转让 payer           | 仅自己| ❌        | ❌
"""
from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.database import (
    FamilyAccount,
    FamilyAccountInvite,
    FamilyAccountMember,
    User,
    UserAuth,
)

logger = logging.getLogger(__name__)


# ===== 常量 =====

VALID_ROLES = ("payer", "caretaker", "observer")
DEFAULT_INVITE_TTL_DAYS = 7
INVITE_CODE_LEN = 6  # 0-9 + 大写字母（去掉 O/I/0/1 防混淆）
_SAFE_INVITE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _generate_invite_code() -> str:
    return "".join(secrets.choice(_SAFE_INVITE_ALPHABET) for _ in range(INVITE_CODE_LEN))


# ===== 异常类 =====


class FamilyAccountError(Exception):
    """家庭账户操作异常基类"""


class NotAMemberError(FamilyAccountError):
    """操作者不是该家庭账户成员"""


class InsufficientPermissionError(FamilyAccountError):
    """权限不足（如非 payer 试图改订阅）"""


class InviteExpiredOrUsedError(FamilyAccountError):
    """邀请码已过期或已被使用"""


class CannotRemoveLastPayerError(FamilyAccountError):
    """家庭账户不能没有 payer（必须先转让再退会）"""


# ===== 服务类 =====


@dataclass
class MemberInfo:
    """对外暴露的成员信息（脱敏 user_auth_id 已经够用）"""
    user_auth_id: int
    username: str
    role: str
    permission_level: int
    joined_at: datetime
    is_self: bool = False


class FamilyAccountService:
    """家庭账户服务（无状态，所有方法接受 db 注入）"""

    # ----- 创建 -----

    def create_account(
        self,
        db: Session,
        creator_user_auth_id: int,
        account_name: str,
        beneficiary_user_id: Optional[int] = None,
    ) -> FamilyAccount:
        """创建家庭账户；creator 自动成为 payer。"""
        account = FamilyAccount(
            account_name=account_name or "未命名家庭",
            beneficiary_user_id=beneficiary_user_id,
            primary_payer_user_auth_id=creator_user_auth_id,
        )
        db.add(account)
        db.flush()  # 拿 id

        # 写 member 行
        member = FamilyAccountMember(
            family_account_id=account.id,
            user_auth_id=creator_user_auth_id,
            role="payer",
            permission_level=5,
        )
        db.add(member)
        db.commit()
        db.refresh(account)

        # r20 · T 选项：北极星埋点
        try:
            from app.core.north_star_metrics import record_family_account_created
            record_family_account_created()
        except Exception:
            pass

        logger.info(f"FamilyAccount 创建: id={account.id} creator_user_auth={creator_user_auth_id}")
        return account

    # ----- 查询 -----

    def list_my_accounts(self, db: Session, user_auth_id: int) -> List[FamilyAccount]:
        """我所属的全部家庭账户（一个人可同时关心父母+岳父母两户）"""
        return (
            db.query(FamilyAccount)
            .join(FamilyAccountMember, FamilyAccountMember.family_account_id == FamilyAccount.id)
            .filter(FamilyAccountMember.user_auth_id == user_auth_id)
            .filter(FamilyAccount.status != "archived")
            .all()
        )

    def get_member(
        self,
        db: Session,
        family_account_id: int,
        user_auth_id: int,
    ) -> Optional[FamilyAccountMember]:
        return (
            db.query(FamilyAccountMember)
            .filter(
                FamilyAccountMember.family_account_id == family_account_id,
                FamilyAccountMember.user_auth_id == user_auth_id,
            )
            .first()
        )

    def list_members(
        self,
        db: Session,
        family_account_id: int,
        viewer_user_auth_id: int,
    ) -> List[MemberInfo]:
        """成员列表 —— viewer 必须是该账户成员"""
        if not self.get_member(db, family_account_id, viewer_user_auth_id):
            raise NotAMemberError("您不是该家庭账户成员")

        rows = (
            db.query(FamilyAccountMember, UserAuth)
            .join(UserAuth, UserAuth.id == FamilyAccountMember.user_auth_id)
            .filter(FamilyAccountMember.family_account_id == family_account_id)
            .all()
        )
        return [
            MemberInfo(
                user_auth_id=m.user_auth_id,
                username=ua.username,
                role=m.role,
                permission_level=m.permission_level,
                joined_at=m.joined_at,
                is_self=(ua.id == viewer_user_auth_id),
            )
            for m, ua in rows
        ]

    # ----- 邀请 -----

    def create_invite(
        self,
        db: Session,
        family_account_id: int,
        inviter_user_auth_id: int,
        invited_role: str = "caretaker",
        ttl_days: int = DEFAULT_INVITE_TTL_DAYS,
        note: Optional[str] = None,
    ) -> FamilyAccountInvite:
        """payer 创建邀请码（默认 caretaker 角色，7 天过期）"""
        self._require_role(db, family_account_id, inviter_user_auth_id, required="payer")

        if invited_role not in VALID_ROLES:
            raise FamilyAccountError(f"非法角色: {invited_role}")

        # 邀请码碰撞极小（6 位 32 字母 = 1B），但仍循环避免
        for _ in range(5):
            code = _generate_invite_code()
            existing = db.query(FamilyAccountInvite).filter(
                FamilyAccountInvite.invite_code == code
            ).first()
            if not existing:
                break
        else:
            raise FamilyAccountError("邀请码生成多次冲突，稍后重试")

        invite = FamilyAccountInvite(
            invite_code=code,
            family_account_id=family_account_id,
            invited_role=invited_role,
            inviter_user_auth_id=inviter_user_auth_id,
            expires_at=datetime.now() + timedelta(days=max(1, min(30, ttl_days))),
            note=note,
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    def accept_invite(
        self,
        db: Session,
        invite_code: str,
        accepter_user_auth_id: int,
    ) -> FamilyAccountMember:
        """被邀请人接受邀请加入家庭账户"""
        invite = (
            db.query(FamilyAccountInvite)
            .filter(FamilyAccountInvite.invite_code == invite_code.strip().upper())
            .first()
        )
        if not invite:
            raise InviteExpiredOrUsedError("邀请码不存在")
        if invite.used_at is not None:
            raise InviteExpiredOrUsedError("邀请码已被使用")
        if invite.expires_at < datetime.now():
            raise InviteExpiredOrUsedError("邀请码已过期")
        if invite.inviter_user_auth_id == accepter_user_auth_id:
            raise FamilyAccountError("不能接受自己发出的邀请")

        # 已是成员？
        existing = self.get_member(db, invite.family_account_id, accepter_user_auth_id)
        if existing:
            # 标记 invite 为已用，但不重复加入
            invite.used_at = datetime.now()
            invite.used_by_user_auth_id = accepter_user_auth_id
            db.commit()
            return existing

        # 加入
        permission_map = {"payer": 5, "caretaker": 3, "observer": 1}
        member = FamilyAccountMember(
            family_account_id=invite.family_account_id,
            user_auth_id=accepter_user_auth_id,
            role=invite.invited_role,
            permission_level=permission_map.get(invite.invited_role, 3),
            invited_by_user_auth_id=invite.inviter_user_auth_id,
        )
        db.add(member)
        invite.used_at = datetime.now()
        invite.used_by_user_auth_id = accepter_user_auth_id

        try:
            db.commit()
            db.refresh(member)
        except IntegrityError:
            # 极端竞态：另一线程刚加入，回滚后查询返回
            db.rollback()
            return self.get_member(db, invite.family_account_id, accepter_user_auth_id)

        # r20 · T 选项：北极星埋点
        try:
            from app.core.north_star_metrics import record_family_invite_accepted
            record_family_invite_accepted(invited_role=invite.invited_role)
        except Exception:
            pass

        logger.info(
            f"FamilyAccount {invite.family_account_id} 新成员加入: "
            f"user_auth={accepter_user_auth_id} role={invite.invited_role}"
        )
        return member

    # ----- 角色与转让 -----

    def transfer_payer(
        self,
        db: Session,
        family_account_id: int,
        current_payer_user_auth_id: int,
        new_payer_user_auth_id: int,
    ) -> FamilyAccount:
        """主付费人转让（仅当前 payer 自己可执行）"""
        self._require_role(db, family_account_id, current_payer_user_auth_id, required="payer")

        new_member = self.get_member(db, family_account_id, new_payer_user_auth_id)
        if not new_member:
            raise FamilyAccountError("接手人不是该家庭账户成员，请先邀请加入")

        # 升新 payer
        new_member.role = "payer"
        new_member.permission_level = 5
        # 老 payer 降级 caretaker（保持 access 不彻底失去）
        old_member = self.get_member(db, family_account_id, current_payer_user_auth_id)
        if old_member and old_member.user_auth_id != new_payer_user_auth_id:
            old_member.role = "caretaker"
            old_member.permission_level = 3

        # 更新 family_account.primary_payer_user_auth_id
        account = db.query(FamilyAccount).filter(FamilyAccount.id == family_account_id).first()
        if account:
            account.primary_payer_user_auth_id = new_payer_user_auth_id
            account.updated_at = datetime.now()

        db.commit()
        if account:
            db.refresh(account)
        logger.info(
            f"FamilyAccount {family_account_id} payer 转让: "
            f"{current_payer_user_auth_id} → {new_payer_user_auth_id}"
        )
        return account

    def change_beneficiary(
        self,
        db: Session,
        family_account_id: int,
        operator_user_auth_id: int,
        new_beneficiary_user_id: int,
    ) -> FamilyAccount:
        """变更受益老人（仅 payer 可执行；如老人去世/转移护理重心）"""
        self._require_role(db, family_account_id, operator_user_auth_id, required="payer")

        # 验证新受益人 user_id 真实存在
        user_exists = db.query(User).filter(User.id == new_beneficiary_user_id).first()
        if not user_exists:
            raise FamilyAccountError("指定的受益老人不存在")

        account = db.query(FamilyAccount).filter(FamilyAccount.id == family_account_id).first()
        account.beneficiary_user_id = new_beneficiary_user_id
        account.updated_at = datetime.now()
        db.commit()
        db.refresh(account)
        return account

    # ----- 退会 -----

    def leave_account(
        self,
        db: Session,
        family_account_id: int,
        member_user_auth_id: int,
    ) -> None:
        """成员退出家庭账户（如果是唯一 payer 必须先转让）"""
        member = self.get_member(db, family_account_id, member_user_auth_id)
        if not member:
            raise NotAMemberError("您不是该家庭账户成员")

        if member.role == "payer":
            # 检查是否还有其他 payer
            other_payers = (
                db.query(FamilyAccountMember)
                .filter(
                    FamilyAccountMember.family_account_id == family_account_id,
                    FamilyAccountMember.role == "payer",
                    FamilyAccountMember.user_auth_id != member_user_auth_id,
                )
                .count()
            )
            if other_payers == 0:
                raise CannotRemoveLastPayerError(
                    "您是唯一付费人，必须先把 payer 角色转让给其他成员才能退会"
                )

        db.delete(member)
        db.commit()
        logger.info(
            f"FamilyAccount {family_account_id} 成员退出: user_auth={member_user_auth_id}"
        )

    # ----- 内部 -----

    def _require_role(
        self,
        db: Session,
        family_account_id: int,
        user_auth_id: int,
        required: str,
    ) -> None:
        """断言 user_auth_id 在该 family_account 中拥有 required 角色"""
        member = self.get_member(db, family_account_id, user_auth_id)
        if not member:
            raise NotAMemberError("您不是该家庭账户成员")
        # payer > caretaker > observer
        rank = {"payer": 3, "caretaker": 2, "observer": 1}
        if rank.get(member.role, 0) < rank.get(required, 99):
            raise InsufficientPermissionError(
                f"此操作需要 {required} 角色，您当前角色: {member.role}"
            )


# 全局单例（无状态，可复用）
family_account_service = FamilyAccountService()
