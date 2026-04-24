"""
审计日志服务
提供操作记录、安全追踪、行为分析等功能
"""
import logging
import json
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from collections import defaultdict
import secrets
import hashlib

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class AuditAction(Enum):
    """审计动作类型"""
    # 认证相关
    LOGIN = "login"
    LOGOUT = 'logout'
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"

    # 用户操作
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PROFILE_UPDATE = "profile_update"

    # 数据访问
    DATA_READ = "data_read"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # 健康数据
    HEALTH_RECORD = "health_record"
    HEALTH_VIEW = "health_view"
    MEDICATION_RECORD = "medication_record"

    # 家庭操作
    FAMILY_BIND = "family_bind"
    FAMILY_UNBIND = "family_unbind"
    GUARDIAN_ACCESS = "guardian_access"

    # 紧急事件
    SOS_TRIGGER = "sos_trigger"
    SOS_RESPONSE = "sos_response"
    ALERT_TRIGGER = "alert_trigger"

    # 系统操作
    SETTINGS_CHANGE = "settings_change"
    PERMISSION_CHANGE = "permission_change"
    API_CALL = "api_call"

    # 文件操作
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"

    # 管理操作
    ADMIN_ACTION = "admin_action"
    SYSTEM_CONFIG = "system_config"


class AuditLevel(Enum):
    """审计级别"""
    DEBUG = "debug"
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class AuditResult(Enum):
    """操作结果"""
    SUCCESS = "success"
    FAILURE = 'failure'
    PARTIAL = 'partial'
    DENIED = 'denied'


# ==================== 数据模型 ====================

@dataclass
class AuditLog:
    """审计日志"""
    log_id: str
    timestamp: datetime
    user_id: Optional[int]
    action: AuditAction
    level: AuditLevel
    result: AuditResult
    resource_type: Optional[str] = None  # 资源类型
    resource_id: Optional[str] = None  # 资源ID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    response_code: Optional[int] = None
    duration_ms: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)
    old_value: Optional[Dict[str, Any]] = None  # 变更前的值
    new_value: Optional[Dict[str, Any]] = None  # 变更后的值
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_id': self.log_id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action.value,
            'level': self.level.value,
            "result": self.result.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            'ip_address': self.ip_address,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "response_code": self.response_code,
            "duration_ms": self.duration_ms,
            'details': self.details,
            "error_message": self.error_message
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class SecurityEvent:
    """安全事件"""
    event_id: str
    timestamp: datetime
    event_type: str  # brute_force/unauthorized_access/suspicious_activity
    severity: str  # low/medium/high/critical
    user_id: Optional[int]
    ip_address: Optional[str]
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    handled_by: Optional[int] = None
    handled_at: Optional[datetime] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'severity': self.severity,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            "description": self.description,
            'details': self.details,
            'handled': self.handled,
            'handled_at': self.handled_at.isoformat() if self.handled_at else None
        }


@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: int
    ip_address: str
    user_agent: str
    started_at: datetime
    last_activity: datetime
    is_active: bool = True
    device_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'started_at': self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            'is_active': self.is_active,
            "device_info": self.device_info
        }


# ==================== 审计日志服务 ====================

