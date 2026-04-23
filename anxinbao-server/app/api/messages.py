"""
消息中心API
提供消息查询、管理、偏好设置等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.message_center_service import (
    message_center,
    message_template,
    MessageType,
    MessagePriority,
    MessageStatus,
    MessageAction,
    DeliveryChannel
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/messages", tags=["消息中心"])


# ==================== 请求/响应模型 ====================

class MessageActionModel(BaseModel):
    """消息操作模型"""
    action_id: str
    label: str
    action_type: str = Field(..., description="操作类型: link/api/dismiss")
    payload: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message_type: str = Field(..., description='消息类型')
    title: str = Field(..., min_length=1, max_length=100, description='标题')
    content: str = Field(..., min_length=1, max_length=2000, description='内容')
    priority: int = Field(default=2, ge=1, le=5, description='优先级1-5')
    summary: Optional[str] = Field(None, max_length=100, description='摘要')
    icon: Optional[str] = Field(None, description='图标')
    image: Optional[str] = Field(None, description='图片URL')
    actions: Optional[List[MessageActionModel]] = Field(None, description='操作按钮')
    voice_content: Optional[str] = Field(None, description='语音播报内容')
    expires_in_hours: Optional[int] = Field(None, ge=1, le=720, description="过期时间（小时）")


class SendTemplateMessageRequest(BaseModel):
    """使用模板发送消息请求"""
    template_name: str = Field(..., description='模板名称')
    params: Dict[str, Any] = Field(default_factory=dict, description="模板参数")
    target_user_id: Optional[int] = Field(None, description="目标用户ID（管理员可指定）")


class PreferenceUpdateRequest(BaseModel):
    """偏好更新请求"""
    enabled_types: Optional[Dict[str, bool]] = Field(None, description='启用的消息类型')
    channels: Optional[Dict[str, bool]] = Field(None, description='启用的推送渠道')
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23, description='免打扰开始时间')
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23, description='免打扰结束时间')
    voice_enabled: Optional[bool] = Field(None, description='是否启用语音播报')
    voice_speed: Optional[float] = Field(None, ge=0.5, le=2.0, description="语音速度")


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    message_type: str
    priority: int
    priority_name: str
    title: str
    content: str
    summary: str
    icon: str
    status: str
    is_read: bool
    created_at: str
    time_ago: str


# ==================== 消息查询API ====================

@router.get("/")
async def get_messages(
    message_type: Optional[str] = Query(None, description="消息类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤: unread/read/archived"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="优先级过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    获取消息列表

    消息类型: system/emergency/health/reminder/social/family/activity/achievement/promotion
    """
    user_id = int(current_user['sub'])

    type_filter = None
    if message_type:
        try:
            type_filter = MessageType(message_type)
        except ValueError:
            pass

    status_filter = None
    if status:
        try:
            status_filter = MessageStatus(status)
        except ValueError:
            pass

    priority_filter = None
    if priority:
        try:
            priority_filter = MessagePriority(priority)
        except ValueError:
            pass

    messages = message_center.get_user_messages(
        user_id=user_id,
        message_type=type_filter,
        status=status_filter,
        priority=priority_filter,
        limit=limit,
        offset=offset
    )

    return {
        'messages': [m.to_dict() for m in messages],
        'count': len(messages),
        'offset': offset,
        'limit': limit
    }


