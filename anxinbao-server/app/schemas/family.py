"""
家庭关系相关模式定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseSchema, TimestampMixin


class FamilyRole(str, Enum):
    """家庭角色"""
    PARENT = 'parent'  # 父母
    CHILD = 'child'  # 子女
    SPOUSE = 'spouse'  # 配偶
    SIBLING = "sibling"  # 兄弟姐妹
    GRANDPARENT = "grandparent"  # 祖父母
    GRANDCHILD = 'grandchild'  # 孙辈
    OTHER = "other"  # 其他


class FamilyRelationStatus(str, Enum):
    """家庭关系状态"""
    PENDING = 'pending'  # 待确认
    ACTIVE = 'active'  # 已激活
    REJECTED = 'rejected'  # 已拒绝
    REMOVED = "removed"  # 已移除


class PermissionLevel(str, Enum):
    """权限级别"""
    VIEW_ONLY = 'view_only'  # 仅查看
    STANDARD = 'standard'  # 标准权限
    FULL = 'full'  # 完全权限
    ADMIN = "admin"  # 管理员


# ========== 家庭关系 ==========

class FamilyRelationBase(BaseSchema):
    """家庭关系基础"""
    role: FamilyRole
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    notes: Optional[str] = Field(None, max_length=200)


class FamilyRelationCreate(FamilyRelationBase):
    """创建家庭关系"""
    elderly_id: str = Field(..., description='老人ID')
    family_id: str = Field(..., description="家属ID")
    permission_level: PermissionLevel = PermissionLevel.STANDARD


class FamilyRelationInvite(BaseSchema):
    """邀请家属"""
    elderly_id: str
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    role: FamilyRole
    nickname: Optional[str] = None
    message: Optional[str] = Field(None, max_length=200, description="邀请留言")


class FamilyRelationResponse(FamilyRelationBase, TimestampMixin):
    """家庭关系响应"""
    id: str
    elderly_id: str
    elderly_name: str
    family_id: str
    family_name: str
    family_phone: str
    family_avatar: Optional[str] = None
    status: FamilyRelationStatus
    permission_level: PermissionLevel
    is_primary_contact: bool = False
    last_interaction_at: Optional[datetime] = None


class FamilyRelationUpdate(BaseSchema):
    """更新家庭关系"""
    role: Optional[FamilyRole] = None
    nickname: Optional[str] = None
    permission_level: Optional[PermissionLevel] = None
    is_primary_contact: Optional[bool] = None
    notes: Optional[str] = None


class AcceptInviteRequest(BaseSchema):
    """接受邀请"""
    invite_code: str


class RejectInviteRequest(BaseSchema):
    """拒绝邀请"""
    reason: Optional[str] = None


# ========== 家属权限 ==========

class FamilyPermissions(BaseSchema):
    """家属权限详情"""
    can_view_health: bool = True
    can_view_medication: bool = True
    can_view_location: bool = False
    can_receive_alerts: bool = True
    can_make_video_calls: bool = True
    can_send_messages: bool = True
    can_modify_settings: bool = False
    can_manage_devices: bool = False


class UpdatePermissionsRequest(BaseSchema):
    """更新权限请求"""
    family_id: str
    permissions: FamilyPermissions


# ========== 老人的家属列表 ==========

class ElderlyFamilyMember(BaseSchema):
    """老人的家属成员"""
    id: str
    user_id: str
    name: str
    phone: str
    avatar: Optional[str] = None
    role: FamilyRole
    nickname: Optional[str] = None
    is_primary_contact: bool
    permission_level: PermissionLevel
    status: FamilyRelationStatus
    last_online_at: Optional[datetime] = None
    joined_at: datetime


class ElderlyFamilyList(BaseSchema):
    """老人的家属列表"""
    elderly_id: str
    family_members: List[ElderlyFamilyMember]
    total_count: int
    pending_invites: int


# ========== 家属关联的老人列表 ==========

class FamilyElderlyMember(BaseSchema):
    """家属关联的老人"""
    id: str
    user_id: str
    name: str
    phone: str
    avatar: Optional[str] = None
    age: Optional[int] = None
    role: FamilyRole  # 我是老人的什么角色
    permission_level: PermissionLevel
    health_score: Optional[int] = None
    last_active_at: Optional[datetime] = None
    has_unread_alerts: bool = False
    unread_alert_count: int = 0


class FamilyElderlyList(BaseSchema):
    """家属关联的老人列表"""
    family_id: str
    elderly_members: List[FamilyElderlyMember]
    total_count: int


# ========== 互动记录 ==========

class FamilyInteractionType(str, Enum):
    """互动类型"""
    VIDEO_CALL = "video_call"
    VOICE_CALL = 'voice_call'
    MESSAGE = 'message'
    VISIT = 'visit'
    SHARE_PHOTO = "share_photo"
    HEALTH_CHECK = "health_check"


class FamilyInteractionRecord(BaseSchema, TimestampMixin):
    """家庭互动记录"""
    id: str
    elderly_id: str
    family_id: str
    interaction_type: FamilyInteractionType
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None


class FamilyInteractionStats(BaseSchema):
    """互动统计"""
    elderly_id: str
    family_id: str
    period: str  # weekly/monthly
    total_interactions: int
    by_type: Dict[str, int]
    total_duration_seconds: int
    last_interaction_at: Optional[datetime] = None


# ========== 家庭群组 ==========

class FamilyGroupBase(BaseSchema):
    """家庭群组基础"""
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class FamilyGroupCreate(FamilyGroupBase):
    """创建家庭群组"""
    elderly_id: str
    member_ids: List[str] = Field(default=[], description="成员ID列表")


class FamilyGroupResponse(FamilyGroupBase, TimestampMixin):
    """家庭群组响应"""
    id: str
    elderly_id: str
    elderly_name: str
    members: List[ElderlyFamilyMember]
    member_count: int
    creator_id: str


class FamilyGroupUpdate(BaseSchema):
    """更新家庭群组"""
    name: Optional[str] = None
    description: Optional[str] = None


class AddGroupMemberRequest(BaseSchema):
    """添加群组成员"""
    member_ids: List[str]


class RemoveGroupMemberRequest(BaseSchema):
    """移除群组成员"""
    member_id: str