class AuditLogService:
    """审计日志服务"""

    def __init__(self, max_logs: int = 100000):
        self.logs: List[AuditLog] = []
        self.max_logs = max_logs

        # 索引
        self.user_logs: Dict[int, List[str]] = defaultdict(list)
        self.action_logs: Dict[AuditAction, List[str]] = defaultdict(list)
        self.log_index: Dict[str, AuditLog] = {}

    def log(
        self,
        action: AuditAction,
        user_id: int = None,
        level: AuditLevel = AuditLevel.INFO,
        result: AuditResult = AuditResult.SUCCESS,
        resource_type: str = None,
        resource_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_method: str = None,
        request_path: str = None,
        request_params: Dict[str, Any] = None,
        response_code: int = None,
        duration_ms: int = None,
        details: Dict[str, Any] = None,
        old_value: Dict[str, Any] = None,
        new_value: Dict[str, Any] = None,
        error_message: str = None
    ) -> AuditLog:
        """记录审计日志"""
        log_id = f"audit_{secrets.token_hex(8)}"

        audit_log = AuditLog(
            log_id=log_id,
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            level=level,
            result=result,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            request_params=self._sanitize_params(request_params),
            response_code=response_code,
            duration_ms=duration_ms,
            # 关键修复：details / old_value / new_value 历史上未脱敏，
            # 调用方一旦把 user dict 整个塞进来（含 password、phone、id_card 等），
            # 这些 PII 会被原文写入审计日志（数据库 + logger.info）。
            # 现在三者都强制走脱敏 + 递归。
            details=self._sanitize_params(details or {}),
            old_value=self._sanitize_params(old_value),
            new_value=self._sanitize_params(new_value),
            error_message=error_message
        )

        self._store_log(audit_log)

        # 记录到日志系统
        log_msg = f"AUDIT: {action.value} user={user_id} result={result.value}"
        if level == AuditLevel.ERROR or level == AuditLevel.CRITICAL:
            logger.error(log_msg)
        elif level == AuditLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return audit_log

    # 敏感字段黑名单（合并：账号凭据 + PII + 支付/身份证件）
    # key 名称只要"包含"以下任一子串（大小写不敏感）即被脱敏。
    # 历史版本只盖账号凭据；老人 PII（手机、身份证、地址）从未脱敏，
    # 一旦运营泄漏审计日志或日志推到 ELK 就是合规事故。
    _SENSITIVE_KEY_HINTS = (
        # 凭据
        "password", "passwd", "pwd", "token", "secret", "credential", "api_key",
        "private_key", "session", "cookie", "auth", "authorization",
        # 中国 PII
        "id_card", "idcard", "id_number", "shenfenzheng", "身份证",
        "phone", "mobile", "telephone", "手机",
        "address", "住址", "地址",
        "bank_account", "card_no", "银行",
        # 健康敏感（HIPAA 等价）
        "medical_record", "diagnosis", "prescription",
    )

    # 替换占位（保留长度提示有助于排错，但不暴露内容）
    @staticmethod
    def _redact(value: Any) -> str:
        if value is None:
            return "***REDACTED(empty)***"
        try:
            length = len(str(value))
        except Exception:
            length = -1
        return f"***REDACTED(len={length})***"

    def _sanitize_params(self, params: Any) -> Any:
        """
        清理敏感参数（递归）。

        改进点（vs v1）：
        1. 递归处理 dict / list / tuple，杜绝"嵌套对象绕过脱敏"
        2. 黑名单扩展到 PII 与健康敏感字段
        3. 用 ***REDACTED(len=N)*** 占位，保留长度便于排错但不暴露内容
        """
        if params is None:
            return None
        if isinstance(params, dict):
            return {
                k: (
                    self._redact(v)
                    if any(h in str(k).lower() for h in self._SENSITIVE_KEY_HINTS)
                    else self._sanitize_params(v)
                )
                for k, v in params.items()
            }
        if isinstance(params, (list, tuple)):
            return type(params)(self._sanitize_params(item) for item in params)
        # 标量原样返回
        return params

    def _store_log(self, audit_log: AuditLog):
        """存储日志"""
        self.logs.append(audit_log)
        self.log_index[audit_log.log_id] = audit_log

        if audit_log.user_id:
            self.user_logs[audit_log.user_id].append(audit_log.log_id)

        self.action_logs[audit_log.action].append(audit_log.log_id)

        # 清理旧日志
        if len(self.logs) > self.max_logs:
            old_logs = self.logs[:1000]
            self.logs = self.logs[1000:]
            for log in old_logs:
                del self.log_index[log.log_id]

    def get_logs(
        self,
        user_id: int = None,
        action: AuditAction = None,
        level: AuditLevel = None,
        result: AuditResult = None,
        start_time: datetime = None,
        end_time: datetime = None,
        ip_address: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AuditLog], int]:
        """查询审计日志"""
        logs = list(reversed(self.logs))  # 最新的在前

        # 过滤
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]

        if action:
            logs = [l for l in logs if l.action == action]

        if level:
            logs = [l for l in logs if l.level == level]

        if result:
            logs = [l for l in logs if l.result == result]

        if start_time:
            logs = [l for l in logs if l.timestamp >= start_time]

        if end_time:
            logs = [l for l in logs if l.timestamp <= end_time]

        if ip_address:
            logs = [l for l in logs if l.ip_address == ip_address]

        total = len(logs)
        logs = logs[offset:offset + limit]

        return logs, total

    def get_user_activity(
        self,
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取用户活动统计"""
        cutoff = datetime.now() - timedelta(days=days)
        log_ids = self.user_logs.get(user_id, [])

        logs = [
            self.log_index[lid]
            for lid in log_ids
            if lid in self.log_index and self.log_index[lid].timestamp >= cutoff
        ]

        # 统计
        action_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        result_counts = defaultdict(int)

        for log in logs:
            action_counts[log.action.value] += 1
            daily_counts[log.timestamp.date().isoformat()] += 1
            result_counts[log.result.value] += 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            'by_action': dict(action_counts),
            'by_day': dict(daily_counts),
            'by_result': dict(result_counts),
            "last_activity": logs[0].timestamp.isoformat() if logs else None
        }

    def get_statistics(
        self,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> Dict[str, Any]:
        """获取审计统计"""
        if not start_time:
            start_time = datetime.now() - timedelta(days=1)
        if not end_time:
            end_time = datetime.now()

        logs = [l for l in self.logs if start_time <= l.timestamp <= end_time]

        action_counts = defaultdict(int)
        level_counts = defaultdict(int)
        result_counts = defaultdict(int)
        unique_users = set()
        unique_ips = set()

        for log in logs:
            action_counts[log.action.value] += 1
            level_counts[log.level.value] += 1
            result_counts[log.result.value] += 1
            if log.user_id:
                unique_users.add(log.user_id)
            if log.ip_address:
                unique_ips.add(log.ip_address)

        return {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'total_logs': len(logs),
            "unique_users": len(unique_users),
            'unique_ips': len(unique_ips),
            'by_action': dict(action_counts),
            'by_level': dict(level_counts),
            'by_result': dict(result_counts)
        }


# ==================== 安全事件服务 ====================

class SecurityEventService:
    """安全事件服务"""

    def __init__(self):
        self.events: Dict[str, SecurityEvent] = {}
        self.user_events: Dict[int, List[str]] = defaultdict(list)
        self.ip_events: Dict[str, List[str]] = defaultdict(list)

        # 登录失败计数
        self.login_failures: Dict[str, List[datetime]] = defaultdict(list)
        self.failed_login_threshold = 5
        self.failed_login_window = 300  # 5分钟

    def record_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: int = None,
        ip_address: str = None,
        details: Dict[str, Any] = None
    ) -> SecurityEvent:
        """记录安全事件"""
        event_id = f"sec_{secrets.token_hex(8)}"

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            details=details or {}
        )

        self.events[event_id] = event

        if user_id:
            self.user_events[user_id].append(event_id)
        if ip_address:
            self.ip_events[ip_address].append(event_id)

        # 高危事件告警
        if severity in ['high', 'critical']:
            logger.warning(f"SECURITY EVENT: {event_type} - {description}")

        return event

    def check_login_attempt(
        self,
        ip_address: str,
        user_id: int = None,
        success: bool = True
    ) -> Tuple[bool, Optional[SecurityEvent]]:
        """检查登录尝试"""
        key = f'{ip_address}_{user_id}' if user_id else ip_address
        now = datetime.now()

        if success:
            # 登录成功，清除失败记录
            self.login_failures[key] = []
            return True, None

        # 记录失败
        self.login_failures[key].append(now)

        # 清理过期记录
        cutoff = now - timedelta(seconds=self.failed_login_window)
        self.login_failures[key] = [
            t for t in self.login_failures[key] if t > cutoff
        ]

        # 检查是否超过阈值
        if len(self.login_failures[key]) >= self.failed_login_threshold:
            event = self.record_event(
                event_type='brute_force',
                severity="high",
                description=f"检测到暴力破解尝试: {len(self.login_failures[key])}次失败",
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "failure_count": len(self.login_failures[key]),
                    "window_seconds": self.failed_login_window
                }
            )
            return False, event

        return True, None

    def check_suspicious_activity(
        self,
        user_id: int,
        action: str,
        ip_address: str = None,
        details: Dict[str, Any] = None
    ) -> Optional[SecurityEvent]:
        """检查可疑活动"""
        # 这里可以实现更复杂的检测逻辑
        # 例如：异常IP、异常时间、异常频率等

        # 示例：检查短时间内的大量操作
        recent_events = [
            self.events[eid]
            for eid in self.user_events.get(user_id, [])[-100:]
            if eid in self.events
        ]

        now = datetime.now()
        recent_count = sum(
            1 for e in recent_events
            if (now - e.timestamp).total_seconds() < 60
        )

        if recent_count > 50:
            return self.record_event(
                event_type="suspicious_activity",
                severity='medium',
                description=f"检测到异常高频操作: 1分钟内{recent_count}次",
                user_id=user_id,
                ip_address=ip_address,
                details={'action': action, "count": recent_count, **(details or {})}
            )

        return None

    def handle_event(
        self,
        event_id: str,
        handled_by: int,
        notes: str = None
    ) -> bool:
        """处理安全事件"""
        event = self.events.get(event_id)
        if not event:
            return False

        event.handled = True
        event.handled_by = handled_by
        event.handled_at = datetime.now()
        event.notes = notes

        return True

    def get_events(
        self,
        event_type: str = None,
        severity: str = None,
        handled: bool = None,
        user_id: int = None,
        ip_address: str = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """获取安全事件"""
        events = list(self.events.values())

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if severity:
            events = [e for e in events if e.severity == severity]

        if handled is not None:
            events = [e for e in events if e.handled == handled]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if ip_address:
            events = [e for e in events if e.ip_address == ip_address]

        events = sorted(events, key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取安全事件统计"""
        events = list(self.events.values())
        now = datetime.now()

        # 24小时内
        recent_events = [
            e for e in events
            if (now - e.timestamp).total_seconds() < 86400
        ]

        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        unhandled_count = 0

        for e in recent_events:
            by_type[e.event_type] += 1
            by_severity[e.severity] += 1
            if not e.handled:
                unhandled_count += 1

        return {
            "total_events_24h": len(recent_events),
            "unhandled_count": unhandled_count,
            'by_type': dict(by_type),
            "by_severity": dict(by_severity)
        }


# ==================== 会话管理服务 ====================

class SessionManagementService:
    """会话管理服务"""

    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[int, List[str]] = defaultdict(list)

    def create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        device_info: Dict[str, Any] = None
    ) -> UserSession:
        """创建会话"""
        session_id = secrets.token_hex(16)

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            device_info=device_info or {}
        )

        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)

        return session

    def update_activity(self, session_id: str) -> bool:
        """更新会话活动时间"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.last_activity = datetime.now()
        return True

    def end_session(self, session_id: str) -> bool:
        """结束会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.is_active = False
        return True

    def get_user_sessions(
        self,
        user_id: int,
        active_only: bool = True
    ) -> List[UserSession]:
        """获取用户会话"""
        session_ids = self.user_sessions.get(user_id, [])
        sessions = [
            self.sessions[sid]
            for sid in session_ids
            if sid in self.sessions
        ]

        if active_only:
            sessions = [s for s in sessions if s.is_active]

        return sessions

    def terminate_user_sessions(
        self,
        user_id: int,
        except_session: str = None
    ) -> int:
        """终止用户所有会话"""
        count = 0
        session_ids = self.user_sessions.get(user_id, [])

        for sid in session_ids:
            if sid != except_session:
                if self.end_session(sid):
                    count += 1

        return count

    def cleanup_inactive(self, timeout_hours: int = 24) -> int:
        """清理不活跃会话"""
        cutoff = datetime.now() - timedelta(hours=timeout_hours)
        count = 0

        for session in list(self.sessions.values()):
            if session.last_activity < cutoff:
                session.is_active = False
                count += 1

        return count


