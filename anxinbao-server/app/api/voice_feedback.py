# -*- coding: utf-8 -*-
"""
语音反馈API
提供语音设置、反馈生成、语音命令等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.voice_feedback_service import (
    voice_feedback,
    voice_guide,
    VoiceStyle,
    VoiceGender
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/voice-feedback", tags=["语音反馈"])


# ==================== 请求/响应模型 ====================

class VoiceSettingsRequest(BaseModel):
    """语音设置请求"""
    enabled: Optional[bool] = Field(None, description='是否启用语音')
    auto_read_messages: Optional[bool] = Field(None, description='自动朗读消息')
    read_time_enabled: Optional[bool] = Field(None, description='朗读时间')
    preferred_name: Optional[str] = Field(None, max_length=20, description='喜欢的称呼')
    dialect: Optional[str] = Field(None, description='方言')
    speed: Optional[float] = Field(None, ge=0.5, le=2.0, description='语速')
    volume: Optional[float] = Field(None, ge=0.1, le=2.0, description="音量")
    style: Optional[str] = Field(None, description="风格: gentle/energetic/calm/warm/professional")
    gender: Optional[str] = Field(None, description="音色: male/female")


class GenerateGreetingRequest(BaseModel):
    """生成问候请求"""
    weather: str = Field(default='晴朗', description='天气')
    activity: str = Field(default='出门散步', description="建议活动")


class GenerateReminderRequest(BaseModel):
    """生成提醒请求"""
    reminder_type: str = Field(..., description="类型: medication/exercise/water/meal/rest")
    medicine: Optional[str] = Field(None, description="药品名（服药提醒时需要）")
    action: Optional[str] = Field(None, description="动作描述")


class GenerateAlertRequest(BaseModel):
    """生成警报请求"""
    alert_type: str = Field(..., description="类型: emergency/health/weather")
    detail: str = Field(..., description="详细信息")
    metric: Optional[str] = Field(None, description="指标名称（健康警报时）")


class OptimizeTextRequest(BaseModel):
    """文本优化请求"""
    text: str = Field(..., min_length=1, max_length=2000, description="待优化文本")


class FormatSpeechRequest(BaseModel):
    """语音合成格式化请求"""
    text: str = Field(..., min_length=1, max_length=2000, description='文本内容')


# ==================== 语音设置API ====================

@router.get("/settings")
async def get_voice_settings(current_user: dict = Depends(get_current_user)):
    """
    获取语音设置
    """
    user_id = int(current_user['sub'])
    settings = voice_feedback.get_settings(user_id)

    return {
        'settings': settings.to_dict(),
        "available_styles": [s.value for s in VoiceStyle],
        "available_genders": [g.value for g in VoiceGender]
    }


@router.put("/settings")
async def update_voice_settings(
    request: VoiceSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新语音设置
    """
    user_id = int(current_user['sub'])

    update_data = {}
    if request.enabled is not None:
        update_data['enabled'] = request.enabled
    if request.auto_read_messages is not None:
        update_data["auto_read_messages"] = request.auto_read_messages
    if request.read_time_enabled is not None:
        update_data["read_time_enabled"] = request.read_time_enabled
    if request.preferred_name is not None:
        update_data["preferred_name"] = request.preferred_name
    if request.dialect is not None:
        update_data['dialect'] = request.dialect
    if request.speed is not None:
        update_data['speed'] = request.speed
    if request.volume is not None:
        update_data['volume'] = request.volume
    if request.style is not None:
        update_data['style'] = request.style
    if request.gender is not None:
        update_data['gender'] = request.gender

    settings = voice_feedback.update_settings(user_id, **update_data)

    return {
        'success': True,
        'settings': settings.to_dict()
    }


@router.put("/settings/name")
async def set_preferred_name(
    name: str = Query(..., min_length=1, max_length=20, description="喜欢的称呼"),
    current_user: dict = Depends(get_current_user)
):
    """
    设置喜欢的称呼

    设置后，语音提示会使用这个名字称呼您
    """
    user_id = int(current_user['sub'])
    settings = voice_feedback.update_settings(user_id, preferred_name=name)

    return {
        'success': True,
        'message': f"好的,以后我会叫您'{name}'",
        'preferred_name': name
    }


