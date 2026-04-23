"""
家庭绑定与监护API
提供家庭组管理、绑定请求、监护功能等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.family_service import (
    family_service,
    remote_operation_service,
    FamilyRole,
    PermissionLevel,
    NotificationType,
    BindingStatus
)
from app.core.security import get_current_user, UserInfo
from app.core.deps import get_db
from app.models.database import UserAuth, FamilyMember, User, FamilyBindingInvite

router = APIRouter(prefix="/api/family", tags=["家庭绑定"])


def _persist_binding_request(binding_req, db: Session) -> None:
    existing = db.query(FamilyBindingInvite).filter(
        FamilyBindingInvite.request_id == binding_req.request_id
    ).first()
    if existing:
        existing.invite_code = binding_req.invite_code
        existing.group_id = binding_req.group_id
        existing.requester_id = binding_req.requester_id
        existing.requester_name = binding_req.requester_name
        existing.target_id = binding_req.target_id
        existing.relationship = binding_req.relationship
        existing.role = binding_req.role.value
        existing.permission_level = binding_req.permission_level.value
        existing.status = binding_req.status.value
        existing.expires_at = binding_req.expires_at
        existing.processed_at = binding_req.processed_at
    else:
        db.add(FamilyBindingInvite(
            request_id=binding_req.request_id,
            invite_code=binding_req.invite_code,
            group_id=binding_req.group_id,
            requester_id=binding_req.requester_id,
            requester_name=binding_req.requester_name,
            target_id=binding_req.target_id,
            relationship=binding_req.relationship,
            role=binding_req.role.value,
            permission_level=binding_req.permission_level.value,
            status=binding_req.status.value,
            expires_at=binding_req.expires_at,
            processed_at=binding_req.processed_at,
        ))
    db.commit()


def _load_binding_request_from_db(invite_code: str, db: Session):
    stored = db.query(FamilyBindingInvite).filter(
        FamilyBindingInvite.invite_code == invite_code.upper()
    ).first()
    if not stored:
        return None

    from app.services.family_service import (
        BindingRequest as ServiceBindingRequest,
        FamilyGroup as ServiceFamilyGroup,
        FamilyMember as ServiceFamilyMember,
    )

    if stored.group_id not in family_service.groups:
        requester_auth = db.query(UserAuth).filter(UserAuth.id == stored.requester_id).first()
        elder_auth = requester_auth
        if requester_auth and not requester_auth.user_id and requester_auth.family_id:
            family_member = db.query(FamilyMember).filter(FamilyMember.id == requester_auth.family_id).first()
            if family_member:
                elder_auth = db.query(UserAuth).filter(UserAuth.user_id == family_member.user_id).first()

        if elder_auth and elder_auth.user_id:
            elder = db.query(User).filter(User.id == elder_auth.user_id).first()
            if elder:
                group = ServiceFamilyGroup(
                    group_id=stored.group_id,
                    name=f"{elder.name}的家庭",
                    elder_id=elder_auth.id,
                    elder_name=elder.name,
                    created_by=stored.requester_id,
                )
                group.settings["elder_profile_id"] = elder.id
                group.members[elder_auth.id] = ServiceFamilyMember(
                    member_id=f"member_{elder_auth.id}",
                    user_id=elder_auth.id,
                    name=elder.name,
                    phone="",
                    role=FamilyRole.ELDER,
                    relationship="本人",
                )
                family_members = db.query(FamilyMember).filter(FamilyMember.user_id == elder.id).all()
                for member in family_members:
                    linked_auth = db.query(UserAuth).filter(UserAuth.family_id == member.id).first()
                    if linked_auth:
                        group.members[linked_auth.id] = ServiceFamilyMember(
                            member_id=f"member_{linked_auth.id}",
                            user_id=linked_auth.id,
                            name=member.name,
                            phone=member.phone or "",
                            role=FamilyRole.GUARDIAN,
                            relationship="家人",
                        )
                        user_group_ids = family_service.user_groups.setdefault(linked_auth.id, [])
                        if stored.group_id not in user_group_ids:
                            user_group_ids.append(stored.group_id)
                family_service.groups[stored.group_id] = group
                elder_group_ids = family_service.user_groups.setdefault(elder_auth.id, [])
                if stored.group_id not in elder_group_ids:
                    elder_group_ids.append(stored.group_id)

    service_request = family_service.binding_requests.get(stored.request_id)
    if service_request:
        return service_request

    service_request = ServiceBindingRequest(
        request_id=stored.request_id,
        group_id=stored.group_id,
        requester_id=stored.requester_id,
        requester_name=stored.requester_name,
        target_id=stored.target_id,
        relationship=stored.relationship,
        role=FamilyRole(stored.role),
        permission_level=PermissionLevel(stored.permission_level),
        status=BindingStatus(stored.status),
        invite_code=stored.invite_code,
        created_at=stored.created_at,
        expires_at=stored.expires_at,
        processed_at=stored.processed_at,
    )
    family_service.binding_requests[stored.request_id] = service_request
    family_service.invite_codes[stored.invite_code] = stored.request_id
    return service_request


def _recover_family_groups_from_db(user_auth_id: int, db: Session):
    """
    基于数据库中的老人/家属绑定关系，重建最小可用的内存家庭组。

    优先复用历史邀请码中已经持久化的 group_id，避免服务重启后为同一老人
    重新生成新的 group_id，导致旧邀请码和恢复后的家庭组分叉。
    """
    from app.services.family_service import (
        FamilyGroup as ServiceFamilyGroup,
        FamilyMember as ServiceFamilyMember,
    )

    auth = db.query(UserAuth).filter(UserAuth.id == user_auth_id).first()
    if not auth:
        return []

    elder_auth = auth
    if auth.family_id:
        family_member = db.query(FamilyMember).filter(FamilyMember.id == auth.family_id).first()
        if not family_member:
            return []
        elder_auth = db.query(UserAuth).filter(UserAuth.user_id == family_member.user_id).first()
        if not elder_auth:
            return []

    if not elder_auth.user_id:
        return []

    elder = db.query(User).filter(User.id == elder_auth.user_id).first()
    if not elder:
        return []

    existing_groups = family_service.get_user_family_groups(elder_auth.id)
    group = next((item for item in existing_groups if item.elder_id == elder_auth.id), None)

    if not group:
        stored_invite = db.query(FamilyBindingInvite).filter(
            FamilyBindingInvite.requester_id == elder_auth.id
        ).order_by(FamilyBindingInvite.created_at.desc()).first()

        if stored_invite:
            group = ServiceFamilyGroup(
                group_id=stored_invite.group_id,
                name=f"{elder.name}的家庭",
                elder_id=elder_auth.id,
                elder_name=elder.name,
                created_by=elder_auth.id,
            )
            family_service.groups[group.group_id] = group
            elder_group_ids = family_service.user_groups.setdefault(elder_auth.id, [])
            if group.group_id not in elder_group_ids:
                elder_group_ids.append(group.group_id)
        else:
            group = family_service.create_family_group(
                elder_id=elder_auth.id,
                elder_name=elder.name,
                group_name=f"{elder.name}的家庭",
                creator_id=elder_auth.id,
            )

    group.settings["elder_profile_id"] = elder.id
    group.members[elder_auth.id] = ServiceFamilyMember(
        member_id=f"member_{elder_auth.id}",
        user_id=elder_auth.id,
        name=elder.name,
        phone="",
        role=FamilyRole.ELDER,
        relationship="本人",
    )

    family_members = db.query(FamilyMember).filter(FamilyMember.user_id == elder.id).all()
    for member in family_members:
        linked_auth = db.query(UserAuth).filter(UserAuth.family_id == member.id).first()
        if not linked_auth:
            continue
        group.members[linked_auth.id] = ServiceFamilyMember(
            member_id=f"member_{linked_auth.id}",
            user_id=linked_auth.id,
            name=member.name,
            phone=member.phone or "",
            role=FamilyRole.GUARDIAN,
            relationship="家人",
        )
        user_group_ids = family_service.user_groups.setdefault(linked_auth.id, [])
        if group.group_id not in user_group_ids:
            user_group_ids.append(group.group_id)

    return [group]


# ==================== 请求/响应模型 ====================

class CreateGroupRequest(BaseModel):
    """创建家庭组请求"""
    group_name: str = Field(..., min_length=1, max_length=50, description="家庭组名称")
    elder_name: str = Field(..., description="老人姓名")


class BindingRequest(BaseModel):
    """创建绑定请求"""
    group_id: str = Field(..., description="家庭组ID")
    target_phone: Optional[str] = Field(None, description="被邀请人手机号（可选）")
    relationship: str = Field(..., description="与老人的关系")
    role: str = Field(default="guardian", description="角色: guardian/family/caregiver")
    permission_level: int = Field(default=3, ge=1, le=5, description="权限级别1-5")


class AcceptBindingRequest(BaseModel):
    """接受绑定请求"""
    name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")


class JoinByCodeRequest(BaseModel):
    """通过邀请码加入"""
    invite_code: str = Field(..., min_length=8, max_length=8, description="邀请码")
    name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")


class NotificationSettingsRequest(BaseModel):
    """通知设置请求"""
    emergency: Optional[bool] = Field(None, description="紧急事件通知")
    health: Optional[bool] = Field(None, description="健康异常通知")
    location: Optional[bool] = Field(None, description="位置变化通知")
    activity: Optional[bool] = Field(None, description="活动状态通知")
    daily_report: Optional[bool] = Field(None, description="每日报告")
    device: Optional[bool] = Field(None, description="设备状态通知")


class ReminderRequest(BaseModel):
    """发送提醒请求"""
    reminder_type: str = Field(..., description="提醒类型: medication/exercise/meal/other")
    message: str = Field(..., max_length=200, description="提醒内容")


class DeviceActionRequest(BaseModel):
    """设备操作请求"""
    device_id: str = Field(..., description="设备ID")
    action: str = Field(..., description="操作: turn_on/turn_off/etc")


# ==================== 家庭组API ====================

@router.post("/groups")
async def create_family_group(
    request: CreateGroupRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    创建家庭组

    创建后，当前用户将作为老人（被监护人）加入家庭组
    """
    user_id = int(current_user.user_id)

    # 检查是否已有家庭组
    existing_groups = family_service.get_user_family_groups(user_id)
    elder_groups = [g for g in existing_groups if g.elder_id == user_id]
    if elder_groups:
        raise HTTPException(
            status_code=400,
            detail="您已创建过家庭组，每位老人只能有一个家庭组"
        )

    group = family_service.create_family_group(
        elder_id=user_id,
        elder_name=request.elder_name,
        group_name=request.group_name,
        creator_id=user_id
    )

    return {
        "success": True,
        "group": group.to_dict(),
        "message": "家庭组创建成功，现在可以邀请家人加入"
    }


