"""
API路由 - 主动交互系统
实现主动问候、智能提醒、行为模式学习等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import json
import random

from app.core.deps import get_db
from app.core.security import get_current_user, UserInfo
from app.models.database import (
    ProactiveGreeting,
    ProactiveReminder,
    UserBehaviorPattern,
    ProactiveInteractionLog,
    UserProfile,
    Medication,
    HealthRecord,
    User
)
from app.schemas.proactive import (
    GreetingType,
    ReminderType,
    TriggerType,
    InteractionType,
    ResponseType,
    ProactiveGreetingCreate,
    ProactiveGreetingUpdate,
    ProactiveGreetingResponse,
    ProactiveReminderCreate,
    ProactiveReminderUpdate,
    ProactiveReminderResponse,
    BehaviorPatternCreate,
    BehaviorPatternResponse,
    ProactiveInteractionLogCreate,
    ProactiveInteractionLogResponse,
    UpdateInteractionResponse,
    TriggerGreetingRequest,
    TriggerGreetingResponse,
    TriggerReminderRequest,
    TriggerReminderResponse,
    GenerateGreetingRequest,
    GenerateGreetingResponse
)

router = APIRouter(prefix="/api/proactive", tags=["主动交互"])


def _check_user_access(
    user_id: int,
    current_user: UserInfo,
    db: Session,
) -> None:
    """校验当前用户是否有权访问指定老人的主动交互数据。"""
    if current_user.role == "admin":
        return

    from app.models.database import UserAuth, FamilyMember, DeviceAuth

    auth = db.query(UserAuth).filter(UserAuth.id == int(current_user.user_id)).first()
    if current_user.role == "elder":
        if not auth or auth.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问该用户的主动问候")
        return

    if current_user.role == "family":
        if not auth or not auth.family_id:
            raise HTTPException(status_code=403, detail="家属账户未绑定老人")
        family = db.query(FamilyMember).filter(FamilyMember.id == auth.family_id).first()
        if not family or family.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问该用户的主动问候")
        return

    if current_user.role == "device":
        device = db.query(DeviceAuth).filter(DeviceAuth.id == int(current_user.user_id)).first()
        if not device or device.user_id != user_id:
            raise HTTPException(status_code=403, detail="设备未绑定该用户")
        return

    raise HTTPException(status_code=403, detail="权限不足")


# ==================== 工具函数 ====================

def parse_json_field(value: Optional[str]) -> Optional[List]:
    """解析JSON字段"""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def serialize_json(value) -> str:
    """序列化为JSON"""
    return json.dumps(value, ensure_ascii=False)


# ==================== 主动问候配置 ====================

@router.post("/greetings", response_model=dict)
def create_greeting_config(
    request: ProactiveGreetingCreate,
    db: Session = Depends(get_db)
):
    """创建主动问候配置"""
    # 检查用户是否存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    greeting = ProactiveGreeting(
        user_id=request.user_id,
        greeting_type=request.greeting_type.value,
        schedule_time=request.schedule_time,
        schedule_days=serialize_json(request.schedule_days),
        greeting_template=request.greeting_template,
        include_weather=request.include_weather,
        include_health_tip=request.include_health_tip,
        include_medication_reminder=request.include_medication_reminder,
        is_enabled=True
    )
    db.add(greeting)
    db.commit()
    db.refresh(greeting)

    return {
        "success": True,
        "greeting_id": greeting.id,
        'message': "主动问候配置创建成功"
    }


@router.get("/greetings/{user_id}", response_model=dict)
def get_greeting_configs(
    user_id: int,
    enabled_only: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """获取用户的主动问候配置列表"""
    query = db.query(ProactiveGreeting).filter(ProactiveGreeting.user_id == user_id)
    if enabled_only:
        query = query.filter(ProactiveGreeting.is_enabled == True)

    greetings = query.all()

    return {
        'user_id': user_id,
        'greetings': [
            {
                'id': g.id,
                "greeting_type": g.greeting_type,
                "schedule_time": g.schedule_time,
                "schedule_days": parse_json_field(g.schedule_days),
                "greeting_template": g.greeting_template,
                "include_weather": g.include_weather,
                "include_health_tip": g.include_health_tip,
                "include_medication_reminder": g.include_medication_reminder,
                'is_enabled': g.is_enabled,
                "last_triggered_at": g.last_triggered_at.isoformat() if g.last_triggered_at else None
            }
            for g in greetings
        ],
        'total': len(greetings)
    }


@router.put("/greetings/{greeting_id}", response_model=dict)
def update_greeting_config(
    greeting_id: int,
    request: ProactiveGreetingUpdate,
    db: Session = Depends(get_db)
):
    """更新主动问候配置"""
    greeting = db.query(ProactiveGreeting).filter(ProactiveGreeting.id == greeting_id).first()
    if not greeting:
        raise HTTPException(status_code=404, detail="问候配置不存在")

    update_data = request.model_dump(exclude_unset=True)
    if "schedule_days" in update_data and update_data["schedule_days"]:
        update_data["schedule_days"] = serialize_json(update_data["schedule_days"])

    for key, value in update_data.items():
        setattr(greeting, key, value)

    db.commit()
    return {'success': True, 'message': "更新成功"}


@router.delete("/greetings/{greeting_id}", response_model=dict)
def delete_greeting_config(
    greeting_id: int,
    db: Session = Depends(get_db)
):
    """删除主动问候配置"""
    greeting = db.query(ProactiveGreeting).filter(ProactiveGreeting.id == greeting_id).first()
    if not greeting:
        raise HTTPException(status_code=404, detail='问候配置不存在')

    db.delete(greeting)
    db.commit()
    return {'success': True, 'message': '删除成功'}


# ==================== 主动提醒配置 ====================

@router.post("/reminders", response_model=dict)
def create_reminder_config(
    request: ProactiveReminderCreate,
    db: Session = Depends(get_db)
):
    """创建主动提醒配置"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    reminder = ProactiveReminder(
        user_id=request.user_id,
        reminder_type=request.reminder_type.value,
        title=request.title,
        content=request.content,
        trigger_type=request.trigger_type.value,
        schedule_time=request.schedule_time,
        interval_minutes=request.interval_minutes,
        behavior_trigger=request.behavior_trigger,
        min_interval_minutes=request.min_interval_minutes,
        quiet_during_sleep=request.quiet_during_sleep,
        skip_if_interacted=request.skip_if_interacted,
        is_enabled=True
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return {
        "success": True,
        "reminder_id": reminder.id,
        'message': "主动提醒配置创建成功"
    }


