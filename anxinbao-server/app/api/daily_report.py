"""
API路由 - 今日爸妈（子女安心日报）
核心卖点功能 — 让子女一目了然"爸妈今天过得怎么样"
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional
import json

from app.core.deps import get_db
from app.core.security import get_current_user, UserInfo
from app.services.daily_report import daily_report_service
from app.models.database import FamilyBindingInvite

router = APIRouter(prefix="/api/daily-report", tags=["今日爸妈"])


def _persist_share_invite(binding_request, db: Session) -> None:
    existing = db.query(FamilyBindingInvite).filter(
        FamilyBindingInvite.request_id == binding_request.request_id
    ).first()
    if existing:
        existing.invite_code = binding_request.invite_code
        existing.group_id = binding_request.group_id
        existing.requester_id = binding_request.requester_id
        existing.requester_name = binding_request.requester_name
        existing.target_id = binding_request.target_id
        existing.relationship = binding_request.relationship
        existing.role = binding_request.role.value
        existing.permission_level = binding_request.permission_level.value
        existing.status = binding_request.status.value
        existing.expires_at = binding_request.expires_at
        existing.processed_at = binding_request.processed_at
    else:
        db.add(FamilyBindingInvite(
            request_id=binding_request.request_id,
            invite_code=binding_request.invite_code,
            group_id=binding_request.group_id,
            requester_id=binding_request.requester_id,
            requester_name=binding_request.requester_name,
            target_id=binding_request.target_id,
            relationship=binding_request.relationship,
            role=binding_request.role.value,
            permission_level=binding_request.permission_level.value,
            status=binding_request.status.value,
            expires_at=binding_request.expires_at,
            processed_at=binding_request.processed_at,
        ))
    db.commit()


def _check_elder_access(
    elder_id: int,
    current_user: UserInfo,
    db: Session,
) -> None:
    """
    校验当前用户是否有权访问指定老人的日报。

    规则：
    - admin   — 全部可见
    - elder   — 只能查自己（UserAuth.user_id == elder_id）
    - family  — 必须与该老人存在家庭绑定关系（FamilyMember.user_id == elder_id）
    - device  — 只能访问绑定老人（DeviceAuth.user_id == elder_id）
    """
    if current_user.role == "admin":
        return

    from app.models.database import UserAuth, FamilyMember, DeviceAuth

    auth = db.query(UserAuth).filter(
        UserAuth.id == int(current_user.user_id)
    ).first()

    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证信息无效")

    if current_user.role == "elder":
        if auth.user_id != elder_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该老人的日报"
            )

    elif current_user.role == "family":
        if not auth.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="家属账户未绑定老人"
            )
        family = db.query(FamilyMember).filter(
            FamilyMember.id == auth.family_id
        ).first()
        if not family or family.user_id != elder_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该老人的日报"
            )

    elif current_user.role == "device":
        device = db.query(DeviceAuth).filter(
            DeviceAuth.id == int(current_user.user_id)
        ).first()
        if not device or device.user_id != elder_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="设备未绑定该老人"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )


def _build_alerts(report, notifications: list[dict], generated_at: str) -> list[dict]:
    alerts: list[dict] = []

    for notification in notifications:
        risk_score = int(notification.get("risk_score", 5))
        severity = "high" if risk_score >= 7 else "medium" if risk_score >= 5 else "low"
        alerts.append({
            "id": notification.get("id"),
            "type": notification.get("category", "system"),
            "severity": severity,
            "title": notification.get("title", "提醒"),
            "summary": notification.get("content", ""),
            "action_suggestion": "建议尽快查看详情并联系家人确认情况" if severity == "high" else "建议留意今天的状态变化",
            "status": "handled" if notification.get("is_handled") else "pending",
            "created_at": notification.get("created_at"),
        })

    for alert in report.health.health_alerts:
        alerts.append({
            "id": f"health-{len(alerts) + 1}",
            "type": "health",
            "severity": "medium" if report.health.overall_status == "注意" else "high",
            "title": "健康提醒",
            "summary": alert,
            "action_suggestion": "建议查看健康趋势，并在今晚主动联系老人",
            "status": "pending",
            "created_at": generated_at,
        })

    return alerts[:3]


def _build_timeline(report) -> list[dict]:
    timeline: list[dict] = []

    if report.conversation.first_chat_time:
        timeline.append({
            "time": report.conversation.first_chat_time,
            "type": "chat",
            "text": "进行了今日首次聊天",
        })

    if report.conversation.last_chat_time and report.conversation.last_chat_time != report.conversation.first_chat_time:
        timeline.append({
            "time": report.conversation.last_chat_time,
            "type": "chat",
            "text": "完成了今天最近一次陪伴交流",
        })

    for item in report.health.medication_details[:2]:
        timeline.append({
            "time": "今日",
            "type": "medication",
            "text": item,
        })

    for symptom in report.health.health_alerts[:2]:
        timeline.append({
            "time": "今日",
            "type": "health",
            "text": symptom,
        })

    if report.activity.steps:
        timeline.append({
            "time": "今日",
            "type": "activity",
            "text": f"今日步数约 {report.activity.steps} 步",
        })

    return timeline[:5]


def _build_empty_state(report, alerts: list[dict], timeline: list[dict]) -> dict:
    has_core_data = (
        report.conversation.total_messages > 0
        or bool(report.health.health_alerts)
        or bool(report.health.medication_details)
        or bool(report.activity.steps)
        or bool(alerts)
        or bool(timeline)
    )

    if has_core_data:
        return {"is_empty": False, "reason": None}

    return {
        "is_empty": True,
        "reason": "刚完成绑定或今天暂未产生足够数据，系统正在持续积累老人日常状态。",
    }


@router.get("/today/{elder_id}")
async def get_today_report(
    elder_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取老人今日安心日报

    子女端核心接口 — 展示老人今日综合状态
    """
    _check_elder_access(elder_id, current_user, db)
    report = daily_report_service.generate_report(db, elder_id)
    return report.to_dict()


