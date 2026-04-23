"""
新手引导API
提供引导流程管理、步骤操作、练习任务等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.onboarding_service import (
    onboarding_service,
    practice_service,
    OnboardingStep,
    StepStatus
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/onboarding", tags=["新手引导"])


# ==================== 请求/响应模型 ====================

class StepDataRequest(BaseModel):
    """步骤数据请求"""
    data: Dict[str, Any] = Field(default_factory=dict, description="步骤收集的数据")


class VoicePracticeRequest(BaseModel):
    """语音练习请求"""
    spoken_text: str = Field(..., description='用户说的内容')


# ==================== 引导流程API ====================

@router.post("/start")
async def start_onboarding(current_user: dict = Depends(get_current_user)):
    """
    开始新手引导

    为新用户初始化引导流程
    """
    user_id = int(current_user['sub'])

    # 检查是否已有进度
    existing = onboarding_service.get_progress(user_id)
    if existing and existing.is_completed:
        return {
            'message': '您已完成新手引导',
            "progress": existing.to_dict(),
            "is_completed": True
        }

    if existing:
        # 继续已有进度
        return {
            'message': '继续您的引导流程',
            "progress": existing.to_dict(),
            "current_step": onboarding_service.get_current_step_info(user_id).to_dict()
        }

    # 开始新引导
    progress = onboarding_service.start_onboarding(user_id)
    step_info = onboarding_service.get_current_step_info(user_id)

    return {
        "message": "欢迎！让我们开始设置吧",
        "progress": progress.to_dict(),
        "current_step": step_info.to_dict() if step_info else None
    }


@router.get("/progress")
async def get_progress(current_user: dict = Depends(get_current_user)):
    """
    获取引导进度
    """
    user_id = int(current_user['sub'])
    progress = onboarding_service.get_progress(user_id)

    if not progress:
        return {
            "has_started": False,
            'message': "您还没有开始新手引导"
        }

    step_info = onboarding_service.get_current_step_info(user_id)

    return {
        "has_started": True,
        'progress': progress.to_dict(),
        "current_step": step_info.to_dict() if step_info else None,
        "is_completed": progress.is_completed
    }


@router.get("/steps")
async def get_all_steps(current_user: dict = Depends(get_current_user)):
    """
    获取所有引导步骤

    返回完整的引导流程信息
    """
    user_id = int(current_user['sub'])
    steps = onboarding_service.get_all_steps()
    progress = onboarding_service.get_progress(user_id)

    result = []
    for step in steps:
        step_dict = step.to_dict()
        if progress:
            step_dict['status'] = onboarding_service.get_step_status(
                user_id, step.step
            ).value
        else:
            step_dict['status'] = StepStatus.PENDING.value
        result.append(step_dict)

    return {
        'steps': result,
        "total_count": len(result),
        'estimated_time_minutes': sum(s['duration_minutes'] for s in result)
    }


@router.get("/steps/{step_name}")
async def get_step_info(
    step_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定步骤的详细信息
    """
    try:
        step = OnboardingStep(step_name)
    except ValueError:
        valid_steps = [s.value for s in OnboardingStep]
        raise HTTPException(
            status_code=400,
            detail=f'无效的步骤名称，可选: {valid_steps}'
        )

    step_info = onboarding_service.steps.get(step)
    if not step_info:
        raise HTTPException(status_code=404, detail='步骤信息不存在')

    user_id = int(current_user['sub'])
    result = step_info.to_dict()
    result['status'] = onboarding_service.get_step_status(user_id, step).value

    return result


@router.get("/current")
async def get_current_step(current_user: dict = Depends(get_current_user)):
    """
    获取当前步骤

    返回用户当前需要完成的步骤信息
    """
    user_id = int(current_user['sub'])
    progress = onboarding_service.get_progress(user_id)

    if not progress:
        return {
            "has_started": False,
            'message': "请先开始新手引导"
        }

    if progress.is_completed:
        return {
            "is_completed": True,
            'message': onboarding_service.get_completion_message(user_id)
        }

    step_info = onboarding_service.get_current_step_info(user_id)

    return {
        "is_completed": False,
        "current_step": step_info.to_dict() if step_info else None,
        "voice_guide": onboarding_service.generate_step_voice_guide(
            user_id, progress.current_step
        )
    }


# ==================== 步骤操作API ====================

