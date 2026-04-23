"""
个性化配置API
提供显示、音频、通知、隐私、健康、内容等全面的个性化设置
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.personalization_service import (
    personalization_service,
    ThemeMode,
    FontSize,
    LayoutMode,
    NotificationMode
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/preferences", tags=["个性化配置"])


# ==================== 请求模型 ====================

class DisplaySettingsRequest(BaseModel):
    """显示设置请求"""
    theme: Optional[str] = Field(None, description="主题: light/dark/auto/high_contrast")
    font_size: Optional[str] = Field(None, description="字体: small/medium/large/extra_large")
    layout: Optional[str] = Field(None, description="布局: standard/simplified/large_icon")
    brightness: Optional[int] = Field(None, ge=0, le=100, description='亮度')
    color_blind_mode: Optional[bool] = Field(None, description='色盲模式')
    animations_enabled: Optional[bool] = Field(None, description='动画效果')
    large_buttons: Optional[bool] = Field(None, description='大按钮')
    show_hints: Optional[bool] = Field(None, description="显示提示")


class AudioSettingsRequest(BaseModel):
    """音频设置请求"""
    master_volume: Optional[int] = Field(None, ge=0, le=100, description='主音量')
    voice_volume: Optional[int] = Field(None, ge=0, le=100, description='语音音量')
    music_volume: Optional[int] = Field(None, ge=0, le=100, description='音乐音量')
    alert_volume: Optional[int] = Field(None, ge=0, le=100, description='警报音量')
    voice_speed: Optional[float] = Field(None, ge=0.5, le=2.0, description='语速')
    voice_pitch: Optional[float] = Field(None, ge=0.5, le=2.0, description="音调")
    voice_gender: Optional[str] = Field(None, description="音色: male/female")
    enable_haptic: Optional[bool] = Field(None, description='触觉反馈')
    ring_tone: Optional[str] = Field(None, description="铃声")


class NotificationSettingsRequest(BaseModel):
    """通知设置请求"""
    mode: Optional[str] = Field(None, description="模式: all/important/emergency/none")
    quiet_start: Optional[str] = Field(None, description="免打扰开始时间 HH:MM")
    quiet_end: Optional[str] = Field(None, description="免打扰结束时间 HH:MM")
    voice_announcements: Optional[bool] = Field(None, description='语音播报')
    show_previews: Optional[bool] = Field(None, description='显示预览')
    vibrate: Optional[bool] = Field(None, description='振动')
    led_indicator: Optional[bool] = Field(None, description='LED指示')
    repeat_alerts: Optional[bool] = Field(None, description='重复提醒')
    repeat_interval_minutes: Optional[int] = Field(None, ge=1, le=60, description="重复间隔")


class PrivacySettingsRequest(BaseModel):
    """隐私设置请求"""
    share_location: Optional[bool] = Field(None, description='分享位置')
    share_health_data: Optional[bool] = Field(None, description='分享健康数据')
    share_activity_status: Optional[bool] = Field(None, description='分享活动状态')
    allow_family_view: Optional[bool] = Field(None, description='允许家人查看')
    public_profile: Optional[bool] = Field(None, description='公开资料')
    data_collection: Optional[bool] = Field(None, description='数据收集')
    crash_reports: Optional[bool] = Field(None, description="崩溃报告")


class HealthSettingsRequest(BaseModel):
    """健康设置请求"""
    enable_reminders: Optional[bool] = Field(None, description='启用提醒')
    medication_reminders: Optional[bool] = Field(None, description='服药提醒')
    exercise_reminders: Optional[bool] = Field(None, description='运动提醒')
    water_reminders: Optional[bool] = Field(None, description='喝水提醒')
    sleep_tracking: Optional[bool] = Field(None, description='睡眠追踪')
    auto_health_check: Optional[bool] = Field(None, description="自动健康检查")
    health_report_frequency: Optional[str] = Field(None, description="报告频率: daily/weekly/monthly")
    abnormal_alerts: Optional[bool] = Field(None, description="异常警报")


class ContentPreferencesRequest(BaseModel):
    """内容偏好请求"""
    preferred_music_genres: Optional[List[str]] = Field(None, description='喜欢的音乐类型')
    preferred_news_categories: Optional[List[str]] = Field(None, description='喜欢的新闻分类')
    preferred_activities: Optional[List[str]] = Field(None, description='喜欢的活动')
    language: Optional[str] = Field(None, description='语言')
    dialect: Optional[str] = Field(None, description="方言")
    content_filter_level: Optional[str] = Field(None, description="内容过滤: strict/moderate/none")


class QuickAccessRequest(BaseModel):
    """快捷访问请求"""
    home_shortcuts: Optional[List[str]] = Field(None, description='首页快捷方式')
    voice_shortcuts: Optional[Dict[str, str]] = Field(None, description='语音快捷命令')
    favorite_contacts: Optional[List[int]] = Field(None, description='常用联系人')
    pinned_features: Optional[List[str]] = Field(None, description="置顶功能")


class ImportPreferencesRequest(BaseModel):
    """导入配置请求"""
    json_data: str = Field(..., description="JSON格式的配置数据")


# ==================== 获取配置API ====================

@router.get("/")
async def get_all_preferences(current_user: dict = Depends(get_current_user)):
    """
    获取所有个性化配置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return prefs.to_dict()


