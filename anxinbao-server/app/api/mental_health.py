"""
心理健康API
提供情绪管理、心理评估、放松训练、心理支持等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.mental_health_service import (
    mental_health_service,
    MoodLevel,
    MoodTrigger,
    RelaxationType,
    AssessmentType
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/mental-health", tags=["心理健康"])


# ==================== 请求模型 ====================

class RecordMoodRequest(BaseModel):
    """记录情绪请求"""
    mood: str = Field(..., description='情绪类型')
    intensity: int = Field(5, ge=1, le=10, description='情绪强度(1-10)')
    triggers: Optional[List[str]] = Field(None, description='触发因素')
    notes: Optional[str] = Field(None, max_length=500, description='备注')
    activities: Optional[List[str]] = Field(None, description='当时的活动')
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description='睡眠时长')
    physical_symptoms: Optional[List[str]] = Field(None, description="身体症状")


class SubmitAssessmentRequest(BaseModel):
    """提交评估请求"""
    assessment_type: str = Field(..., description='评估类型')
    answers: List[Dict[str, Any]] = Field(..., description="答案列表")


class RecordRelaxationRequest(BaseModel):
    """记录放松训练请求"""
    exercise_id: str = Field(..., description='练习ID')
    duration_minutes: int = Field(..., ge=1, description='训练时长(分钟)')
    mood_before: Optional[int] = Field(None, ge=1, le=5, description='训练前心情(1-5)')
    mood_after: Optional[int] = Field(None, ge=1, le=5, description='训练后心情(1-5)')
    notes: Optional[str] = Field(None, max_length=500, description='备注')


# ==================== 情绪追踪API ====================

@router.post("/mood")
async def record_mood(
    request: RecordMoodRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    记录情绪

    记录您当前的情绪状态
    """
    user_id = int(current_user['sub'])

    try:
        mood = MoodLevel(request.mood)
    except ValueError:
        valid_moods = [m.value for m in MoodLevel]
        raise HTTPException(status_code=400, detail=f'无效的情绪类型，可选: {valid_moods}')

    triggers = []
    if request.triggers:
        for t in request.triggers:
            try:
                triggers.append(MoodTrigger(t))
            except ValueError:
                pass

    record = mental_health_service.mood_tracking.record_mood(
        user_id,
        mood,
        request.intensity,
        triggers,
        request.notes,
        request.activities,
        request.sleep_hours,
        request.physical_symptoms
    )

    # 生成回应
    response_message = "已记录您的情绪"
    if mood in [MoodLevel.SAD, MoodLevel.VERY_SAD, MoodLevel.LONELY]:
        response_message += "。记得您不是一个人，可以随时和家人聊聊"
    elif mood in [MoodLevel.ANXIOUS]:
        response_message += '。试试深呼吸放松一下'

    return {
        'success': True,
        'record': record.to_dict(),
        "message": response_message
    }


@router.get("/mood/today")
async def get_today_mood(current_user: dict = Depends(get_current_user)):
    """
    获取今日情绪
    """
    user_id = int(current_user['sub'])

    record = mental_health_service.mood_tracking.get_today_mood(user_id)

    if not record:
        return {
            'recorded': False,
            'message': "今天还没有记录情绪，现在记录一下吧"
        }

    return {
        'recorded': True,
        "record": record.to_dict()
    }