@router.get("/history/{elder_id}")
async def get_report_history(
    elder_id: int,
    days: int = Query(default=7, ge=1, le=30),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取历史日报列表

    支持查看最近1-30天的日报
    """
    _check_elder_access(elder_id, current_user, db)

    reports = []
    today = date.today()

    for i in range(days):
        report_date = today - timedelta(days=i)
        try:
            report = daily_report_service.generate_report(db, elder_id, report_date)
            reports.append({
                "date": report.report_date,
                "anxin_score": report.anxin_score,
                "anxin_level": report.anxin_level,
                "one_line_summary": report.one_line_summary,
                "emotion": report.emotion.dominant_emotion,
                "health_status": report.health.overall_status,
            })
        except Exception:
            continue

    return {
        "elder_id": elder_id,
        "total": len(reports),
        "reports": reports,
    }


@router.get("/anxin-score/{elder_id}")
async def get_anxin_score_trend(
    elder_id: int,
    days: int = Query(default=7, ge=1, le=30),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取安心指数趋势

    用于子女端的安心指数折线图
    """
    _check_elder_access(elder_id, current_user, db)

    scores = []
    today = date.today()

    for i in range(days):
        report_date = today - timedelta(days=i)
        try:
            report = daily_report_service.generate_report(db, elder_id, report_date)
            scores.append({
                "date": report.report_date,
                "score": report.anxin_score,
                "level": report.anxin_level,
            })
        except Exception:
            continue

    return {
        "elder_id": elder_id,
        "trend": list(reversed(scores)),  # 按时间正序
    }


@router.get("/summary/{elder_id}")
async def get_dashboard_summary(
    elder_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取子女首页安心中心聚合数据。
    """
    _check_elder_access(elder_id, current_user, db)

    from app.models.database import Notification as NotificationModel, UserAuth

    report = daily_report_service.generate_report(db, elder_id)
    report_data = report.to_dict()
    generated_at = report_data["generated_at"]

    family_id: Optional[int] = None
    if current_user.role == "family":
        family_id = int(current_user.user_id)
    else:
        elder_auth = db.query(UserAuth).filter(UserAuth.user_id == elder_id).first()
        if elder_auth:
            family_member_auth = db.query(UserAuth).filter(UserAuth.family_id.isnot(None)).first()
            if family_member_auth:
                family_id = family_member_auth.id

    notifications: list[dict] = []
    if family_id:
        rows = db.query(NotificationModel).filter(
            NotificationModel.user_id == family_id,
            NotificationModel.is_deleted == False,
        ).order_by(NotificationModel.created_at.desc()).limit(10).all()
        for row in rows:
            meta = {}
            if row.data:
                try:
                    meta = json.loads(row.data)
                except json.JSONDecodeError:
                    meta = {}
            source_user_id = meta.get("source_user_id")
            if source_user_id and str(source_user_id) != str(elder_id):
                continue
            notifications.append({
                "id": str(row.id),
                "title": row.title,
                "content": row.content or "",
                "risk_score": int(meta.get("risk_score", 5)),
                "category": str(meta.get("category", "health")),
                "is_read": row.is_read,
                "is_handled": bool(meta.get("is_handled", False)),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })

    alerts = _build_alerts(report, notifications, generated_at)
    timeline = _build_timeline(report)
    empty_state = _build_empty_state(report, alerts, timeline)
    score_trend = 0

    return {
        "elder": {
            "id": elder_id,
            "name": report.user_name,
        },
        "overview": {
            "score": report.anxin_score,
            "score_trend": score_trend,
            "status": "alert" if report.anxin_score <= 4 else "attention" if report.anxin_score <= 7 else "stable",
            "summary": report.one_line_summary,
            "health_status": report.health.overall_status,
            "emotion_status": report.emotion.dominant_emotion,
            "medication_status": "taken" if report.health.medication_taken else "pending",
            "generated_at": generated_at,
        },
        "alerts": alerts,
        "timeline": timeline,
        "recommended_actions": report.tips_for_children[:3],
        "empty_state": empty_state,
        "report": report.to_dict(),
    }


@router.get("/share/{elder_id}")
async def get_daily_report_share_payload(
    elder_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取适合家属分享的今日日报摘要文案

    用于前端生成分享卡片、复制文案和邀请家人联动。
    """
    _check_elder_access(elder_id, current_user, db)
    report = daily_report_service.generate_report(db, elder_id)

    health_summary = report.health.overall_status or "状态平稳"
    top_tip = report.tips_for_children[0] if report.tips_for_children else "有空记得联系一下爸妈。"
    quote = report.conversation.key_quotes[0] if report.conversation.key_quotes else "今天陪伴交流平稳。"

    import secrets

    from app.models.database import User, UserAuth
    from app.services.family_service import (
        FamilyRole,
        PermissionLevel,
        family_service,
    )

    invite_code = secrets.token_hex(4).upper()

    elder_auth = db.query(UserAuth).filter(UserAuth.user_id == elder_id).first()
    if elder_auth:
        groups = family_service.get_user_family_groups(elder_auth.id)
        group = next((item for item in groups if item.elder_id == elder_auth.id), None)
        if not group:
            elder = db.query(User).filter(User.id == elder_id).first()
            group = family_service.create_family_group(
                elder_id=elder_auth.id,
                elder_name=elder.name if elder else report.user_name,
                group_name=f"{report.user_name}的家庭",
                creator_id=elder_auth.id,
            )

        requester_id = int(current_user.user_id) if str(current_user.user_id).isdigit() else elder_auth.id
        binding_request = family_service.create_binding_request(
            group_id=group.group_id,
            requester_id=requester_id,
            requester_name=f"用户{current_user.user_id}",
            target_id=0,
            relationship="家人",
            role=FamilyRole.GUARDIAN,
            permission_level=PermissionLevel.STANDARD,
        )
        _persist_share_invite(binding_request, db)
        invite_code = binding_request.invite_code

    share_title = f"今日爸妈 · {report.user_name}的安心日报"
    share_text = (
        f"{report.user_name}今天安心指数 {report.anxin_score} 分（{report.anxin_level}）。"
        f"{report.one_line_summary} 健康状态：{health_summary}。"
        f"我最想记住的一句话：{quote} 给家人的建议：{top_tip}"
    )

    return {
        "elder_id": elder_id,
        "elder_name": report.user_name,
        "share_title": share_title,
        "share_text": share_text,
        "one_line_summary": report.one_line_summary,
        "anxin_score": report.anxin_score,
        "anxin_level": report.anxin_level,
        "top_tip": top_tip,
        "quote": quote,
        "health_status": health_summary,
        "report_date": report.report_date,
        "invite_code": invite_code,
        "invite_expires_in_days": 7,
        "report": {
            "anxin_score": report.anxin_score,
            "anxin_level": report.anxin_level,
            "one_line_summary": report.one_line_summary,
            "health_status": health_summary,
            "top_tip": top_tip,
            "quote": quote,
            "report_date": report.report_date,
        },
    }