@router.put("/settings/speed")
async def set_voice_speed(
    speed: float = Query(..., ge=0.5, le=2.0, description="语速（0.5-2.0）"),
    current_user: dict = Depends(get_current_user)
):
    """
    设置语速

    推荐老年人使用0.8-1.0的语速
    """
    user_id = int(current_user['sub'])
    settings = voice_feedback.update_settings(user_id, speed=speed)

    speed_desc = '正常'
    if speed < 0.8:
        speed_desc = '较慢'
    elif speed < 1.0:
        speed_desc = '稍慢'
    elif speed > 1.2:
        speed_desc = '较快'

    return {
        'success': True,
        "speed": speed,
        "description": speed_desc
    }


# ==================== 语音反馈生成API ====================

@router.get("/greeting")
async def get_greeting(
    weather: str = Query('晴朗', description='天气'),
    activity: str = Query('出门散步', description="建议活动"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取问候语

    根据当前时间段生成合适的问候语
    """
    user_id = int(current_user['sub'])
    greeting = voice_feedback.generate_greeting(user_id, weather, activity)

    return {
        'greeting': greeting,
        'speech': voice_feedback.format_for_speech(greeting, user_id)
    }


@router.post("/confirmation")
async def generate_confirmation(
    action: str = Query(..., description="操作描述"),
    detail: str = Query("", description='详细信息'),
    success: bool = Query(True, description="是否成功"),
    current_user: dict = Depends(get_current_user)
):
    """
    生成操作确认反馈
    """
    user_id = int(current_user['sub'])
    confirmation = voice_feedback.generate_confirmation(user_id, action, detail, success)

    return {
        "confirmation": confirmation,
        'speech': voice_feedback.format_for_speech(confirmation, user_id)
    }


@router.post("/error")
async def generate_error_feedback(
    error_type: str = Query('default', description="错误类型: default/network/permission/not_found"),
    error: str = Query("", description="错误描述"),
    current_user: dict = Depends(get_current_user)
):
    """
    生成错误反馈
    """
    user_id = int(current_user['sub'])
    error_msg = voice_feedback.generate_error(user_id, error_type, error)

    return {
        "error_message": error_msg,
        'speech': voice_feedback.format_for_speech(error_msg, user_id)
    }


@router.post("/reminder")
async def generate_reminder(
    request: GenerateReminderRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    生成提醒语

    提醒类型:
    - medication: 服药提醒
    - exercise: 运动提醒
    - water: 喝水提醒
    - meal: 用餐提醒
    - rest: 休息提醒
    """
    user_id = int(current_user['sub'])

    valid_types = ['medication', 'exercise', 'water', 'meal', 'rest']
    if request.reminder_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的提醒类型，可选: {valid_types}"
        )

    kwargs = {}
    if request.medicine:
        kwargs['medicine'] = request.medicine
    if request.action:
        kwargs['action'] = request.action

    reminder = voice_feedback.generate_reminder(user_id, request.reminder_type, **kwargs)

    return {
        'reminder': reminder,
        'speech': voice_feedback.format_for_speech(reminder, user_id)
    }


@router.post("/alert")
async def generate_alert(
    request: GenerateAlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    生成警报语
    """
    user_id = int(current_user['sub'])

    valid_types = ['emergency', 'health', 'weather']
    if request.alert_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的警报类型，可选: {valid_types}"
        )

    kwargs = {'detail': request.detail}
    if request.metric:
        kwargs['metric'] = request.metric

    alert = voice_feedback.generate_alert(user_id, request.alert_type, **kwargs)

    return {
        'alert': alert,
        'speech': voice_feedback.format_for_speech(alert, user_id)
    }


@router.get("/farewell")
async def get_farewell(
    current_user: dict = Depends(get_current_user)
):
    """
    获取告别语
    """
    user_id = int(current_user['sub'])
    from datetime import datetime

    is_night = datetime.now().hour >= 21 or datetime.now().hour < 6
    farewell = voice_feedback.generate_farewell(user_id, is_night)

    return {
        'farewell': farewell,
        'speech': voice_feedback.format_for_speech(farewell, user_id)
    }


@router.get("/time")
async def read_time(current_user: dict = Depends(get_current_user)):
    """
    朗读当前时间
    """
    user_id = int(current_user['sub'])
    time_text = voice_feedback.read_time()

    return {
        'time_text': time_text,
        'speech': voice_feedback.format_for_speech(time_text, user_id)
    }


# ==================== 文本处理API ====================

@router.post("/optimize")
async def optimize_text(
    request: OptimizeTextRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    优化文本使其更适合老年人理解

    会自动:
    - 替换复杂技术术语
    - 添加适当停顿
    - 简化长句子
    """
    optimized = voice_feedback.optimize_for_elderly(request.text)

    return {
        'original': request.text,
        'optimized': optimized
    }


@router.post("/format-speech")
async def format_for_speech(
    request: FormatSpeechRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    格式化文本用于语音合成

    返回优化后的文本和语音配置
    """
    user_id = int(current_user['sub'])
    result = voice_feedback.format_for_speech(request.text, user_id)

    return result


# ==================== 语音命令API ====================

@router.get("/commands")
async def get_voice_commands(
    category: Optional[str] = Query(None, description="命令分类")
):
    """
    获取可用的语音命令列表

    分类: 通用/健康/社交/娱乐/紧急
    """
    commands = voice_guide.get_available_commands(category)

    # 转换为更友好的格式
    result = {}
    for cat, cmds in commands.items():
        result[cat] = [{"command": c[0], "description": c[1]} for c in cmds]

    return {'commands': result}


@router.get("/help")
async def get_voice_help(
    category: Optional[str] = Query(None, description="帮助分类"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取语音帮助

    生成适合语音播报的帮助内容
    """
    user_id = int(current_user['sub'])
    help_text = voice_guide.generate_help_speech(category)

    return {
        'help_text': help_text,
        'speech': voice_feedback.format_for_speech(help_text, user_id)
    }


@router.get("/suggest")
async def suggest_command(
    context: str = Query('home', description="当前上下文: home/health/social/entertainment"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取命令建议

    根据当前上下文给出合适的语音命令建议
    """
    user_id = int(current_user['sub'])
    suggestion = voice_guide.suggest_command(context)

    return {
        'suggestion': suggestion,
        'speech': voice_feedback.format_for_speech(suggestion, user_id)
    }


# ==================== 数字朗读API ====================

@router.get("/read-number")
async def read_number(
    number_type: str = Query(..., description="类型: temperature/blood_pressure/heart_rate/blood_glucose/time/date/money"),
    value: Optional[float] = Query(None, description='数值'),
    systolic: Optional[int] = Query(None, description='收缩压'),
    diastolic: Optional[int] = Query(None, description='舒张压'),
    hour: Optional[int] = Query(None, description='小时'),
    minute: Optional[int] = Query(None, description='分钟'),
    month: Optional[int] = Query(None, description='月'),
    day: Optional[int] = Query(None, description='日'),
    weekday: Optional[str] = Query(None, description='星期'),
    yuan: Optional[int] = Query(None, description='元'),
    jiao: Optional[int] = Query(None, description="角"),
    current_user: dict = Depends(get_current_user)
):
    """
    朗读数字

    将数字转换为更自然的朗读方式
    """
    kwargs = {}
    if value is not None:
        kwargs['value'] = value
    if systolic is not None:
        kwargs['systolic'] = systolic
    if diastolic is not None:
        kwargs['diastolic'] = diastolic
    if hour is not None:
        kwargs['hour'] = hour
    if minute is not None:
        kwargs['minute'] = minute
    if month is not None:
        kwargs['month'] = month
    if day is not None:
        kwargs['day'] = day
    if weekday is not None:
        kwargs['weekday'] = weekday
    if yuan is not None:
        kwargs['yuan'] = yuan
    if jiao is not None:
        kwargs['jiao'] = jiao

    user_id = int(current_user['sub'])
    text = voice_feedback.read_number(number_type, **kwargs)

    return {
        'text': text,
        'speech': voice_feedback.format_for_speech(text, user_id)
    }