@router.post("/steps/{step_name}/complete")
async def complete_step(
    step_name: str,
    request: StepDataRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    完成当前步骤

    提交步骤数据并进入下一步
    """
    user_id = int(current_user['sub'])

    try:
        step = OnboardingStep(step_name)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的步骤名称')

    progress = onboarding_service.complete_step(user_id, step, request.data)
    if not progress:
        raise HTTPException(status_code=400, detail='无法完成步骤')

    # 获取下一步信息
    next_step_info = None
    if not progress.is_completed:
        next_step_info = onboarding_service.get_current_step_info(user_id)

    return {
        'success': True,
        "progress": progress.to_dict(),
        "is_completed": progress.is_completed,
        'next_step': next_step_info.to_dict() if next_step_info else None,
        "completion_message": onboarding_service.get_completion_message(user_id) if progress.is_completed else None
    }


@router.post("/steps/{step_name}/skip")
async def skip_step(
    step_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    跳过当前步骤

    只有非必需步骤可以跳过
    """
    user_id = int(current_user['sub'])

    try:
        step = OnboardingStep(step_name)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的步骤名称')

    progress = onboarding_service.skip_step(user_id, step)
    if not progress:
        raise HTTPException(status_code=400, detail='此步骤不能跳过')

    next_step_info = None
    if not progress.is_completed:
        next_step_info = onboarding_service.get_current_step_info(user_id)

    return {
        'success': True,
        "message": "已跳过此步骤，您可以稍后在设置中完成",
        'progress': progress.to_dict(),
        'next_step': next_step_info.to_dict() if next_step_info else None
    }


@router.post("/back")
async def go_back(current_user: dict = Depends(get_current_user)):
    """
    返回上一步
    """
    user_id = int(current_user['sub'])
    progress = onboarding_service.go_back(user_id)

    if not progress:
        raise HTTPException(status_code=400, detail='无法返回')

    step_info = onboarding_service.get_current_step_info(user_id)

    return {
        'success': True,
        "progress": progress.to_dict(),
        "current_step": step_info.to_dict() if step_info else None
    }


@router.post("/reset")
async def reset_onboarding(current_user: dict = Depends(get_current_user)):
    """
    重置引导流程

    重新开始新手引导
    """
    user_id = int(current_user['sub'])
    progress = onboarding_service.reset_onboarding(user_id)
    step_info = onboarding_service.get_current_step_info(user_id)

    return {
        'success': True,
        'message': '引导流程已重置',
        "progress": progress.to_dict(),
        "current_step": step_info.to_dict() if step_info else None
    }


# ==================== 练习任务API ====================

@router.get("/practice")
async def get_practice_tasks(current_user: dict = Depends(get_current_user)):
    """
    获取所有练习任务
    """
    tasks = practice_service.get_all_practice_tasks()
    return {'tasks': tasks}


@router.get("/practice/{task_id}")
async def get_practice_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定练习任务
    """
    task = practice_service.get_practice_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='练习任务不存在')

    return {'task': {"id": task_id, **task}}


@router.post("/practice/voice/verify")
async def verify_voice_practice(
    request: VoicePracticeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    验证语音练习

    检查用户的语音输入是否正确
    """
    success = practice_service.verify_voice_practice(request.spoken_text)
    task = practice_service.get_practice_task("voice_practice")

    if success:
        return {
            'success': True,
            'message': task["success_message"],
            "spoken_text": request.spoken_text
        }
    else:
        return {
            'success': False,
            'message': '没关系，再试一次！',
            'hint': task["hint"],
            "spoken_text": request.spoken_text
        }


# ==================== 语音引导API ====================

@router.get("/voice-guide")
async def get_voice_guide(
    step: Optional[str] = Query(None, description="步骤名称"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取语音引导内容

    返回适合语音播报的引导内容
    """
    user_id = int(current_user['sub'])

    if step:
        try:
            step_enum = OnboardingStep(step)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的步骤名称")
        voice_guide = onboarding_service.generate_step_voice_guide(user_id, step_enum)
    else:
        progress = onboarding_service.get_progress(user_id)
        if progress:
            voice_guide = onboarding_service.generate_step_voice_guide(
                user_id, progress.current_step
            )
        else:
            voice_guide = "您好!欢迎使用安心宝。请点击'开始'按钮,我来帮您完成设置。"

    return {
        "voice_guide": voice_guide,
        'step': step
    }


# ==================== 快捷状态API ====================

@router.get("/status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """
    获取引导状态摘要

    快速检查用户的引导完成情况
    """
    user_id = int(current_user['sub'])
    progress = onboarding_service.get_progress(user_id)

    if not progress:
        return {
            'status': "not_started",
            "should_show_onboarding": True,
            'message': "建议完成新手引导，了解如何使用安心宝"
        }

    if progress.is_completed:
        return {
            'status': "completed",
            "should_show_onboarding": False,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None
        }

    return {
        'status': 'in_progress',
        'should_show_onboarding': True,
        "current_step": progress.current_step.value,
        "progress_percent": progress._calculate_progress()
    }