@router.get("/reminders/{user_id}", response_model=dict)
def get_reminder_configs(
    user_id: int,
    reminder_type: Optional[str] = None,
    enabled_only: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """获取用户的主动提醒配置列表"""
    query = db.query(ProactiveReminder).filter(ProactiveReminder.user_id == user_id)
    if enabled_only:
        query = query.filter(ProactiveReminder.is_enabled == True)
    if reminder_type:
        query = query.filter(ProactiveReminder.reminder_type == reminder_type)

    reminders = query.all()

    return {
        'user_id': user_id,
        'reminders': [
            {
                'id': r.id,
                "reminder_type": r.reminder_type,
                'title': r.title,
                'content': r.content,
                "trigger_type": r.trigger_type,
                "schedule_time": r.schedule_time,
                "interval_minutes": r.interval_minutes,
                'is_enabled': r.is_enabled,
                "trigger_count": r.trigger_count,
                "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None
            }
            for r in reminders
        ],
        'total': len(reminders)
    }


@router.put("/reminders/{reminder_id}", response_model=dict)
def update_reminder_config(
    reminder_id: int,
    request: ProactiveReminderUpdate,
    db: Session = Depends(get_db)
):
    """更新主动提醒配置"""
    reminder = db.query(ProactiveReminder).filter(ProactiveReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail='提醒配置不存在')

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)

    db.commit()
    return {'success': True, 'message': "更新成功"}