@router.get("/groups")
async def get_my_groups(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取我的家庭组列表

    兼容服务重启后的恢复场景：若内存家庭组丢失，会基于 UserAuth/FamilyMember
    的持久化绑定关系重建最小可用家庭组，保证邀请链路不断。
    """
    user_id = int(current_user.user_id)
    groups = family_service.get_user_family_groups(user_id)

    if not groups:
        groups = _recover_family_groups_from_db(user_id, db)

    result = []
    for group in groups:
        group_dict = group.to_dict()
        group_dict["id"] = group.group_id
        group_dict["group_name"] = group.name
        group_dict["is_elder"] = group.elder_id == user_id
        result.append(group_dict)

    return {"groups": result, "count": len(result)}


@router.get("/groups/{group_id}")
async def get_group_detail(
    group_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取家庭组详情
    """
    user_id = int(current_user.user_id)
    group = family_service.groups.get(group_id)

    if not group:
        raise HTTPException(status_code=404, detail="家庭组不存在")

    if user_id not in group.members:
        raise HTTPException(status_code=403, detail="您不是该家庭组成员")

    return group.to_dict()


# ==================== 绑定请求API ====================

@router.post("/bindings/request")
async def create_binding_request(
    request: BindingRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建绑定邀请

    返回邀请码，被邀请人可通过邀请码加入家庭组
    """
    user_id = int(current_user.user_id)
    user_name = f"用户{user_id}"

    group = family_service.groups.get(request.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="家庭组不存在")

    if user_id not in group.members:
        raise HTTPException(status_code=403, detail="您不是该家庭组成员")

    # 验证角色
    try:
        role = FamilyRole(request.role)
    except ValueError:
        valid_roles = [r.value for r in FamilyRole if r != FamilyRole.ELDER]
        raise HTTPException(
            status_code=400,
            detail=f"无效的角色，可选: {valid_roles}"
        )

    permission_level = PermissionLevel(min(max(request.permission_level, 1), 5))

    binding_req = family_service.create_binding_request(
        group_id=request.group_id,
        requester_id=user_id,
        requester_name=user_name,
        target_id=0,  # 通过邀请码加入时不指定
        relationship=request.relationship,
        role=role,
        permission_level=permission_level
    )
    _persist_binding_request(binding_req, db)

    return {
        "success": True,
        "request": binding_req.to_dict(),
        "invite_code": binding_req.invite_code,
        "message": f"邀请码: {binding_req.invite_code}，有效期7天"
    }


@router.post("/bindings/join")
async def join_by_code(
    request: JoinByCodeRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    通过邀请码加入家庭组
    """
    if current_user.role != "family":
        raise HTTPException(status_code=403, detail="仅家属账号可加入家庭组")

    user_id = int(current_user.user_id)

    binding_req = family_service.get_binding_by_code(request.invite_code)
    if not binding_req:
        binding_req = _load_binding_request_from_db(request.invite_code, db)
    if not binding_req:
        raise HTTPException(status_code=404, detail="邀请码无效")

    if binding_req.status != BindingStatus.PENDING:
        raise HTTPException(status_code=400, detail="该邀请已被使用或已过期")

    # 检查是否已是家庭成员；如果服务重启导致内存组丢失，则先尝试恢复老人家庭组
    group = family_service.groups.get(binding_req.group_id)
    if not group:
        _recover_family_groups_from_db(binding_req.requester_id, db)
        group = family_service.groups.get(binding_req.group_id)
    if group and user_id in group.members:
        raise HTTPException(status_code=400, detail="您已是该家庭组成员")

    binding = family_service.accept_binding(
        request_id=binding_req.request_id,
        accepter_id=user_id,
        accepter_name=request.name,
        accepter_phone=request.phone
    )

    if not binding:
        raise HTTPException(status_code=400, detail="加入失败，请检查邀请码")

    _persist_binding_request(binding_req, db)

    # 将绑定关系持久化到数据库，以便 /me 端点能返回 elder_id
    if group:
        elder_auth = db.query(UserAuth).filter(UserAuth.id == group.elder_id).first()
        my_auth = db.query(UserAuth).filter(UserAuth.id == user_id).first()
        if elder_auth and elder_auth.user_id and my_auth:
            family_member = None
            if my_auth.family_id:
                family_member = db.query(FamilyMember).filter(
                    FamilyMember.id == my_auth.family_id,
                    FamilyMember.user_id == elder_auth.user_id,
                ).first()
            if not family_member:
                family_member = FamilyMember(
                    user_id=elder_auth.user_id,
                    name=request.name,
                    phone=request.phone,
                )
                db.add(family_member)
                db.flush()  # 获取自增 id
            else:
                family_member.name = request.name
                family_member.phone = request.phone

            my_auth.family_id = family_member.id
            db.commit()

    return {
        "success": True,
        "binding": binding.to_dict() if binding else None,
        "group_id": binding_req.group_id,
        "message": "已成功加入家庭组"
    }


@router.get("/bindings/pending")
async def get_pending_requests(current_user: UserInfo = Depends(get_current_user)):
    """
    获取待处理的绑定请求
    """
    user_id = int(current_user.user_id)
    requests = family_service.get_pending_requests(user_id)

    return {
        "requests": [r.to_dict() for r in requests],
        "count": len(requests)
    }


@router.post("/bindings/{request_id}/accept")
async def accept_binding(
    request_id: str,
    request: AcceptBindingRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    接受绑定请求
    """
    if current_user.role != "family":
        raise HTTPException(status_code=403, detail="仅家属账号可接受绑定请求")

    user_id = int(current_user.user_id)

    binding_req = family_service.binding_requests.get(request_id)
    if not binding_req:
        stored_req = db.query(FamilyBindingInvite).filter(FamilyBindingInvite.request_id == request_id).first()
        if stored_req:
            binding_req = _load_binding_request_from_db(stored_req.invite_code, db)
    if not binding_req:
        raise HTTPException(status_code=404, detail="请求不存在")

    if binding_req.target_id != 0 and binding_req.target_id != user_id:
        raise HTTPException(status_code=403, detail="此邀请不是发给您的")

    if binding_req.group_id not in family_service.groups:
        _recover_family_groups_from_db(binding_req.requester_id, db)

    binding = family_service.accept_binding(
        request_id=request_id,
        accepter_id=user_id,
        accepter_name=request.name,
        accepter_phone=request.phone
    )

    if not binding:
        raise HTTPException(status_code=400, detail="接受失败，请求可能已过期")

    _persist_binding_request(binding_req, db)

    # 持久化绑定关系到数据库
    group = family_service.groups.get(binding_req.group_id)
    if group:
        elder_auth = db.query(UserAuth).filter(UserAuth.id == group.elder_id).first()
        my_auth = db.query(UserAuth).filter(UserAuth.id == user_id).first()
        if elder_auth and elder_auth.user_id and my_auth:
            family_member = None
            if my_auth.family_id:
                family_member = db.query(FamilyMember).filter(
                    FamilyMember.id == my_auth.family_id,
                    FamilyMember.user_id == elder_auth.user_id,
                ).first()
            if not family_member:
                family_member = FamilyMember(
                    user_id=elder_auth.user_id,
                    name=request.name,
                    phone=request.phone,
                )
                db.add(family_member)
                db.flush()
            else:
                family_member.name = request.name
                family_member.phone = request.phone

            my_auth.family_id = family_member.id
            db.commit()

    return {
        "success": True,
        "binding": binding.to_dict() if binding else None,
        "message": "已成功绑定"
    }


@router.post("/bindings/{request_id}/reject")
async def reject_binding(
    request_id: str,
    reason: str = Query("", description="拒绝原因"),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    拒绝绑定请求
    """
    if current_user.role != "family":
        raise HTTPException(status_code=403, detail="仅家属账号可拒绝绑定请求")

    user_id = int(current_user.user_id)

    binding_req = family_service.binding_requests.get(request_id)
    if not binding_req:
        stored_req = db.query(FamilyBindingInvite).filter(FamilyBindingInvite.request_id == request_id).first()
        if stored_req:
            binding_req = _load_binding_request_from_db(stored_req.invite_code, db)
    if not binding_req:
        raise HTTPException(status_code=404, detail="请求不存在")

    if binding_req.target_id != 0 and binding_req.target_id != user_id:
        raise HTTPException(status_code=403, detail="此邀请不是发给您的")

    success = family_service.reject_binding(request_id, reason)
    if not success:
        raise HTTPException(status_code=400, detail="拒绝失败")

    _persist_binding_request(binding_req, db)

    return {"success": True, "message": "已拒绝绑定请求"}


@router.delete("/bindings/{binding_id}")
async def revoke_binding(
    binding_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    解除监护绑定
    """
    user_id = int(current_user.user_id)
    success = family_service.revoke_binding(binding_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail="解除绑定失败，可能无权操作")

    return {"success": True, "message": "已解除绑定关系"}


# ==================== 监护功能API ====================

@router.get("/guardian/dashboard")
async def get_guardian_dashboard(current_user: UserInfo = Depends(get_current_user)):
    """
    获取监护人仪表板

    显示所有被监护老人的状态概览
    """
    user_id = int(current_user.user_id)
    dashboard = family_service.get_guardian_dashboard(user_id)
    return dashboard


@router.get("/guardian/elders")
async def get_monitored_elders(current_user: UserInfo = Depends(get_current_user)):
    """
    获取监护的老人列表
    """
    user_id = int(current_user.user_id)
    bindings = family_service.get_guardian_bindings(user_id)

    elders = []
    for binding in bindings:
        status = family_service.get_elder_status(binding.elder_id)
        elders.append({
            "binding": binding.to_dict(),
            "status": status.to_dict() if status else None
        })

    return {"elders": elders, "count": len(elders)}


@router.get("/guardian/elders/{elder_id}/status")
async def get_elder_status(
    elder_id: int,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取老人详细状态
    """
    user_id = int(current_user.user_id)

    if not family_service.check_permission(user_id, elder_id, PermissionLevel.VIEW_ONLY):
        raise HTTPException(status_code=403, detail="无权查看该老人状态")

    status = family_service.get_elder_status(elder_id)
    if not status:
        raise HTTPException(status_code=404, detail="老人状态不存在")

    return status.to_dict()


@router.get("/guardian/elders/{elder_id}/location")
async def get_elder_location(
    elder_id: int,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取老人位置
    """
    user_id = int(current_user.user_id)

    location = remote_operation_service.request_location(user_id, elder_id)
    if location is None:
        if not family_service.check_permission(user_id, elder_id, PermissionLevel.STANDARD):
            raise HTTPException(status_code=403, detail="无权查看位置信息")
        raise HTTPException(status_code=404, detail="暂无位置信息")

    return {"location": location}


@router.get("/guardian/elders/{elder_id}/health")
async def get_elder_health(
    elder_id: int,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取老人健康数据
    """
    user_id = int(current_user.user_id)

    health_data = remote_operation_service.request_health_data(user_id, elder_id)
    if health_data is None:
        if not family_service.check_permission(user_id, elder_id, PermissionLevel.FULL):
            raise HTTPException(status_code=403, detail="无权查看健康数据")
        raise HTTPException(status_code=404, detail="暂无健康数据")

    return {"health_data": health_data}


@router.post("/guardian/elders/{elder_id}/remind")
async def send_reminder_to_elder(
    elder_id: int,
    request: ReminderRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    发送提醒给老人

    提醒类型:
    - medication: 服药提醒
    - exercise: 运动提醒
    - meal: 用餐提醒
    - other: 其他提醒
    """
    user_id = int(current_user.user_id)

    valid_types = ["medication", "exercise", "meal", "other"]
    if request.reminder_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的提醒类型，可选: {valid_types}"
        )

    success = remote_operation_service.send_reminder(
        guardian_id=user_id,
        elder_id=elder_id,
        reminder_type=request.reminder_type,
        message=request.message
    )

    if not success:
        raise HTTPException(status_code=403, detail="无权发送提醒或老人不存在")

    return {"success": True, "message": "提醒已发送"}


@router.post("/guardian/elders/{elder_id}/device-action")
async def trigger_device_action(
    elder_id: int,
    request: DeviceActionRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    远程操作老人设备

    需要完整权限
    """
    user_id = int(current_user.user_id)

    result = remote_operation_service.trigger_device_action(
        guardian_id=user_id,
        elder_id=elder_id,
        device_id=request.device_id,
        action=request.action
    )

    if not result["success"]:
        raise HTTPException(status_code=403, detail=result.get("error", "操作失败"))

    return result


# ==================== 通知设置API ====================

@router.get("/bindings/{binding_id}/notifications")
async def get_notification_settings(
    binding_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取通知设置
    """
    user_id = int(current_user.user_id)
    binding = family_service.guardian_bindings.get(binding_id)

    if not binding or binding.guardian_id != user_id:
        raise HTTPException(status_code=404, detail="绑定不存在")

    return {
        "binding_id": binding_id,
        "settings": binding.notification_settings
    }


@router.put("/bindings/{binding_id}/notifications")
async def update_notification_settings(
    binding_id: str,
    request: NotificationSettingsRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    更新通知设置
    """
    user_id = int(current_user.user_id)
    binding = family_service.guardian_bindings.get(binding_id)

    if not binding or binding.guardian_id != user_id:
        raise HTTPException(status_code=404, detail="绑定不存在")

    settings = {}
    if request.emergency is not None:
        settings["emergency"] = request.emergency
    if request.health is not None:
        settings["health"] = request.health
    if request.location is not None:
        settings["location"] = request.location
    if request.activity is not None:
        settings["activity"] = request.activity
    if request.daily_report is not None:
        settings["daily_report"] = request.daily_report
    if request.device is not None:
        settings["device"] = request.device

    family_service.update_notification_settings(binding_id, settings)

    return {
        "success": True,
        "settings": binding.notification_settings
    }


# ==================== 老人视角API ====================

@router.get("/elder/guardians")
async def get_my_guardians(current_user: UserInfo = Depends(get_current_user)):
    """
    获取我的监护人列表（老人视角）
    """
    user_id = int(current_user.user_id)
    guardians = family_service.get_elder_guardians(user_id)

    return {
        "guardians": [g.to_dict() for g in guardians],
        "count": len(guardians)
    }


@router.get("/operation-log")
async def get_operation_log(
    limit: int = Query(50, ge=1, le=200),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取操作日志（可查看监护人对老人的操作记录）
    """
    user_id = int(current_user.user_id)

    # 获取作为监护人的日志
    guardian_logs = remote_operation_service.get_operation_log(
        guardian_id=user_id, limit=limit
    )

    # 获取作为被监护人的日志
    elder_logs = remote_operation_service.get_operation_log(
        elder_id=user_id, limit=limit
    )

    return {
        "as_guardian": guardian_logs,
        "as_elder": elder_logs
    }
