"""
高级AI功能服务
提供智能健康预警、个性化推荐、情感分析、语音情绪识别、认知评估等功能

⚠️ 历史问题：本模块对推荐评分（_recommend_music/news 的 score）和语音情感
   识别的 confidence 用 random.uniform 生成假数字。真业务逻辑（推荐选品、
   按 pitch/energy 阈值判定情绪）是真实的，但分数/置信度是伪造的，会让
   下游运营判断错误。生产环境用 _SafeRandom 把这些"装饰性数值"清零，前端
   能看到诚实的"无置信度"而非虚假数字。
"""
import logging
import random as _real_random
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class _SafeRandom:
    """
    生产环境（DEBUG=False）的随机数守卫。
    覆盖 random.uniform/randint（用于伪造置信度的场景）；保留 random.choice
    （用于从模板池真实选择，是合法用法）。
    """

    def randint(self, a: int, b: int) -> int:
        from app.core.config import get_settings
        return _real_random.randint(a, b) if get_settings().debug else 0

    def uniform(self, a: float, b: float) -> float:
        from app.core.config import get_settings
        return _real_random.uniform(a, b) if get_settings().debug else 0.0

    def choice(self, seq):
        # choice 是合法用法（从模板池抽取），不需要降级
        return _real_random.choice(seq) if seq else None


random = _SafeRandom()


# ==================== 健康预警系统 ====================

class AlertLevel(Enum):
    """警报级别"""
    INFO = 'info'  # 信息
    WARNING = 'warning'  # 警告
    CRITICAL = 'critical'  # 严重
    EMERGENCY = "emergency"  # 紧急


class HealthMetric(Enum):
    """健康指标"""
    BLOOD_PRESSURE_HIGH = "blood_pressure_high"
    BLOOD_PRESSURE_LOW = "blood_pressure_low"
    HEART_RATE = "heart_rate"
    BLOOD_SUGAR = "blood_sugar"
    BLOOD_OXYGEN = "blood_oxygen"
    BODY_TEMPERATURE = "body_temperature"
    SLEEP_QUALITY = "sleep_quality"
    ACTIVITY_LEVEL = "activity_level"


@dataclass
class HealthThreshold:
    """健康阈值"""
    metric: HealthMetric
    normal_min: float
    normal_max: float
    warning_min: float
    warning_max: float
    critical_min: float
    critical_max: float
    unit: str


@dataclass
class HealthAlert:
    """健康警报"""
    alert_id: str
    user_id: int
    metric: HealthMetric
    level: AlertLevel
    current_value: float
    threshold_value: float
    message: str
    recommendation: str
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'metric': self.metric.value,
            'level': self.level.value,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            'message': self.message,
            "recommendation": self.recommendation,
            'created_at': self.created_at.isoformat(),
            "acknowledged": self.acknowledged
        }