@router.get("/unread")
async def get_unread_messages(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取未读消息
    """
    user_id = int(current_user['sub'])
    messages = message_center.get_unread_messages(user_id, limit)

    return {
        'messages': [m.to_dict() for m in messages],
        'count': len(messages)
    }


@router.get("/unread/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """
    获取未读消息数量统计
    """
    user_id = int(current_user['sub'])
    count = message_center.get_unread_count(user_id)
    return count


@router.get("/important")
async def get_important_messages(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取重要消息（高优先级未读消息）
    """
    user_id = int(current_user['sub'])
    messages = message_center.get_important_messages(user_id, limit)

    return {
        'messages': [m.to_dict() for m in messages],
        'count': len(messages)
    }


@router.get("/types")
async def get_message_types():
    """
    获取所有消息类型
    """
    types = [
        {'type': MessageType.SYSTEM.value, 'name': '系统通知', 'icon': 'info'},
        {'type': MessageType.EMERGENCY.value, 'name': '紧急警报', 'icon': 'warning'},
        {'type': MessageType.HEALTH.value, 'name': '健康提醒', 'icon': 'heart'},
        {'type': MessageType.REMINDER.value, 'name': '日常提醒', 'icon': 'bell'},
        {'type': MessageType.SOCIAL.value, 'name': '社交通知', 'icon': 'users'},
        {'type': MessageType.FAMILY.value, 'name': '家庭通知', 'icon': 'home'},
        {'type': MessageType.ACTIVITY.value, 'name': '活动通知', 'icon': 'calendar'},
        {'type': MessageType.ACHIEVEMENT.value, 'name': '成就通知', 'icon': 'trophy'},
        {'type': MessageType.PROMOTION.value, 'name': '推广信息', 'icon': 'gift'}
    ]
    return {"types": types}


@router.get("/{message_id}")
async def get_message(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取消息详情
    """
    user_id = int(current_user['sub'])
    message = message_center.get_message(message_id)

    if not message or message.user_id != user_id:
        raise HTTPException(status_code=404, detail="消息不存在")

    return message.to_dict()


# ==================== 消息操作API ====================

@router.post("/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    标记消息为已读
    """
    user_id = int(current_user['sub'])
    message = message_center.get_message(message_id)

    if not message or message.user_id != user_id:
        raise HTTPException(status_code=404, detail='消息不存在')

    message_center.mark_as_read(message_id)
    return {'success': True, 'message': '已标记为已读'}


@router.post('/read-all')
async def mark_all_as_read(
    message_type: Optional[str] = Query(None, description="消息类型"),
    current_user: dict = Depends(get_current_user)
):
    """
    标记所有消息为已读
    """
    user_id = int(current_user['sub'])

    type_filter = None
    if message_type:
        try:
            type_filter = MessageType(message_type)
        except ValueError:
            pass

    count = message_center.mark_all_as_read(user_id, type_filter)
    return {'success': True, "marked_count": count}


@router.post("/{message_id}/archive")
async def archive_message(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    归档消息
    """
    user_id = int(current_user['sub'])
    message = message_center.get_message(message_id)

    if not message or message.user_id != user_id:
        raise HTTPException(status_code=404, detail='消息不存在')

    message_center.archive_message(message_id)
    return {'success': True, 'message': "已归档"}


@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除消息
    """
    user_id = int(current_user['sub'])
    success = message_center.delete_message(message_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='消息不存在或无权删除')

    return {'success': True, 'message': '已删除'}


@router.post('/clear')
async def clear_messages(
    message_type: Optional[str] = Query(None, description='消息类型'),
    days_old: int = Query(30, ge=1, le=365, description="清理多少天前的消息"),
    current_user: dict = Depends(get_current_user)
):
    """
    清理旧消息
    """
    user_id = int(current_user['sub'])
    from datetime import datetime, timedelta

    type_filter = None
    if message_type:
        try:
            type_filter = MessageType(message_type)
        except ValueError:
            pass

    before_date = datetime.now() - timedelta(days=days_old)
    count = message_center.clear_messages(user_id, type_filter, before_date)

    return {'success': True, "cleared_count": count}


# ==================== 消息发送API ====================

@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发送消息给自己（主要用于测试）
    """
    user_id = int(current_user['sub'])

    try:
        msg_type = MessageType(request.message_type)
    except ValueError:
        valid_types = [t.value for t in MessageType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的消息类型，可选: {valid_types}"
        )

    actions = None
    if request.actions:
        actions = [
            MessageAction(
                action_id=a.action_id,
                label=a.label,
                action_type=a.action_type,
                payload=a.payload or {}
            ) for a in request.actions
        ]

    message = await message_center.send_message(
        user_id=user_id,
        message_type=msg_type,
        title=request.title,
        content=request.content,
        priority=MessagePriority(request.priority),
        summary=request.summary,
        icon=request.icon,
        actions=actions,
        voice_content=request.voice_content,
        expires_in_hours=request.expires_in_hours
    )

    return {
        'success': True,
        "message": message.to_dict()
    }


@router.post("/send-template")
async def send_template_message(
    request: SendTemplateMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    使用模板发送消息

    可用模板:
    - sos_alert: SOS警报
    - fall_alert: 跌倒警报
    - health_abnormal: 健康异常
    - medication_reminder: 服药提醒
    - new_friend_request: 好友请求
    - post_liked: 点赞通知
    - new_comment: 评论通知
    - family_binding_request: 家庭绑定请求
    - guardian_reminder: 监护人提醒
    - activity_reminder: 活动提醒
    - checkin_streak: 打卡成就
    - game_achievement: 游戏成就
    - system_update: 系统更新
    - device_offline: 设备离线
    """
    user_id = int(current_user['sub'])

    # 目标用户默认为自己
    target_id = request.target_user_id or user_id

    # 检查模板是否存在
    if request.template_name not in message_template.TEMPLATES:
        available = list(message_template.TEMPLATES.keys())
        raise HTTPException(
            status_code=400,
            detail=f'模板不存在，可用模板: {available}'
        )

    message = await message_template.send_from_template(
        user_id=target_id,
        template_name=request.template_name,
        params=request.params
    )

    if not message:
        raise HTTPException(status_code=500, detail='发送失败')

    return {
        'success': True,
        "message": message.to_dict()
    }


# ==================== 偏好设置API ====================

@router.get("/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    """
    获取消息偏好设置
    """
    user_id = int(current_user['sub'])
    pref = message_center.get_preference(user_id)

    return {
        "preferences": pref.to_dict(),
        "available_types": [t.value for t in MessageType],
        "available_channels": [c.value for c in DeliveryChannel]
    }


@router.put("/preferences")
async def update_preferences(
    request: PreferenceUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新消息偏好设置
    """
    user_id = int(current_user['sub'])

    pref = message_center.update_preference(
        user_id=user_id,
        enabled_types=request.enabled_types,
        channels=request.channels,
        quiet_hours_start=request.quiet_hours_start,
        quiet_hours_end=request.quiet_hours_end,
        voice_enabled=request.voice_enabled,
        voice_speed=request.voice_speed
    )

    return {
        'success': True,
        "preferences": pref.to_dict()
    }


@router.put("/preferences/quiet-hours")
async def set_quiet_hours(
    start: int = Query(..., ge=0, le=23, description='开始时间（0-23）'),
    end: int = Query(..., ge=0, le=23, description="结束时间（0-23）"),
    current_user: dict = Depends(get_current_user)
):
    """
    设置免打扰时间段
    """
    user_id = int(current_user['sub'])

    pref = message_center.update_preference(
        user_id=user_id,
        quiet_hours_start=start,
        quiet_hours_end=end
    )

    return {
        'success': True,
        "quiet_hours": {
            'start': start,
            'end': end
        }
    }


@router.delete("/preferences/quiet-hours")
async def disable_quiet_hours(current_user: dict = Depends(get_current_user)):
    """
    禁用免打扰
    """
    user_id = int(current_user['sub'])

    pref = message_center.get_preference(user_id)
    pref.quiet_hours_start = None
    pref.quiet_hours_end = None

    return {'success': True, 'message': '已禁用免打扰'}


# ==================== 快捷操作 ====================

@router.get("/summary")
async def get_message_summary(current_user: dict = Depends(get_current_user)):
    """
    获取消息概览

    适合首页展示的消息摘要
    """
    user_id = int(current_user['sub'])

    unread = message_center.get_unread_count(user_id)
    important = message_center.get_important_messages(user_id, limit=3)
    recent = message_center.get_user_messages(user_id, limit=5)

    return {
        'unread_count': unread['total'],
        'unread_by_type': unread['by_type'],
        "important_messages": [m.to_dict() for m in important],
        "recent_messages": [m.to_dict() for m in recent]
    }
