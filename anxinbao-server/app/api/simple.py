"""
简化操作模式API
为老人提供简洁易用的操作接口
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.simplified_mode import (
    simplified_mode_manager,
    operation_guide,
    SimplifiedModeLevel,
    PRESET_QUICK_ACTIONS
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/simple", tags=["简化模式"])


# ==================== 请求/响应模型 ====================

class SetModeRequest(BaseModel):
    """设置模式请求"""
    mode: str = Field(..., description="模式: standard/simplified/minimal/voice_only")


class SetQuickActionsRequest(BaseModel):
    """设置快捷操作请求"""
    action_ids: List[str] = Field(..., description="快捷操作ID列表")


class VoiceCommandRequest(BaseModel):
    """语音命令请求"""
    text: str = Field(..., description="语音识别文本")


class QuickActionResponse(BaseModel):
    """快捷操作响应"""
    action_id: str
    name: str
    icon: str
    description: str
    command: str
    params: Dict[str, Any]
    priority: int


class MenuResponse(BaseModel):
    """菜单响应"""
    menu_id: str
    name: str
    icon: str
    is_visible: bool
    actions: List[Dict[str, Any]]


class GuideStep(BaseModel):
    """操作步骤"""
    step: int
    text: str
    voice: str


# ==================== API端点 ====================

@router.get("/mode")
async def get_current_mode(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户的操作模式
    """
    user_id = int(current_user['sub'])
    mode = simplified_mode_manager.get_user_mode(user_id)

    mode_info = {
        SimplifiedModeLevel.STANDARD: {
            'name': '标准模式',
            'description': '完整功能，适合熟悉操作的用户'
        },
        SimplifiedModeLevel.SIMPLIFIED: {
            'name': '简化模式',
            'description': '精简功能，大按钮，适合大多数老人'
        },
        SimplifiedModeLevel.MINIMAL: {
            'name': '极简模式',
            'description': '核心功能，只保留最常用操作'
        },
        SimplifiedModeLevel.VOICE_ONLY: {
            'name': '语音模式',
            'description': '纯语音操作，无需触屏'
        }
    }

    info = mode_info.get(mode, {})
    return {
        'mode': mode.value,
        'name': info.get("name", mode.value),
        "description": info.get('description', '')
    }


@router.post('/mode')
async def set_mode(
    request: SetModeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    设置操作模式

    可选模式:
    - standard: 标准模式（完整功能）
    - simplified: 简化模式（推荐）
    - minimal: 极简模式
    - voice_only: 纯语音模式
    """
    user_id = int(current_user['sub'])

    try:
        mode = SimplifiedModeLevel(request.mode)
    except ValueError:
        valid_modes = [m.value for m in SimplifiedModeLevel]
        raise HTTPException(
            status_code=400,
            detail=f"无效的模式，可选: {valid_modes}"
        )

    simplified_mode_manager.set_user_mode(user_id, mode)

    return {
        'success': True,
        'mode': mode.value
    }


@router.get("/modes")
async def get_available_modes():
    """
    获取所有可用的操作模式
    """
    return {
        'modes': [
            {
                'mode': SimplifiedModeLevel.STANDARD.value,
                'name': '标准模式',
                'description': '完整功能，适合熟悉操作的用户',
                'features': ['全部菜单', '完整设置', '高级功能']
            },
            {
                'mode': SimplifiedModeLevel.SIMPLIFIED.value,
                'name': '简化模式',
                'description': '精简功能，大按钮，适合大多数老人',
                'features': ['大按钮', '简化菜单', "常用功能"],
                "recommended": True
            },
            {
                'mode': SimplifiedModeLevel.MINIMAL.value,
                'name': '极简模式',
                'description': '核心功能，只保留最常用操作',
                'features': ['核心功能', '最大按钮', '简单操作']
            },
            {
                'mode': SimplifiedModeLevel.VOICE_ONLY.value,
                'name': '语音模式',
                'description': '纯语音操作，无需触屏',
                'features': ['语音控制', '语音反馈', '无需触屏']
            }
        ]
    }


@router.get("/menus", response_model=List[MenuResponse])
async def get_menus(current_user: dict = Depends(get_current_user)):
    """
    获取简化菜单

    根据用户当前模式返回适合的菜单结构
    """
    user_id = int(current_user['sub'])
    menus = simplified_mode_manager.get_menus(user_id)
    return menus


@router.get("/quick-actions", response_model=List[QuickActionResponse])
async def get_quick_actions(current_user: dict = Depends(get_current_user)):
    """
    获取快捷操作列表

    返回用户可用的快捷操作，按优先级排序
    """
    user_id = int(current_user['sub'])
    actions = simplified_mode_manager.get_quick_actions(user_id)
    return actions


@router.put("/quick-actions")
async def set_quick_actions(
    request: SetQuickActionsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    自定义快捷操作

    设置用户偏好的快捷操作列表
    """
    user_id = int(current_user['sub'])

    # 验证操作ID
    invalid_ids = [
        aid for aid in request.action_ids
        if aid not in PRESET_QUICK_ACTIONS
    ]
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"无效的操作ID: {invalid_ids}"
        )

    simplified_mode_manager.set_user_quick_actions(user_id, request.action_ids)

    return {
        'success': True,
        'action_ids': request.action_ids
    }


