"""
审计日志API
提供操作记录、安全事件、会话管理等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.services.audit_service import (
    audit_service,
    AuditAction,
    AuditLevel,
    AuditResult
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/audit", tags=["审计日志"])


# ==================== 请求模型 ====================

class HandleSecurityEventRequest(BaseModel):
    """处理安全事件请求"""
    notes: Optional[str] = Field(None, max_length=1000, description='处理备注')


# ==================== 审计日志API ====================

@router.get('/logs')
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description='用户ID筛选'),
    action: Optional[str] = Query(None, description='动作类型'),
    level: Optional[str] = Query(None, description='日志级别'),
    result: Optional[str] = Query(None, description='操作结果'),
    start_time: Optional[datetime] = Query(None, description='开始时间'),
    end_time: Optional[datetime] = Query(None, description='结束时间'),
    ip_address: Optional[str] = Query(None, description='IP地址'),
    limit: int = Query(50, ge=1, le=500, description='返回数量'),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user)
):
    """
    查询审计日志

    管理员可查询所有日志，普通用户只能查询自己的日志
    """
    current_user_id = int(current_user['sub'])
    is_admin = current_user.get("role") == 'admin'

    # 非管理员只能查看自己的日志
    if not is_admin:
        user_id = current_user_id

    # 解析筛选条件
    action_filter = None
    if action:
        try:
            action_filter = AuditAction(action)
        except ValueError:
            pass

    level_filter = None
    if level:
        try:
            level_filter = AuditLevel(level)
        except ValueError:
            pass

    result_filter = None
    if result:
        try:
            result_filter = AuditResult(result)
        except ValueError:
            pass

    logs, total = audit_service.logs.get_logs(
        user_id=user_id,
        action=action_filter,
        level=level_filter,
        result=result_filter,
        start_time=start_time,
        end_time=end_time,
        ip_address=ip_address,
        limit=limit,
        offset=offset
    )

    return {
        'logs': [l.to_dict() for l in logs],
        'total': total,
        'limit': limit,
        "offset": offset
    }


@router.get("/logs/my-activity")
async def get_my_activity(
    days: int = Query(7, ge=1, le=90, description="天数"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的活动统计
    """
    user_id = int(current_user['sub'])

    activity = audit_service.logs.get_user_activity(user_id, days)

    return activity


@router.get("/logs/statistics")
async def get_audit_statistics(
    start_time: Optional[datetime] = Query(None, description='开始时间'),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取审计统计

    管理员专用
    """
    # 检查权限
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = audit_service.logs.get_statistics(start_time, end_time)

    return stats


@router.get("/logs/actions")
async def get_audit_actions(current_user: dict = Depends(get_current_user)):
    """
    获取审计动作类型列表
    """
    actions = [
        {'value': a.value, 'label': a.value}
        for a in AuditAction
    ]

    return {'actions': actions}


# ==================== 安全事件API ====================

@router.get("/security/events")
async def get_security_events(
    event_type: Optional[str] = Query(None, description='事件类型'),
    severity: Optional[str] = Query(None, description='严重程度'),
    handled: Optional[bool] = Query(None, description='是否已处理'),
    user_id: Optional[int] = Query(None, description='用户ID'),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取安全事件列表

    管理员专用
    """
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail='需要管理员权限')

    events = audit_service.security.get_events(
        event_type=event_type,
        severity=severity,
        handled=handled,
        user_id=user_id,
        limit=limit
    )

    return {
        'events': [e.to_dict() for e in events],
        "count": len(events)
    }


@router.get("/security/events/{event_id}")
async def get_security_event_detail(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取安全事件详情
    """
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail='需要管理员权限')

    event = audit_service.security.events.get(event_id)

    if not event:
        raise HTTPException(status_code=404, detail='事件不存在')

    return {"event": event.to_dict()}


@router.post("/security/events/{event_id}/handle")
async def handle_security_event(
    event_id: str,
    request: HandleSecurityEventRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    处理安全事件
    """
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail='需要管理员权限')

    admin_id = int(current_user['sub'])

    success = audit_service.security.handle_event(
        event_id, admin_id, request.notes
    )

    if not success:
        raise HTTPException(status_code=404, detail='事件不存在')

    return {
        'success': True,
        'message': "事件已处理"
    }


