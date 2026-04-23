"""
API路由 - 通知和推送
处理子女端通知
"""
from datetime import datetime
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import UserInfo, get_current_user
from app.models.database import Notification as NotificationModel

router = APIRouter(prefix="/api/notify", tags=["通知"])


class Notification(BaseModel):
    """通知模型"""
    id: str
    user_id: str  # 老人ID
    family_id: str  # 家属认证ID
    title: str
    content: str
    risk_score: int
    category: str  # health/emergency/reminder
    is_read: bool = False
    is_handled: bool = False
    created_at: str


class NotificationCreate(BaseModel):
    """创建通知请求"""
    user_id: str
    family_id: str
    title: str
    content: str
    risk_score: int = 5
    category: str = "health"


def _check_family_access(family_id: str, current_user: UserInfo) -> None:
    if current_user.role == "admin":
        return
    if current_user.role != "family" or family_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该通知列表")


def _serialize_meta(notification: NotificationModel) -> dict:
    if not notification.data:
        return {}
    try:
        return json.loads(notification.data)
    except json.JSONDecodeError:
        return {}


def _deserialize_meta(data: Optional[dict]) -> str:
    return json.dumps(data or {}, ensure_ascii=False)


def _to_response(notification: NotificationModel) -> Notification:
    meta = _serialize_meta(notification)
    return Notification(
        id=str(notification.id),
        user_id=str(meta.get("source_user_id", "")),
        family_id=str(notification.user_id),
        title=notification.title,
        content=notification.content or "",
        risk_score=int(meta.get("risk_score", 5)),
        category=str(meta.get("category", "health")),
        is_read=notification.is_read,
        is_handled=bool(meta.get("is_handled", False)),
        created_at=notification.created_at.isoformat() if notification.created_at else datetime.now().isoformat(),
    )


def create_family_notification(
    *,
    db: Session,
    user_id: str,
    family_id: str,
    title: str,
    content: str,
    risk_score: int = 5,
    category: str = "health",
) -> Notification:
    type_map = {
        "health": "health_alert",
        "emergency": "emergency",
        "reminder": "system",
    }
    priority = "urgent" if risk_score >= 9 else "high" if risk_score >= 7 else "normal"
    record = NotificationModel(
        user_id=int(family_id),
        notification_type=type_map.get(category, "system"),
        priority=priority,
        title=title,
        content=content,
        data=_deserialize_meta({
            "source_user_id": user_id,
            "risk_score": risk_score,
            "category": category,
            "is_handled": False,
        }),
        is_read=False,
        is_deleted=False,
        created_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_response(record)


@router.post("/create")
async def create_notification(
    request: NotificationCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新通知（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可创建通知")

    notification = create_family_notification(
        db=db,
        user_id=request.user_id,
        family_id=request.family_id,
        title=request.title,
        content=request.content,
        risk_score=request.risk_score,
        category=request.category,
    )

    return {
        "success": True,
        "notification_id": notification.id,
        "message": "通知已发送",
    }


@router.get("/list/{family_id}")
async def get_notifications(
    family_id: str,
    unread_only: bool = False,
    limit: int = 20,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取家属的通知列表"""
    _check_family_access(family_id, current_user)

    query = db.query(NotificationModel).filter(
        NotificationModel.user_id == int(family_id),
        NotificationModel.is_deleted == False,
    )
    if unread_only:
        query = query.filter(NotificationModel.is_read == False)

    notifications = query.order_by(NotificationModel.created_at.desc()).limit(limit).all()
    unread_count = db.query(NotificationModel).filter(
        NotificationModel.user_id == int(family_id),
        NotificationModel.is_deleted == False,
        NotificationModel.is_read == False,
    ).count()

    return {
        "family_id": family_id,
        "notifications": [_to_response(item).model_dump() for item in notifications],
        "unread_count": unread_count,
    }


@router.put("/read/{notification_id}")
async def mark_as_read(
    notification_id: str,
    family_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记通知为已读"""
    _check_family_access(family_id, current_user)
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == int(notification_id),
        NotificationModel.user_id == int(family_id),
        NotificationModel.is_deleted == False,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()
    return {"success": True, "message": "已标记为已读"}


@router.put("/handle/{notification_id}")
async def mark_as_handled(
    notification_id: str,
    family_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记通知为已处理"""
    _check_family_access(family_id, current_user)
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == int(notification_id),
        NotificationModel.user_id == int(family_id),
        NotificationModel.is_deleted == False,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    meta = _serialize_meta(notification)
    meta["is_handled"] = True
    notification.data = _deserialize_meta(meta)
    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()
    return {"success": True, "message": "已标记为已处理"}


@router.delete("/clear/{family_id}")
async def clear_notifications(
    family_id: str,
    handled_only: bool = True,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清除通知"""
    _check_family_access(family_id, current_user)

    notifications = db.query(NotificationModel).filter(
        NotificationModel.user_id == int(family_id),
        NotificationModel.is_deleted == False,
    ).all()
    for notification in notifications:
        meta = _serialize_meta(notification)
        if handled_only and not meta.get("is_handled", False):
            continue
        notification.is_deleted = True
    db.commit()

    return {"success": True, "message": "通知已清除"}


@router.get("/stats/{family_id}")
async def get_notification_stats(
    family_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取通知统计"""
    _check_family_access(family_id, current_user)
    notifications = db.query(NotificationModel).filter(
        NotificationModel.user_id == int(family_id),
        NotificationModel.is_deleted == False,
    ).all()
    responses = [_to_response(item) for item in notifications]

    return {
        "family_id": family_id,
        "total": len(responses),
        "unread": sum(1 for n in responses if not n.is_read),
        "unhandled": sum(1 for n in responses if not n.is_handled),
        "high_risk": sum(1 for n in responses if n.risk_score >= 7),
        "by_category": {
            "health": sum(1 for n in responses if n.category == "health"),
            "emergency": sum(1 for n in responses if n.category == "emergency"),
            "reminder": sum(1 for n in responses if n.category == "reminder"),
        },
    }
