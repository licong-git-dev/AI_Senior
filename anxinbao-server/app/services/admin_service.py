"""
运营管理后台服务
提供用户管理、数据统计、内容审核、系统配置等功能
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

logger = logging.getLogger(__name__)


class AdminRole(Enum):
    """管理员角色"""
    SUPER_ADMIN = "super_admin"  # 超级管理员
    ADMIN = 'admin'  # 普通管理员
    OPERATOR = "operator"  # 运营人员
    CUSTOMER_SERVICE = "customer_service"  # 客服
    ANALYST = "analyst"  # 数据分析师


class ContentStatus(Enum):
    """内容状态"""
    PENDING = 'pending'  # 待审核
    APPROVED = 'approved'  # 已通过
    REJECTED = 'rejected'  # 已拒绝
    HIDDEN = "hidden"  # 已隐藏


class ReportType(Enum):
    """举报类型"""
    SPAM = 'spam'  # 垃圾信息
    ABUSE = "abuse"  # 辱骂
    INAPPROPRIATE = "inappropriate"  # 不当内容
    FRAUD = 'fraud'  # 欺诈
    OTHER = "other"  # 其他


@dataclass
class AdminUser:
    """管理员用户"""
    admin_id: int
    username: str
    role: AdminRole
    name: str
    email: str
    phone: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'admin_id': self.admin_id,
            'username': self.username,
            'role': self.role.value,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            "permissions": self.permissions,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


@dataclass
class ContentReport:
    """内容举报"""
    report_id: str
    content_type: str  # post/comment/message
    content_id: str
    reporter_id: int
    report_type: ReportType
    reason: str
    status: str = 'pending'  # pending/processed/dismissed
    handler_id: Optional[int] = None
    handle_result: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    handled_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            "content_type": self.content_type,
            'content_id': self.content_id,
            "reporter_id": self.reporter_id,
            "report_type": self.report_type.value,
            'reason': self.reason,
            'status': self.status,
            'handler_id': self.handler_id,
            "handle_result": self.handle_result,
            'created_at': self.created_at.isoformat(),
            'handled_at': self.handled_at.isoformat() if self.handled_at else None
        }


@dataclass
class SystemConfig:
    """系统配置"""
    key: str
    value: Any
    description: str
    category: str
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'value': self.value,
            "description": self.description,
            'category': self.category,
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class AuditLog:
    """操作审计日志"""
    log_id: str
    admin_id: int
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_id': self.log_id,
            'admin_id': self.admin_id,
            'action': self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }


# ==================== 数据仪表盘服务 ====================

class DashboardService:
    """仪表盘服务"""

    def get_overview(self) -> Dict[str, Any]:
        """获取概览数据"""
        today = date.today()

        return {
            'users': {
                'total': self._get_mock_count(50000, 60000),
                'today_new': self._get_mock_count(100, 200),
                "active_today": self._get_mock_count(15000, 20000),
                "active_week": self._get_mock_count(35000, 45000)
            },
            'revenue': {
                'today': self._get_mock_amount(10000, 20000),
                'week': self._get_mock_amount(80000, 120000),
                'month': self._get_mock_amount(300000, 500000),
                'total': self._get_mock_amount(5000000, 8000000)
            },
            "subscriptions": {
                "total_active": self._get_mock_count(8000, 12000),
                'today_new': self._get_mock_count(50, 100),
                "today_cancelled": self._get_mock_count(5, 20),
                "conversion_rate": round(random.uniform(0.15, 0.25), 3)
            },
            'health': {
                "total_records": self._get_mock_count(500000, 800000),
                "today_checks": self._get_mock_count(10000, 15000),
                "alerts_today": self._get_mock_count(50, 100)
            },
            'emergency': {
                'total_sos': self._get_mock_count(500, 1000),
                'today_sos': self._get_mock_count(2, 10),
                "avg_response_time": round(random.uniform(30, 120), 1)
            },
            'updated_at': datetime.now().isoformat()
        }

    def get_trends(self, days: int = 30) -> Dict[str, Any]:
        """获取趋势数据"""
        dates = []
        user_growth = []
        revenue = []
        active_users = []

        for i in range(days, 0, -1):
            d = date.today() - timedelta(days=i)
            dates.append(d.isoformat())
            user_growth.append(self._get_mock_count(80, 200))
            revenue.append(self._get_mock_amount(8000, 20000))
            active_users.append(self._get_mock_count(12000, 20000))

        return {
            'dates': dates,
            "user_growth": user_growth,
            'revenue': revenue,
            "active_users": active_users
        }

    def get_user_distribution(self) -> Dict[str, Any]:
        """获取用户分布"""
        return {
            'by_age': [
                {'range': '60-65岁', 'count': self._get_mock_count(10000, 15000)},
                {'range': '66-70岁', 'count': self._get_mock_count(15000, 20000)},
                {'range': '71-75岁', 'count': self._get_mock_count(12000, 16000)},
                {'range': '76-80岁', 'count': self._get_mock_count(8000, 12000)},
                {'range': '80岁以上', 'count': self._get_mock_count(5000, 8000)}
            ],
            'by_region': [
                {'region': '华东', 'count': self._get_mock_count(15000, 20000)},
                {'region': '华北', 'count': self._get_mock_count(10000, 15000)},
                {'region': '华南', 'count': self._get_mock_count(10000, 14000)},
                {'region': '西南', 'count': self._get_mock_count(6000, 10000)},
                {'region': '其他', "count": self._get_mock_count(5000, 8000)}
            ],
            "by_membership": [
                {'tier': '免费用户', 'count': self._get_mock_count(40000, 50000)},
                {'tier': '基础会员', 'count': self._get_mock_count(5000, 8000)},
                {'tier': '高级会员', 'count': self._get_mock_count(2000, 4000)},
                {'tier': '家庭会员', "count": self._get_mock_count(500, 1500)}
            ]
        }

    def get_feature_usage(self) -> Dict[str, Any]:
        """获取功能使用统计"""
        return {
            'ai_chat': {
                "daily_calls": self._get_mock_count(80000, 120000),
                "avg_per_user": round(random.uniform(3, 8), 1)
            },
            "health_check": {
                "daily_checks": self._get_mock_count(15000, 25000),
                "completion_rate": round(random.uniform(0.7, 0.9), 2)
            },
            "entertainment": {
                "daily_plays": self._get_mock_count(30000, 50000),
                "avg_duration_min": round(random.uniform(15, 45), 1)
            },
            'games': {
                "daily_sessions": self._get_mock_count(10000, 20000),
                "avg_score_improvement": round(random.uniform(0.02, 0.08), 3)
            },
            'social': {
                "daily_posts": self._get_mock_count(1000, 3000),
                "daily_interactions": self._get_mock_count(10000, 20000)
            }
        }

    def _get_mock_count(self, min_val: int, max_val: int) -> int:
        return random.randint(min_val, max_val)

    def _get_mock_amount(self, min_val: float, max_val: float) -> float:
        return round(random.uniform(min_val, max_val), 2)


# ==================== 用户管理服务 ====================

class UserManagementService:
    """用户管理服务"""

    def __init__(self):
        self.blocked_users: Dict[int, Dict] = {}

    def search_users(
        self,
        keyword: Optional[str] = None,
        membership: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """搜索用户"""
        # 模拟用户数据
        users = []
        for i in range(page_size):
            user_id = (page - 1) * page_size + i + 1
            users.append({
                'user_id': user_id,
                'nickname': f'用户{user_id}',
                'phone': f'138****{1000 + user_id:04d}',
                'membership': random.choice(['free', 'basic', 'premium']),
                'status': 'active',
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "last_active": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat()
            })

        return {
            'users': users,
            'total': 50000,
            'page': page,
            'page_size': page_size,
            "total_pages": 2500
        }

    def get_user_detail(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详情"""
        return {
            'user_id': user_id,
            'nickname': f'用户{user_id}',
            'phone': f'138****{1000 + user_id:04d}',
            'email': f'user{user_id}@example.com',
            'membership': 'premium',
            'status': 'active',
            'profile': {
                'age': random.randint(60, 85),
                'gender': random.choice(['male', 'female']),
                'city': random.choice(['北京', '上海', '广州', '深圳'])
            },
            "statistics": {
                "total_chats": random.randint(100, 1000),
                "total_health_checks": random.randint(50, 300),
                "total_games": random.randint(20, 200),
                "total_payments": random.randint(0, 10)
            },
            'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
            "last_active": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
        }

    def block_user(
        self,
        user_id: int,
        reason: str,
        admin_id: int,
        duration_days: Optional[int] = None
    ) -> bool:
        """封禁用户"""
        self.blocked_users[user_id] = {
            'reason': reason,
            'admin_id': admin_id,
            'blocked_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=duration_days) if duration_days else None
        }
        logger.info(f"管理员 {admin_id} 封禁用户 {user_id}: {reason}")
        return True

    def unblock_user(self, user_id: int, admin_id: int) -> bool:
        """解封用户"""
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
            logger.info(f"管理员 {admin_id} 解封用户 {user_id}")
            return True
        return False

    def is_blocked(self, user_id: int) -> bool:
        """检查用户是否被封禁"""
        if user_id not in self.blocked_users:
            return False
        block_info = self.blocked_users[user_id]
        if block_info['expires_at'] and datetime.now() > block_info['expires_at']:
            del self.blocked_users[user_id]
            return False
        return True


