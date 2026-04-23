"""
认知训练模块 API 路由

提供认知游戏、评估、训练计划等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import random
import json

from app.models.database import get_db
from app.models.database import (
    CognitiveGame, CognitiveGameSession, CognitiveAssessment,
    CognitiveTrainingPlan, User
)
from app.schemas.cognitive import (
    # 游戏相关
    CognitiveGameCreate, CognitiveGameUpdate, CognitiveGameResponse, CognitiveGameBrief,
    GameType, SessionStatus,
    # 游戏会话
    StartGameSessionRequest, StartGameSessionResponse,
    SubmitGameAnswerRequest, SubmitGameAnswerResponse,
    EndGameSessionRequest, GameSessionResponse, GameSessionDetailResponse,
    # 认知评估
    AssessmentType, CognitiveLevel, Trend,
    StartAssessmentRequest, StartAssessmentResponse,
    SubmitAssessmentRequest, CognitiveAssessmentResponse, AssessmentResultResponse,
    # 训练计划
    CognitiveTrainingPlanCreate, CognitiveTrainingPlanUpdate, CognitiveTrainingPlanResponse,
    # 统计与报告
    CognitiveStatsRequest, CognitiveStatsResponse, DimensionStats,
    GenerateTrainingReportRequest, TrainingReportResponse,
    # 推荐
    GetRecommendedGamesRequest, GetRecommendedGamesResponse, RecommendedGame
)

router = APIRouter(prefix="/cognitive", tags=['认知训练'])


# ==================== 游戏管理 ====================

@router.post('/games', response_model=CognitiveGameResponse, summary='创建认知游戏')
async def create_cognitive_game(
    game_data: CognitiveGameCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的认知游戏配置

    - **name**: 游戏名称
    - **game_type**: 游戏类型 (memory/attention/calculation/language/spatial)
    - **difficulty_levels**: 难度级别数
    """
    game = CognitiveGame(
        name=game_data.name,
        game_type=game_data.game_type.value,
        difficulty_levels=game_data.difficulty_levels,
        description=game_data.description,
        instructions=game_data.instructions,
        benefits=game_data.benefits,
        config=json.dumps(game_data.config) if game_data.config else None,
        icon_url=game_data.icon_url,
        is_active=True
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    return _format_game_response(game)


@router.get('/games', response_model=List[CognitiveGameResponse], summary='获取游戏列表')
async def get_cognitive_games(
    game_type: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """获取认知游戏列表"""
    query = db.query(CognitiveGame)

    if game_type:
        query = query.filter(CognitiveGame.game_type == game_type)
    if is_active is not None:
        query = query.filter(CognitiveGame.is_active == is_active)

    games = query.all()
    return [_format_game_response(g) for g in games]


@router.get("/games/{game_id}", response_model=CognitiveGameResponse, summary='获取游戏详情')
async def get_cognitive_game(game_id: int, db: Session = Depends(get_db)):
    """获取指定认知游戏的详细信息"""
    game = db.query(CognitiveGame).filter(CognitiveGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在')
    return _format_game_response(game)


@router.put("/games/{game_id}", response_model=CognitiveGameResponse, summary='更新游戏')
async def update_cognitive_game(
    game_id: int,
    update_data: CognitiveGameUpdate,
    db: Session = Depends(get_db)
):
    """更新认知游戏配置"""
    game = db.query(CognitiveGame).filter(CognitiveGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在')

    update_dict = update_data.model_dump(exclude_unset=True)
    if 'config' in update_dict and update_dict['config']:
        update_dict['config'] = json.dumps(update_dict['config'])

    for key, value in update_dict.items():
        setattr(game, key, value)

    game.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(game)

    return _format_game_response(game)


# ==================== 游戏会话 ====================

@router.post("/sessions/start", response_model=StartGameSessionResponse, summary='开始游戏会话')
async def start_game_session(
    request: StartGameSessionRequest,
    db: Session = Depends(get_db)
):
    """
    开始一个新的游戏会话

    返回游戏数据（题目等）供前端展示
    """
    # 验证用户和游戏
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    game = db.query(CognitiveGame).filter(
        CognitiveGame.id == request.game_id,
        CognitiveGame.is_active == True
    ).first()
    if not game:
        raise HTTPException(status_code=404, detail='游戏不存在或已停用')

    # 验证难度级别
    if request.difficulty > game.difficulty_levels:
        raise HTTPException(status_code=400, detail=f'难度级别不能超过 {game.difficulty_levels}')

    # 生成游戏数据
    game_data = _generate_game_data(game.game_type, request.difficulty)

    # 创建游戏会话
    session = CognitiveGameSession(
        user_id=request.user_id,
        game_id=request.game_id,
        difficulty=request.difficulty,
        score=0,
        max_score=game_data.get('max_score', 100),
        status="in_progress",
        game_data=json.dumps(game_data),
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return StartGameSessionResponse(
        session_id=session.id,
        game=CognitiveGameBrief(
            id=game.id,
            name=game.name,
            game_type=game.game_type,
            difficulty_levels=game.difficulty_levels,
            icon_url=game.icon_url
        ),
        difficulty=request.difficulty,
        game_data=game_data
    )


@router.post("/sessions/answer", response_model=SubmitGameAnswerResponse, summary='提交游戏答案')
async def submit_game_answer(
    request: SubmitGameAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    提交游戏答案并获取反馈

    返回答案正确性、当前得分、下一题等
    """
    session = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.id == request.session_id,
        CognitiveGameSession.status == "in_progress"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="游戏会话不存在或已结束")

    # 解析游戏数据
    game_data = json.loads(session.game_data) if session.game_data else {}
    current_question_index = game_data.get('current_question_index', 0)
    questions = game_data.get('questions', [])

    if current_question_index >= len(questions):
        raise HTTPException(status_code=400, detail='没有更多题目')

    current_question = questions[current_question_index]
    correct_answer = current_question.get('answer')

    # 判断答案是否正确
    is_correct = _check_answer(request.answer, correct_answer)

    # 更新得分
    if is_correct:
        points = current_question.get('points', 10)
        session.score += points

    # 记录答题时间
    if request.time_taken_seconds:
        total_time = game_data.get("total_time_seconds", 0)
        game_data["total_time_seconds"] = total_time + request.time_taken_seconds

    # 移动到下一题
    game_data["current_question_index"] = current_question_index + 1
    session.game_data = json.dumps(game_data)

    # 生成反馈
    feedback = _generate_feedback(is_correct, current_question)

    # 获取下一题（如果有）
    next_question = None
    if current_question_index + 1 < len(questions):
        next_q = questions[current_question_index + 1]
        next_question = {
            "question_index": current_question_index + 1,
            'question': next_q.get('question'),
            'options': next_q.get('options'),
            'type': next_q.get('type')
        }

    db.commit()

    return SubmitGameAnswerResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        current_score=session.score,
        feedback=feedback,
        next_question=next_question
    )


@router.post("/sessions/end", response_model=GameSessionResponse, summary='结束游戏会话')
async def end_game_session(
    request: EndGameSessionRequest,
    db: Session = Depends(get_db)
):
    """
    结束游戏会话

    - **abandon**: 是否放弃游戏（未完成）
    """
    session = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.id == request.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail='游戏会话不存在')

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail='游戏会话已结束')

    # 设置状态
    session.status = 'abandoned' if request.abandon else 'completed'
    session.ended_at = datetime.utcnow()

    # 计算完成时间和准确率
    if session.started_at and session.ended_at:
        session.completion_time_seconds = int(
            (session.ended_at - session.started_at).total_seconds()
        )

    # 计算准确率
    game_data = json.loads(session.game_data) if session.game_data else {}
    total_questions = len(game_data.get('questions', []))
    answered = game_data.get("current_question_index", 0)
    if total_questions > 0 and session.max_score > 0:
        session.accuracy = session.score / session.max_score

    db.commit()
    db.refresh(session)

    return _format_session_response(session)


@router.get("/sessions/{session_id}", response_model=GameSessionDetailResponse, summary='获取会话详情')
async def get_game_session_detail(
    session_id: int,
    db: Session = Depends(get_db)
):
    """获取游戏会话详细信息"""
    session = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail='游戏会话不存在')

    game = db.query(CognitiveGame).filter(CognitiveGame.id == session.game_id).first()

    # 性能分析
    performance_analysis = None
    if session.status == 'completed':
        performance_analysis = _analyze_game_performance(session)

    return GameSessionDetailResponse(
        session=_format_session_response(session),
        game=CognitiveGameBrief(
            id=game.id,
            name=game.name,
            game_type=game.game_type,
            difficulty_levels=game.difficulty_levels,
            icon_url=game.icon_url
        ) if game else None,
        game_data=json.loads(session.game_data) if session.game_data else None,
        performance_analysis=performance_analysis
    )


@router.get("/sessions/user/{user_id}", response_model=List[GameSessionResponse], summary='获取用户游戏记录')
async def get_user_game_sessions(
    user_id: int,
    game_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取用户的游戏会话历史"""
    query = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.user_id == user_id
    )

    if game_type:
        query = query.join(CognitiveGame).filter(CognitiveGame.game_type == game_type)
    if status:
        query = query.filter(CognitiveGameSession.status == status)

    sessions = query.order_by(desc(CognitiveGameSession.created_at)).limit(limit).all()
    return [_format_session_response(s) for s in sessions]


# ==================== 认知评估 ====================

@router.post("/assessments/start", response_model=StartAssessmentResponse, summary='开始认知评估')
async def start_cognitive_assessment(
    request: StartAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    开始认知评估

    - **assessment_type**: 评估类型 (mmse/moca/custom/daily)
    """
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    # 生成评估题目
    questions = _generate_assessment_questions(request.assessment_type.value)

    # 创建评估记录
    assessment = CognitiveAssessment(
        user_id=request.user_id,
        assessment_type=request.assessment_type.value,
        assessment_date=datetime.utcnow(),
        total_score=0,
        max_score=sum(q.get('max_points', 1) for q in questions),
        dimension_scores=json.dumps({'questions': questions, 'answers': []})
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return StartAssessmentResponse(
        assessment_id=assessment.id,
        assessment_type=assessment.assessment_type,
        total_questions=len(questions),
        questions=questions
    )


@router.post("/assessments/submit", response_model=AssessmentResultResponse, summary='提交评估答案')
async def submit_cognitive_assessment(
    request: SubmitAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    提交认知评估答案并获取结果
    """
    assessment = db.query(CognitiveAssessment).filter(
        CognitiveAssessment.id == request.assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail='评估记录不存在')

    if assessment.total_score > 0:
        raise HTTPException(status_code=400, detail='评估已完成')

    # 解析评估数据
    assessment_data = json.loads(assessment.dimension_scores) if assessment.dimension_scores else {}
    questions = assessment_data.get('questions', [])

    # 计算各维度得分
    dimension_scores = {}
    total_score = 0

    for answer in request.answers:
        question_id = answer.get('question_id')
        user_answer = answer.get('answer')

        # 找到对应题目
        question = next((q for q in questions if q.get('id') == question_id), None)
        if question:
            dimension = question.get('dimension', 'general')
            max_points = question.get('max_points', 1)

            # 评分（简化逻辑）
            score = _score_assessment_answer(question, user_answer)
            total_score += score

            if dimension not in dimension_scores:
                dimension_scores[dimension] = {'score': 0, 'max': 0}
            dimension_scores[dimension]['score'] += score
            dimension_scores[dimension]['max'] += max_points

    # 更新评估记录
    assessment.total_score = total_score
    assessment.dimension_scores = json.dumps(dimension_scores)

    # 确定认知水平
    score_ratio = total_score / assessment.max_score if assessment.max_score > 0 else 0
    if score_ratio >= 0.9:
        cognitive_level = 'normal'
    elif score_ratio >= 0.7:
        cognitive_level = "mild_decline"
    elif score_ratio >= 0.5:
        cognitive_level = "moderate_decline"
    else:
        cognitive_level = "severe_decline"

    assessment.cognitive_level = cognitive_level

    # 计算趋势（与上次评估比较）
    previous = db.query(CognitiveAssessment).filter(
        CognitiveAssessment.user_id == assessment.user_id,
        CognitiveAssessment.id != assessment.id,
        CognitiveAssessment.assessment_type == assessment.assessment_type,
        CognitiveAssessment.total_score > 0
    ).order_by(desc(CognitiveAssessment.assessment_date)).first()

    trend = "stable"
    comparison = None
    if previous:
        prev_ratio = previous.total_score / previous.max_score if previous.max_score > 0 else 0
        diff = score_ratio - prev_ratio
        if diff > 0.05:
            trend = 'improving'
        elif diff < -0.05:
            trend = 'declining'

        comparison = {
            "previous_score": previous.total_score,
            "previous_max": previous.max_score,
            "previous_date": previous.assessment_date.isoformat(),
            "score_change": total_score - previous.total_score,
            'trend': trend
        }

    assessment.trend = trend

    # 生成分析和建议
    analysis = _generate_assessment_analysis(dimension_scores, cognitive_level)
    recommendations = _generate_assessment_recommendations(dimension_scores, cognitive_level)

    assessment.analysis = analysis
    assessment.recommendations = json.dumps(recommendations)

    # 检查是否需要通知家属
    if cognitive_level in ['moderate_decline', 'severe_decline']:
        assessment.notified_family = True
        assessment.notification_level = 'warning' if cognitive_level == 'moderate_decline' else 'critical'

    db.commit()
    db.refresh(assessment)

    # 生成训练计划建议
    training_plan = _generate_training_plan_suggestion(dimension_scores, cognitive_level)

    return AssessmentResultResponse(
        assessment=_format_assessment_response(assessment),
        comparison_with_previous=comparison,
        detailed_analysis={
            "dimension_breakdown": dimension_scores,
            "score_percentage": round(score_ratio * 100, 1),
            'analysis': analysis
        },
        personalized_recommendations=recommendations,
        suggested_training_plan=training_plan
    )


@router.get("/assessments/{assessment_id}", response_model=CognitiveAssessmentResponse, summary='获取评估详情')
async def get_assessment_detail(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """获取认知评估详细结果"""
    assessment = db.query(CognitiveAssessment).filter(
        CognitiveAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail='评估记录不存在')

    return _format_assessment_response(assessment)


@router.get("/assessments/user/{user_id}", response_model=List[CognitiveAssessmentResponse], summary='获取用户评估历史')
async def get_user_assessments(
    user_id: int,
    assessment_type: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取用户的认知评估历史记录"""
    query = db.query(CognitiveAssessment).filter(
        CognitiveAssessment.user_id == user_id,
        CognitiveAssessment.total_score > 0  # 只返回已完成的
    )

    if assessment_type:
        query = query.filter(CognitiveAssessment.assessment_type == assessment_type)

    assessments = query.order_by(desc(CognitiveAssessment.assessment_date)).limit(limit).all()
    return [_format_assessment_response(a) for a in assessments]


# ==================== 训练计划 ====================

@router.post("/training-plans", response_model=CognitiveTrainingPlanResponse, summary='创建训练计划')
async def create_training_plan(
    plan_data: CognitiveTrainingPlanCreate,
    db: Session = Depends(get_db)
):
    """
    创建个性化认知训练计划
    """
    user = db.query(User).filter(User.id == plan_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    plan = CognitiveTrainingPlan(
        user_id=plan_data.user_id,
        name=plan_data.name,
        description=plan_data.description,
        target_dimensions=json.dumps(plan_data.target_dimensions) if plan_data.target_dimensions else None,
        weekly_sessions=plan_data.weekly_sessions,
        session_duration_minutes=plan_data.session_duration_minutes,
        games_config=json.dumps([g.model_dump() for g in plan_data.games_config]) if plan_data.games_config else None,
        schedule_days=json.dumps(plan_data.schedule_days) if plan_data.schedule_days else None,
        schedule_time=plan_data.schedule_time,
        start_date=plan_data.start_date,
        end_date=plan_data.end_date,
        reminder_enabled=plan_data.reminder_enabled,
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return _format_training_plan_response(plan)


@router.get("/training-plans/{plan_id}", response_model=CognitiveTrainingPlanResponse, summary='获取训练计划详情')
async def get_training_plan(plan_id: int, db: Session = Depends(get_db)):
    """获取训练计划详情"""
    plan = db.query(CognitiveTrainingPlan).filter(CognitiveTrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail='训练计划不存在')
    return _format_training_plan_response(plan)


@router.put("/training-plans/{plan_id}", response_model=CognitiveTrainingPlanResponse, summary='更新训练计划')
async def update_training_plan(
    plan_id: int,
    update_data: CognitiveTrainingPlanUpdate,
    db: Session = Depends(get_db)
):
    """更新训练计划"""
    plan = db.query(CognitiveTrainingPlan).filter(CognitiveTrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail='训练计划不存在')

    update_dict = update_data.model_dump(exclude_unset=True)

    # 处理JSON字段
    if 'target_dimensions' in update_dict and update_dict['target_dimensions']:
        update_dict['target_dimensions'] = json.dumps(update_dict['target_dimensions'])
    if 'games_config' in update_dict and update_dict['games_config']:
        update_dict['games_config'] = json.dumps([g.model_dump() for g in update_dict['games_config']])
    if 'schedule_days' in update_dict and update_dict['schedule_days']:
        update_dict['schedule_days'] = json.dumps(update_dict['schedule_days'])

    for key, value in update_dict.items():
        setattr(plan, key, value)

    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)

    return _format_training_plan_response(plan)


@router.delete("/training-plans/{plan_id}", summary='删除训练计划')
async def delete_training_plan(plan_id: int, db: Session = Depends(get_db)):
    """删除训练计划"""
    plan = db.query(CognitiveTrainingPlan).filter(CognitiveTrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail='训练计划不存在')

    # 软删除
    plan.is_active = False
    plan.updated_at = datetime.utcnow()
    db.commit()

    return {'message': '训练计划已删除'}


@router.get("/training-plans/user/{user_id}", response_model=List[CognitiveTrainingPlanResponse], summary='获取用户训练计划')
async def get_user_training_plans(
    user_id: int,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """获取用户的所有训练计划"""
    query = db.query(CognitiveTrainingPlan).filter(
        CognitiveTrainingPlan.user_id == user_id
    )

    if is_active is not None:
        query = query.filter(CognitiveTrainingPlan.is_active == is_active)

    plans = query.order_by(desc(CognitiveTrainingPlan.created_at)).all()
    return [_format_training_plan_response(p) for p in plans]


# ==================== 统计与报告 ====================

@router.post("/stats", response_model=CognitiveStatsResponse, summary='获取认知统计')
async def get_cognitive_stats(
    request: CognitiveStatsRequest,
    db: Session = Depends(get_db)
):
    """
    获取用户认知训练统计数据
    """
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    start_date = datetime.utcnow() - timedelta(days=request.days)

    # 获取游戏会话统计
    sessions = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.user_id == request.user_id,
        CognitiveGameSession.created_at >= start_date,
        CognitiveGameSession.status == 'completed'
    ).all()

    total_sessions = len(sessions)
    total_time = sum(s.completion_time_seconds or 0 for s in sessions) // 60
    average_score = sum(s.accuracy or 0 for s in sessions) / total_sessions if total_sessions > 0 else 0

    # 按维度统计
    dimension_stats = _calculate_dimension_stats(sessions, db)

    # 找出最强和最弱维度
    best_dimension = max(dimension_stats, key=lambda d: d.average_score, default=DimensionStats(dimension='general', average_score=0, trend='stable', sessions_count=0))
    weakest_dimension = min(dimension_stats, key=lambda d: d.average_score, default=DimensionStats(dimension='general', average_score=0, trend='stable', sessions_count=0))

    # 获取最近评估
    recent_assessments = db.query(CognitiveAssessment).filter(
        CognitiveAssessment.user_id == request.user_id,
        CognitiveAssessment.total_score > 0
    ).order_by(desc(CognitiveAssessment.assessment_date)).limit(5).all()

    # 计算连续训练天数
    streak_days = _calculate_streak_days(request.user_id, db)

    # 整体趋势
    overall_trend = _calculate_overall_trend(sessions)

    return CognitiveStatsResponse(
        user_id=request.user_id,
        period_days=request.days,
        total_sessions=total_sessions,
        total_time_minutes=total_time,
        average_score=round(average_score * 100, 1),
        best_dimension=best_dimension.dimension,
        weakest_dimension=weakest_dimension.dimension,
        dimension_stats=dimension_stats,
        recent_assessments=[_format_assessment_response(a) for a in recent_assessments],
        overall_trend=overall_trend,
        streak_days=streak_days
    )


@router.post("/reports/generate", response_model=TrainingReportResponse, summary='生成训练报告')
async def generate_training_report(
    request: GenerateTrainingReportRequest,
    db: Session = Depends(get_db)
):
    """
    生成认知训练报告
    """
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    start_date = datetime.utcnow() - timedelta(days=request.period_days)
    end_date = datetime.utcnow()

    # 获取统计数据
    sessions = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.user_id == request.user_id,
        CognitiveGameSession.created_at >= start_date,
        CognitiveGameSession.status == 'completed'
    ).all()

    # 计划完成率
    plans = db.query(CognitiveTrainingPlan).filter(
        CognitiveTrainingPlan.user_id == request.user_id,
        CognitiveTrainingPlan.is_active == True
    ).all()

    expected_sessions = sum(p.weekly_sessions * (request.period_days // 7) for p in plans) if plans else request.period_days // 7 * 3
    completion_rate = len(sessions) / expected_sessions if expected_sessions > 0 else 0

    # 按维度的表现
    performance_by_dimension = _calculate_performance_by_dimension(sessions, db)

    # 进度图表数据
    progress_chart = _generate_progress_chart_data(sessions, request.period_days)

    # 成就
    achievements = _calculate_achievements(sessions, request.user_id, db)

    # 建议
    recommendations = _generate_training_recommendations(performance_by_dimension)

    # 生成总结
    summary = _generate_report_summary(
        total_sessions=len(sessions),
        completion_rate=completion_rate,
        performance_by_dimension=performance_by_dimension
    )

    return TrainingReportResponse(
        user_id=request.user_id,
        report_period=f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
        summary=summary,
        total_sessions=len(sessions),
        total_time_minutes=sum(s.completion_time_seconds or 0 for s in sessions) // 60,
        completion_rate=round(completion_rate * 100, 1),
        performance_by_dimension=performance_by_dimension,
        progress_chart_data=progress_chart,
        achievements=achievements,
        recommendations=recommendations,
        generated_at=datetime.utcnow()
    )


# ==================== 推荐系统 ====================

@router.post('/recommendations/games', response_model=GetRecommendedGamesResponse, summary='获取推荐游戏')
async def get_recommended_games(
    request: GetRecommendedGamesRequest,
    db: Session = Depends(get_db)
):
    """
    基于用户表现和训练计划获取推荐游戏
    """
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    # 获取用户最近的游戏表现
    recent_sessions = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.user_id == request.user_id,
        CognitiveGameSession.status == 'completed'
    ).order_by(desc(CognitiveGameSession.created_at)).limit(20).all()

    # 获取所有活跃游戏
    games = db.query(CognitiveGame).filter(CognitiveGame.is_active == True).all()

    # 计算各维度表现，找出弱项
    weak_dimensions = _find_weak_dimensions(recent_sessions, db)

    # 生成推荐
    recommended = []
    for game in games:
        # 优先推荐针对弱项维度的游戏
        priority = 1
        if game.game_type in weak_dimensions:
            priority = 3

        # 计算推荐难度
        recent_game_sessions = [s for s in recent_sessions if s.game_id == game.id]
        if recent_game_sessions:
            avg_accuracy = sum(s.accuracy or 0 for s in recent_game_sessions) / len(recent_game_sessions)
            if avg_accuracy > 0.8:
                recommended_difficulty = min(game.difficulty_levels, int(recent_game_sessions[0].difficulty) + 1)
            elif avg_accuracy < 0.5:
                recommended_difficulty = max(1, int(recent_game_sessions[0].difficulty) - 1)
            else:
                recommended_difficulty = int(recent_game_sessions[0].difficulty)
        else:
            recommended_difficulty = 1

        reason = _generate_recommendation_reason(game, weak_dimensions, recent_game_sessions)
        benefit = _generate_expected_benefit(game)

        recommended.append({
            'game': game,
            'difficulty': recommended_difficulty,
            'reason': reason,
            'benefit': benefit,
            'priority': priority
        })

    # 按优先级排序并取前N个
    recommended.sort(key=lambda x: x['priority'], reverse=True)
    recommended = recommended[:request.limit]

    # 检查今日目标
    today = datetime.utcnow().date()
    today_sessions = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.user_id == request.user_id,
        func.date(CognitiveGameSession.created_at) == today,
        CognitiveGameSession.status == 'completed'
    ).count()

    # 获取下次计划时间
    active_plan = db.query(CognitiveTrainingPlan).filter(
        CognitiveTrainingPlan.user_id == request.user_id,
        CognitiveTrainingPlan.is_active == True
    ).first()

    next_scheduled = None
    if active_plan and active_plan.schedule_time:
        # 简化：返回今天或明天的计划时间
        schedule_time = datetime.strptime(active_plan.schedule_time, '%H:%M').time()
        next_scheduled = datetime.combine(today, schedule_time)
        if next_scheduled < datetime.utcnow():
            next_scheduled = datetime.combine(today + timedelta(days=1), schedule_time)

    return GetRecommendedGamesResponse(
        recommended_games=[
            RecommendedGame(
                game=CognitiveGameBrief(
                    id=r['game'].id,
                    name=r['game'].name,
                    game_type=r['game'].game_type,
                    difficulty_levels=r['game'].difficulty_levels,
                    icon_url=r['game'].icon_url
                ),
                recommended_difficulty=r['difficulty'],
                reason=r['reason'],
                expected_benefit=r['benefit']
            ) for r in recommended
        ],
        daily_goal_completed=today_sessions >= 3,  # 每日目标：3次训练
        next_scheduled_session=next_scheduled
    )


# ==================== 辅助函数 ====================

def _format_game_response(game: CognitiveGame) -> CognitiveGameResponse:
    """格式化游戏响应"""
    return CognitiveGameResponse(
        id=game.id,
        name=game.name,
        game_type=game.game_type,
        difficulty_levels=game.difficulty_levels,
        description=game.description,
        instructions=game.instructions,
        benefits=game.benefits,
        config=json.loads(game.config) if game.config else None,
        icon_url=game.icon_url,
        is_active=game.is_active,
        created_at=game.created_at
    )


def _format_session_response(session: CognitiveGameSession) -> GameSessionResponse:
    """格式化会话响应"""
    return GameSessionResponse(
        id=session.id,
        user_id=session.user_id,
        game_id=session.game_id,
        difficulty=session.difficulty,
        score=session.score,
        max_score=session.max_score,
        accuracy=session.accuracy,
        completion_time_seconds=session.completion_time_seconds,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at
    )


def _format_assessment_response(assessment: CognitiveAssessment) -> CognitiveAssessmentResponse:
    """格式化评估响应"""
    return CognitiveAssessmentResponse(
        id=assessment.id,
        user_id=assessment.user_id,
        assessment_type=assessment.assessment_type,
        assessment_date=assessment.assessment_date,
        dimension_scores=json.loads(assessment.dimension_scores) if assessment.dimension_scores else None,
        total_score=assessment.total_score,
        max_score=assessment.max_score,
        percentile=assessment.percentile,
        cognitive_level=assessment.cognitive_level,
        trend=assessment.trend,
        analysis=assessment.analysis,
        recommendations=json.loads(assessment.recommendations) if assessment.recommendations else None,
        notified_family=assessment.notified_family,
        notification_level=assessment.notification_level,
        created_at=assessment.created_at
    )


def _format_training_plan_response(plan: CognitiveTrainingPlan) -> CognitiveTrainingPlanResponse:
    """格式化训练计划响应"""
    return CognitiveTrainingPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        target_dimensions=json.loads(plan.target_dimensions) if plan.target_dimensions else None,
        weekly_sessions=plan.weekly_sessions,
        session_duration_minutes=plan.session_duration_minutes,
        games_config=json.loads(plan.games_config) if plan.games_config else None,
        schedule_days=json.loads(plan.schedule_days) if plan.schedule_days else None,
        schedule_time=plan.schedule_time,
        start_date=plan.start_date,
        end_date=plan.end_date,
        reminder_enabled=plan.reminder_enabled,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


def _generate_game_data(game_type: str, difficulty: int) -> dict:
    """
    生成游戏数据（题目）

    实际项目中应该从题库读取或动态生成
    """
    questions = []
    num_questions = 5 + difficulty * 2  # 难度越高题目越多

    if game_type == 'memory':
        # 记忆力游戏 - 数字记忆
        for i in range(num_questions):
            length = 3 + difficulty + i // 3
            sequence = [random.randint(0, 9) for _ in range(length)]
            questions.append({
                'id': i + 1,
                'type': "sequence_recall",
                'question': f"请记住这组数字：{' '.join(map(str, sequence))}",
                'answer': sequence,
                'points': length * 2,
                'time_limit': length * 3
            })

    elif game_type == 'attention':
        # 注意力游戏 - 找不同
        for i in range(num_questions):
            target = random.choice(['A', 'B', 'C', 'D'])
            options = ['A', 'B', 'C', 'D']
            questions.append({
                'id': i + 1,
                'type': "find_target",
                'question': f"在下面的选项中找到 '{target}'",
                'options': options,
                'answer': target,
                'points': 10,
                'time_limit': 10 - difficulty
            })

    elif game_type == "calculation":
        # 计算游戏
        for i in range(num_questions):
            a = random.randint(1, 10 * difficulty)
            b = random.randint(1, 10 * difficulty)
            op = random.choice(["+", '-']) if difficulty < 3 else random.choice(['+', '-', '*'])

            if op == '+':
                answer = a + b
            elif op == '-':
                a, b = max(a, b), min(a, b)  # 确保结果为正
                answer = a - b
            else:
                answer = a * b

            questions.append({
                'id': i + 1,
                'type': 'arithmetic',
                'question': f'{a} {op} {b} = ?',
                'answer': answer,
                'points': 10 + (5 if op == '*' else 0),
                'time_limit': 15
            })

    elif game_type == 'language':
        # 语言游戏 - 词语联想
        word_pairs = [
            ('天空', '蓝色'), ('苹果', '红色'), ('草地', '绿色'),
            ('太阳', '温暖'), ('冬天', '寒冷'), ('春天', '花开')
        ]
        random.shuffle(word_pairs)
        for i, (word, related) in enumerate(word_pairs[:num_questions]):
            questions.append({
                'id': i + 1,
                'type': "word_association",
                'question': f"'{word}' 最常让人联想到什么？",
                'options': [related, '汽车', '电脑', '手机'],
                'answer': related,
                'points': 10
            })

    elif game_type == 'spatial':
        # 空间游戏 - 图形旋转
        directions = ['上', '下', '左', '右']
        for i in range(num_questions):
            start = random.choice(directions)
            rotations = random.randint(1, 3)
            # 简化：只计算90度旋转
            idx = directions.index(start)
            end_idx = (idx + rotations) % 4
            questions.append({
                'id': i + 1,
                'type': 'rotation',
                'question': f"箭头指向'{start}'，顺时针旋转{rotations * 90}度后指向哪里？",
                'options': directions,
                'answer': directions[end_idx],
                'points': 10 + rotations * 5
            })

    else:
        # 默认：混合题型
        questions = [
            {
                'id': 1,
                'type': 'general',
                'question': '今天星期几？',
                'options': ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'],
                'answer': None,  # 答案需要实时判断
                'points': 5
            }
        ]

    return {
        'questions': questions,
        "current_question_index": 0,
        'max_score': sum(q.get('points', 10) for q in questions),
        "total_time_seconds": 0
    }


def _check_answer(user_answer, correct_answer) -> bool:
    """检查答案是否正确"""
    if isinstance(correct_answer, list):
        if isinstance(user_answer, list):
            return user_answer == correct_answer
        return False
    return str(user_answer).lower().strip() == str(correct_answer).lower().strip()


def _generate_feedback(is_correct: bool, question: dict) -> str:
    """生成答题反馈"""
    if is_correct:
        feedbacks = [
            '回答正确！继续保持！',
            '太棒了！答对了！',
            '非常好！思维很敏捷！',
            "正确！您的记忆力真好！"
        ]
    else:
        feedbacks = [
            "这道题有点难度，下次再试试看。",
            "没关系，我们继续下一题。",
            "加油！下一题会更简单的。"
        ]
    return random.choice(feedbacks)


def _analyze_game_performance(session: CognitiveGameSession) -> dict:
    """分析游戏表现"""
    game_data = json.loads(session.game_data) if session.game_data else {}

    return {
        "score_percentage": round((session.accuracy or 0) * 100, 1),
        'time_efficiency': '良好' if session.completion_time_seconds and session.completion_time_seconds < 300 else '需要加强',
        'difficulty_rating': '适中' if session.accuracy and 0.5 <= session.accuracy <= 0.8 else ('偏难' if session.accuracy and session.accuracy < 0.5 else '偏易'),
        'recommendation': '建议提高难度' if session.accuracy and session.accuracy > 0.8 else ('建议降低难度' if session.accuracy and session.accuracy < 0.5 else "当前难度合适")
    }


def _generate_assessment_questions(assessment_type: str) -> list:
    """生成评估题目"""
    if assessment_type == 'mmse':
        # 简化版MMSE
        return [
            {'id': 1, 'dimension': 'orientation', 'question': '请问今天是几月几日？', 'type': 'text', 'max_points': 2},
            {'id': 2, 'dimension': 'orientation', 'question': '请问现在是什么季节？', 'type': 'choice', 'options': ['春天', '夏天', '秋天', '冬天'], 'max_points': 1},
            {'id': 3, 'dimension': 'memory', 'question': '请记住这三个词：苹果、桌子、硬币', 'type': 'recall', 'max_points': 3},
            {'id': 4, 'dimension': 'attention', 'question': '请从100开始，每次减7，说出连续5个数', 'type': 'calculation', 'max_points': 5},
            {'id': 5, 'dimension': 'language', 'question': '请说出这是什么（图片：手表）', 'type': 'naming', 'max_points': 1},
            {'id': 6, 'dimension': 'memory', 'question': '请回忆刚才记住的三个词', 'type': 'delayed_recall', 'max_points': 3},
        ]
    elif assessment_type == 'daily':
        # 日常简易评估
        return [
            {'id': 1, 'dimension': 'memory', 'question': '请记住这5个词：蓝色、汽车、花朵、医院、快乐', 'type': 'recall', 'max_points': 5},
            {'id': 2, 'dimension': 'calculation', 'question': '25 + 17 = ?', 'type': 'arithmetic', 'answer': 42, 'max_points': 2},
            {'id': 3, 'dimension': 'attention', 'question': '请按顺序点击: 1-A-2-B-3-C', 'type': 'sequence', 'max_points': 3},
            {'id': 4, 'dimension': 'memory', 'question': '请回忆刚才的5个词', 'type': 'delayed_recall', 'max_points': 5},
        ]
    else:
        # 自定义评估
        return [
            {'id': 1, 'dimension': 'general', 'question': '请说出今天的日期', 'type': 'text', 'max_points': 2},
            {'id': 2, 'dimension': 'memory', 'question': '请记住：红色、蓝色、绿色', 'type': 'recall', 'max_points': 3},
            {'id': 3, 'dimension': 'calculation', 'question': '8 × 7 = ?', 'type': 'arithmetic', 'answer': 56, 'max_points': 2},
        ]


def _score_assessment_answer(question: dict, answer) -> int:
    """评分评估答案"""
    max_points = question.get('max_points', 1)
    correct_answer = question.get('answer')

    if question.get('type') == 'arithmetic':
        try:
            return max_points if int(answer) == correct_answer else 0
        except:
            return 0
    elif question.get('type') in ['recall', "delayed_recall"]:
        # 简化：返回部分分数
        return max_points // 2
    else:
        # 简化：返回满分
        return max_points


def _generate_assessment_analysis(dimension_scores: dict, cognitive_level: str) -> str:
    """生成评估分析"""
    analyses = {
        'normal': '您的认知功能整体表现良好，各项指标均在正常范围内。建议继续保持健康的生活方式和适度的脑力活动。',
        'mild_decline': '您的认知功能存在轻度下降，这可能是正常老化的表现。建议增加认知训练频率，保持社交活动。',
        'moderate_decline': '您的认知功能存在中度下降，建议尽快咨询医生进行专业评估。同时可以通过认知训练和健康生活方式延缓进展。',
        'severe_decline': '您的认知功能存在明显下降，强烈建议尽快就医进行详细检查。我们已通知您的紧急联系人。'
    }
    return analyses.get(cognitive_level, analyses['normal'])


def _generate_assessment_recommendations(dimension_scores: dict, cognitive_level: str) -> list:
    """生成评估建议"""
    base_recommendations = [
        '每天进行15-30分钟的认知训练',
        '保持规律作息，确保充足睡眠',
        '适度运动，如散步、太极等'
    ]

    if cognitive_level in ['moderate_decline', 'severe_decline']:
        base_recommendations.insert(0, '建议尽快到医院神经内科就诊')

    # 根据维度表现添加针对性建议
    for dim, scores in dimension_scores.items():
        ratio = scores['score'] / scores['max'] if scores['max'] > 0 else 0
        if ratio < 0.6:
            if dim == 'memory':
                base_recommendations.append('加强记忆力训练，可以尝试数字记忆游戏')
            elif dim == 'attention':
                base_recommendations.append("加强注意力训练，减少分心因素")
            elif dim == "calculation":
                base_recommendations.append('多做简单算术练习')

    return base_recommendations


def _generate_training_plan_suggestion(dimension_scores: dict, cognitive_level: str) -> dict:
    """生成训练计划建议"""
    weak_dimensions = []
    for dim, scores in dimension_scores.items():
        if scores['max'] > 0 and scores['score'] / scores['max'] < 0.7:
            weak_dimensions.append(dim)

    return {
        "recommended_weekly_sessions": 5 if cognitive_level in ['mild_decline', 'moderate_decline'] else 3,
        "recommended_session_duration": 15,
        "focus_dimensions": weak_dimensions or ['memory', 'attention'],
        'suggested_games': ['数字记忆', '找不同', '简单计算'],
        "difficulty_start": 1 if cognitive_level in ['moderate_decline', 'severe_decline'] else 2
    }


def _calculate_dimension_stats(sessions: list, db: Session) -> List[DimensionStats]:
    """计算各维度统计"""
    dimension_data = {}

    for session in sessions:
        game = db.query(CognitiveGame).filter(CognitiveGame.id == session.game_id).first()
        if game:
            dim = game.game_type
            if dim not in dimension_data:
                dimension_data[dim] = {'scores': [], 'count': 0}
            dimension_data[dim]['scores'].append(session.accuracy or 0)
            dimension_data[dim]['count'] += 1

    result = []
    for dim, data in dimension_data.items():
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        # 简化趋势计算
        trend = "stable"
        if len(data['scores']) >= 5:
            recent = sum(data['scores'][-3:]) / 3
            earlier = sum(data['scores'][:3]) / 3
            if recent > earlier + 0.1:
                trend = 'improving'
            elif recent < earlier - 0.1:
                trend = 'declining'

        result.append(DimensionStats(
            dimension=dim,
            average_score=round(avg_score * 100, 1),
            trend=trend,
            sessions_count=data['count']
        ))

    return result


def _calculate_streak_days(user_id: int, db: Session) -> int:
    """计算连续训练天数"""
    sessions = db.query(CognitiveGameSession).filter(
        CognitiveGameSession.user_id == user_id,
        CognitiveGameSession.status == 'completed'
    ).order_by(desc(CognitiveGameSession.created_at)).all()

    if not sessions:
        return 0

    streak = 0
    current_date = datetime.utcnow().date()

    session_dates = set(s.created_at.date() for s in sessions)

    while current_date in session_dates or (streak == 0 and (current_date - timedelta(days=1)) in session_dates):
        if current_date in session_dates:
            streak += 1
        elif streak == 0:
            current_date = current_date - timedelta(days=1)
            continue
        else:
            break
        current_date = current_date - timedelta(days=1)

    return streak


def _calculate_overall_trend(sessions: list) -> str:
    """计算整体趋势"""
    if len(sessions) < 5:
        return 'stable'

    # 按时间排序
    sorted_sessions = sorted(sessions, key=lambda s: s.created_at)

    # 比较前半部分和后半部分的平均分
    mid = len(sorted_sessions) // 2
    early_avg = sum(s.accuracy or 0 for s in sorted_sessions[:mid]) / mid
    late_avg = sum(s.accuracy or 0 for s in sorted_sessions[mid:]) / (len(sorted_sessions) - mid)

    if late_avg > early_avg + 0.1:
        return 'improving'
    elif late_avg < early_avg - 0.1:
        return 'declining'
    return 'stable'


def _calculate_performance_by_dimension(sessions: list, db: Session) -> dict:
    """按维度计算表现"""
    result = {}

    for session in sessions:
        game = db.query(CognitiveGame).filter(CognitiveGame.id == session.game_id).first()
        if game:
            dim = game.game_type
            if dim not in result:
                result[dim] = {
                    'sessions': 0,
                    "total_score": 0,
                    'total_time': 0,
                    "average_accuracy": 0
                }
            result[dim]['sessions'] += 1
            result[dim]["total_score"] += session.score or 0
            result[dim]['total_time'] += session.completion_time_seconds or 0

    # 计算平均值
    for dim in result:
        if result[dim]['sessions'] > 0:
            result[dim]["average_accuracy"] = round(
                result[dim]["total_score"] / result[dim]['sessions'], 1
            )

    return result


def _generate_progress_chart_data(sessions: list, period_days: int) -> list:
    """生成进度图表数据"""
    chart_data = []

    # 按周统计
    weeks = period_days // 7
    for week in range(weeks):
        start = datetime.utcnow() - timedelta(days=(weeks - week) * 7)
        end = start + timedelta(days=7)

        week_sessions = [s for s in sessions if start <= s.created_at < end]
        avg_score = sum(s.accuracy or 0 for s in week_sessions) / len(week_sessions) if week_sessions else 0

        chart_data.append({
            'week': f'第{week + 1}周',
            'sessions': len(week_sessions),
            "average_score": round(avg_score * 100, 1)
        })

    return chart_data


def _calculate_achievements(sessions: list, user_id: int, db: Session) -> list:
    """计算成就"""
    achievements = []

    if len(sessions) >= 10:
        achievements.append("坚持训练者 - 完成10次训练")
    if len(sessions) >= 50:
        achievements.append("训练达人 - 完成50次训练")

    streak = _calculate_streak_days(user_id, db)
    if streak >= 7:
        achievements.append("一周坚持 - 连续训练7天")
    if streak >= 30:
        achievements.append("月度之星 - 连续训练30天")

    # 检查高分
    high_scores = [s for s in sessions if s.accuracy and s.accuracy >= 0.9]
    if len(high_scores) >= 5:
        achievements.append("学霸 - 5次获得90%以上正确率")

    return achievements


def _generate_training_recommendations(performance: dict) -> list:
    """生成训练建议"""
    recommendations = []

    # 找出弱项
    weakest = None
    lowest_score = float("inf")
    for dim, stats in performance.items():
        if stats["average_accuracy"] < lowest_score:
            lowest_score = stats["average_accuracy"]
            weakest = dim

    if weakest:
        dim_names = {
            'memory': '记忆力',
            'attention': '注意力',
            'calculation': '计算能力',
            'language': '语言能力',
            'spatial': '空间感知'
        }
        recommendations.append(f'建议加强{dim_names.get(weakest, weakest)}训练')

    recommendations.extend([
        '每天坚持训练15-30分钟效果最佳',
        '训练后适当休息，避免疲劳',
        '可以尝试不同类型的游戏，全面锻炼'
    ])

    return recommendations


def _generate_report_summary(total_sessions: int, completion_rate: float, performance_by_dimension: dict) -> str:
    """生成报告摘要"""
    if total_sessions == 0:
        return '在此期间暂无训练记录，建议开始进行认知训练以保持大脑活力。'

    summary = f'在此期间您共完成了{total_sessions}次认知训练，'

    if completion_rate >= 0.8:
        summary += '训练完成率很高，表现优秀！'
    elif completion_rate >= 0.5:
        summary += "训练完成率良好，继续保持！"
    else:
        summary += "训练完成率还有提升空间，建议增加训练频率。"

    if performance_by_dimension:
        best_dim = max(performance_by_dimension.items(), key=lambda x: x[1]["average_accuracy"])
        summary += f'您在{best_dim[0]}方面表现最佳。'

    return summary


def _find_weak_dimensions(sessions: list, db: Session) -> list:
    """找出弱项维度"""
    dimension_scores = {}

    for session in sessions:
        game = db.query(CognitiveGame).filter(CognitiveGame.id == session.game_id).first()
        if game:
            dim = game.game_type
            if dim not in dimension_scores:
                dimension_scores[dim] = []
            dimension_scores[dim].append(session.accuracy or 0)

    weak = []
    for dim, scores in dimension_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        if avg < 0.7:
            weak.append(dim)

    return weak


def _generate_recommendation_reason(game: CognitiveGame, weak_dimensions: list, recent_sessions: list) -> str:
    """生成推荐理由"""
    if game.game_type in weak_dimensions:
        return f'您在{game.game_type}方面还有提升空间，此游戏可以帮助您加强训练'
    elif not recent_sessions:
        return '您还没有尝试过这款游戏，试试看吧！'
    else:
        return "继续练习可以巩固您的能力"


def _generate_expected_benefit(game: CognitiveGame) -> str:
    """生成预期收益描述"""
    benefits = {
        'memory': '提升记忆力，帮助您更好地记住重要事项',
        'attention': '增强注意力集中，提高日常生活效率',
        'calculation': '锻炼计算能力，保持大脑敏捷',
        'language': '提升语言能力，促进表达和理解',
        'spatial': '增强空间感知，改善方向感和定位能力'
    }
    return benefits.get(game.game_type, '全面锻炼大脑，延缓认知衰退')
