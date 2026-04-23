"""
高级AI功能API
提供智能健康预警、个性化推荐、情感分析、语音情绪、认知评估等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.ai_service import (
    ai_service,
    HealthMetric,
    AlertLevel,
    RecommendationType,
    EmotionType
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/ai", tags=["高级AI功能"])


# ==================== 请求模型 ====================

class HealthDataRequest(BaseModel):
    """健康数据请求"""
    metric: str = Field(..., description="指标类型: blood_pressure_high/heart_rate/blood_sugar等")
    value: float = Field(..., description="测量值")


class TextAnalysisRequest(BaseModel):
    """文本分析请求"""
    text: str = Field(..., max_length=1000, description="要分析的文本")


class VoiceAnalysisRequest(BaseModel):
    """语音分析请求"""
    pitch: float = Field(200, description='音高Hz')
    energy: float = Field(0.5, ge=0, le=1, description='能量0-1')
    speed: float = Field(1.0, description='语速倍率')
    pause_ratio: float = Field(0.1, ge=0, le=1, description="停顿比例")


class CognitiveResultRequest(BaseModel):
    """认知评估结果请求"""
    assessment_type: str = Field(..., description="评估类型: memory/attention/reasoning")
    correct_count: int = Field(..., ge=0, description='正确数量')
    total_count: int = Field(..., gt=0, description='总题数')
    time_seconds: int = Field(..., gt=0, description="用时秒数")


class PreferencesUpdateRequest(BaseModel):
    """偏好更新请求"""
    music_genres: Optional[List[str]] = Field(None, description='喜欢的音乐类型')
    news_categories: Optional[List[str]] = Field(None, description='喜欢的新闻分类')
    activities: Optional[List[str]] = Field(None, description="喜欢的活动")


# ==================== 健康预警API ====================

@router.post("/health/analyze")
async def analyze_health_data(
    request: HealthDataRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    分析健康数据并生成预警

    支持的指标:
    - blood_pressure_high: 收缩压
    - blood_pressure_low: 舒张压
    - heart_rate: 心率
    - blood_sugar: 血糖
    - blood_oxygen: 血氧
    - body_temperature: 体温
    """
    user_id = int(current_user['sub'])

    try:
        metric = HealthMetric(request.metric)
    except ValueError:
        valid_metrics = [m.value for m in HealthMetric]
        raise HTTPException(
            status_code=400,
            detail=f"无效的指标类型，可选: {valid_metrics}"
        )

    alert = ai_service.health_alert.analyze_health_data(
        user_id, metric, request.value
    )

    return {
        'analyzed': True,
        'has_alert': alert is not None,
        'alert': alert.to_dict() if alert else None,
        'metric': request.metric,
        "value": request.value
    }