@router.get("/display")
async def get_display_settings(current_user: dict = Depends(get_current_user)):
    """
    获取显示设置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {
        'settings': prefs.display.to_dict(),
        'options': {
            'themes': [t.value for t in ThemeMode],
            'font_sizes': [f.value for f in FontSize],
            'layouts': [l.value for l in LayoutMode]
        }
    }


@router.get("/audio")
async def get_audio_settings(current_user: dict = Depends(get_current_user)):
    """
    获取音频设置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {
        'settings': prefs.audio.to_dict(),
        'options': {
            'voice_genders': ['male', 'female'],
            'ring_tones': ['gentle', 'cheerful', 'classic', 'nature']
        }
    }


@router.get("/notification")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    """
    获取通知设置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {
        'settings': prefs.notification.to_dict(),
        'options': {
            'modes': [m.value for m in NotificationMode]
        }
    }


@router.get("/privacy")
async def get_privacy_settings(current_user: dict = Depends(get_current_user)):
    """
    获取隐私设置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {'settings': prefs.privacy.to_dict()}


@router.get("/health")
async def get_health_settings(current_user: dict = Depends(get_current_user)):
    """
    获取健康设置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {
        'settings': prefs.health.to_dict(),
        'options': {
            'report_frequencies': ['daily', 'weekly', 'monthly']
        }
    }


@router.get("/content")
async def get_content_preferences(current_user: dict = Depends(get_current_user)):
    """
    获取内容偏好
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {
        'settings': prefs.content.to_dict(),
        'options': {
            'music_genres': ['经典老歌', '戏曲', '红歌', '民歌', '轻音乐', '广场舞曲'],
            'news_categories': ['健康', '养生', '时事', '娱乐', '科技', '生活'],
            'activities': ['太极', '广场舞', '散步', '书法', '园艺', '棋牌'],
            'dialects': ['mandarin', 'cantonese', 'sichuan', 'shanghai', "minnan"]
        }
    }


@router.get("/quick-access")
async def get_quick_access_settings(current_user: dict = Depends(get_current_user)):
    """
    获取快捷访问设置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.get_preferences(user_id)
    return {
        'settings': prefs.quick_access.to_dict(),
        "available_shortcuts": [
            {'id': 'health_check', 'name': '健康检查', 'icon': 'heart'},
            {'id': 'call_family', 'name': '联系家人', 'icon': 'phone'},
            {'id': 'entertainment', 'name': '娱乐', 'icon': 'music'},
            {'id': 'sos', 'name': '紧急求助', 'icon': 'alert'},
            {'id': 'games', 'name': '认知游戏', 'icon': 'game'},
            {'id': 'social', 'name': '朋友圈', 'icon': 'users'},
            {'id': 'weather', 'name': '天气', 'icon': 'cloud'},
            {'id': 'news', 'name': '新闻', 'icon': 'newspaper'}
        ]
    }


# ==================== 更新配置API ====================

@router.put("/display")
async def update_display_settings(
    request: DisplaySettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新显示设置
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail='没有提供设置项')

    prefs = personalization_service.update_preferences(user_id, 'display', settings)
    return {
        'success': True,
        'settings': prefs.display.to_dict()
    }


@router.put("/audio")
async def update_audio_settings(
    request: AudioSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新音频设置
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail='没有提供设置项')

    prefs = personalization_service.update_preferences(user_id, 'audio', settings)
    return {
        'success': True,
        "settings": prefs.audio.to_dict()
    }


@router.put("/notification")
async def update_notification_settings(
    request: NotificationSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新通知设置
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail="没有提供设置项")

    prefs = personalization_service.update_preferences(user_id, "notification", settings)
    return {
        'success': True,
        'settings': prefs.notification.to_dict()
    }


@router.put('/privacy')
async def update_privacy_settings(
    request: PrivacySettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新隐私设置
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail='没有提供设置项')

    prefs = personalization_service.update_preferences(user_id, 'privacy', settings)
    return {
        'success': True,
        'settings': prefs.privacy.to_dict()
    }


@router.put("/health")
async def update_health_settings(
    request: HealthSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新健康设置
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail='没有提供设置项')

    prefs = personalization_service.update_preferences(user_id, 'health', settings)
    return {
        'success': True,
        'settings': prefs.health.to_dict()
    }


@router.put("/content")
async def update_content_preferences(
    request: ContentPreferencesRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新内容偏好
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail='没有提供设置项')

    prefs = personalization_service.update_preferences(user_id, 'content', settings)
    return {
        'success': True,
        "settings": prefs.content.to_dict()
    }


@router.put("/quick-access")
async def update_quick_access_settings(
    request: QuickAccessRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新快捷访问设置
    """
    user_id = int(current_user['sub'])
    settings = request.model_dump(exclude_none=True)

    if not settings:
        raise HTTPException(status_code=400, detail="没有提供设置项")

    prefs = personalization_service.update_preferences(user_id, "quick_access", settings)
    return {
        'success': True,
        'settings': prefs.quick_access.to_dict()
    }