@router.delete("/reminders/{reminder_id}", response_model=dict)
def delete_reminder_config(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    """删除主动提醒配置"""
    reminder = db.query(ProactiveReminder).filter(ProactiveReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail='提醒配置不存在')

    db.delete(reminder)
    db.commit()
    return {'success': True, 'message': "删除成功"}


# ==================== 触发主动交互 ====================

@router.post("/trigger/greeting", response_model=dict)
def trigger_greeting(
    request: TriggerGreetingRequest,
    db: Session = Depends(get_db)
):
    """触发主动问候"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    # 生成问候内容
    now = datetime.now()
    hour = now.hour

    # 确定问候类型
    if request.greeting_type:
        greeting_type = request.greeting_type.value
    elif hour < 12:
        greeting_type = 'morning'
    elif hour < 18:
        greeting_type = 'afternoon'
    else:
        greeting_type = 'evening'

    # 构建问候内容
    greeting_parts = []
    includes = {}

    # 基本问候
    greetings_template = {
        'morning': [
            f"{user.name}，早上好！新的一天开始了。",
            f"早安，{user.name}！今天感觉怎么样？",
            f"{user.name}，早上好呀！昨晚睡得好吗？"
        ],
        'afternoon': [
            f"{user.name}，下午好！中午休息得怎么样？",
            f"下午好，{user.name}！现在精神还好吧？",
            f"{user.name}，下午了，喝杯水休息一下吧。"
        ],
        'evening': [
            f"{user.name}，晚上好！今天过得怎么样？",
            f"晚上好，{user.name}！吃晚饭了吗？",
            f"{user.name}，晚上好呀！今天累不累？"
        ]
    }

    base_greeting = random.choice(greetings_template.get(greeting_type, greetings_template["morning"]))
    greeting_parts.append(base_greeting)

    # 获取问候配置
    greeting_config = db.query(ProactiveGreeting).filter(
        ProactiveGreeting.user_id == request.user_id,
        ProactiveGreeting.greeting_type == greeting_type,
        ProactiveGreeting.is_enabled == True
    ).first()

    # 天气信息（模拟）
    if not greeting_config or greeting_config.include_weather:
        weather_info = "今天天气晴朗，温度适宜，适合出去走走。"
        greeting_parts.append(weather_info)
        includes["weather"] = weather_info

    # 健康提示
    if not greeting_config or greeting_config.include_health_tip:
        health_tips = [
            "记得多喝水，保持身体水分充足。",
            "适当活动一下筋骨，对身体好。",
            "今天要注意保暖哦。",
            "饭后可以散散步，有助于消化。"
        ]
        health_tip = random.choice(health_tips)
        greeting_parts.append(health_tip)
        includes['health_tip'] = health_tip

    # 用药提醒
    if not greeting_config or greeting_config.include_medication_reminder:
        medications = db.query(Medication).filter(
            Medication.user_id == request.user_id,
            Medication.is_active == True
        ).all()
        if medications:
            med_names = [m.name for m in medications[:3]]
            med_reminder = f"别忘了按时吃药哦，今天要吃的有：{', '.join(med_names)}。"
            greeting_parts.append(med_reminder)
            includes['medication'] = med_reminder

    # 自定义消息
    if request.custom_message:
        greeting_parts.append(request.custom_message)

    greeting_content = ' '.join(greeting_parts)

    # 记录交互日志
    log = ProactiveInteractionLog(
        user_id=request.user_id,
        interaction_type='greeting',
        trigger_source='manual',
        content=greeting_content,
        triggered_at=now
    )
    db.add(log)

    # 更新问候配置的触发时间
    if greeting_config:
        greeting_config.last_triggered_at = now

    db.commit()
    db.refresh(log)

    return {
        "success": True,
        "interaction_id": log.id,
        "greeting_type": greeting_type,
        "greeting_content": greeting_content,
        'includes': includes
    }


@router.post("/trigger/reminder", response_model=dict)
def trigger_reminder(
    request: TriggerReminderRequest,
    db: Session = Depends(get_db)
):
    """触发主动提醒"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    now = datetime.now()
    reminder_content = ""
    reminder_type = ""

    if request.reminder_id:
        # 触发指定提醒
        reminder = db.query(ProactiveReminder).filter(
            ProactiveReminder.id == request.reminder_id
        ).first()
        if not reminder:
            raise HTTPException(status_code=404, detail="提醒配置不存在")
        reminder_content = f"{reminder.title}：{reminder.content}" if reminder.content else reminder.title
        reminder_type = reminder.reminder_type

        # 更新提醒统计
        reminder.last_triggered_at = now
        reminder.trigger_count += 1
    elif request.reminder_type:
        # 按类型触发
        reminder_type = request.reminder_type.value
        reminder_templates = {
            'water': f"{user.name}，该喝水了！保持水分充足对身体好。",
            'stand_up': f"{user.name}，坐久了要站起来活动一下哦！",
            'exercise': f"{user.name}，是时候做做运动了，活动活动筋骨吧。",
            'rest': f"{user.name}，休息一下吧，眼睛和身体都需要放松。",
            "medication": f"{user.name}，该吃药了，别忘了哦！"
        }
        reminder_content = reminder_templates.get(reminder_type, f"{user.name}，这是一条提醒。")
    elif request.custom_content:
        reminder_content = request.custom_content
        reminder_type = "custom"
    else:
        raise HTTPException(status_code=400, detail="请提供提醒ID、类型或自定义内容")

    # 记录交互日志
    log = ProactiveInteractionLog(
        user_id=request.user_id,
        interaction_type='reminder',
        trigger_source='manual',
        content=reminder_content,
        triggered_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "success": True,
        "interaction_id": log.id,
        "reminder_type": reminder_type,
        "reminder_content": reminder_content
    }


# ==================== 交互日志 ====================

@router.get("/interactions/{user_id}", response_model=dict)
def get_interaction_logs(
    user_id: int,
    interaction_type: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取主动交互日志"""
    start_date = datetime.now() - timedelta(days=days)

    query = db.query(ProactiveInteractionLog).filter(
        ProactiveInteractionLog.user_id == user_id,
        ProactiveInteractionLog.triggered_at >= start_date
    )
    if interaction_type:
        query = query.filter(ProactiveInteractionLog.interaction_type == interaction_type)

    logs = query.order_by(ProactiveInteractionLog.triggered_at.desc()).limit(limit).all()

    return {
        'user_id': user_id,
        "period_days": days,
        "interactions": [
            {
                'id': log.id,
                "interaction_type": log.interaction_type,
                "trigger_source": log.trigger_source,
                'content': log.content,
                "user_response": log.user_response,
                "response_type": log.response_type,
                "triggered_at": log.triggered_at.isoformat(),
                "responded_at": log.responded_at.isoformat() if log.responded_at else None
            }
            for log in logs
        ],
        'total': len(logs)
    }


@router.put("/interactions/{interaction_id}/response", response_model=dict)
def update_interaction_response(
    interaction_id: int,
    request: UpdateInteractionResponse,
    db: Session = Depends(get_db)
):
    """更新用户对主动交互的回应"""
    log = db.query(ProactiveInteractionLog).filter(
        ProactiveInteractionLog.id == interaction_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail='交互记录不存在')

    log.user_response = request.user_response
    log.response_type = request.response_type.value
    log.responded_at = datetime.now()

    db.commit()
    return {'success': True, 'message': "回应已记录"}


# ==================== 行为模式 ====================

@router.get("/behavior-patterns/{user_id}", response_model=dict)
def get_behavior_patterns(
    user_id: int,
    pattern_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取用户行为模式"""
    query = db.query(UserBehaviorPattern).filter(
        UserBehaviorPattern.user_id == user_id
    )
    if pattern_type:
        query = query.filter(UserBehaviorPattern.pattern_type == pattern_type)

    patterns = query.all()

    return {
        'user_id': user_id,
        'patterns': [
            {
                'id': p.id,
                "pattern_type": p.pattern_type,
                "pattern_value": p.pattern_value,
                'confidence': p.confidence,
                "sample_count": p.sample_count,
                "last_occurrence": p.last_occurrence.isoformat() if p.last_occurrence else None
            }
            for p in patterns
        ],
        'total': len(patterns)
    }


@router.post("/behavior-patterns/learn", response_model=dict)
def learn_behavior_pattern(
    request: BehaviorPatternCreate,
    db: Session = Depends(get_db)
):
    """学习/更新用户行为模式"""
    # 查找现有模式
    existing = db.query(UserBehaviorPattern).filter(
        UserBehaviorPattern.user_id == request.user_id,
        UserBehaviorPattern.pattern_type == request.pattern_type.value
    ).first()

    if existing:
        # 更新现有模式
        existing.pattern_value = request.pattern_value
        existing.sample_count += 1
        # 使用移动平均更新置信度
        existing.confidence = (existing.confidence * 0.8) + (request.confidence * 0.2)
        existing.last_occurrence = datetime.now()
        pattern_id = existing.id
    else:
        # 创建新模式
        pattern = UserBehaviorPattern(
            user_id=request.user_id,
            pattern_type=request.pattern_type.value,
            pattern_value=request.pattern_value,
            confidence=request.confidence,
            sample_count=1,
            last_occurrence=datetime.now()
        )
        db.add(pattern)
        db.commit()
        db.refresh(pattern)
        pattern_id = pattern.id

    db.commit()
    return {
        'success': True,
        'pattern_id': pattern_id,
        'message': "行为模式已更新"
    }


# ==================== 智能问候生成 ====================

@router.post("/generate-greeting", response_model=dict)
def generate_smart_greeting(
    request: GenerateGreetingRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成智能个性化问候"""
    _check_user_access(request.user_id, current_user, db)
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    now = datetime.now()
    hour = now.hour
    components = {}
    personalization_applied = []

    # 获取用户画像
    profile = db.query(UserProfile).filter(UserProfile.user_id == request.user_id).first()

    # 基本问候
    if hour < 6:
        base = f"{user.name}，这么早就醒了？"
    elif hour < 9:
        base = f"{user.name}，早上好！"
    elif hour < 12:
        base = f"{user.name}，上午好！"
    elif hour < 14:
        base = f"{user.name}，中午好！吃饭了吗？"
    elif hour < 18:
        base = f"{user.name}，下午好！"
    elif hour < 21:
        base = f"{user.name}，晚上好！"
    else:
        base = f"{user.name}，夜深了，还没休息吗？"
    components['base_greeting'] = base

    # 个性化元素
    greeting_parts = [base]

    # 如果有用户画像，添加个性化内容
    if profile:
        # 根据兴趣爱好个性化
        hobbies = parse_json_field(profile.hobbies)
        if hobbies:
            hobby = random.choice(hobbies)
            hobby_mention = f"今天有没有{hobby}呀？"
            greeting_parts.append(hobby_mention)
            personalization_applied.append("hobbies")

    # 检查最近健康状况
    recent_health = db.query(HealthRecord).filter(
        HealthRecord.user_id == request.user_id,
        HealthRecord.measured_at >= now - timedelta(days=1)
    ).order_by(HealthRecord.measured_at.desc()).first()

    if recent_health:
        if recent_health.is_abnormal:
            health_concern = "昨天身体不太舒服，今天感觉好点了吗？"
            greeting_parts.append(health_concern)
            components["health_followup"] = health_concern
            personalization_applied.append("health_status")

    # 检查用药情况
    today_medications = db.query(Medication).filter(
        Medication.user_id == request.user_id,
        Medication.is_active == True
    ).count()

    if today_medications > 0:
        med_reminder = "别忘了按时吃药哦。"
        greeting_parts.append(med_reminder)
        components["medication_reminder"] = med_reminder
        personalization_applied.append("medication")

    # 组合最终问候
    greeting = ' '.join(greeting_parts)

    return {
        'greeting': greeting,
        "components": components,
        "personalization_applied": personalization_applied,
        "generated_at": now.isoformat()
    }


# ==================== 待触发任务查询 ====================

@router.get("/pending/{user_id}", response_model=dict)
def get_pending_interactions(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取待触发的主动交互"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_weekday = now.isoweekday()

    pending_greetings = []
    pending_reminders = []

    # 检查问候配置
    greetings = db.query(ProactiveGreeting).filter(
        ProactiveGreeting.user_id == user_id,
        ProactiveGreeting.is_enabled == True
    ).all()

    for g in greetings:
        schedule_days = parse_json_field(g.schedule_days) or [1, 2, 3, 4, 5, 6, 7]
        if current_weekday in schedule_days:
            if g.schedule_time <= current_time:
                # 检查今天是否已触发
                if not g.last_triggered_at or g.last_triggered_at.date() < now.date():
                    pending_greetings.append({
                        'id': g.id,
                        "type": g.greeting_type,
                        "schedule_time": g.schedule_time
                    })

    # 检查提醒配置
    reminders = db.query(ProactiveReminder).filter(
        ProactiveReminder.user_id == user_id,
        ProactiveReminder.is_enabled == True
    ).all()

    for r in reminders:
        should_trigger = False

        if r.trigger_type == 'time_based' and r.schedule_time:
            if r.schedule_time <= current_time:
                if not r.last_triggered_at or r.last_triggered_at.date() < now.date():
                    should_trigger = True

        elif r.trigger_type == 'interval' and r.interval_minutes:
            if r.last_triggered_at:
                minutes_since_last = (now - r.last_triggered_at).total_seconds() / 60
                if minutes_since_last >= r.interval_minutes:
                    should_trigger = True
            else:
                should_trigger = True

        if should_trigger:
            pending_reminders.append({
                'id': r.id,
                'type': r.reminder_type,
                'title': r.title
            })

    return {
        "user_id": user_id,
        "current_time": current_time,
        "pending_greetings": pending_greetings,
        "pending_reminders": pending_reminders,
        "total_pending": len(pending_greetings) + len(pending_reminders)
    }


# ==================== 统计数据 ====================

@router.get("/stats/{user_id}", response_model=dict)
def get_interaction_stats(
    user_id: int,
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """获取主动交互统计数据"""
    start_date = datetime.now() - timedelta(days=days)

    # 总交互次数
    total_interactions = db.query(func.count(ProactiveInteractionLog.id)).filter(
        ProactiveInteractionLog.user_id == user_id,
        ProactiveInteractionLog.triggered_at >= start_date
    ).scalar()

    # 按类型统计
    by_type = db.query(
        ProactiveInteractionLog.interaction_type,
        func.count(ProactiveInteractionLog.id)
    ).filter(
        ProactiveInteractionLog.user_id == user_id,
        ProactiveInteractionLog.triggered_at >= start_date
    ).group_by(ProactiveInteractionLog.interaction_type).all()

    # 响应率
    responded = db.query(func.count(ProactiveInteractionLog.id)).filter(
        ProactiveInteractionLog.user_id == user_id,
        ProactiveInteractionLog.triggered_at >= start_date,
        ProactiveInteractionLog.user_response != None
    ).scalar()

    response_rate = (responded / total_interactions * 100) if total_interactions > 0 else 0

    # 正面响应率
    positive_responses = db.query(func.count(ProactiveInteractionLog.id)).filter(
        ProactiveInteractionLog.user_id == user_id,
        ProactiveInteractionLog.triggered_at >= start_date,
        ProactiveInteractionLog.response_type == "positive"
    ).scalar()

    positive_rate = (positive_responses / responded * 100) if responded > 0 else 0

    return {
        'user_id': user_id,
        "period_days": days,
        "total_interactions": total_interactions,
        "interactions_by_type": {t: c for t, c in by_type},
        "response_rate": round(response_rate, 1),
        "positive_response_rate": round(positive_rate, 1),
        "average_daily": round(total_interactions / days, 1)
    }