@router.get("/actions")
async def get_all_available_actions():
    """
    获取所有可用的快捷操作

    供用户选择自定义快捷操作
    """
    actions = []
    for action_id, action in PRESET_QUICK_ACTIONS.items():
        actions.append({
            'action_id': action.action_id,
            'name': action.name,
            'icon': action.icon,
            "description": action.description,
            "voice_triggers": action.voice_trigger
        })

    return {'actions': actions}


@router.post("/execute/{action_id}")
async def execute_action(
    action_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    执行快捷操作

    根据action_id执行对应的操作
    """
    user_id = int(current_user['sub'])

    if action_id not in PRESET_QUICK_ACTIONS:
        raise HTTPException(status_code=404, detail="未知操作")

    result = simplified_mode_manager.execute_action(user_id, action_id)
    return result


# ==================== 语音命令API ====================

@router.post("/voice/parse")
async def parse_voice_command(request: VoiceCommandRequest):
    """
    解析语音命令

    将语音识别文本匹配到对应的快捷操作
    """
    result = simplified_mode_manager.parse_voice_command(request.text)
    return result


@router.post("/voice/suggest")
async def get_voice_suggestions(request: VoiceCommandRequest):
    """
    获取语音命令建议

    基于部分输入返回可能的操作建议
    """
    suggestions = simplified_mode_manager.get_voice_suggestions(request.text)
    return {"suggestions": suggestions}


@router.get("/voice/triggers")
async def get_all_voice_triggers():
    """
    获取所有语音触发词

    返回所有操作及其触发词，用于语音引导
    """
    triggers = simplified_mode_manager.get_all_voice_triggers()
    return {'triggers': triggers}


# ==================== 操作引导API ====================

@router.get("/guide/{action_id}", response_model=List[GuideStep])
async def get_operation_guide(action_id: str):
    """
    获取操作步骤指引

    返回操作的详细步骤和语音提示
    """
    guide = operation_guide.get_guide(action_id)
    if not guide:
        raise HTTPException(status_code=404, detail="未找到该操作的指引")
    return guide


@router.get("/guide/{action_id}/step/{step}")
async def get_guide_step(action_id: str, step: int):
    """
    获取单个步骤的指引
    """
    voice = operation_guide.get_step_voice(action_id, step)
    if not voice:
        raise HTTPException(status_code=404, detail='未找到该步骤')

    return {
        'action_id': action_id,
        'step': step,
        'voice': voice
    }


# ==================== 快捷入口 ====================

@router.post("/sos")
async def quick_sos(current_user: dict = Depends(get_current_user)):
    """
    快捷SOS求助

    一键触发紧急求助
    """
    user_id = int(current_user['sub'])
    result = simplified_mode_manager.execute_action(user_id, "sos")

    # 这里应该调用实际的紧急通知服务
    # await notification_service.send_emergency_alert(user_id, ...)

    return {
        'success': True,
        "message": "紧急求助已发送，正在通知您的家人",
        "action": result
    }


@router.post("/call-family")
async def quick_call_family(current_user: dict = Depends(get_current_user)):
    """
    快捷呼叫家人

    一键呼叫主要联系人
    """
    user_id = int(current_user['sub'])
    result = simplified_mode_manager.execute_action(user_id, "call_family")

    return {
        'success': True,
        'message': '正在呼叫家人...',
        "action": result
    }


@router.post("/start-chat")
async def quick_start_chat(current_user: dict = Depends(get_current_user)):
    """
    快捷开始聊天

    一键开始与安心宝聊天
    """
    user_id = int(current_user['sub'])
    result = simplified_mode_manager.execute_action(user_id, "start_chat")

    return {
        'success': True,
        'message': "您好！有什么想和我聊的吗？",
        "action": result
    }