@router.get("/mood/history")
async def get_mood_history(
    days: int = Query(30, ge=1, le=365, description='查询天数'),
    mood: Optional[str] = Query(None, description="情绪筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取情绪历史
    """
    user_id = int(current_user['sub'])

    mood_filter = None
    if mood:
        try:
            mood_filter = MoodLevel(mood)
        except ValueError:
            pass

    records = mental_health_service.mood_tracking.get_user_records(user_id, days, mood_filter)

    return {
        'records': [r.to_dict() for r in records],
        'count': len(records)
    }


@router.get("/mood/statistics")
async def get_mood_statistics(
    days: int = Query(30, ge=7, le=365, description="统计天数"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取情绪统计

    分析您的情绪趋势和模式
    """
    user_id = int(current_user['sub'])

    stats = mental_health_service.mood_tracking.get_mood_statistics(user_id, days)

    return stats


@router.get("/mood/options")
async def get_mood_options(current_user: dict = Depends(get_current_user)):
    """
    获取情绪选项
    """
    moods = [
        {'value': m.value, 'label': m.value, 'emoji': _get_mood_emoji(m)}
        for m in MoodLevel
    ]
    triggers = [{'value': t.value, 'label': t.value} for t in MoodTrigger]

    return {
        'moods': moods,
        'triggers': triggers
    }


def _get_mood_emoji(mood: MoodLevel) -> str:
    """获取情绪对应的表情"""
    emoji_map = {
        MoodLevel.VERY_HAPPY: "😄",
        MoodLevel.HAPPY: '🙂',
        MoodLevel.NEUTRAL: '😐',
        MoodLevel.SAD: '😢',
        MoodLevel.VERY_SAD: '😭',
        MoodLevel.ANXIOUS: '😰',
        MoodLevel.ANGRY: '😠',
        MoodLevel.LONELY: '😔'
    }
    return emoji_map.get(mood, '😐')


# ==================== 心理评估API ====================

@router.get("/assessments/types")
async def get_assessment_types(current_user: dict = Depends(get_current_user)):
    """
    获取可用的评估类型
    """
    types = [
        {
            'type': AssessmentType.DEPRESSION.value,
            'name': '抑郁筛查',
            'description': '快速评估抑郁风险',
            'duration': '2分钟'
        },
        {
            'type': AssessmentType.ANXIETY.value,
            'name': '焦虑筛查',
            'description': '评估焦虑水平',
            'duration': '2分钟'
        },
        {
            'type': AssessmentType.LONELINESS.value,
            'name': '孤独感评估',
            'description': '了解您的社交状态',
            'duration': '2分钟'
        },
        {
            'type': AssessmentType.LIFE_SATISFACTION.value,
            'name': '生活满意度',
            'description': '评估对生活的满意程度',
            'duration': "2分钟"
        }
    ]

    return {"assessment_types": types}


@router.get("/assessments/{assessment_type}/questions")
async def get_assessment_questions(
    assessment_type: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取评估问题
    """
    try:
        atype = AssessmentType(assessment_type)
    except ValueError:
        valid_types = [t.value for t in AssessmentType]
        raise HTTPException(status_code=400, detail=f"无效的评估类型，可选: {valid_types}")

    questions = mental_health_service.assessment.get_assessment_questions(atype)

    return {
        "assessment_type": assessment_type,
        'questions': questions,
        "total_questions": len(questions),
        'instructions': "请根据过去两周的感受选择最符合的选项"
    }


@router.post("/assessments/submit")
async def submit_assessment(
    request: SubmitAssessmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交评估

    提交完成的心理评估
    """
    user_id = int(current_user['sub'])

    try:
        atype = AssessmentType(request.assessment_type)
    except ValueError:
        valid_types = [t.value for t in AssessmentType]
        raise HTTPException(status_code=400, detail=f"无效的评估类型，可选: {valid_types}")

    result = mental_health_service.assessment.submit_assessment(
        user_id, atype, request.answers
    )

    return {
        'success': True,
        'result': result.to_dict(),
        'message': "评估完成"
    }


@router.get("/assessments/history")
async def get_assessment_history(
    assessment_type: Optional[str] = Query(None, description="评估类型筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取评估历史
    """
    user_id = int(current_user['sub'])

    atype = None
    if assessment_type:
        try:
            atype = AssessmentType(assessment_type)
        except ValueError:
            pass

    results = mental_health_service.assessment.get_user_assessments(user_id, atype)

    return {
        'results': [r.to_dict() for r in results],
        'count': len(results)
    }


# ==================== 放松训练API ====================

@router.get("/relaxation/exercises")
async def get_relaxation_exercises(
    exercise_type: Optional[str] = Query(None, description='练习类型'),
    max_duration: Optional[int] = Query(None, ge=1, description="最大时长(分钟)"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取放松练习列表
    """
    type_filter = None
    if exercise_type:
        try:
            type_filter = RelaxationType(exercise_type)
        except ValueError:
            pass

    exercises = mental_health_service.relaxation.get_exercises(type_filter, max_duration)

    return {
        'exercises': [e.to_dict() for e in exercises],
        'count': len(exercises)
    }


@router.get("/relaxation/exercises/{exercise_id}")
async def get_relaxation_exercise_detail(
    exercise_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取放松练习详情
    """
    exercise = mental_health_service.relaxation.exercises.get(exercise_id)

    if not exercise:
        raise HTTPException(status_code=404, detail='练习不存在')

    return {
        "exercise": exercise.to_dict()
    }


@router.get("/relaxation/recommended")
async def get_recommended_exercise(
    mood_score: Optional[int] = Query(None, ge=1, le=5, description="当前心情(1-5)"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取推荐的放松练习

    根据您的心情推荐合适的练习
    """
    exercise = mental_health_service.relaxation.get_recommended_exercise(mood_score)

    return {
        'exercise': exercise.to_dict(),
        'reason': "根据您当前的状态，推荐这个练习"
    }


@router.post("/relaxation/sessions")
async def record_relaxation_session(
    request: RecordRelaxationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    记录放松训练

    记录完成的放松练习
    """
    user_id = int(current_user['sub'])

    session = mental_health_service.relaxation.record_session(
        user_id,
        request.exercise_id,
        request.duration_minutes,
        request.mood_before,
        request.mood_after,
        request.notes
    )

    if not session:
        raise HTTPException(status_code=404, detail="练习不存在")

    mood_change = ""
    if request.mood_before and request.mood_after:
        if request.mood_after > request.mood_before:
            mood_change = "，心情有所改善，继续保持！"
        elif request.mood_after == request.mood_before:
            mood_change = "，继续坚持练习会有更好的效果"

    return {
        'success': True,
        'session': session.to_dict(),
        "message": f"放松训练已完成{mood_change}"
    }


@router.get("/relaxation/history")
async def get_relaxation_history(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取放松训练历史
    """
    user_id = int(current_user['sub'])

    sessions = mental_health_service.relaxation.get_user_sessions(user_id, days)

    return {
        'sessions': [s.to_dict() for s in sessions],
        'count': len(sessions),
        "total_minutes": sum(s.duration_minutes for s in sessions)
    }


@router.get("/relaxation/types")
async def get_relaxation_types(current_user: dict = Depends(get_current_user)):
    """
    获取放松练习类型
    """
    types = [
        {'value': t.value, 'label': t.value}
        for t in RelaxationType
    ]

    return {'types': types}


# ==================== 心理支持资源API ====================

@router.get("/support/resources")
async def get_support_resources(
    resource_type: Optional[str] = Query(None, description="资源类型: hotline/article/video"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取支持资源

    心理健康支持资源列表
    """
    resources = mental_health_service.support.get_resources(resource_type)

    return {
        'resources': [r.to_dict() for r in resources],
        'count': len(resources)
    }


@router.get("/support/hotlines")
async def get_emergency_hotlines(current_user: dict = Depends(get_current_user)):
    """
    获取紧急求助热线

    24小时心理援助热线
    """
    hotlines = mental_health_service.support.get_emergency_hotlines()

    return {
        'hotlines': [h.to_dict() for h in hotlines],
        'message': "如果您感到非常难过或有伤害自己的想法，请立即拨打求助热线"
    }


# ==================== 心理健康仪表板API ====================

@router.get("/dashboard")
async def get_mental_health_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取心理健康仪表板

    综合展示心理健康数据
    """
    user_id = int(current_user['sub'])

    summary = mental_health_service.get_mental_health_summary(user_id)

    # 推荐练习
    mood_score = 3
    if summary['mood']['today']:
        mood_value = summary['mood']['today']['mood']
        mood_score_map = {
            'very_happy': 5, 'happy': 4, 'neutral': 3,
            'sad': 2, 'very_sad': 1, 'anxious': 2,
            'angry': 2, 'lonely': 2
        }
        mood_score = mood_score_map.get(mood_value, 3)

    recommended = mental_health_service.relaxation.get_recommended_exercise(mood_score)

    return {
        "summary": summary,
        "recommended_exercise": recommended.to_dict() if recommended else None,
        'daily_tip': _get_daily_tip(),
        'encouragement': "关注自己的心理健康，和身体健康同样重要"
    }


def _get_daily_tip() -> str:
    """获取每日提示"""
    tips = [
        "每天花几分钟做深呼吸，能有效减轻压力",
        '保持规律的作息对心理健康很重要',
        '和亲朋好友聊天是最好的心灵慰藉',
        '适当的运动能改善心情',
        '写下今天值得感恩的三件小事',
        '接受自己的情绪，无论好坏都是正常的',
        '做一件让自己开心的小事'
    ]
    import random
    return random.choice(tips)


@router.get("/summary")
async def get_mental_health_summary(current_user: dict = Depends(get_current_user)):
    """
    获取心理健康摘要
    """
    user_id = int(current_user['sub'])

    summary = mental_health_service.get_mental_health_summary(user_id)

    return summary
