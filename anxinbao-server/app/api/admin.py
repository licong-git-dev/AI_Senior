"""
运营管理后台API
提供数据仪表盘、用户管理、内容审核、系统配置等接口

⚠️ 安全：本路由全量数据是当前 admin_service 的 mock 输出（生产环境已通过
   _SafeRandom 清零）。即便如此，所有端点必须强鉴权 admin 角色，避免任意
   登录用户拼路径访问。历史 verify_admin 注释了"为演示目的，允许任何登录
   用户访问"——这是上线前必修的提权漏洞。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.admin_service import (
    admin_service,
    AdminRole,
    ReportType
)
from app.core.security import get_current_user, UserInfo
from app.core.deps import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["运营管理"])


# ==================== 权限验证 ====================

async def verify_admin(current_user: UserInfo = Depends(get_current_admin)) -> Dict[str, Any]:
    """
    验证管理员身份。

    历史版本对"未注册到 admin_service 的用户"放行（自承"演示目的"），
    任意登录用户都能访问 /api/admin/*。本版本：
    1. 通过 get_current_admin 强校验 JWT.role == 'admin'
    2. 再核对 admin_service 中确实注册了该 admin_id，防御 token 伪造或角色提升
    """
    user_id_str = current_user.user_id  # JWT sub
    try:
        user_id_int = int(user_id_str)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=403,
            detail="管理员身份无效（user_id 非数字）",
        )

    admin = admin_service.get_admin(user_id_int)
    if not admin:
        raise HTTPException(
            status_code=403,
            detail="管理员账号未在 admin_service 中注册，请联系超级管理员开通",
        )

    return {"admin_id": admin.admin_id, "role": admin.role.value}


# ==================== 请求模型 ====================

class BlockUserRequest(BaseModel):
    """封禁用户请求"""
    user_id: int = Field(..., description='用户ID')
    reason: str = Field(..., max_length=500, description='封禁原因')
    duration_days: Optional[int] = Field(None, ge=1, le=3650, description="封禁天数，不填为永久")


class ContentActionRequest(BaseModel):
    """内容操作请求"""
    content_id: str = Field(..., description="内容ID")
    reason: Optional[str] = Field(default="", max_length=500, description="原因")


class HandleReportRequest(BaseModel):
    """处理举报请求"""
    report_id: str = Field(..., description="举报ID")
    action: str = Field(..., description="处理动作: approve/dismiss")
    result: str = Field(..., max_length=500, description="处理结果说明")


class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    key: str = Field(..., description='配置键')
    value: Any = Field(..., description="配置值")


class CreateReportRequest(BaseModel):
    """创建举报请求"""
    content_type: str = Field(..., description="内容类型: post/comment/message")
    content_id: str = Field(..., description="内容ID")
    report_type: str = Field(..., description="举报类型: spam/abuse/inappropriate/fraud/other")
    reason: str = Field(..., max_length=500, description="举报原因")


# ==================== 仪表盘API ====================

@router.get("/dashboard/overview")
async def get_dashboard_overview(admin: dict = Depends(verify_admin)):
    """
    获取仪表盘概览

    返回用户、收入、订阅、健康、紧急求助等核心数据
    """
    overview = admin_service.dashboard.get_overview()
    return overview


@router.get("/dashboard/trends")
async def get_dashboard_trends(
    days: int = Query(30, ge=7, le=90, description="天数"),
    admin: dict = Depends(verify_admin)
):
    """
    获取趋势数据

    返回指定天数的用户增长、收入、活跃用户趋势
    """
    trends = admin_service.dashboard.get_trends(days)
    return trends


@router.get("/dashboard/user-distribution")
async def get_user_distribution(admin: dict = Depends(verify_admin)):
    """
    获取用户分布数据

    返回年龄、地区、会员等级分布
    """
    distribution = admin_service.dashboard.get_user_distribution()
    return distribution


@router.get("/dashboard/feature-usage")
async def get_feature_usage(admin: dict = Depends(verify_admin)):
    """
    获取功能使用统计

    返回各功能模块的使用情况
    """
    usage = admin_service.dashboard.get_feature_usage()
    return usage


# ==================== 用户管理API ====================

@router.get("/users")
async def search_users(
    keyword: Optional[str] = Query(None, description='搜索关键词'),
    membership: Optional[str] = Query(None, description='会员类型'),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(verify_admin)
):
    """
    搜索用户列表
    """
    result = admin_service.user_mgmt.search_users(
        keyword=keyword,
        membership=membership,
        status=status,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    admin: dict = Depends(verify_admin)
):
    """
    获取用户详情
    """
    user = admin_service.user_mgmt.get_user_detail(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/users/block")
async def block_user(
    request: BlockUserRequest,
    admin: dict = Depends(verify_admin)
):
    """
    封禁用户
    """
    success = admin_service.user_mgmt.block_user(
        user_id=request.user_id,
        reason=request.reason,
        admin_id=admin['admin_id'],
        duration_days=request.duration_days
    )

    # 记录审计日志
    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action='block_user',
        resource_type='user',
        resource_id=str(request.user_id),
        details={'reason': request.reason, 'duration': request.duration_days}
    )

    return {
        'success': success,
        "message": f"用户 {request.user_id} 已被封禁"
    }


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    admin: dict = Depends(verify_admin)
):
    """
    解封用户
    """
    success = admin_service.user_mgmt.unblock_user(user_id, admin['admin_id'])

    if success:
        admin_service.audit_log.log_action(
            admin_id=admin['admin_id'],
            action="unblock_user",
            resource_type='user',
            resource_id=str(user_id)
        )

    return {
        'success': success,
        'message': f'用户 {user_id} 已解封' if success else "用户未被封禁"
    }


# ==================== 内容审核API ====================

@router.get("/content/pending")
async def get_pending_content(
    content_type: Optional[str] = Query(None, description="内容类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(verify_admin)
):
    """
    获取待审核内容
    """
    result = admin_service.content_mod.get_pending_content(
        content_type=content_type,
        page=page,
        page_size=page_size
    )
    return result


@router.post("/content/approve")
async def approve_content(
    request: ContentActionRequest,
    admin: dict = Depends(verify_admin)
):
    """
    通过内容审核
    """
    success = admin_service.content_mod.approve_content(
        request.content_id,
        admin['admin_id']
    )

    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action="approve_content",
        resource_type='content',
        resource_id=request.content_id
    )

    return {'success': success, 'message': "内容已通过"}


@router.post("/content/reject")
async def reject_content(
    request: ContentActionRequest,
    admin: dict = Depends(verify_admin)
):
    """
    拒绝内容
    """
    success = admin_service.content_mod.reject_content(
        request.content_id,
        admin['admin_id'],
        request.reason
    )

    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action="reject_content",
        resource_type='content',
        resource_id=request.content_id,
        details={'reason': request.reason}
    )

    return {'success': success, 'message': '内容已拒绝'}


# ==================== 举报管理API ====================

@router.get("/reports")
async def get_reports(
    status: Optional[str] = Query(None, description="状态: pending/processed/dismissed"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(verify_admin)
):
    """
    获取举报列表
    """
    result = admin_service.content_mod.get_reports(
        status=status,
        page=page,
        page_size=page_size
    )
    return result


@router.post("/reports")
async def create_report(
    request: CreateReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建举报（用户端）
    """
    user_id = int(current_user['sub'])

    try:
        report_type = ReportType(request.report_type)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的举报类型')

    report = admin_service.content_mod.create_report(
        content_type=request.content_type,
        content_id=request.content_id,
        reporter_id=user_id,
        report_type=report_type,
        reason=request.reason
    )

    return {
        'success': True,
        'report_id': report.report_id,
        "message": "举报已提交，我们会尽快处理"
    }


@router.post("/reports/handle")
async def handle_report(
    request: HandleReportRequest,
    admin: dict = Depends(verify_admin)
):
    """
    处理举报
    """
    if request.action not in ['approve', 'dismiss']:
        raise HTTPException(status_code=400, detail='无效的处理动作')

    report = admin_service.content_mod.handle_report(
        report_id=request.report_id,
        admin_id=admin['admin_id'],
        action=request.action,
        result=request.result
    )

    if not report:
        raise HTTPException(status_code=404, detail='举报不存在')

    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action=f'handle_report_{request.action}',
        resource_type='report',
        resource_id=request.report_id,
        details={'result': request.result}
    )

    return {
        'success': True,
        'report': report.to_dict(),
        'message': '举报已处理'
    }


# ==================== 系统配置API ====================

@router.get("/config")
async def get_all_configs(admin: dict = Depends(verify_admin)):
    """
    获取所有系统配置（按类别分组）
    """
    configs = admin_service.sys_config.get_all_configs()
    return {'configs': configs}


@router.get("/config/{category}")
async def get_configs_by_category(
    category: str,
    admin: dict = Depends(verify_admin)
):
    """
    获取指定类别的配置
    """
    configs = admin_service.sys_config.get_configs_by_category(category)
    return {'configs': [c.to_dict() for c in configs]}


@router.put("/config")
async def update_config(
    request: UpdateConfigRequest,
    admin: dict = Depends(verify_admin)
):
    """
    更新配置
    """
    config = admin_service.sys_config.update_config(
        key=request.key,
        value=request.value,
        admin_id=admin['admin_id']
    )

    if not config:
        raise HTTPException(status_code=404, detail='配置项不存在')

    admin_service.audit_log.log_action(
        admin_id=admin["admin_id"],
        action="update_config",
        resource_type='config',
        resource_id=request.key,
        details={'new_value': request.value}
    )

    return {
        'success': True,
        'config': config.to_dict(),
        'message': "配置已更新"
    }


# ==================== 审计日志API ====================

@router.get("/audit-logs")
async def get_audit_logs(
    admin_id: Optional[int] = Query(None, description='管理员ID'),
    action: Optional[str] = Query(None, description='操作类型'),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin: dict = Depends(verify_admin)
):
    """
    查询审计日志
    """
    result = admin_service.audit_log.get_logs(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        page=page,
        page_size=page_size
    )
    return result


# ==================== 系统状态API ====================

@router.get("/system/status")
async def get_system_status(admin: dict = Depends(verify_admin)):
    """
    获取系统状态
    """
    return {
        'status': 'healthy',
        'version': '1.0.0',
        'uptime': "30d 12h 45m",
        'services': {
            'database': 'healthy',
            'redis': 'healthy',
            'ai_service': 'healthy',
            'payment': 'healthy'
        },
        "performance": {
            'cpu_usage': "35%",
            'memory_usage': "62%",
            'disk_usage': '45%',
            "active_connections": 1234
        },
        'checked_at': datetime.now().isoformat()
    }


@router.post("/system/announcement")
async def set_announcement(
    message: str = Query(..., max_length=500, description="公告内容"),
    admin: dict = Depends(verify_admin)
):
    """
    设置系统公告
    """
    admin_service.sys_config.update_config(
        "app.announcement",
        message,
        admin['admin_id']
    )

    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action="set_announcement",
        resource_type='system',
        resource_id="announcement",
        details={'message': message}
    )

    return {
        'success': True,
        'message': "公告已发布"
    }


# ==================== 死信队列（DLQ）查看与维护 ====================

@router.get("/dlq")
async def list_dead_letters(
    channel: Optional[str] = Query(None, description="按通道筛选: wechat / sms / app_push / multi / payment_callback"),
    severity: Optional[str] = Query(None, description="按级别筛选: info / warning / critical"),
    limit: int = Query(100, ge=1, le=500, description="最多返回多少条"),
    admin: dict = Depends(verify_admin),
):
    """
    查看死信队列（推送 / 通知 / 支付回调 等关键消息重试用尽后的失败档案）。

    用途：运维 / 客服可在此 UI 看到"哪些 SOS 通知没送到家属"、"哪些紧急
    短信发不出去"，做人工补偿（例如直接打电话）。

    DLQ 由 [`app/core/dead_letter.py`](anxinbao-server/app/core/dead_letter.py) 维护，当前是内存实现，
    服务重启后会清空 — 计划后续迁移到 DB 表（DeadLetter）。
    """
    from app.core.dead_letter import dead_letter_queue
    items = dead_letter_queue.list(channel=channel, severity=severity, limit=limit)

    # log this admin action for audit
    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action="view_dlq",
        resource_type='dlq',
        resource_id=channel or "all",
        details={'severity': severity, 'limit': limit, 'count': len(items)},
    )

    return {
        "total_in_memory": dead_letter_queue.size(),
        "channel_counts": dead_letter_queue.counts,
        "filtered_count": len(items),
        "items": [
            {
                "channel": r.channel,
                "recipient": r.recipient,
                "template": r.template,
                "payload": r.payload,
                "error": r.error,
                "severity": r.severity,
                "occurred_at": r.occurred_at,
                "attempts": r.attempts,
            }
            for r in items
        ],
    }


@router.post("/dlq/clear")
async def clear_dead_letters(
    confirm: bool = Query(False, description="必须传 confirm=true 才执行清空，避免误操作"),
    admin: dict = Depends(verify_admin),
):
    """
    清空死信队列（运维确认人工补偿完成后调用）。

    必须传 confirm=true 才会执行。审计日志会记录管理员 ID + 清空数量。
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="需要确认操作：在 query 中传 confirm=true",
        )

    from app.core.dead_letter import dead_letter_queue
    cleared = dead_letter_queue.clear()

    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action="clear_dlq",
        resource_type='dlq',
        resource_id="all",
        details={'cleared_count': cleared},
    )

    return {'success': True, 'cleared_count': cleared}


# ===== r20 · 北极星指标看板 =====


@router.get("/north-star")
async def get_north_star_dashboard(admin: dict = Depends(verify_admin)):
    """
    北极星指标快照（运营快速验证用）。

    重要：返回的是**进程内累计**，重启清零；生产场景应配合 Prometheus 时间
    序列。这里只验证埋点是否生效。
    """
    from app.core.north_star_metrics import compute_north_star_view

    view = compute_north_star_view()

    # 顺手记录管理员查看动作（审计）
    admin_service.audit_log.log_action(
        admin_id=admin["admin_id"],
        action="view_north_star",
        resource_type="metrics",
        resource_id="north_star",
    )
    return view


@router.post("/system/maintenance")
async def toggle_maintenance(
    enabled: bool = Query(..., description="是否开启维护模式"),
    admin: dict = Depends(verify_admin)
):
    """
    切换维护模式
    """
    admin_service.sys_config.update_config(
        "app.maintenance_mode",
        enabled,
        admin['admin_id']
    )

    admin_service.audit_log.log_action(
        admin_id=admin['admin_id'],
        action="toggle_maintenance",
        resource_type='system',
        resource_id="maintenance",
        details={'enabled': enabled}
    )

    return {
        'success': True,
        "maintenance_mode": enabled,
        'message': f"维护模式已{'开启' if enabled else '关闭'}"
    }
