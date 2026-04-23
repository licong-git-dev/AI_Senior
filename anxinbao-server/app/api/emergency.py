"""
API路由 - 紧急服务
实现SOS触发、跌倒检测、紧急联系人管理、告警处理等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from app.core.deps import get_db
from app.core.security import get_current_user, UserInfo
from app.models.database import (
    DeviceAuth,
    EmergencyEvent as EmergencyEventModel,
    EmergencyNotification as EmergencyNotificationModel,
    EmergencyContact as EmergencyContactModel,
    FamilyMember,
    User,
    UserAuth
)
from app.services.sms_service import sms_service
from app.services.notification_service import notification_service
from app.core.limiter import limiter
from app.api.notify import create_family_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emergency", tags=["紧急服务"])


# ========== 请求模型 ==========

class CreateContactRequest(BaseModel):
    """创建紧急联系人请求"""
    name: str = Field(..., description="联系人姓名")
    phone: str = Field(..., description="电话号码")
    relationship: Optional[str] = Field(None, description="关系")
    is_primary: bool = Field(default=False, description="是否主要联系人")


class UpdateContactRequest(BaseModel):
    """更新紧急联系人请求"""
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    is_primary: Optional[bool] = None
    notification_enabled: Optional[bool] = None
    notify_order: Optional[int] = None


class TriggerSOSRequest(BaseModel):
    """触发SOS请求"""
    description: Optional[str] = Field("紧急求助", description="求助描述")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None


class TriggerFallAlertRequest(BaseModel):
    """触发跌倒告警请求"""
    confidence: float = Field(0.8, ge=0, le=1, description="检测置信度")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_id: Optional[str] = None


class TriggerHealthAlertRequest(BaseModel):
    """触发健康异常告警请求"""
    systolic: Optional[int] = Field(None, description="收缩压")
    diastolic: Optional[int] = Field(None, description="舒张压")
    heart_rate: Optional[int] = Field(None, description="心率")
    blood_glucose: Optional[float] = Field(None, description="血糖")
    blood_oxygen: Optional[int] = Field(None, description="血氧")


class HandleAlertRequest(BaseModel):
    """处理告警请求"""
    handler: str = Field(..., description="处理人")
    notes: Optional[str] = Field(None, description="处理备注")


# ========== 工具函数 ==========

def _check_user_access(elder_user_id: int, current_user: UserInfo, db: Session):
    """验证当前用户是否有权限访问指定老人（User.id）的紧急数据"""
    if current_user.role == 'admin':
        return  # 管理员可访问所有数据

    if current_user.role == 'device':
        raise HTTPException(status_code=403, detail='设备无权执行该操作')

    auth = db.query(UserAuth).filter(UserAuth.id == int(current_user.user_id)).first()
    if not auth:
        raise HTTPException(status_code=403, detail="无权限")

    if current_user.role == 'elder':
        if auth.user_id != elder_user_id:
            raise HTTPException(status_code=403, detail="无权限访问他人数据")

    elif current_user.role == 'family':
        if not auth.family_id:
            raise HTTPException(status_code=403, detail="尚未绑定老人")
        family_member = db.query(FamilyMember).filter(
            FamilyMember.id == auth.family_id
        ).first()
        if not family_member or family_member.user_id != elder_user_id:
            raise HTTPException(status_code=403, detail="无权限访问该老人数据")


def _check_device_trigger_access(elder_user_id: int, current_user: UserInfo, db: Session):
    """仅允许设备对已绑定老人触发设备侧告警。"""
    if current_user.role != 'device':
        _check_user_access(elder_user_id, current_user, db)
        return

    device_auth = db.query(DeviceAuth).filter(DeviceAuth.id == int(current_user.user_id)).first()
    if not device_auth or device_auth.user_id != elder_user_id:
        raise HTTPException(status_code=403, detail='无权限访问该老人数据')


def get_severity_from_type(emergency_type: str) -> str:
    """根据紧急类型确定严重程度"""
    severity_map = {
        'sos': 'critical',
        'fall': 'critical',
        'health_crisis': 'high',
        'distress': 'high',
        'location_alert': 'medium',
        'device_alert': 'medium'
    }
    return severity_map.get(emergency_type, 'high')


async def send_notifications(db: Session, event: EmergencyEventModel, contacts: List[EmergencyContactModel]):
    """发送紧急通知给联系人，并同步写入家属通知中心。"""
    elder = db.query(User).filter(User.id == event.user_id).first()
    elder_name = elder.name if elder else f'用户{event.user_id}'

    for contact in contacts:
        notification = EmergencyNotificationModel(
            event_id=event.id,
            contact_id=contact.id,
            contact_name=contact.name,
            contact_phone=contact.phone,
            notification_method='push',
            status='sent',
            sent_at=datetime.now()
        )
        db.add(notification)

    family_auths = (
        db.query(UserAuth)
        .join(FamilyMember, UserAuth.family_id == FamilyMember.id)
        .filter(FamilyMember.user_id == event.user_id)
        .all()
    )
    for family_auth in family_auths:
        title = '紧急求助通知' if event.emergency_type == 'sos' else '健康异常通知' if event.emergency_type == 'health_crisis' else '紧急告警通知'
        content = f'{elder_name}：{event.description}'
        create_family_notification(
            db=db,
            user_id=str(event.user_id),
            family_id=str(family_auth.id),
            title=title,
            content=content,
            risk_score=10 if event.severity == 'critical' else 8,
            category='emergency' if event.emergency_type in {'sos', 'fall'} else 'health'
        )

    event.status = 'notifying'
    db.commit()

    try:
        phone_numbers = [contact.phone for contact in contacts]
        location_address = event.address or ""
        await sms_service.send_emergency_alert(
            phone_numbers=phone_numbers,
            user_name=elder_name,
            phone="",
            location_address=location_address
        )
    except Exception as e:
        logger.error(f"Failed to send SMS emergency alert: {e}")

    try:
        await notification_service.send_notification(
            user_id=event.user_id,
            template="EMERGENCY",
            event=event
        )
    except Exception as e:
        logger.error(f"Failed to send notification via notification_service: {e}")


# ========== 紧急联系人管理 ==========

@router.post("/contacts", response_model=dict)
async def create_contact(
    user_id: str,
    request: CreateContactRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """添加紧急联系人"""
    _check_user_access(int(user_id), current_user, db)
    # 获取当前最大通知顺序
    max_order = db.query(func.max(EmergencyContactModel.notify_order)).filter(
        EmergencyContactModel.user_id == int(user_id)
    ).scalar() or 0

    contact = EmergencyContactModel(
        user_id=int(user_id),
        name=request.name,
        phone=request.phone,
        relation_type=request.relationship,
        is_primary=request.is_primary,
        notify_order=max_order + 1,
        notification_enabled=True
    )

    # 如果设为主要联系人，取消其他主要联系人
    if request.is_primary:
        db.query(EmergencyContactModel).filter(
            EmergencyContactModel.user_id == int(user_id),
            EmergencyContactModel.is_primary == True
        ).update({'is_primary': False})

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return {
        'success': True,
        'contact_id': str(contact.id),
        'message': f"紧急联系人 {request.name} 已添加"
    }


@router.get("/contacts/{user_id}", response_model=dict)
async def get_contacts(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取紧急联系人列表"""
    _check_user_access(int(user_id), current_user, db)
    contacts = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.user_id == int(user_id)
    ).order_by(
        EmergencyContactModel.is_primary.desc(),
        EmergencyContactModel.notify_order
    ).all()

    return {
        'user_id': user_id,
        'contacts': [
            {
                'id': str(c.id),
                'name': c.name,
                'phone': c.phone,
                "relationship": c.relation_type,
                'is_primary': c.is_primary,
                "notify_order": c.notify_order,
                "notification_enabled": c.notification_enabled
            }
            for c in contacts
        ],
        'count': len(contacts)
    }