@router.get("/health/alerts")
async def get_health_alerts(
    level: Optional[str] = Query(None, description="级别筛选: warning/critical/emergency"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取健康预警列表
    """
    user_id = int(current_user['sub'])

    alert_level = None
    if level:
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            pass

    alerts = ai_service.health_alert.get_user_alerts(user_id, alert_level, limit)

    return {
        'alerts': [a.to_dict() for a in alerts],
        'count': len(alerts)
    }


@router.get("/health/risk")
async def predict_health_risk(current_user: dict = Depends(get_current_user)):
    """
    预测健康风险

    基于历史健康数据进行风险评估
    """
    user_id = int(current_user['sub'])
    risk = ai_service.health_alert.predict_health_risk(user_id)
    return risk


@router.post("/health/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    确认健康预警
    """
    alert = ai_service.health_alert.alerts.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail='预警不存在')

    from datetime import datetime
    alert.acknowledged = True
    alert.acknowledged_at = datetime.now()

    return {
        'success': True,
        'alert_id': alert_id,
        'message': "预警已确认"
    }


# ==================== 个性化推荐API ====================

@router.get("/recommendations")
async def get_recommendations(
    rec_type: Optional[str] = Query(None, description="推荐类型: music/news/activity/health"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取个性化推荐
    """
    user_id = int(current_user['sub'])

    recommendation_type = None
    if rec_type:
        try:
            recommendation_type = RecommendationType(rec_type)
        except ValueError:
            pass

    recommendations = ai_service.recommendation.get_recommendations(
        user_id, recommendation_type, limit
    )

    return {
        "recommendations": [r.to_dict() for r in recommendations],
        'count': len(recommendations)
    }


@router.post("/recommendations/{item_id}/interact")
async def record_recommendation_interaction(
    item_id: str,
    action: str = Query(..., description="动作: view/like/dislike/complete"),
    current_user: dict = Depends(get_current_user)
):
    """
    记录推荐交互

    用于优化后续推荐
    """
    user_id = int(current_user['sub'])

    if action not in ['view', 'like', 'dislike', 'complete']:
        raise HTTPException(status_code=400, detail='无效的动作类型')

    ai_service.recommendation.record_interaction(user_id, item_id, action)

    return {
        'success': True,
        'item_id': item_id,
        "action": action
    }


@router.put("/recommendations/preferences")
async def update_recommendation_preferences(
    request: PreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新推荐偏好
    """
    user_id = int(current_user['sub'])

    preferences = {}
    if request.music_genres:
        preferences["music_genres"] = request.music_genres
    if request.news_categories:
        preferences["news_categories"] = request.news_categories
    if request.activities:
        preferences['activities'] = request.activities

    ai_service.recommendation.update_preferences(user_id, preferences)

    return {
        'success': True,
        "preferences": preferences,
        'message': "偏好已更新"
    }


# ==================== 情感分析API ====================

@router.post("/emotion/analyze-text")
async def analyze_text_emotion(
    request: TextAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    分析文本情感

    识别文本中的情绪并提供关怀建议
    """
    analysis = ai_service.emotion_analysis.analyze_text(request.text)
    return analysis.to_dict()


@router.post("/emotion/analyze-voice")
async def analyze_voice_emotion(
    request: VoiceAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    分析语音情绪

    基于语音特征识别情绪
    """
    features = {
        'pitch': request.pitch,
        'energy': request.energy,
        'speed': request.speed,
        "pause_ratio": request.pause_ratio
    }

    result = ai_service.voice_emotion.analyze_voice_features(features)
    return result


@router.get("/emotion/support/{emotion}")
async def get_emotional_support(
    emotion: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取心理支持内容

    根据情绪类型提供支持建议和资源
    """
    try:
        emotion_type = EmotionType(emotion)
    except ValueError:
        valid_emotions = [e.value for e in EmotionType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的情绪类型，可选: {valid_emotions}"
        )

    support = ai_service.emotion_analysis.get_psychological_support(emotion_type)
    return {
        'emotion': emotion,
        "support": support
    }


# ==================== 认知评估API ====================

@router.get("/cognitive/assessments")
async def get_available_assessments():
    """
    获取可用的认知评估类型
    """
    return {
        "assessments": [
            {
                'type': 'memory',
                'name': '短期记忆测试',
                'description': "测试短期记忆能力",
                "duration_minutes": 5
            },
            {
                'type': 'attention',
                'name': '注意力测试',
                'description': "测试注意力集中能力",
                "duration_minutes": 3
            },
            {
                'type': 'reasoning',
                'name': '逻辑推理测试',
                'description': "测试逻辑思维能力",
                "duration_minutes": 5
            }
        ]
    }


@router.get("/cognitive/assessments/{assessment_type}")
async def get_assessment_tasks(
    assessment_type: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取认知评估任务

    返回具体的测试题目
    """
    if assessment_type not in ['memory', 'attention', 'reasoning']:
        raise HTTPException(status_code=400, detail="无效的评估类型")

    assessment = ai_service.cognitive.generate_assessment(assessment_type)
    return assessment


@router.post("/cognitive/evaluate")
async def evaluate_cognitive_result(
    request: CognitiveResultRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    评估认知测试结果
    """
    user_id = int(current_user['sub'])

    if request.assessment_type not in ['memory', 'attention', 'reasoning']:
        raise HTTPException(status_code=400, detail="无效的评估类型")

    results = {
        "correct_count": request.correct_count,
        "total_count": request.total_count,
        "time_seconds": request.time_seconds
    }

    evaluation = ai_service.cognitive.evaluate_result(
        user_id, request.assessment_type, results
    )

    return evaluation


@router.get("/cognitive/history")
async def get_cognitive_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取认知评估历史

    用于追踪认知能力变化
    """
    user_id = int(current_user['sub'])

    # 模拟历史数据
    import random
    from datetime import datetime, timedelta

    history = []
    for i in range(min(limit, 10)):
        history.append({
            "assessment_type": random.choice(['memory', 'attention', 'reasoning']),
            'score': random.uniform(60, 95),
            'level': random.choice(['优秀', '良好', "需加强"]),
            "evaluated_at": (datetime.now() - timedelta(days=i * 7)).isoformat()
        })

    return {
        'history': history,
        'summary': {
            'average_score': sum(h['score'] for h in history) / len(history) if history else 0,
            'trend': 'stable',
            "total_assessments": len(history)
        }
    }


# ==================== AI助手综合API ====================

@router.post("/assistant/understand")
async def ai_understand(
    text: str = Query(..., description="用户输入文本"),
    current_user: dict = Depends(get_current_user)
):
    """
    AI理解用户意图

    综合分析用户输入，识别情感和意图
    """
    user_id = int(current_user['sub'])

    # 情感分析
    emotion = ai_service.emotion_analysis.analyze_text(text)

    # 意图识别（简化版）
    intent = "chat"
    if any(kw in text for kw in ['测血压', '测心率', "健康"]):
        intent = "health_check"
    elif any(kw in text for kw in ['听歌', '音乐', "戏曲"]):
        intent = "entertainment"
    elif any(kw in text for kw in ['打电话', '联系', "视频"]):
        intent = "communication"
    elif any(kw in text for kw in ['救命', '帮助', '紧急']):
        intent = 'emergency'

    return {
        'text': text,
        'emotion': emotion.to_dict(),
        "intent": intent,
        "suggested_response": emotion.suggested_response
    }
