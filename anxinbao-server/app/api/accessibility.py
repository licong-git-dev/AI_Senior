"""
无障碍设置API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.core.accessibility import (
    accessibility_manager,
    AccessibilitySettings,
    FontSize,
    ContrastMode,
    VoiceSpeed,
    InteractionMode
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/accessibility", tags=["无障碍设置"])


# ==================== 请求/响应模型 ====================

class AccessibilitySettingsUpdate(BaseModel):
    """无障碍设置更新请求"""
    font_size: Optional[str] = Field(None, description="字体大小: small/normal/large/extra_large")
    contrast_mode: Optional[str] = Field(None, description="对比度模式: normal/high/dark/light")
    voice_speed: Optional[str] = Field(None, description="语音速度: slow/normal/fast")
    voice_volume: Optional[int] = Field(None, ge=0, le=100, description="语音音量: 0-100")
    interaction_mode: Optional[str] = Field(None, description="交互模式: standard/simplified/voice_first/touch_friendly")
    enable_animations: Optional[bool] = Field(None, description="是否启用动画")
    button_size: Optional[str] = Field(None, description="按钮大小: small/medium/large/extra_large")
    enable_sound_feedback: Optional[bool] = Field(None, description='操作音效反馈')
    auto_read_messages: Optional[bool] = Field(None, description='自动朗读消息')
    enable_haptic_feedback: Optional[bool] = Field(None, description='触觉反馈')
    show_operation_hints: Optional[bool] = Field(None, description='显示操作提示')
    confirm_important_actions: Optional[bool] = Field(None, description='重要操作二次确认')
    simplified_menu: Optional[bool] = Field(None, description='简化菜单')
    max_menu_items: Optional[int] = Field(None, ge=3, le=10, description='每屏最多菜单项')
    sos_button_visible: Optional[bool] = Field(None, description='SOS按钮可见')
    sos_button_size: Optional[str] = Field(None, description='SOS按钮大小')
    emergency_contact_quick_dial: Optional[bool] = Field(None, description="紧急联系人快速拨号")


class AccessibilitySettingsResponse(BaseModel):
    """无障碍设置响应"""
    font_size: str
    contrast_mode: str
    voice_speed: str
    voice_volume: int
    interaction_mode: str
    enable_animations: bool
    button_size: str
    enable_sound_feedback: bool
    auto_read_messages: bool
    enable_haptic_feedback: bool
    show_operation_hints: bool
    confirm_important_actions: bool
    simplified_menu: bool
    max_menu_items: int
    sos_button_visible: bool
    sos_button_size: str
    emergency_contact_quick_dial: bool


class PresetInfo(BaseModel):
    """预设信息"""
    id: str
    name: str
    description: str


class CSSVariablesResponse(BaseModel):
    """CSS变量响应"""
    variables: Dict[str, str]


class CSSResponse(BaseModel):
    """完整CSS响应"""
    css: str


class VoiceGuidanceConfig(BaseModel):
    """语音引导配置"""
    rate: float
    volume: float
    pitch: float
    voice: str


# ==================== API端点 ====================

@router.get("/settings", response_model=AccessibilitySettingsResponse)
async def get_accessibility_settings(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户的无障碍设置
    """
    user_id = int(current_user['sub'])
    settings = accessibility_manager.get_user_settings(user_id)
    return AccessibilitySettingsResponse(**settings.to_dict())