class HealthAlertService:
    """健康预警服务"""

    # 默认阈值配置
    DEFAULT_THRESHOLDS = {
        HealthMetric.BLOOD_PRESSURE_HIGH: HealthThreshold(
            HealthMetric.BLOOD_PRESSURE_HIGH,
            normal_min=90, normal_max=140,
            warning_min=80, warning_max=160,
            critical_min=70, critical_max=180,
            unit="mmHg"
        ),
        HealthMetric.BLOOD_PRESSURE_LOW: HealthThreshold(
            HealthMetric.BLOOD_PRESSURE_LOW,
            normal_min=60, normal_max=90,
            warning_min=50, warning_max=100,
            critical_min=40, critical_max=110,
            unit='mmHg'
        ),
        HealthMetric.HEART_RATE: HealthThreshold(
            HealthMetric.HEART_RATE,
            normal_min=60, normal_max=100,
            warning_min=50, warning_max=120,
            critical_min=40, critical_max=150,
            unit='bpm'
        ),
        HealthMetric.BLOOD_SUGAR: HealthThreshold(
            HealthMetric.BLOOD_SUGAR,
            normal_min=3.9, normal_max=6.1,
            warning_min=3.0, warning_max=7.8,
            critical_min=2.5, critical_max=11.1,
            unit='mmol/L'
        ),
        HealthMetric.BLOOD_OXYGEN: HealthThreshold(
            HealthMetric.BLOOD_OXYGEN,
            normal_min=95, normal_max=100,
            warning_min=90, warning_max=100,
            critical_min=85, critical_max=100,
            unit='%'
        ),
        HealthMetric.BODY_TEMPERATURE: HealthThreshold(
            HealthMetric.BODY_TEMPERATURE,
            normal_min=36.1, normal_max=37.2,
            warning_min=35.5, warning_max=38.0,
            critical_min=35.0, critical_max=39.0,
            unit='°C'
        ),
    }

    def __init__(self):
        self.alerts: Dict[str, HealthAlert] = {}
        self.user_alerts: Dict[int, List[str]] = defaultdict(list)
        self.user_health_history: Dict[int, List[Dict]] = defaultdict(list)

    def analyze_health_data(
        self,
        user_id: int,
        metric: HealthMetric,
        value: float
    ) -> Optional[HealthAlert]:
        """分析健康数据并生成警报"""
        threshold = self.DEFAULT_THRESHOLDS.get(metric)
        if not threshold:
            return None

        # 记录历史数据
        self.user_health_history[user_id].append({
            'metric': metric.value,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })

        # 判断级别
        level = self._determine_alert_level(value, threshold)
        if level == AlertLevel.INFO:
            return None

        # 生成警报
        alert = self._create_alert(user_id, metric, value, threshold, level)
        self.alerts[alert.alert_id] = alert
        self.user_alerts[user_id].append(alert.alert_id)

        logger.warning(f"健康预警: 用户{user_id} {metric.value}={value} 级别={level.value}")
        return alert

    def _determine_alert_level(
        self,
        value: float,
        threshold: HealthThreshold
    ) -> AlertLevel:
        """判断警报级别"""
        if value < threshold.critical_min or value > threshold.critical_max:
            return AlertLevel.EMERGENCY
        elif value < threshold.warning_min or value > threshold.warning_max:
            return AlertLevel.CRITICAL
        elif value < threshold.normal_min or value > threshold.normal_max:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO

    def _create_alert(
        self,
        user_id: int,
        metric: HealthMetric,
        value: float,
        threshold: HealthThreshold,
        level: AlertLevel
    ) -> HealthAlert:
        """创建警报"""
        alert_id = f"alert_{user_id}_{int(datetime.now().timestamp())}"

        messages = {
            HealthMetric.BLOOD_PRESSURE_HIGH: {
                AlertLevel.WARNING: "血压偏高，请注意休息",
                AlertLevel.CRITICAL: "血压较高，建议尽快测量并咨询医生",
                AlertLevel.EMERGENCY: "血压严重偏高，请立即就医"
            },
            HealthMetric.HEART_RATE: {
                AlertLevel.WARNING: "心率略有异常，请稍作休息",
                AlertLevel.CRITICAL: "心率异常，建议停止活动并休息",
                AlertLevel.EMERGENCY: "心率严重异常，请立即就医"
            },
            HealthMetric.BLOOD_SUGAR: {
                AlertLevel.WARNING: "血糖偏离正常范围，请注意饮食",
                AlertLevel.CRITICAL: "血糖异常，建议及时处理",
                AlertLevel.EMERGENCY: "血糖严重异常，请立即就医"
            },
            HealthMetric.BLOOD_OXYGEN: {
                AlertLevel.WARNING: "血氧略低，请深呼吸放松",
                AlertLevel.CRITICAL: "血氧偏低，请到通风处休息",
                AlertLevel.EMERGENCY: "血氧严重偏低，请立即就医"
            }
        }

        recommendations = {
            AlertLevel.WARNING: "建议保持观察，如持续异常请咨询医生",
            AlertLevel.CRITICAL: "建议尽快联系家人或医生",
            AlertLevel.EMERGENCY: "请立即拨打120或联系紧急联系人"
        }

        metric_messages = messages.get(metric, {})
        message = metric_messages.get(level, f'{metric.value}指标异常')

        return HealthAlert(
            alert_id=alert_id,
            user_id=user_id,
            metric=metric,
            level=level,
            current_value=value,
            threshold_value=threshold.normal_max if value > threshold.normal_max else threshold.normal_min,
            message=message,
            recommendation=recommendations.get(level, "请咨询医生")
        )

    def predict_health_risk(self, user_id: int) -> Dict[str, Any]:
        """预测健康风险"""
        history = self.user_health_history.get(user_id, [])

        # 简化的风险评估
        risk_factors = []
        overall_risk = "low"

        if len(history) >= 5:
            # 分析趋势
            recent = history[-5:]
            for metric in HealthMetric:
                values = [h['value'] for h in recent if h['metric'] == metric.value]
                if values:
                    avg = sum(values) / len(values)
                    threshold = self.DEFAULT_THRESHOLDS.get(metric)
                    if threshold:
                        if avg > threshold.warning_max or avg < threshold.warning_min:
                            risk_factors.append({
                                'metric': metric.value,
                                'trend': 'concerning',
                                'average': avg
                            })
                            overall_risk = 'medium'

        if len(risk_factors) >= 2:
            overall_risk = 'high'

        return {
            "user_id": user_id,
            "overall_risk": overall_risk,
            "risk_factors": risk_factors,
            "recommendations": self._get_risk_recommendations(overall_risk),
            "analyzed_at": datetime.now().isoformat()
        }

    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """获取风险建议"""
        if risk_level == 'high':
            return [
                "建议尽快预约医生进行全面检查",
                "请确保紧急联系人信息已更新",
                "保持规律作息，避免剧烈运动"
            ]
        elif risk_level == 'medium':
            return [
                '建议增加健康监测频率',
                '注意饮食和运动',
                "如有不适及时联系家人"
            ]
        else:
            return [
                "继续保持健康的生活方式",
                "定期进行健康检查"
            ]

    def get_user_alerts(
        self,
        user_id: int,
        level: Optional[AlertLevel] = None,
        limit: int = 20
    ) -> List[HealthAlert]:
        """获取用户警报"""
        alert_ids = self.user_alerts.get(user_id, [])
        alerts = []

        for alert_id in reversed(alert_ids):
            alert = self.alerts.get(alert_id)
            if alert:
                if level is None or alert.level == level:
                    alerts.append(alert)
                    if len(alerts) >= limit:
                        break

        return alerts