# ==================== 预设配置API ====================

@router.get("/presets")
async def get_available_presets():
    """
    获取可用的预设配置方案
    """
    presets = personalization_service.get_available_presets()
    return {'presets': presets}


@router.post("/presets/{preset_name}/apply")
async def apply_preset(
    preset_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    应用预设配置

    可用预设:
    - default_elderly: 标准老年模式
    - vision_impaired: 视力辅助模式
    - hearing_impaired: 听力辅助模式
    - simplified: 极简模式
    - tech_savvy: 标准模式
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.apply_preset(user_id, preset_name)

    if not prefs:
        valid_presets = [p['name'] for p in personalization_service.get_available_presets()]
        raise HTTPException(
            status_code=400,
            detail=f"无效的预设名称，可选: {valid_presets}"
        )

    return {
        'success': True,
        'message': f"已应用'{preset_name}'预设",
        "preferences": prefs.to_dict()
    }


# ==================== 导入导出API ====================

@router.get("/export")
async def export_preferences(current_user: dict = Depends(get_current_user)):
    """
    导出配置

    返回JSON格式的配置数据
    """
    user_id = int(current_user['sub'])
    json_data = personalization_service.export_preferences(user_id)
    return {
        'json_data': json_data,
        "export_time": datetime.now().isoformat()
    }


@router.post("/import")
async def import_preferences(
    request: ImportPreferencesRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    导入配置

    从JSON数据恢复配置
    """
    user_id = int(current_user['sub'])
    success = personalization_service.import_preferences(user_id, request.json_data)

    if not success:
        raise HTTPException(status_code=400, detail="导入配置失败，请检查数据格式")

    prefs = personalization_service.get_preferences(user_id)
    return {
        'success': True,
        'message': "配置已导入",
        "preferences": prefs.to_dict()
    }


@router.post("/reset")
async def reset_preferences(current_user: dict = Depends(get_current_user)):
    """
    重置为默认配置
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.reset_preferences(user_id)
    return {
        'success': True,
        'message': "已重置为默认配置",
        "preferences": prefs.to_dict()
    }


# ==================== 快捷设置API ====================

@router.put("/font-size")
async def set_font_size(
    size: str = Query(..., description="字体大小: small/medium/large/extra_large"),
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置字体大小
    """
    user_id = int(current_user['sub'])

    try:
        FontSize(size)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的字体大小')

    prefs = personalization_service.update_preferences(
        user_id, 'display', {'font_size': size}
    )

    size_names = {'small': '小', 'medium': '中', 'large': '大', 'extra_large': '特大'}
    return {
        'success': True,
        'message': f'字体已设置为{size_names.get(size, size)}',
        'font_size': size
    }


@router.put('/volume')
async def set_volume(
    volume: int = Query(..., ge=0, le=100, description="音量0-100"),
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置主音量
    """
    user_id = int(current_user['sub'])
    prefs = personalization_service.update_preferences(
        user_id, 'audio', {"master_volume": volume}
    )
    return {
        'success': True,
        'message': f'音量已设置为{volume}%',
        'volume': volume
    }


@router.put("/theme")
async def set_theme(
    theme: str = Query(..., description="主题: light/dark/auto/high_contrast"),
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置主题
    """
    user_id = int(current_user['sub'])

    try:
        ThemeMode(theme)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的主题')

    prefs = personalization_service.update_preferences(
        user_id, 'display', {'theme': theme}
    )

    theme_names = {
        'light': '浅色', 'dark': '深色',
        'auto': '自动', 'high_contrast': '高对比度'
    }
    return {
        'success': True,
        'message': f'主题已设置为{theme_names.get(theme, theme)}',
        "theme": theme
    }


# 需要导入datetime
from datetime import datetime
