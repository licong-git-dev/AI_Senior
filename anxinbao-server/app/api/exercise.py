"""
运动康复API
提供运动计划、康复训练、运动数据分析等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.exercise_service import (
    exercise_service,
    ExerciseType,
    ExerciseIntensity,
    RehabilitationType,
    BodyPart
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/exercise", tags=["运动康复"])


# ==================== 请求模型 ====================

class CreateExercisePlanRequest(BaseModel):
    """创建运动计划请求"""
    name: str = Field(..., max_length=100, description='计划名称')
    exercise_type: str = Field(..., description='运动类型')
    intensity: str = Field("moderate", description="运动强度: light/moderate/vigorous")
    frequency_per_week: int = Field(3, ge=1, le=7, description='每周次数')
    duration_minutes: int = Field(30, ge=10, le=120, description='每次时长(分钟)')
    moves: Optional[List[str]] = Field(None, description='动作ID列表')
    goals: Optional[List[str]] = Field(None, description='目标列表')
    start_date: datetime = Field(default_factory=datetime.now, description='开始日期')
    end_date: Optional[datetime] = Field(None, description='结束日期')
    notes: Optional[str] = Field(None, description="备注")


class StartSessionRequest(BaseModel):
    """开始运动请求"""
    exercise_type: str = Field(..., description='运动类型')
    plan_id: Optional[str] = Field(None, description="关联计划ID")


class EndSessionRequest(BaseModel):
    """结束运动请求"""
    duration_minutes: int = Field(..., ge=1, description='运动时长(分钟)')
    calories_burned: Optional[int] = Field(None, ge=0, description='消耗卡路里')
    distance_meters: Optional[int] = Field(None, ge=0, description='距离(米)')
    steps: Optional[int] = Field(None, ge=0, description='步数')
    heart_rate_avg: Optional[int] = Field(None, ge=40, le=200, description='平均心率')
    heart_rate_max: Optional[int] = Field(None, ge=40, le=220, description="最高心率")
    feeling: Optional[str] = Field(None, description="感觉: good/normal/tired/pain")
    notes: Optional[str] = Field(None, description='备注')
    completed_moves: Optional[List[str]] = Field(None, description="完成的动作")


class CreateRehabProgramRequest(BaseModel):
    """创建康复计划请求"""
    name: str = Field(..., max_length=100, description='计划名称')
    rehab_type: str = Field(..., description='康复类型')
    target_body_parts: List[str] = Field(..., description='目标部位')
    phases: Optional[List[Dict[str, Any]]] = Field(None, description='康复阶段')
    prescribed_by: Optional[str] = Field(None, description='处方医生')
    hospital: Optional[str] = Field(None, description='医院')
    notes: Optional[str] = Field(None, description="备注")


class CreateFromTemplateRequest(BaseModel):
    """从模板创建康复计划请求"""
    template_key: str = Field(..., description='模板键名')
    prescribed_by: Optional[str] = Field(None, description='处方医生')
    hospital: Optional[str] = Field(None, description="医院")


class RecordRehabSessionRequest(BaseModel):
    """记录康复训练请求"""
    program_id: str = Field(..., description='康复计划ID')
    exercises_completed: List[Dict[str, Any]] = Field(..., description='完成的练习')
    pain_level: int = Field(0, ge=0, le=10, description='疼痛等级(0-10)')
    mobility_score: Optional[int] = Field(None, ge=0, le=100, description='活动度评分')
    notes: Optional[str] = Field(None, description='备注')


# ==================== 运动计划API ====================

@router.post("/plans")
async def create_exercise_plan(
    request: CreateExercisePlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建运动计划

    设定个人运动目标和计划
    """
    user_id = int(current_user['sub'])

    try:
        exercise_type = ExerciseType(request.exercise_type)
    except ValueError:
        valid_types = [t.value for t in ExerciseType]
        raise HTTPException(status_code=400, detail=f"无效的运动类型，可选: {valid_types}")

    try:
        intensity = ExerciseIntensity(request.intensity)
    except ValueError:
        valid_intensities = [i.value for i in ExerciseIntensity]
        raise HTTPException(status_code=400, detail=f"无效的运动强度，可选: {valid_intensities}")

    plan = exercise_service.exercise_plan.create_plan(
        user_id,
        request.name,
        exercise_type,
        intensity,
        request.frequency_per_week,
        request.duration_minutes,
        request.moves,
        request.goals,
        request.start_date,
        request.end_date,
        request.notes
    )

    return {
        'success': True,
        'plan': plan.to_dict(),
        "message": f"运动计划 {request.name} 创建成功"
    }