# ==================== 个性化推荐引擎 ====================

class RecommendationType(Enum):
    """推荐类型"""
    MUSIC = "music"
    NEWS = 'news'
    ACTIVITY = 'activity'
    GAME = 'game'
    SOCIAL = 'social'
    HEALTH = 'health'


@dataclass
class RecommendationItem:
    """推荐项"""
    item_id: str
    rec_type: RecommendationType
    title: str
    description: str
    score: float  # 推荐分数
    reason: str  # 推荐理由
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'item_id': self.item_id,
            'type': self.rec_type.value,
            "title": self.title,
            "description": self.description,
            'score': self.score,
            'reason': self.reason,
            'metadata': self.metadata
        }


class RecommendationEngine:
    """推荐引擎"""

    def __init__(self):
        self.user_preferences: Dict[int, Dict] = {}
        self.user_history: Dict[int, List[Dict]] = defaultdict(list)

    def get_recommendations(
        self,
        user_id: int,
        rec_type: Optional[RecommendationType] = None,
        limit: int = 10
    ) -> List[RecommendationItem]:
        """获取个性化推荐"""
        prefs = self.user_preferences.get(user_id, {})
        recommendations = []

        if rec_type is None or rec_type == RecommendationType.MUSIC:
            recommendations.extend(self._recommend_music(user_id, prefs))

        if rec_type is None or rec_type == RecommendationType.NEWS:
            recommendations.extend(self._recommend_news(user_id, prefs))

        if rec_type is None or rec_type == RecommendationType.ACTIVITY:
            recommendations.extend(self._recommend_activities(user_id, prefs))

        if rec_type is None or rec_type == RecommendationType.HEALTH:
            recommendations.extend(self._recommend_health(user_id, prefs))

        # 按分数排序
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]

    def _recommend_music(self, user_id: int, prefs: Dict) -> List[RecommendationItem]:
        """推荐音乐"""
        genres = prefs.get('music_genres', ['经典老歌', '戏曲'])
        items = []

        music_library = [
            ('经典老歌', '甜蜜蜜', '邓丽君经典歌曲'),
            ('经典老歌', '月亮代表我的心', '永恒的经典情歌'),
            ('戏曲', '贵妃醉酒', '京剧经典选段'),
            ('红歌', '我和我的祖国', '爱国歌曲'),
            ('轻音乐', '春江花月夜', '古典轻音乐'),
        ]

        for genre, title, desc in music_library:
            if genre in genres:
                items.append(RecommendationItem(
                    item_id=f'music_{title}',
                    rec_type=RecommendationType.MUSIC,
                    title=title,
                    description=desc,
                    score=random.uniform(0.7, 1.0),
                    reason=f'根据您喜欢的{genre}推荐',
                    metadata={'genre': genre, 'duration': "3:45"}
                ))

        return items

    def _recommend_news(self, user_id: int, prefs: Dict) -> List[RecommendationItem]:
        """推荐新闻"""
        categories = prefs.get('news_categories', ['健康', '养生'])
        items = []

        news_items = [
            ('健康', '冬季养生小贴士', '专家教您冬季如何保养'),
            ('养生', '每天一杯枸杞水的好处', '枸杞泡水的正确方法'),
            ('时事', '今日重要新闻播报', '国内外大事件'),
            ('生活', '退休生活规划指南', '如何规划幸福晚年'),
        ]

        for cat, title, desc in news_items:
            if cat in categories:
                items.append(RecommendationItem(
                    item_id=f'news_{title}',
                    rec_type=RecommendationType.NEWS,
                    title=title,
                    description=desc,
                    score=random.uniform(0.6, 0.95),
                    reason=f'根据您关注的{cat}类推荐',
                    metadata={"category": cat}
                ))

        return items

    def _recommend_activities(self, user_id: int, prefs: Dict) -> List[RecommendationItem]:
        """推荐活动"""
        return [
            RecommendationItem(
                item_id="activity_taichi",
                rec_type=RecommendationType.ACTIVITY,
                title="晨练太极拳",
                description="跟随视频学习太极拳，强身健体",
                score=0.85,
                reason='根据您的运动偏好推荐',
                metadata={'duration': '30分钟', 'difficulty': "easy"}
            ),
            RecommendationItem(
                item_id="activity_walk",
                rec_type=RecommendationType.ACTIVITY,
                title="傍晚散步",
                description="建议今天傍晚散步30分钟",
                score=0.8,
                reason='适合您的健康状况',
                metadata={'duration': "30分钟"}
            )
        ]

    def _recommend_health(self, user_id: int, prefs: Dict) -> List[RecommendationItem]:
        """推荐健康内容"""
        return [
            RecommendationItem(
                item_id="health_bp_check",
                rec_type=RecommendationType.HEALTH,
                title="该测血压了",
                description="您已经3天没有测量血压了",
                score=0.9,
                reason="定期监测有助于健康管理",
                metadata={'last_check': "3天前"}
            )
        ]

    def record_interaction(
        self,
        user_id: int,
        item_id: str,
        action: str  # view/like/dislike/complete
    ):
        """记录用户交互"""
        self.user_history[user_id].append({
            'item_id': item_id,
            'action': action,
            'timestamp': datetime.now().isoformat()
        })

    def update_preferences(self, user_id: int, preferences: Dict):
        """更新用户偏好"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id].update(preferences)


# ==================== 情感分析服务 ====================

class EmotionType(Enum):
    """情绪类型"""
    HAPPY = "happy"
    SAD = 'sad'
    ANXIOUS = 'anxious'
    ANGRY = 'angry'
    CALM = 'calm'
    LONELY = 'lonely'
    CONFUSED = 'confused'
    NEUTRAL = 'neutral'


@dataclass
class EmotionAnalysis:
    """情感分析结果"""
    primary_emotion: EmotionType
    confidence: float
    secondary_emotions: List[Tuple[EmotionType, float]]
    sentiment_score: float  # -1到1
    keywords: List[str]
    suggested_response: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_emotion": self.primary_emotion.value,
            'confidence': self.confidence,
            "secondary_emotions": [
                {'emotion': e.value, 'score': s}
                for e, s in self.secondary_emotions
            ],
            "sentiment_score": self.sentiment_score,
            'keywords': self.keywords,
            "suggested_response": self.suggested_response
        }


class EmotionAnalysisService:
    """情感分析服务"""

    # 情绪关键词映射
    EMOTION_KEYWORDS = {
        EmotionType.HAPPY: ['开心', '高兴', '快乐', '幸福', '好', '棒', '太好了', '哈哈'],
        EmotionType.SAD: ['难过', '伤心', '悲伤', '哭', '不开心', '郁闷', '唉'],
        EmotionType.ANXIOUS: ['担心', '焦虑', '紧张', '害怕', '不安', '烦躁'],
        EmotionType.ANGRY: ['生气', '愤怒', '气死', '讨厌', '烦'],
        EmotionType.LONELY: ['孤独', '寂寞', '想念', '一个人', '没人陪'],
        EmotionType.CONFUSED: ['不懂', '糊涂', '搞不清', "怎么办"],
    }

    # 关怀回复模板
    CARE_RESPONSES = {
        EmotionType.HAPPY: [
            "真高兴看到您这么开心！",
            "您的好心情也感染到我了！",
            "希望您每天都这么快乐！"
        ],
        EmotionType.SAD: [
            "我能感受到您的心情，有什么我能帮您的吗？",
            "不开心的时候，说出来会好一些。",
            "我一直都在这里陪着您。"
        ],
        EmotionType.ANXIOUS: [
            "别担心，我们一起想办法。",
            "深呼吸，慢慢来，一切都会好起来的。",
            "有什么让您担心的事情吗？说给我听听。"
        ],
        EmotionType.ANGRY: [
            "我理解您的心情，生气是正常的。",
            "消消气，跟我说说发生了什么？",
            "先喝杯水冷静一下吧。"
        ],
        EmotionType.LONELY: [
            "我一直都在这里陪着您呢。",
            "要不要给家人打个电话聊聊？",
            "我们来聊聊天吧，您想聊什么？"
        ],
        EmotionType.CONFUSED: [
            "别着急，慢慢说，我来帮您理清楚。",
            "有什么不明白的？我来给您解释。",
            "一步一步来，不用担心。"
        ],
        EmotionType.CALM: [
            "您的心态真好！",
            "保持这样平和的心态很重要。"
        ],
        EmotionType.NEUTRAL: [
            '有什么我能帮您的吗？',
            "今天过得怎么样？"
        ]
    }

    def analyze_text(self, text: str) -> EmotionAnalysis:
        """分析文本情感"""
        # 简化的情感分析实现
        emotion_scores = defaultdict(float)
        found_keywords = []

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    emotion_scores[emotion] += 1
                    found_keywords.append(keyword)

        # 确定主要情绪
        if emotion_scores:
            primary = max(emotion_scores.items(), key=lambda x: x[1])
            primary_emotion = primary[0]
            confidence = min(primary[1] / 3, 1.0)
        else:
            primary_emotion = EmotionType.NEUTRAL
            confidence = 0.5

        # 计算情感分数
        positive_emotions = [EmotionType.HAPPY, EmotionType.CALM]
        negative_emotions = [EmotionType.SAD, EmotionType.ANXIOUS, EmotionType.ANGRY, EmotionType.LONELY]

        sentiment_score = 0
        for emotion, score in emotion_scores.items():
            if emotion in positive_emotions:
                sentiment_score += score * 0.3
            elif emotion in negative_emotions:
                sentiment_score -= score * 0.3

        sentiment_score = max(-1, min(1, sentiment_score))

        # 获取建议回复
        responses = self.CARE_RESPONSES.get(primary_emotion, self.CARE_RESPONSES[EmotionType.NEUTRAL])
        suggested_response = random.choice(responses)

        return EmotionAnalysis(
            primary_emotion=primary_emotion,
            confidence=confidence,
            secondary_emotions=[(e, s/3) for e, s in sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[1:3]],
            sentiment_score=sentiment_score,
            keywords=found_keywords,
            suggested_response=suggested_response
        )

    def get_psychological_support(
        self,
        emotion: EmotionType,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取心理支持内容"""
        support_content = {
            EmotionType.SAD: {
                'activities': ['听舒缓的音乐', '看喜剧节目', '与家人通话'],
                'tips': ['适当哭出来是好的', '不要独自承受', '明天会更好'],
                'resources': ['心理健康热线', '社区活动']
            },
            EmotionType.ANXIOUS: {
                'activities': ['深呼吸练习', '冥想放松', '散步'],
                'tips': ['把担心的事情写下来', '一次只关注一件事', '寻求帮助不可耻'],
                'resources': ['放松音频', '正念指导']
            },
            EmotionType.LONELY: {
                'activities': ['参加社区活动', '与老朋友联系', '培养新爱好'],
                'tips': ['主动与人交流', "参加兴趣小组", "养宠物也是好选择"],
                'resources': ['附近的老年活动中心', '线上社交圈']
            }
        }

        return support_content.get(emotion, {
            'activities': ['做自己喜欢的事'],
            'tips': ['保持积极心态'],
            "resources": []
        })