@router.get("/security/statistics")
async def get_security_statistics(current_user: dict = Depends(get_current_user)):
    """
    获取安全事件统计
    """
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = audit_service.security.get_statistics()

    return stats


@router.get("/security/event-types")
async def get_security_event_types(current_user: dict = Depends(get_current_user)):
    """
    获取安全事件类型列表
    """
    types = [
        {'value': 'brute_force', 'label': '暴力破解', 'severity': 'high'},
        {'value': 'unauthorized_access', 'label': '未授权访问', 'severity': 'high'},
        {'value': 'suspicious_activity', 'label': '可疑活动', 'severity': 'medium'},
        {'value': 'sos_triggered', 'label': '紧急求助', 'severity': 'high'},
        {'value': 'data_breach', 'label': '数据泄露', 'severity': 'critical'}
    ]

    return {'types': types}


# ==================== 会话管理API ====================

@router.get("/sessions")
async def get_my_sessions(current_user: dict = Depends(get_current_user)):
    """
    获取我的会话列表
    """
    user_id = int(current_user['sub'])

    sessions = audit_service.sessions.get_user_sessions(user_id, active_only=True)

    return {
        'sessions': [s.to_dict() for s in sessions],
        'count': len(sessions)
    }


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    终止指定会话
    """
    user_id = int(current_user['sub'])

    # 检查会话是否属于当前用户
    session = audit_service.sessions.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='会话不存在')

    if session.user_id != user_id and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='无权终止此会话')

    success = audit_service.sessions.end_session(session_id)

    if not success:
        raise HTTPException(status_code=400, detail='终止会话失败')

    return {
        'success': True,
        'message': "会话已终止"
    }


@router.post("/sessions/terminate-all")
async def terminate_all_sessions(
    except_current: bool = Query(True, description="保留当前会话"),
    current_user: dict = Depends(get_current_user)
):
    """
    终止所有其他会话
    """
    user_id = int(current_user['sub'])
    current_session = current_user.get("session_id") if except_current else None

    count = audit_service.sessions.terminate_user_sessions(
        user_id, except_session=current_session
    )

    return {
        'success': True,
        "terminated_count": count,
        'message': f"已终止{count}个会话"
    }


# ==================== 用户活动监控API ====================

@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    days: int = Query(7, ge=1, le=90, description="天数"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户活动统计

    管理员或用户本人可查询
    """
    current_user_id = int(current_user['sub'])
    is_admin = current_user.get("role") == 'admin'

    if not is_admin and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="无权查看此用户活动")

    activity = audit_service.logs.get_user_activity(user_id, days)

    return activity


@router.get("/users/{user_id}/sessions")
async def get_user_sessions(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户会话列表

    管理员专用
    """
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail='需要管理员权限')

    sessions = audit_service.sessions.get_user_sessions(user_id, active_only=False)

    return {
        'user_id': user_id,
        "sessions": [s.to_dict() for s in sessions],
        "active_count": sum(1 for s in sessions if s.is_active)
    }


# ==================== 仪表板API ====================

@router.get("/dashboard")
async def get_audit_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取审计仪表板

    管理员专用，综合展示安全和审计数据
    """
    if current_user.get("role") != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")

    # 审计统计
    audit_stats = audit_service.logs.get_statistics()

    # 安全事件统计
    security_stats = audit_service.security.get_statistics()

    # 最近的安全事件
    recent_events = audit_service.security.get_events(limit=5)

    # 最近的错误日志
    error_logs, _ = audit_service.logs.get_logs(
        level=AuditLevel.ERROR,
        limit=5
    )

    return {
        "audit_statistics": audit_stats,
        "security_statistics": security_stats,
        "recent_security_events": [e.to_dict() for e in recent_events],
        "recent_errors": [l.to_dict() for l in error_logs],
        'alerts': {
            "unhandled_security_events": security_stats.get("unhandled_count", 0),
            "high_severity_events": security_stats.get('by_severity', {}).get('high', 0) +
                                   security_stats.get('by_severity', {}).get('critical', 0)
        }
    }
