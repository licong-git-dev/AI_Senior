"""
家庭账户 API（r18 · 解耦付费者≠使用者）

8 个端点：
- POST /api/family-account/                    创建账户
- GET  /api/family-account/                    我所属的全部账户
- GET  /api/family-account/{id}/members        成员列表
- POST /api/family-account/{id}/invite         payer 创建邀请码
- POST /api/family-account/accept-invite       接受邀请
- POST /api/family-account/{id}/transfer-payer 转让主付费人
- PUT  /api/family-account/{id}/beneficiary    变更受益老人
- DELETE /api/family-account/{id}/leave        退出账户

权限模型：
- payer:     可执行所有
- caretaker: list_members + accept_invite + leave
- observer:  list_members + leave
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db
from app.core.security import get_current_user, UserInfo
from app.services.family_account_service import (
    CannotRemoveLastPayerError,
    FamilyAccountError,
    InsufficientPermissionError,
    InviteExpiredOrUsedError,
    NotAMemberError,
    family_account_service,
)


router = APIRouter(prefix="/api/family-account", tags=["家庭账户"])


# ===== 请求 / 响应模型 =====


class CreateAccountRequest(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=100, description="家庭账户名称")
    beneficiary_user_id: Optional[int] = Field(
        None, description="受益老人的 User.id（可后续设置）"
    )


class CreateInviteRequest(BaseModel):
    invited_role: str = Field(
        "caretaker",
        description="被邀请人的角色: payer / caretaker / observer",
    )
    ttl_days: int = Field(7, ge=1, le=30, description="邀请有效期（天）")
    note: Optional[str] = Field(None, max_length=200)


class AcceptInviteRequest(BaseModel):
    invite_code: str = Field(..., min_length=4, max_length=16)


class TransferPayerRequest(BaseModel):
    new_payer_user_auth_id: int = Field(..., description="新付费人的 user_auth.id")


class ChangeBeneficiaryRequest(BaseModel):
    new_beneficiary_user_id: int = Field(..., description="新受益老人的 User.id")


# ===== 工具：把 service 异常翻译为 HTTPException =====


def _handle_service_errors(fn):
    """装饰器：捕获 service 异常翻译为合适的 HTTP 状态码"""
    from functools import wraps

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except NotAMemberError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except InsufficientPermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except InviteExpiredOrUsedError as e:
            raise HTTPException(status_code=410, detail=str(e))  # 410 Gone 表达"已失效"
        except CannotRemoveLastPayerError as e:
            raise HTTPException(status_code=409, detail=str(e))  # 409 Conflict
        except FamilyAccountError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return wrapper


def _user_auth_id(current_user: UserInfo) -> int:
    """从 UserInfo 提取 user_auth.id（JWT.sub 是字符串）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="JWT 中 user_id 非数字，无法用于家庭账户")


# ===== 端点 =====