@router.get("/plans")
async def get_exercise_plans(
    enabled_only: bool = Query(True, description="仅显示启用的计划"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取运动计划列表
    """
    user_id = int(current_user['sub'])

    plans = exercise_service.exercise_plan.get_user_plans(user_id, enabled_only)

    return {
        'plans': [p.to_dict() for p in plans],
        'count': len(plans)
    }


@router.delete("/plans/{plan_id}")
async def disable_exercise_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    禁用运动计划
    """
    user_id = int(current_user['sub'])

    plan = exercise_service.exercise_plan.plans.get(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail='计划不存在')

    plan.enabled = False

    return {
        'success': True,
        'message': "运动计划已禁用"
    }


# ==================== 运动记录API ====================

@router.post("/sessions/start")
async def start_exercise_session(
    request: StartSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    开始运动

    开始记录一次运动
    """
    user_id = int(current_user['sub'])

    try:
        exercise_type = ExerciseType(request.exercise_type)
    except ValueError:
        valid_types = [t.value for t in ExerciseType]
        raise HTTPException(status_code=400, detail=f"无效的运动类型，可选: {valid_types}")

    session = exercise_service.exercise_plan.start_session(
        user_id,
        exercise_type,
        request.plan_id
    )

    return {
        'success': True,
        'session': session.to_dict(),
        'message': "运动已开始，加油！"
    }


@router.post("/sessions/{session_id}/end")
async def end_exercise_session(
    session_id: str,
    request: EndSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    结束运动

    结束并保存运动数据
    """
    user_id = int(current_user['sub'])

    session = exercise_service.exercise_plan.end_session(
        session_id,
        user_id,
        request.duration_minutes,
        request.calories_burned,
        request.distance_meters,
        request.steps,
        request.heart_rate_avg,
        request.heart_rate_max,
        request.feeling,
        request.notes,
        request.completed_moves
    )

    if not session:
        raise HTTPException(status_code=404, detail='运动记录不存在')

    return {
        'success': True,
        'session': session.to_dict(),
        "message": f"运动完成！消耗 {session.calories_burned} 卡路里"
    }


@router.get("/sessions")
async def get_exercise_sessions(
    days: int = Query(30, ge=1, le=365, description='查询天数'),
    exercise_type: Optional[str] = Query(None, description="运动类型筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取运动记录
    """
    user_id = int(current_user['sub'])

    type_filter = None
    if exercise_type:
        try:
            type_filter = ExerciseType(exercise_type)
        except ValueError:
            pass

    sessions = exercise_service.exercise_plan.get_user_sessions(user_id, days, type_filter)

    return {
        'sessions': [s.to_dict() for s in sessions],
        'count': len(sessions)
    }


@router.get("/statistics/weekly")
async def get_weekly_statistics(current_user: dict = Depends(get_current_user)):
    """
    获取每周运动统计

    包含运动时长、卡路里消耗等
    """
    user_id = int(current_user['sub'])

    stats = exercise_service.exercise_plan.get_weekly_stats(user_id)

    return stats


# ==================== 动作库API ====================

@router.get("/moves")
async def get_move_library(
    body_part: Optional[str] = Query(None, description='身体部位筛选'),
    max_difficulty: int = Query(5, ge=1, le=5, description="最大难度"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取动作库

    获取可用的运动动作
    """
    part_filter = None
    if body_part:
        try:
            part_filter = BodyPart(body_part)
        except ValueError:
            valid_parts = [p.value for p in BodyPart]
            raise HTTPException(status_code=400, detail=f"无效的身体部位，可选: {valid_parts}")

    moves = exercise_service.exercise_plan.get_move_library(part_filter, max_difficulty)

    return {
        'moves': [m.to_dict() for m in moves],
        "count": len(moves)
    }


@router.get("/moves/{move_id}")
async def get_move_detail(
    move_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取动作详情
    """
    move = exercise_service.exercise_plan.EXERCISE_MOVES.get(move_id)
    if not move:
        raise HTTPException(status_code=404, detail='动作不存在')

    return {
        "move": move.to_dict()
    }


# ==================== 康复计划API ====================

@router.post("/rehabilitation/programs")
async def create_rehab_program(
    request: CreateRehabProgramRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建康复计划

    自定义康复训练计划
    """
    user_id = int(current_user['sub'])

    try:
        rehab_type = RehabilitationType(request.rehab_type)
    except ValueError:
        valid_types = [t.value for t in RehabilitationType]
        raise HTTPException(status_code=400, detail=f"无效的康复类型，可选: {valid_types}")

    target_parts = []
    for part in request.target_body_parts:
        try:
            target_parts.append(BodyPart(part))
        except ValueError:
            valid_parts = [p.value for p in BodyPart]
            raise HTTPException(status_code=400, detail=f"无效的身体部位 {part}，可选: {valid_parts}")

    program = exercise_service.rehabilitation.create_program(
        user_id,
        request.name,
        rehab_type,
        target_parts,
        request.phases,
        request.prescribed_by,
        request.hospital,
        request.notes
    )

    return {
        'success': True,
        'program': program.to_dict(),
        "message": f"康复计划 {request.name} 创建成功"
    }


@router.post("/rehabilitation/programs/from-template")
async def create_rehab_from_template(
    request: CreateFromTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    从模板创建康复计划

    使用预设模板快速创建
    """
    user_id = int(current_user['sub'])

    program = exercise_service.rehabilitation.create_from_template(
        user_id,
        request.template_key,
        request.prescribed_by,
        request.hospital
    )

    if not program:
        raise HTTPException(status_code=404, detail='模板不存在')

    return {
        'success': True,
        'program': program.to_dict(),
        "message": f"康复计划 {program.name} 创建成功"
    }


@router.get("/rehabilitation/templates")
async def get_rehab_templates(current_user: dict = Depends(get_current_user)):
    """
    获取康复计划模板

    获取可用的预设模板
    """
    templates = exercise_service.rehabilitation.get_available_templates()

    return {
        'templates': templates,
        'count': len(templates)
    }


@router.get("/rehabilitation/programs")
async def get_rehab_programs(
    enabled_only: bool = Query(True, description="仅显示启用的计划"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取康复计划列表
    """
    user_id = int(current_user['sub'])

    programs = exercise_service.rehabilitation.get_user_programs(user_id, enabled_only)

    return {
        'programs': [p.to_dict() for p in programs],
        'count': len(programs)
    }


@router.post("/rehabilitation/programs/{program_id}/advance")
async def advance_rehab_phase(
    program_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    进入下一康复阶段
    """
    user_id = int(current_user['sub'])

    success = exercise_service.rehabilitation.advance_phase(program_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail='无法进入下一阶段')

    program = exercise_service.rehabilitation.programs.get(program_id)

    return {
        "success": True,
        "current_phase": program.current_phase if program else 0,
        'message': "已进入下一康复阶段"
    }


@router.delete("/rehabilitation/programs/{program_id}")
async def disable_rehab_program(
    program_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    禁用康复计划
    """
    user_id = int(current_user['sub'])

    program = exercise_service.rehabilitation.programs.get(program_id)
    if not program or program.user_id != user_id:
        raise HTTPException(status_code=404, detail='康复计划不存在')

    program.enabled = False

    return {
        'success': True,
        'message': "康复计划已禁用"
    }


# ==================== 康复训练记录API ====================

@router.post("/rehabilitation/sessions")
async def record_rehab_session(
    request: RecordRehabSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    记录康复训练

    记录一次康复训练的完成情况
    """
    user_id = int(current_user['sub'])

    session = exercise_service.rehabilitation.record_rehab_session(
        user_id,
        request.program_id,
        request.exercises_completed,
        request.pain_level,
        request.mobility_score,
        request.notes
    )

    if not session:
        raise HTTPException(status_code=404, detail="康复计划不存在")

    pain_message = ""
    if request.pain_level >= 7:
        pain_message = "，疼痛较重，建议咨询医生"
    elif request.pain_level >= 4:
        pain_message = '，注意观察疼痛变化'

    return {
        'success': True,
        'session': session.to_dict(),
        "message": f"康复训练已记录{pain_message}"
    }


@router.get("/rehabilitation/programs/{program_id}/progress")
async def get_rehab_progress(
    program_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取康复进度

    查看康复计划的执行进度
    """
    user_id = int(current_user['sub'])

    progress = exercise_service.rehabilitation.get_rehab_progress(user_id, program_id)

    if not progress:
        raise HTTPException(status_code=404, detail='康复计划不存在')

    return progress


# ==================== 运动康复仪表板API ====================

@router.get("/dashboard")
async def get_exercise_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取运动康复仪表板

    综合展示运动和康复数据
    """
    user_id = int(current_user['sub'])

    # 每周运动统计
    weekly_stats = exercise_service.exercise_plan.get_weekly_stats(user_id)

    # 运动计划
    active_plans = exercise_service.exercise_plan.get_user_plans(user_id, enabled_only=True)

    # 最近运动
    recent_sessions = exercise_service.exercise_plan.get_user_sessions(user_id, days=7)

    # 康复计划
    active_rehab = exercise_service.rehabilitation.get_user_programs(user_id, enabled_only=True)

    # 康复进度摘要
    rehab_progress = []
    for program in active_rehab[:3]:
        progress = exercise_service.rehabilitation.get_rehab_progress(user_id, program.program_id)
        if progress:
            rehab_progress.append({
                "program_name": progress["program_name"],
                "current_phase": progress["current_phase"],
                "total_phases": progress["total_phases"],
                "total_sessions": progress["total_sessions"]
            })

    return {
        'exercise': {
            "weekly_stats": weekly_stats,
            "active_plans": len(active_plans),
            "recent_sessions": len(recent_sessions),
            "last_session": recent_sessions[0].to_dict() if recent_sessions else None
        },
        "rehabilitation": {
            "active_programs": len(active_rehab),
            "progress_summary": rehab_progress
        },
        "recommendations": [
            weekly_stats.get('recommendation', ''),
            "建议每周进行2-3次平衡训练预防跌倒" if weekly_stats.get("total_sessions", 0) < 3 else ""
        ],
        'overall_status': "active" if weekly_stats.get("total_sessions", 0) >= 3 else "needs_improvement"
    }
