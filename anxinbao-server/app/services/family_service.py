"""
家庭绑定与监护服务
提供家庭成员绑定、监护关系管理、实时监护、活动通知等功能
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets

from app.services.notification_service import notification_service, NotificationTemplate

logger = logging.getLogger(__name__)


class FamilyRole(Enum):
    """家庭角色"""
    ELDER = "elder"  # 老人（被监护人）
    GUARDIAN = "guardian"  # 监护人
    FAMILY = "family"  # 普通家庭成员
    CAREGIVER = "caregiver"  # 护工/保姆


class BindingStatus(Enum):
    """绑定状态"""
    PENDING = "pending"  # 待确认
    ACTIVE = "active"  # 已激活
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期
    REVOKED = "revoked"  # 已解除


class PermissionLevel(Enum):
    """权限级别"""
    VIEW_ONLY = 1  # 仅查看
    BASIC = 2  # 基础权限（查看+接收通知）
    STANDARD = 3  # 标准权限（+位置查看）
    FULL = 4  # 完全权限（+健康数据+远程操作）
    ADMIN = 5  # 管理员权限


class NotificationType(Enum):
    """通知类型"""
    EMERGENCY = "emergency"  # 紧急事件
    HEALTH = "health"  # 健康异常
    LOCATION = "location"  # 位置变化
    ACTIVITY = "activity"  # 活动状态
    DAILY_REPORT = "daily_report"  # 每日报告
    DEVICE = "device"  # 设备状态


@dataclass
class FamilyMember:
    """家庭成员"""
    member_id: str
    user_id: int
    name: str
    phone: str
    role: FamilyRole
    avatar: Optional[str] = None
    relationship: str = ""  # 与老人的关系描述
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "role": self.role.value,
            "avatar": self.avatar,
            "relationship": self.relationship,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class FamilyGroup:
    """家庭组"""
    group_id: str
    name: str
    elder_id: int  # 老人用户ID
    elder_name: str
    created_by: int
    members: Dict[int, FamilyMember] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        elder_profile_id = self.settings.get("elder_profile_id", self.elder_id)
        return {
            "id": self.group_id,
            "group_id": self.group_id,
            "group_name": self.name,
            "name": self.name,
            "elder_auth_id": self.elder_id,
            "elder_id": elder_profile_id,
            "elder_name": self.elder_name,
            "member_count": len(self.members),
            "members": [m.to_dict() for m in self.members.values()],
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BindingRequest:
    """绑定请求"""
    request_id: str
    group_id: str
    requester_id: int
    requester_name: str
    target_id: int  # 被邀请人
    relationship: str
    role: FamilyRole
    permission_level: PermissionLevel
    status: BindingStatus = BindingStatus.PENDING
    invite_code: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    processed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "group_id": self.group_id,
            "requester_id": self.requester_id,
            "requester_name": self.requester_name,
            "relationship": self.relationship,
            "role": self.role.value,
            "permission_level": self.permission_level.value,
            "status": self.status.value,
            "invite_code": self.invite_code,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": datetime.now() > self.expires_at
        }


@dataclass
class GuardianBinding:
    """监护绑定关系"""
    binding_id: str
    group_id: str
    guardian_id: int
    elder_id: int
    guardian_name: str
    elder_name: str
    relationship: str
    permission_level: PermissionLevel
    status: BindingStatus
    notification_settings: Dict[str, bool] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "group_id": self.group_id,
            "guardian_id": self.guardian_id,
            "elder_id": self.elder_id,
            "guardian_name": self.guardian_name,
            "elder_name": self.elder_name,
            "relationship": self.relationship,
            "permission_level": self.permission_level.value,
            "status": self.status.value,
            "notification_settings": self.notification_settings,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ElderStatus:
    """老人状态"""
    elder_id: int
    elder_name: str
    last_active_at: Optional[datetime] = None
    last_location: Optional[Dict] = None
    last_health_check: Optional[Dict] = None
    device_status: str = "unknown"  # online/offline/unknown
    activity_level: str = "normal"  # active/normal/inactive/concerning
    alerts_today: int = 0
    mood_indicator: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "elder_id": self.elder_id,
            "elder_name": self.elder_name,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "last_active_ago": self._format_time_ago() if self.last_active_at else "未知",
            "last_location": self.last_location,
            "last_health_check": self.last_health_check,
            "device_status": self.device_status,
            "activity_level": self.activity_level,
            "alerts_today": self.alerts_today,
            "mood_indicator": self.mood_indicator
        }

    def _format_time_ago(self) -> str:
        if not self.last_active_at:
            return "未知"
        delta = datetime.now() - self.last_active_at
        if delta.days > 0:
            return f"{delta.days}天前"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}小时前"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}分钟前"
        return "刚刚"


# ==================== 家庭服务 ====================

class FamilyService:
    """家庭绑定服务"""

    def __init__(self):
        self.groups: Dict[str, FamilyGroup] = {}  # group_id -> FamilyGroup
        self.user_groups: Dict[int, List[str]] = {}  # user_id -> group_ids
        self.binding_requests: Dict[str, BindingRequest] = {}
        self.invite_codes: Dict[str, str] = {}  # code -> request_id
        self.guardian_bindings: Dict[str, GuardianBinding] = {}
        self.user_bindings: Dict[int, List[str]] = {}  # guardian_id -> binding_ids
        self.elder_statuses: Dict[int, ElderStatus] = {}

    def create_family_group(
        self,
        elder_id: int,
        elder_name: str,
        group_name: str,
        creator_id: int
    ) -> FamilyGroup:
        """创建家庭组"""
        group_id = f"family_{elder_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        group = FamilyGroup(
            group_id=group_id,
            name=group_name,
            elder_id=elder_id,
            elder_name=elder_name,
            created_by=creator_id
        )

        # 添加老人为成员
        elder_member = FamilyMember(
            member_id=f"member_{elder_id}",
            user_id=elder_id,
            name=elder_name,
            phone="",
            role=FamilyRole.ELDER,
            relationship="本人"
        )
        group.members[elder_id] = elder_member

        self.groups[group_id] = group

        # 更新用户组映射
        if elder_id not in self.user_groups:
            self.user_groups[elder_id] = []
        self.user_groups[elder_id].append(group_id)

        # 初始化老人状态
        self.elder_statuses[elder_id] = ElderStatus(
            elder_id=elder_id,
            elder_name=elder_name,
            last_active_at=datetime.now()
        )

        logger.info(f"创建家庭组: {group_id} for elder {elder_id}")
        return group

    def create_binding_request(
        self,
        group_id: str,
        requester_id: int,
        requester_name: str,
        target_id: int,
        relationship: str,
        role: FamilyRole = FamilyRole.GUARDIAN,
        permission_level: PermissionLevel = PermissionLevel.STANDARD
    ) -> BindingRequest:
        """创建绑定请求"""
        group = self.groups.get(group_id)
        if not group:
            raise ValueError("家庭组不存在")

        request_id = f"req_{requester_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(2)}"

        # 生成邀请码
        invite_code = secrets.token_hex(4).upper()

        request = BindingRequest(
            request_id=request_id,
            group_id=group_id,
            requester_id=requester_id,
            requester_name=requester_name,
            target_id=target_id,
            relationship=relationship,
            role=role,
            permission_level=permission_level,
            invite_code=invite_code
        )

        self.binding_requests[request_id] = request
        self.invite_codes[invite_code] = request_id

        logger.info(f"创建绑定请求: {request_id}, 邀请码: {invite_code}")
        return request

    def accept_binding(
        self,
        request_id: str,
        accepter_id: int,
        accepter_name: str,
        accepter_phone: str
    ) -> Optional[GuardianBinding]:
        """接受绑定请求"""
        request = self.binding_requests.get(request_id)
        if not request:
            return None

        if request.status != BindingStatus.PENDING:
            return None

        if datetime.now() > request.expires_at:
            request.status = BindingStatus.EXPIRED
            return None

        group = self.groups.get(request.group_id)
        if not group:
            return None

        # 更新请求状态
        request.status = BindingStatus.ACTIVE
        request.processed_at = datetime.now()

        # 添加成员到家庭组
        member = FamilyMember(
            member_id=f"member_{accepter_id}",
            user_id=accepter_id,
            name=accepter_name,
            phone=accepter_phone,
            role=request.role,
            relationship=request.relationship
        )
        group.members[accepter_id] = member

        # 更新用户组映射
        if accepter_id not in self.user_groups:
            self.user_groups[accepter_id] = []
        if request.group_id not in self.user_groups[accepter_id]:
            self.user_groups[accepter_id].append(request.group_id)

        # 如果是监护人角色，创建监护绑定
        binding = None
        if request.role in [FamilyRole.GUARDIAN, FamilyRole.CAREGIVER]:
            binding = self._create_guardian_binding(
                group_id=request.group_id,
                guardian_id=accepter_id,
                guardian_name=accepter_name,
                elder_id=group.elder_id,
                elder_name=group.elder_name,
                relationship=request.relationship,
                permission_level=request.permission_level
            )

        logger.info(f"绑定请求已接受: {request_id}")
        return binding

    def _create_guardian_binding(
        self,
        group_id: str,
        guardian_id: int,
        guardian_name: str,
        elder_id: int,
        elder_name: str,
        relationship: str,
        permission_level: PermissionLevel
    ) -> GuardianBinding:
        """创建监护绑定"""
        binding_id = f"bind_{guardian_id}_{elder_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 默认通知设置
        default_notifications = {
            NotificationType.EMERGENCY.value: True,
            NotificationType.HEALTH.value: True,
            NotificationType.LOCATION.value: permission_level.value >= PermissionLevel.STANDARD.value,
            NotificationType.ACTIVITY.value: False,
            NotificationType.DAILY_REPORT.value: True,
            NotificationType.DEVICE.value: False
        }

        binding = GuardianBinding(
            binding_id=binding_id,
            group_id=group_id,
            guardian_id=guardian_id,
            elder_id=elder_id,
            guardian_name=guardian_name,
            elder_name=elder_name,
            relationship=relationship,
            permission_level=permission_level,
            status=BindingStatus.ACTIVE,
            notification_settings=default_notifications
        )

        self.guardian_bindings[binding_id] = binding

        if guardian_id not in self.user_bindings:
            self.user_bindings[guardian_id] = []
        self.user_bindings[guardian_id].append(binding_id)

        return binding

    def reject_binding(self, request_id: str, reason: str = "") -> bool:
        """拒绝绑定请求"""
        request = self.binding_requests.get(request_id)
        if not request or request.status != BindingStatus.PENDING:
            return False

        request.status = BindingStatus.REJECTED
        request.processed_at = datetime.now()

        logger.info(f"绑定请求已拒绝: {request_id}, 原因: {reason}")
        return True

    def revoke_binding(self, binding_id: str, revoker_id: int) -> bool:
        """解除监护绑定"""
        binding = self.guardian_bindings.get(binding_id)
        if not binding:
            return False

        # 只有监护人或老人可以解除绑定
        if revoker_id not in [binding.guardian_id, binding.elder_id]:
            return False

        binding.status = BindingStatus.REVOKED

        # 从用户绑定列表中移除
        if binding.guardian_id in self.user_bindings:
            if binding_id in self.user_bindings[binding.guardian_id]:
                self.user_bindings[binding.guardian_id].remove(binding_id)

        logger.info(f"监护绑定已解除: {binding_id}")
        return True

    def get_binding_by_code(self, invite_code: str) -> Optional[BindingRequest]:
        """通过邀请码获取绑定请求"""
        request_id = self.invite_codes.get(invite_code.upper())
        if not request_id:
            return None
        return self.binding_requests.get(request_id)

    def get_user_family_groups(self, user_id: int) -> List[FamilyGroup]:
        """获取用户的家庭组"""
        group_ids = self.user_groups.get(user_id, [])
        return [self.groups[gid] for gid in group_ids if gid in self.groups]

    def get_guardian_bindings(self, guardian_id: int) -> List[GuardianBinding]:
        """获取监护人的所有绑定"""
        binding_ids = self.user_bindings.get(guardian_id, [])
        bindings = [self.guardian_bindings[bid] for bid in binding_ids if bid in self.guardian_bindings]
        return [b for b in bindings if b.status == BindingStatus.ACTIVE]

    def get_elder_guardians(self, elder_id: int) -> List[GuardianBinding]:
        """获取老人的所有监护人"""
        return [
            b for b in self.guardian_bindings.values()
            if b.elder_id == elder_id and b.status == BindingStatus.ACTIVE
        ]

    def get_pending_requests(self, user_id: int) -> List[BindingRequest]:
        """获取待处理的绑定请求"""
        return [
            r for r in self.binding_requests.values()
            if r.target_id == user_id and r.status == BindingStatus.PENDING
            and datetime.now() <= r.expires_at
        ]

    def update_notification_settings(
        self,
        binding_id: str,
        settings: Dict[str, bool]
    ) -> bool:
        """更新通知设置"""
        binding = self.guardian_bindings.get(binding_id)
        if not binding:
            return False

        binding.notification_settings.update(settings)
        return True

    # ==================== 监护功能 ====================

    def update_elder_status(
        self,
        elder_id: int,
        **kwargs
    ) -> Optional[ElderStatus]:
        """更新老人状态"""
        status = self.elder_statuses.get(elder_id)
        if not status:
            return None

        if "last_active_at" in kwargs:
            status.last_active_at = kwargs["last_active_at"]
        if "last_location" in kwargs:
            status.last_location = kwargs["last_location"]
        if "last_health_check" in kwargs:
            status.last_health_check = kwargs["last_health_check"]
        if "device_status" in kwargs:
            status.device_status = kwargs["device_status"]
        if "activity_level" in kwargs:
            status.activity_level = kwargs["activity_level"]
        if "alerts_today" in kwargs:
            status.alerts_today = kwargs["alerts_today"]
        if "mood_indicator" in kwargs:
            status.mood_indicator = kwargs["mood_indicator"]

        return status

    def get_elder_status(self, elder_id: int) -> Optional[ElderStatus]:
        """获取老人状态"""
        return self.elder_statuses.get(elder_id)

    def get_guardian_dashboard(self, guardian_id: int) -> Dict[str, Any]:
        """获取监护人仪表板数据"""
        bindings = self.get_guardian_bindings(guardian_id)

        dashboard = {
            "elder_count": len(bindings),
            "elders": [],
            "alerts_today": 0,
            "needs_attention": []
        }

        for binding in bindings:
            status = self.elder_statuses.get(binding.elder_id)
            if status:
                elder_info = {
                    "elder_id": binding.elder_id,
                    "elder_name": binding.elder_name,
                    "relationship": binding.relationship,
                    "status": status.to_dict(),
                    "permission_level": binding.permission_level.value
                }
                dashboard["elders"].append(elder_info)
                dashboard["alerts_today"] += status.alerts_today

                # 检查是否需要关注
                if status.activity_level in ["inactive", "concerning"]:
                    dashboard["needs_attention"].append({
                        "elder_id": binding.elder_id,
                        "elder_name": binding.elder_name,
                        "reason": "长时间无活动" if status.activity_level == "inactive" else "状态异常"
                    })

        return dashboard

    def check_permission(
        self,
        guardian_id: int,
        elder_id: int,
        required_level: PermissionLevel
    ) -> bool:
        """检查监护人权限"""
        bindings = self.get_guardian_bindings(guardian_id)
        for binding in bindings:
            if binding.elder_id == elder_id:
                return binding.permission_level.value >= required_level.value
        return False

    def should_notify(
        self,
        guardian_id: int,
        elder_id: int,
        notification_type: NotificationType
    ) -> bool:
        """检查是否应该发送通知"""
        bindings = self.get_guardian_bindings(guardian_id)
        for binding in bindings:
            if binding.elder_id == elder_id:
                return binding.notification_settings.get(notification_type.value, False)
        return False

    async def notify_guardians(
        self,
        elder_id: int,
        notification_type: NotificationType,
        message: str,
        data: Optional[Dict] = None
    ) -> List[int]:
        """通知所有监护人"""
        guardians = self.get_elder_guardians(elder_id)
        notified = []

        # Map family notification types to notification service templates
        type_to_template = {
            NotificationType.EMERGENCY: NotificationTemplate.EMERGENCY,
            NotificationType.HEALTH: NotificationTemplate.HEALTH_ALERT,
            NotificationType.ACTIVITY: NotificationTemplate.INACTIVITY_ALERT,
            NotificationType.DAILY_REPORT: NotificationTemplate.DAILY_REPORT,
        }
        template = type_to_template.get(notification_type, NotificationTemplate.PROACTIVE_CARE)

        for binding in guardians:
            if self.should_notify(binding.guardian_id, elder_id, notification_type):
                # 发送通知
                logger.info(f"通知监护人 {binding.guardian_id}: {message}")
                notified.append(binding.guardian_id)

                # 调用实际通知服务
                await notification_service.send_notification(
                    user_id=elder_id,
                    template=template,
                    content=message,
                    extra_data=data
                )

        return notified


# ==================== 远程操作服务 ====================

class RemoteOperationService:
    """远程操作服务（监护人远程协助老人）"""

    def __init__(self, family_service: FamilyService):
        self.family = family_service
        self.operation_log: List[Dict] = []

    def request_location(
        self,
        guardian_id: int,
        elder_id: int
    ) -> Optional[Dict]:
        """请求老人位置"""
        if not self.family.check_permission(
            guardian_id, elder_id, PermissionLevel.STANDARD
        ):
            return None

        status = self.family.get_elder_status(elder_id)
        if status and status.last_location:
            self._log_operation(guardian_id, elder_id, "request_location")
            return status.last_location
        return None

    def request_health_data(
        self,
        guardian_id: int,
        elder_id: int
    ) -> Optional[Dict]:
        """请求健康数据"""
        if not self.family.check_permission(
            guardian_id, elder_id, PermissionLevel.FULL
        ):
            return None

        status = self.family.get_elder_status(elder_id)
        if status and status.last_health_check:
            self._log_operation(guardian_id, elder_id, "request_health_data")
            return status.last_health_check
        return None

    def send_reminder(
        self,
        guardian_id: int,
        elder_id: int,
        reminder_type: str,
        message: str
    ) -> bool:
        """发送提醒给老人"""
        if not self.family.check_permission(
            guardian_id, elder_id, PermissionLevel.BASIC
        ):
            return False

        self._log_operation(
            guardian_id, elder_id, "send_reminder",
            {"type": reminder_type, "message": message}
        )

        logger.info(f"监护人 {guardian_id} 向老人 {elder_id} 发送提醒: {message}")
        return True

    def trigger_device_action(
        self,
        guardian_id: int,
        elder_id: int,
        device_id: str,
        action: str
    ) -> Dict[str, Any]:
        """远程触发设备操作"""
        if not self.family.check_permission(
            guardian_id, elder_id, PermissionLevel.FULL
        ):
            return {"success": False, "error": "权限不足"}

        self._log_operation(
            guardian_id, elder_id, "device_action",
            {"device_id": device_id, "action": action}
        )

        return {"success": True, "message": f"已执行设备操作: {action}"}

    def _log_operation(
        self,
        guardian_id: int,
        elder_id: int,
        operation: str,
        data: Optional[Dict] = None
    ):
        """记录操作日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "guardian_id": guardian_id,
            "elder_id": elder_id,
            "operation": operation,
            "data": data
        }
        self.operation_log.append(log_entry)

        # 保留最近1000条记录
        if len(self.operation_log) > 1000:
            self.operation_log = self.operation_log[-1000:]

    def get_operation_log(
        self,
        guardian_id: Optional[int] = None,
        elder_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict]:
        """获取操作日志"""
        logs = self.operation_log

        if guardian_id:
            logs = [l for l in logs if l["guardian_id"] == guardian_id]
        if elder_id:
            logs = [l for l in logs if l["elder_id"] == elder_id]

        return logs[-limit:]


# 全局服务实例
family_service = FamilyService()
remote_operation_service = RemoteOperationService(family_service)