@router.put("/contacts/{contact_id}", response_model=dict)
async def update_contact(
    contact_id: str,
    request: UpdateContactRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """更新紧急联系人"""
    contact = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.id == int(contact_id)
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail='联系人不存在')

    _check_user_access(contact.user_id, current_user, db)

    if request.name is not None:
        contact.name = request.name
    if request.phone is not None:
        contact.phone = request.phone
    if request.relationship is not None:
        contact.relation_type = request.relationship
    if request.notification_enabled is not None:
        contact.notification_enabled = request.notification_enabled
    if request.notify_order is not None:
        contact.notify_order = request.notify_order

    if request.is_primary is True:
        # 取消其他主要联系人
        db.query(EmergencyContactModel).filter(
            EmergencyContactModel.user_id == contact.user_id,
            EmergencyContactModel.id != contact.id,
            EmergencyContactModel.is_primary == True
        ).update({'is_primary': False})
        contact.is_primary = True
    elif request.is_primary is False:
        contact.is_primary = False

    db.commit()

    return {
        'success': True,
        'message': '联系人信息已更新'
    }


@router.delete("/contacts/{contact_id}", response_model=dict)
async def delete_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """删除紧急联系人"""
    contact = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.id == int(contact_id)
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail='联系人不存在')

    _check_user_access(contact.user_id, current_user, db)

    db.delete(contact)
    db.commit()

    return {
        'success': True,
        'message': '联系人已删除'
    }