# ==================== 统一审计服务 ====================

class AuditService:
    """统一审计服务"""

    def __init__(self):
        self.logs = AuditLogService()
        self.security = SecurityEventService()
        self.sessions = SessionManagementService()

    # 便捷方法

    def log_login(
        self,
        user_id: int,
        success: bool,
        ip_address: str,
        user_agent: str = None,
        error_message: str = None
    ) -> AuditLog:
        """记录登录"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        result = AuditResult.SUCCESS if success else AuditResult.FAILURE

        # 检查暴力破解
        self.security.check_login_attempt(ip_address, user_id, success)

        return self.logs.log(
            action=action,
            user_id=user_id,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message
        )

    def log_data_access(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """记录数据访问"""
        action_map = {
            'read': AuditAction.DATA_READ,
            'create': AuditAction.DATA_CREATE,
            'update': AuditAction.DATA_UPDATE,
            'delete': AuditAction.DATA_DELETE,
            'export': AuditAction.DATA_EXPORT
        }

        return self.logs.log(
            action=action_map.get(action, AuditAction.DATA_READ),
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details
        )

    def log_health_access(
        self,
        user_id: int,
        accessed_user_id: int,
        action: str,
        ip_address: str = None
    ) -> AuditLog:
        """记录健康数据访问"""
        return self.logs.log(
            action=AuditAction.HEALTH_VIEW if action == 'view' else AuditAction.HEALTH_RECORD,
            user_id=user_id,
            resource_type="health_data",
            resource_id=str(accessed_user_id),
            ip_address=ip_address,
            details={"accessed_user_id": accessed_user_id}
        )

    def log_sos_event(
        self,
        user_id: int,
        location: str = None,
        ip_address: str = None
    ) -> AuditLog:
        """记录紧急求助"""
        # 同时记录安全事件
        self.security.record_event(
            event_type="sos_triggered",
            severity='high',
            description=f"用户{user_id}触发紧急求助",
            user_id=user_id,
            ip_address=ip_address,
            details={'location': location}
        )

        return self.logs.log(
            action=AuditAction.SOS_TRIGGER,
            user_id=user_id,
            level=AuditLevel.CRITICAL,
            ip_address=ip_address,
            details={"location": location}
        )


# ==================== 全局实例 ====================

audit_service = AuditService()