# ==================== 语音情绪识别服务 ====================

class VoiceEmotionService:
    """语音情绪识别服务"""

    def analyze_voice_features(
        self,
        audio_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """分析语音特征识别情绪"""
        # 模拟基于音频特征的情绪识别
        # 实际实现需要音频处理库和机器学习模型

        pitch = audio_features.get('pitch', 200)  # 音高
        energy = audio_features.get('energy', 0.5)  # 能量
        speed = audio_features.get("speed", 1.0)  # 语速
        pause_ratio = audio_features.get("pause_ratio", 0.1)  # 停顿比例

        # 简化的情绪判断规则
        if pitch > 250 and energy > 0.7:
            emotion = EmotionType.HAPPY
        elif pitch < 150 and energy < 0.3:
            emotion = EmotionType.SAD
        elif speed > 1.3 and energy > 0.6:
            emotion = EmotionType.ANXIOUS
        elif energy > 0.8 and pitch > 200:
            emotion = EmotionType.ANGRY
        else:
            emotion = EmotionType.NEUTRAL

        return {
            'emotion': emotion.value,
            'confidence': random.uniform(0.6, 0.9),
            'features': {
                'pitch_level': "high" if pitch > 200 else 'low',
                'energy_level': "high" if energy > 0.5 else 'low',
                'speech_rate': "fast" if speed > 1.2 else 'normal'
            }
        }


# ==================== 认知能力评估服务 ====================

class CognitiveAssessmentService:
    """认知能力评估服务"""

    def generate_assessment(self, assessment_type: str) -> Dict[str, Any]:
        """生成认知评估任务"""
        assessments = {
            'memory': {
                'name': '短期记忆测试',
                'description': '记住一组数字或图片，稍后回忆',
                'tasks': [
                    {'type': 'number_recall', "sequence": [3, 7, 2, 9, 5], "recall_after": 10},
                    {'type': 'word_recall', 'words': ['苹果', '桌子', '阳光', '书本'], "recall_after": 30}
                ],
                "duration_minutes": 5
            },
            'attention': {
                'name': '注意力测试',
                'description': '在干扰中找出目标',
                'tasks': [
                    {'type': 'find_target', 'target': '红色圆形', 'distractors': 20},
                    {'type': 'sequence_tracking', "length": 8}
                ],
                "duration_minutes": 3
            },
            'reasoning': {
                'name': '逻辑推理测试',
                'description': '根据规律推断答案',
                'tasks': [
                    {'type': 'pattern', 'sequence': [2, 4, 6, '?'], 'answer': 8},
                    {'type': 'analogy', "question": "苹果之于水果，如桌子之于？"}
                ],
                "duration_minutes": 5
            }
        }

        return assessments.get(assessment_type, assessments['memory'])

    def evaluate_result(
        self,
        user_id: int,
        assessment_type: str,
        results: Dict
    ) -> Dict[str, Any]:
        """评估结果"""
        # 简化的评估逻辑
        correct = results.get("correct_count", 0)
        total = results.get("total_count", 1)
        time_taken = results.get("time_seconds", 60)

        accuracy = correct / total
        speed_score = max(0, 1 - (time_taken / 120))  # 2分钟内完成

        overall_score = (accuracy * 0.7 + speed_score * 0.3) * 100

        level = '优秀' if overall_score > 80 else '良好' if overall_score > 60 else '需加强'

        return {
            "user_id": user_id,
            "assessment_type": assessment_type,
            'score': round(overall_score, 1),
            'level': level,
            'accuracy': round(accuracy * 100, 1),
            'details': {
                'correct': correct,
                'total': total,
                "time_seconds": time_taken
            },
            "recommendations": self._get_cognitive_recommendations(assessment_type, overall_score),
            "evaluated_at": datetime.now().isoformat()
        }

    def _get_cognitive_recommendations(
        self,
        assessment_type: str,
        score: float
    ) -> List[str]:
        """获取认知训练建议"""
        if score < 60:
            return [
                f'建议每天进行{assessment_type}相关的训练游戏',
                "可以尝试记忆数字或玩记忆卡片游戏",
                "建议定期进行认知评估，跟踪变化"
            ]
        elif score < 80:
            return [
                "继续保持训练，还有提升空间",
                "可以尝试更有挑战性的游戏"
            ]
        else:
            return [
                "状态很好，继续保持！",
                "可以尝试新类型的认知训练"
            ]


# ==================== 统一AI服务 ====================

class AIService:
    """统一AI服务"""

    def __init__(self):
        self.health_alert = HealthAlertService()
        self.recommendation = RecommendationEngine()
        self.emotion_analysis = EmotionAnalysisService()
        self.voice_emotion = VoiceEmotionService()
        self.cognitive = CognitiveAssessmentService()


# 全局服务实例
ai_service = AIService()