# ========== SOS触发 ==========

@router.post("/sos", response_model=dict)
@limiter.limit("10/minute")
async def trigger_sos(
    request: Request,
    user_id: str,
    body: TriggerSOSRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    触发SOS紧急求助

    这将立即：
    1. 创建危急级别事件
    2. 通知所有紧急联系人
    3. 记录位置信息
    """
    _check_device_trigger_access(int(user_id), current_user, db)
    # 创建紧急事件
    event = EmergencyEventModel(
        user_id=int(user_id),
        emergency_type='sos',
        severity='critical',
        description=body.description,
        latitude=body.latitude,
        longitude=body.longitude,
        address=body.address,
        trigger_source='manual',
        status='triggered',
        triggered_at=datetime.now()
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # 获取紧急联系人
    contacts = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.user_id == int(user_id),
        EmergencyContactModel.notification_enabled == True
    ).order_by(
        EmergencyContactModel.notify_order
    ).all()

    # 发送通知
    await send_notifications(db, event, contacts)

    return {
        'success': True,
        'event_id': str(event.id),
        'status': event.status,
        "notified_contacts": len(contacts),
        'message': "紧急求助已发送，正在通知您的家人！"
    }


@router.post("/fall-alert", response_model=dict)
async def trigger_fall_alert(
    user_id: str,
    request: TriggerFallAlertRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    触发跌倒告警

    通常由设备自动检测后触发
    """
    _check_device_trigger_access(int(user_id), current_user, db)
    event = EmergencyEventModel(
        user_id=int(user_id),
        emergency_type='fall',
        severity='critical',
        description=f'检测到跌倒，置信度: {request.confidence:.0%}',
        latitude=request.latitude,
        longitude=request.longitude,
        trigger_source='fall_detection',
        device_id=request.device_id,
        status='triggered',
        triggered_at=datetime.now()
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # 获取紧急联系人
    contacts = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.user_id == int(user_id),
        EmergencyContactModel.notification_enabled == True
    ).order_by(
        EmergencyContactModel.notify_order
    ).all()

    # 发送通知
    await send_notifications(db, event, contacts)

    return {
        'success': True,
        'event_id': str(event.id),
        'emergency_type': 'fall',
        'severity': 'critical',
        'notified_contacts': len(contacts),
        'message': '跌倒告警已发送'
    }


@router.post("/health-alert", response_model=dict)
async def trigger_health_alert(
    user_id: str,
    request: TriggerHealthAlertRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """触发健康异常告警"""
    _check_device_trigger_access(int(user_id), current_user, db)
    # 构建描述
    descriptions = []
    severity = "high"

    if request.systolic and request.diastolic:
        if request.systolic >= 180 or request.diastolic >= 120:
            severity = 'critical'
            descriptions.append(f'血压危急: {request.systolic}/{request.diastolic} mmHg')
        elif request.systolic >= 140 or request.diastolic >= 90:
            descriptions.append(f'血压偏高: {request.systolic}/{request.diastolic} mmHg')

    if request.heart_rate:
        if request.heart_rate > 150 or request.heart_rate < 40:
            severity = 'critical'
            descriptions.append(f'心率异常: {request.heart_rate} bpm')
        elif request.heart_rate > 100 or request.heart_rate < 50:
            descriptions.append(f'心率偏离正常: {request.heart_rate} bpm')

    if request.blood_glucose:
        if request.blood_glucose >= 16.7 or request.blood_glucose < 3.0:
            severity = 'critical'
            descriptions.append(f'血糖危险: {request.blood_glucose} mmol/L')
        elif request.blood_glucose >= 11.1:
            descriptions.append(f'血糖偏高: {request.blood_glucose} mmol/L')

    if request.blood_oxygen:
        if request.blood_oxygen < 90:
            severity = 'critical'
            descriptions.append(f'血氧危险: {request.blood_oxygen}%')
        elif request.blood_oxygen < 94:
            descriptions.append(f'血氧偏低: {request.blood_oxygen}%')

    if not descriptions:
        raise HTTPException(status_code=400, detail='未检测到异常健康指标')

    description = '健康异常: ' + '; '.join(descriptions)

    event = EmergencyEventModel(
        user_id=int(user_id),
        emergency_type="health_crisis",
        severity=severity,
        description=description,
        trigger_source="health_alert",
        status='triggered',
        triggered_at=datetime.now()
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # 获取紧急联系人
    contacts = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.user_id == int(user_id),
        EmergencyContactModel.notification_enabled == True
    ).order_by(
        EmergencyContactModel.notify_order
    ).all()

    # 发送通知
    await send_notifications(db, event, contacts)

    return {
        'success': True,
        'event_id': str(event.id),
        'emergency_type': 'health_crisis',
        'severity': severity,
        "description": description,
        "notified_contacts": len(contacts)
    }


# ========== 告警管理 ==========

@router.get("/events/{user_id}", response_model=dict)
async def get_emergency_events(
    user_id: str,
    status: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取紧急事件列表"""
    _check_user_access(int(user_id), current_user, db)
    cutoff = datetime.now() - timedelta(days=days)

    query = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.user_id == int(user_id),
        EmergencyEventModel.triggered_at > cutoff
    )

    if status:
        query = query.filter(EmergencyEventModel.status == status)

    total = query.count()
    events = query.order_by(
        EmergencyEventModel.triggered_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        'user_id': user_id,
        'total': total,
        'events': [
            {
                'id': str(e.id),
                "emergency_type": e.emergency_type,
                'severity': e.severity,
                "description": e.description,
                'status': e.status,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'address': e.address,
                "trigger_source": e.trigger_source,
                "triggered_at": e.triggered_at.isoformat(),
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
                "resolved_by": e.resolved_by,
                "resolution_notes": e.resolution_notes,
                "is_false_alarm": e.is_false_alarm,
                "response_time_seconds": e.response_time_seconds
            }
            for e in events
        ]
    }


@router.get("/events/active/{user_id}", response_model=dict)
async def get_active_events(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取活跃的紧急事件"""
    _check_user_access(int(user_id), current_user, db)
    events = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.user_id == int(user_id),
        EmergencyEventModel.status.in_(['triggered', 'notifying', 'responding'])
    ).order_by(
        EmergencyEventModel.triggered_at.desc()
    ).all()

    return {
        'user_id': user_id,
        "active_events": [
            {
                'id': str(e.id),
                "emergency_type": e.emergency_type,
                'severity': e.severity,
                "description": e.description,
                'status': e.status,
                "triggered_at": e.triggered_at.isoformat(),
                "duration_minutes": int((datetime.now() - e.triggered_at).total_seconds() / 60)
            }
            for e in events
        ],
        'count': len(events)
    }


@router.get("/event/{event_id}", response_model=dict)
async def get_event_detail(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取紧急事件详情"""
    event = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.id == int(event_id)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail='事件不存在')

    _check_user_access(event.user_id, current_user, db)

    # 获取通知记录
    notifications = db.query(EmergencyNotificationModel).filter(
        EmergencyNotificationModel.event_id == event.id
    ).all()

    return {
        'id': str(event.id),
        'user_id': str(event.user_id),
        "emergency_type": event.emergency_type,
        'severity': event.severity,
        "description": event.description,
        'status': event.status,
        'latitude': event.latitude,
        'longitude': event.longitude,
        'address': event.address,
        "trigger_source": event.trigger_source,
        'device_id': event.device_id,
        "triggered_at": event.triggered_at.isoformat(),
        "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
        "resolved_by": event.resolved_by,
        "resolution_notes": event.resolution_notes,
        "is_false_alarm": event.is_false_alarm,
        "first_response_at": event.first_response_at.isoformat() if event.first_response_at else None,
        "response_time_seconds": event.response_time_seconds,
        "notifications": [
            {
                'id': str(n.id),
                "contact_name": n.contact_name,
                "contact_phone": n.contact_phone,
                'method': n.notification_method,
                'status': n.status,
                'sent_at': n.sent_at.isoformat() if n.sent_at else None,
                "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
                "response_at": n.response_at.isoformat() if n.response_at else None
            }
            for n in notifications
        ]
    }


@router.post("/event/{event_id}/acknowledge", response_model=dict)
async def acknowledge_event(
    event_id: str,
    request: HandleAlertRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """确认事件（表示已收到并正在处理）"""
    event = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.id == int(event_id)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail='事件不存在')

    _check_user_access(event.user_id, current_user, db)

    if event.status in ['resolved', 'cancelled', "false_alarm"]:
        raise HTTPException(status_code=400, detail='事件已结束')

    event.status = 'responding'
    if not event.first_response_at:
        event.first_response_at = datetime.now()
        event.response_time_seconds = int((event.first_response_at - event.triggered_at).total_seconds())

    db.commit()

    return {
        'success': True,
        'message': '已确认事件',
        "response_time_seconds": event.response_time_seconds
    }


@router.post("/event/{event_id}/resolve", response_model=dict)
async def resolve_event(
    event_id: str,
    request: HandleAlertRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """解决事件"""
    event = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.id == int(event_id)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail='事件不存在')

    _check_user_access(event.user_id, current_user, db)

    event.status = 'resolved'
    event.resolved_at = datetime.now()
    event.resolved_by = request.handler
    event.resolution_notes = request.notes

    if not event.first_response_at:
        event.first_response_at = datetime.now()
        event.response_time_seconds = int((event.first_response_at - event.triggered_at).total_seconds())

    db.commit()

    return {
        'success': True,
        'message': '事件已解决'
    }


@router.post("/event/{event_id}/cancel", response_model=dict)
async def cancel_event(
    event_id: str,
    reason: str = Query('用户取消', description='取消原因'),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """取消事件"""
    event = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.id == int(event_id)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail='事件不存在')

    _check_user_access(event.user_id, current_user, db)

    event.status = 'cancelled'
    event.resolved_at = datetime.now()
    event.resolution_notes = reason

    db.commit()

    return {
        'success': True,
        'message': '事件已取消'
    }


@router.post("/event/{event_id}/false-alarm", response_model=dict)
async def mark_false_alarm(
    event_id: str,
    reason: str = Query('误报', description='误报原因'),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """标记为误报"""
    event = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.id == int(event_id)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail='事件不存在')

    _check_user_access(event.user_id, current_user, db)

    event.status = 'false_alarm'
    event.is_false_alarm = True
    event.resolved_at = datetime.now()
    event.resolution_notes = reason

    db.commit()

    return {
        'success': True,
        'message': '已标记为误报'
    }


# ========== 快捷操作 ==========

@router.post("/quick-sos/{user_id}", response_model=dict)
async def quick_sos(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """一键SOS（最简化的紧急求助）"""
    _check_user_access(int(user_id), current_user, db)
    event = EmergencyEventModel(
        user_id=int(user_id),
        emergency_type='sos',
        severity='critical',
        description='一键紧急求助',
        trigger_source='manual',
        status='triggered',
        triggered_at=datetime.now()
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # 获取紧急联系人
    contacts = db.query(EmergencyContactModel).filter(
        EmergencyContactModel.user_id == int(user_id),
        EmergencyContactModel.notification_enabled == True
    ).order_by(
        EmergencyContactModel.notify_order
    ).all()

    # 发送通知
    await send_notifications(db, event, contacts)

    return {
        'success': True,
        'event_id': str(event.id),
        'message': '紧急求助已发送，正在通知您的家人！',
        'notified_contacts': len(contacts)
    }


@router.post("/i-am-safe/{user_id}", response_model=dict)
async def report_safe(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """报平安 - 取消所有活跃的事件"""
    _check_user_access(int(user_id), current_user, db)
    active_events = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.user_id == int(user_id),
        EmergencyEventModel.status.in_(['triggered', 'notifying', 'responding'])
    ).all()

    cancelled_count = 0
    for event in active_events:
        event.status = 'cancelled'
        event.resolved_at = datetime.now()
        event.resolution_notes = '用户报平安'
        cancelled_count += 1

    db.commit()

    return {
        'success': True,
        'message': '已报平安！' if cancelled_count > 0 else '当前没有活跃事件',
        "cancelled_events": cancelled_count
    }


# ========== 统计 ==========

@router.get("/statistics/{user_id}", response_model=dict)
async def get_statistics(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取紧急事件统计"""
    _check_user_access(int(user_id), current_user, db)
    cutoff = datetime.now() - timedelta(days=days)

    events = db.query(EmergencyEventModel).filter(
        EmergencyEventModel.user_id == int(user_id),
        EmergencyEventModel.triggered_at > cutoff
    ).all()

    total = len(events)
    by_type = {}
    by_severity = {}
    false_alarm_count = 0
    resolved_count = 0
    avg_response_time = None

    response_times = []
    for e in events:
        by_type[e.emergency_type] = by_type.get(e.emergency_type, 0) + 1
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1

        if e.is_false_alarm:
            false_alarm_count += 1
        if e.status == 'resolved':
            resolved_count += 1
        if e.response_time_seconds:
            response_times.append(e.response_time_seconds)

    if response_times:
        avg_response_time = sum(response_times) / len(response_times)

    return {
        'user_id': user_id,
        "period_days": days,
        "total_events": total,
        'by_type': by_type,
        "by_severity": by_severity,
        "resolved_count": resolved_count,
        "false_alarm_count": false_alarm_count,
        "false_alarm_rate": round(false_alarm_count / total * 100, 1) if total > 0 else 0,
        "average_response_time_seconds": round(avg_response_time) if avg_response_time else None
    }