@router.put("/settings", response_model=AccessibilitySettingsResponse)
async def update_accessibility_settings(
    update_data: AccessibilitySettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新无障碍设置
    """
    user_id = int(current_user['sub'])

    # 过滤掉None值
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    if not update_dict:
        raise HTTPException(status_code=400, detail='没有提供任何更新数据')

    settings = accessibility_manager.update_user_settings(user_id, update_dict)
    return AccessibilitySettingsResponse(**settings.to_dict())


@router.get("/presets", response_model=List[PresetInfo])
async def get_available_presets():
    """
    获取可用的预设配置列表
    """
    presets = accessibility_manager.get_available_presets()
    return [PresetInfo(**p) for p in presets]


@router.post("/presets/{preset_id}/apply", response_model=AccessibilitySettingsResponse)
async def apply_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    应用预设配置

    可选预设:
    - standard: 标准老人模式
    - vision_impaired: 视力障碍模式
    - hearing_impaired: 听力障碍模式
    - cognitive: 认知辅助模式
    - motor_impaired: 运动障碍模式
    """
    user_id = int(current_user['sub'])

    valid_presets = ['standard', 'vision_impaired', 'hearing_impaired', 'cognitive', 'motor_impaired']
    if preset_id not in valid_presets:
        raise HTTPException(status_code=400, detail=f'无效的预设ID，可选: {valid_presets}')

    settings = accessibility_manager.apply_preset(user_id, preset_id)
    return AccessibilitySettingsResponse(**settings.to_dict())


@router.get("/css", response_model=CSSResponse)
async def get_user_css(current_user: dict = Depends(get_current_user)):
    """
    获取用户自定义CSS样式

    返回根据用户无障碍设置生成的完整CSS样式表
    """
    user_id = int(current_user['sub'])
    css = accessibility_manager.get_css(user_id)
    return CSSResponse(css=css)


@router.get("/css/variables", response_model=CSSVariablesResponse)
async def get_css_variables(current_user: dict = Depends(get_current_user)):
    """
    获取CSS变量

    返回可用于动态样式的CSS变量字典
    """
    user_id = int(current_user['sub'])
    variables = accessibility_manager.get_css_variables(user_id)
    return CSSVariablesResponse(variables=variables)


@router.get("/voice/config", response_model=VoiceGuidanceConfig)
async def get_voice_guidance_config(current_user: dict = Depends(get_current_user)):
    """
    获取语音引导配置

    用于前端TTS（文字转语音）设置
    """
    user_id = int(current_user['sub'])
    voice_service = accessibility_manager.get_voice_guidance(user_id)
    return VoiceGuidanceConfig(**voice_service.get_tts_config())


@router.get("/voice/prompts")
async def get_voice_prompts(current_user: dict = Depends(get_current_user)):
    """
    获取所有语音提示文本

    返回系统预设的语音提示文本列表
    """
    user_id = int(current_user['sub'])
    voice_service = accessibility_manager.get_voice_guidance(user_id)

    prompts = {}
    for key in voice_service.VOICE_PROMPTS.keys():
        prompt = voice_service.get_prompt(key)
        if prompt:
            prompts[key] = prompt

    return {
        'enabled': voice_service.enabled,
        'prompts': prompts
    }


@router.post("/settings/reset", response_model=AccessibilitySettingsResponse)
async def reset_to_default(current_user: dict = Depends(get_current_user)):
    """
    重置为默认设置（标准老人模式）
    """
    user_id = int(current_user['sub'])
    settings = accessibility_manager.apply_preset(user_id, "standard")
    return AccessibilitySettingsResponse(**settings.to_dict())


# ==================== 快捷设置端点 ====================

@router.post("/quick/font-size/{size}")
async def quick_set_font_size(
    size: str,
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置字体大小

    可选值: small, normal, large, extra_large
    """
    valid_sizes = ['small', 'normal', 'large', "extra_large"]
    if size not in valid_sizes:
        raise HTTPException(status_code=400, detail=f'无效的字体大小，可选: {valid_sizes}')

    user_id = int(current_user['sub'])
    settings = accessibility_manager.update_user_settings(user_id, {'font_size': size})
    return {'success': True, "font_size": size}


@router.post("/quick/contrast/{mode}")
async def quick_set_contrast(
    mode: str,
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置对比度模式

    可选值: normal, high, dark, light
    """
    valid_modes = ['normal', 'high', 'dark', 'light']
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f'无效的对比度模式，可选: {valid_modes}')

    user_id = int(current_user["sub"])
    settings = accessibility_manager.update_user_settings(user_id, {"contrast_mode": mode})
    return {'success': True, "contrast_mode": mode}


@router.post("/quick/voice-speed/{speed}")
async def quick_set_voice_speed(
    speed: str,
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置语音速度

    可选值: slow, normal, fast
    """
    valid_speeds = ['slow', 'normal', 'fast']
    if speed not in valid_speeds:
        raise HTTPException(status_code=400, detail=f'无效的语音速度，可选: {valid_speeds}')

    user_id = int(current_user["sub"])
    settings = accessibility_manager.update_user_settings(user_id, {"voice_speed": speed})
    return {'success': True, "voice_speed": speed}


@router.post("/quick/volume/{level}")
async def quick_set_volume(
    level: int,
    current_user: dict = Depends(get_current_user)
):
    """
    快速设置音量

    取值范围: 0-100
    """
    if not 0 <= level <= 100:
        raise HTTPException(status_code=400, detail="音量必须在0-100之间")

    user_id = int(current_user["sub"])
    settings = accessibility_manager.update_user_settings(user_id, {"voice_volume": level})
    return {'success': True, "voice_volume": level}