@router.post("/", status_code=201)
@_handle_service_errors
async def create_account(
    body: CreateAccountRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建家庭账户（创建者自动成为 payer，permission_level=5）"""
    ua_id = _user_auth_id(current_user)
    account = family_account_service.create_account(
        db=db,
        creator_user_auth_id=ua_id,
        account_name=body.account_name,
        beneficiary_user_id=body.beneficiary_user_id,
    )
    return {
        "id": account.id,
        "account_name": account.account_name,
        "beneficiary_user_id": account.beneficiary_user_id,
        "primary_payer_user_auth_id": account.primary_payer_user_auth_id,
        "status": account.status,
        "created_at": account.created_at.isoformat(),
    }


@router.get("/")
@_handle_service_errors
async def list_my_accounts(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我所属的全部家庭账户（一个人可同时关心父母+岳父母两户）"""
    ua_id = _user_auth_id(current_user)
    accounts = family_account_service.list_my_accounts(db=db, user_auth_id=ua_id)
    return {
        "items": [
            {
                "id": a.id,
                "account_name": a.account_name,
                "beneficiary_user_id": a.beneficiary_user_id,
                "primary_payer_user_auth_id": a.primary_payer_user_auth_id,
                "is_primary_payer": a.primary_payer_user_auth_id == ua_id,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in accounts
        ]
    }


@router.get("/{family_account_id}/members")
@_handle_service_errors
async def list_members(
    family_account_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家庭账户成员列表（所有角色都可查看自己同伴）"""
    ua_id = _user_auth_id(current_user)
    members = family_account_service.list_members(
        db=db, family_account_id=family_account_id, viewer_user_auth_id=ua_id
    )
    return {
        "items": [
            {
                "user_auth_id": m.user_auth_id,
                "username": m.username,
                "role": m.role,
                "permission_level": m.permission_level,
                "joined_at": m.joined_at.isoformat(),
                "is_self": m.is_self,
            }
            for m in members
        ]
    }


@router.post("/{family_account_id}/invite")
@_handle_service_errors
async def create_invite(
    family_account_id: int,
    body: CreateInviteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """payer 生成邀请码（caretaker / observer / 另一 payer）"""
    ua_id = _user_auth_id(current_user)
    invite = family_account_service.create_invite(
        db=db,
        family_account_id=family_account_id,
        inviter_user_auth_id=ua_id,
        invited_role=body.invited_role,
        ttl_days=body.ttl_days,
        note=body.note,
    )
    return {
        "invite_code": invite.invite_code,
        "invited_role": invite.invited_role,
        "expires_at": invite.expires_at.isoformat(),
        "share_hint": (
            f"复制邀请码 {invite.invite_code} 给家人，"
            f"或分享链接：anxinbao://invite?code={invite.invite_code}"
        ),
    }


@router.post("/accept-invite", status_code=201)
@_handle_service_errors
async def accept_invite(
    body: AcceptInviteRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """接受邀请加入家庭账户"""
    ua_id = _user_auth_id(current_user)
    member = family_account_service.accept_invite(
        db=db, invite_code=body.invite_code, accepter_user_auth_id=ua_id
    )
    return {
        "family_account_id": member.family_account_id,
        "role": member.role,
        "permission_level": member.permission_level,
        "joined_at": member.joined_at.isoformat(),
    }


@router.post("/{family_account_id}/transfer-payer")
@_handle_service_errors
async def transfer_payer(
    family_account_id: int,
    body: TransferPayerRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """主付费人转让（仅当前 payer 自己可执行）"""
    ua_id = _user_auth_id(current_user)
    account = family_account_service.transfer_payer(
        db=db,
        family_account_id=family_account_id,
        current_payer_user_auth_id=ua_id,
        new_payer_user_auth_id=body.new_payer_user_auth_id,
    )
    return {
        "id": account.id,
        "primary_payer_user_auth_id": account.primary_payer_user_auth_id,
        "updated_at": account.updated_at.isoformat(),
    }


@router.put("/{family_account_id}/beneficiary")
@_handle_service_errors
async def change_beneficiary(
    family_account_id: int,
    body: ChangeBeneficiaryRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """变更受益老人（仅 payer）"""
    ua_id = _user_auth_id(current_user)
    account = family_account_service.change_beneficiary(
        db=db,
        family_account_id=family_account_id,
        operator_user_auth_id=ua_id,
        new_beneficiary_user_id=body.new_beneficiary_user_id,
    )
    return {
        "id": account.id,
        "beneficiary_user_id": account.beneficiary_user_id,
        "updated_at": account.updated_at.isoformat(),
    }


@router.delete("/{family_account_id}/leave", status_code=204)
@_handle_service_errors
async def leave_account(
    family_account_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """退出家庭账户（唯一 payer 必须先转让）"""
    ua_id = _user_auth_id(current_user)
    family_account_service.leave_account(
        db=db, family_account_id=family_account_id, member_user_auth_id=ua_id
    )
    return None