# ==================== 内容审核服务 ====================

class ContentModerationService:
    """内容审核服务"""

    def __init__(self):
        self.reports: Dict[str, ContentReport] = {}
        self.content_status: Dict[str, ContentStatus] = {}

    def get_pending_content(
        self,
        content_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取待审核内容"""
        items = []
        for i in range(page_size):
            item_id = f"content_{(page - 1) * page_size + i + 1}"
            items.append({
                'content_id': item_id,
                'type': content_type or random.choice(['post', 'comment']),
                'user_id': random.randint(1, 50000),
                'content': f'这是一段待审核的内容示例 {i + 1}',
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                'status': 'pending'
            })

        return {
            'items': items,
            'total': 150,
            'page': page,
            "page_size": page_size
        }

    def approve_content(self, content_id: str, admin_id: int) -> bool:
        """通过内容"""
        self.content_status[content_id] = ContentStatus.APPROVED
        logger.info(f"管理员 {admin_id} 通过内容 {content_id}")
        return True

    def reject_content(
        self,
        content_id: str,
        admin_id: int,
        reason: str
    ) -> bool:
        """拒绝内容"""
        self.content_status[content_id] = ContentStatus.REJECTED
        logger.info(f"管理员 {admin_id} 拒绝内容 {content_id}: {reason}")
        return True

    def create_report(
        self,
        content_type: str,
        content_id: str,
        reporter_id: int,
        report_type: ReportType,
        reason: str
    ) -> ContentReport:
        """创建举报"""
        report_id = f"report_{len(self.reports) + 1}_{int(datetime.now().timestamp())}"

        report = ContentReport(
            report_id=report_id,
            content_type=content_type,
            content_id=content_id,
            reporter_id=reporter_id,
            report_type=report_type,
            reason=reason
        )

        self.reports[report_id] = report
        return report

    def get_reports(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取举报列表"""
        reports = list(self.reports.values())
        if status:
            reports = [r for r in reports if r.status == status]

        start = (page - 1) * page_size
        end = start + page_size

        return {
            'reports': [r.to_dict() for r in reports[start:end]],
            'total': len(reports),
            'page': page,
            'page_size': page_size
        }

    def handle_report(
        self,
        report_id: str,
        admin_id: int,
        action: str,  # approve/dismiss
        result: str
    ) -> Optional[ContentReport]:
        """处理举报"""
        report = self.reports.get(report_id)
        if not report:
            return None

        report.status = 'processed' if action == 'approve' else "dismissed"
        report.handler_id = admin_id
        report.handle_result = result
        report.handled_at = datetime.now()

        if action == 'approve':
            self.content_status[report.content_id] = ContentStatus.HIDDEN

        return report


# ==================== 系统配置服务 ====================

class SystemConfigService:
    """系统配置服务"""

    def __init__(self):
        self.configs: Dict[str, SystemConfig] = {}
        self._init_default_configs()

    def _init_default_configs(self):
        """初始化默认配置"""
        defaults = [
            ("app.maintenance_mode", False, '维护模式', "system"),
            ("app.min_version", '1.0.0', '最低支持版本', "system"),
            ("app.announcement", '', '系统公告', "system"),
            ("chat.daily_limit_free", 100, '免费用户每日对话限制', "feature"),
            ("chat.daily_limit_premium", -1, '付费用户每日对话限制(-1无限)', "feature"),
            ("health.reminder_interval", 4, '健康提醒间隔(小时)', "feature"),
            ("payment.wechat_enabled", True, '微信支付开关', "payment"),
            ("payment.alipay_enabled", True, '支付宝开关', "payment"),
            ("notification.push_enabled", True, '推送通知开关', "notification"),
            ("notification.sms_enabled", True, '短信通知开关', "notification"),
            ("content.auto_audit", True, '内容自动审核', "content"),
            ("content.sensitive_words", [], '敏感词列表', "content"),
        ]

        for key, value, desc, category in defaults:
            self.configs[key] = SystemConfig(
                key=key,
                value=value,
                description=desc,
                category=category
            )

    def get_config(self, key: str) -> Optional[SystemConfig]:
        """获取配置"""
        return self.configs.get(key)

    def get_configs_by_category(self, category: str) -> List[SystemConfig]:
        """按类别获取配置"""
        return [c for c in self.configs.values() if c.category == category]

    def get_all_configs(self) -> Dict[str, List[Dict]]:
        """获取所有配置（按类别分组）"""
        result = {}
        for config in self.configs.values():
            if config.category not in result:
                result[config.category] = []
            result[config.category].append(config.to_dict())
        return result

    def update_config(
        self,
        key: str,
        value: Any,
        admin_id: int
    ) -> Optional[SystemConfig]:
        """更新配置"""
        config = self.configs.get(key)
        if not config:
            return None

        config.value = value
        config.updated_at = datetime.now()
        config.updated_by = admin_id

        logger.info(f"管理员 {admin_id} 更新配置 {key} = {value}")
        return config


# ==================== 审计日志服务 ====================

class AuditLogService:
    """审计日志服务"""

    def __init__(self):
        self.logs: List[AuditLog] = []

    def log_action(
        self,
        admin_id: int,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录操作"""
        log_id = f"log_{len(self.logs) + 1}_{int(datetime.now().timestamp())}"

        log = AuditLog(
            log_id=log_id,
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address
        )

        self.logs.append(log)

        # 只保留最近10000条
        if len(self.logs) > 10000:
            self.logs = self.logs[-10000:]

        return log

    def get_logs(
        self,
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """查询日志"""
        filtered = self.logs.copy()

        if admin_id:
            filtered = [l for l in filtered if l.admin_id == admin_id]
        if action:
            filtered = [l for l in filtered if l.action == action]
        if resource_type:
            filtered = [l for l in filtered if l.resource_type == resource_type]
        if start_date:
            filtered = [l for l in filtered if l.created_at >= start_date]
        if end_date:
            filtered = [l for l in filtered if l.created_at <= end_date]

        # 按时间倒序
        filtered.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return {
            'logs': [l.to_dict() for l in filtered[start:end]],
            'total': len(filtered),
            'page': page,
            "page_size": page_size
        }


# ==================== 统一管理服务 ====================

class AdminService:
    """运营管理服务"""

    def __init__(self):
        self.admins: Dict[int, AdminUser] = {}
        self.dashboard = DashboardService()
        self.user_mgmt = UserManagementService()
        self.content_mod = ContentModerationService()
        self.sys_config = SystemConfigService()
        self.audit_log = AuditLogService()

        # 创建默认管理员
        self._init_default_admin()

    def _init_default_admin(self):
        """初始化默认管理员"""
        admin = AdminUser(
            admin_id=1,
            username='admin',
            role=AdminRole.SUPER_ADMIN,
            name="系统管理员",
            email="admin@anxinbao.com",
            permissions=['*']
        )
        self.admins[1] = admin

    def get_admin(self, admin_id: int) -> Optional[AdminUser]:
        """获取管理员信息"""
        return self.admins.get(admin_id)

    def verify_permission(
        self,
        admin_id: int,
        required_permission: str
    ) -> bool:
        """验证权限"""
        admin = self.admins.get(admin_id)
        if not admin or not admin.is_active:
            return False

        if admin.role == AdminRole.SUPER_ADMIN:
            return True

        if '*' in admin.permissions:
            return True

        return required_permission in admin.permissions

    def record_login(self, admin_id: int):
        """记录登录"""
        admin = self.admins.get(admin_id)
        if admin:
            admin.last_login = datetime.now()


# 全局服务实例
admin_service = AdminService()
