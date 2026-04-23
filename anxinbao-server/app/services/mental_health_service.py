"""
心理健康系统服务
提供情绪管理、心理评估、放松训练、心理支持等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class MoodLevel(Enum):
    """情绪等级"""
    VERY_HAPPY = 'very_happy'  # 非常开心
    HAPPY = 'happy'  # 开心
    NEUTRAL = 'neutral'  # 平静
    SAD = 'sad'  # 难过
    VERY_SAD = 'very_sad'  # 非常难过
    ANXIOUS = 'anxious'  # 焦虑
    ANGRY = 'angry'  # 生气
    LONELY = "lonely"  # 孤独


class MoodTrigger(Enum):
    """情绪触发因素"""
    FAMILY = 'family'  # 家庭
    HEALTH = 'health'  # 健康
    SOCIAL = 'social'  # 社交
    FINANCE = 'finance'  # 经济
    SLEEP = 'sleep'  # 睡眠
    WEATHER = 'weather'  # 天气
    MEMORY = "memory"  # 回忆
    ACHIEVEMENT = "achievement"  # 成就
    LOSS = 'loss'  # 失去
    OTHER = "other"  # 其他


class RelaxationType(Enum):
    """放松类型"""
    BREATHING = 'breathing'  # 呼吸练习
    MEDITATION = 'meditation'  # 冥想
    MUSIC = 'music'  # 音乐放松
    IMAGERY = "imagery"  # 想象放松
    MUSCLE_RELAXATION = "muscle_relaxation"  # 肌肉放松
    MINDFULNESS = "mindfulness"  # 正念练习


class AssessmentType(Enum):
    """评估类型"""
    DEPRESSION = 'depression'  # 抑郁筛查
    ANXIETY = "anxiety"  # 焦虑筛查
    SLEEP_QUALITY = "sleep_quality"  # 睡眠质量
    LIFE_SATISFACTION = "life_satisfaction"  # 生活满意度
    LONELINESS = 'loneliness'  # 孤独感
    COGNITIVE = "cognitive"  # 认知功能


# ==================== 情绪记录 ====================

@dataclass
class MoodRecord:
    """情绪记录"""
    record_id: str
    user_id: int
    mood: MoodLevel
    intensity: int  # 1-10
    triggers: List[MoodTrigger] = field(default_factory=list)
    notes: Optional[str] = None
    activities: List[str] = field(default_factory=list)  # 当时在做什么
    sleep_hours: Optional[float] = None
    physical_symptoms: List[str] = field(default_factory=list)  # 身体症状
    recorded_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'mood': self.mood.value,
            'intensity': self.intensity,
            'triggers': [t.value for t in self.triggers],
            'notes': self.notes,
            "activities": self.activities,
            "sleep_hours": self.sleep_hours,
            "physical_symptoms": self.physical_symptoms,
            "recorded_at": self.recorded_at.isoformat()
        }


class MoodTrackingService:
    """情绪追踪服务"""

    # 情绪分数映射
    MOOD_SCORES = {
        MoodLevel.VERY_HAPPY: 5,
        MoodLevel.HAPPY: 4,
        MoodLevel.NEUTRAL: 3,
        MoodLevel.SAD: 2,
        MoodLevel.VERY_SAD: 1,
        MoodLevel.ANXIOUS: 2,
        MoodLevel.ANGRY: 2,
        MoodLevel.LONELY: 2
    }

    def __init__(self):
        self.records: Dict[str, MoodRecord] = {}
        self.user_records: Dict[int, List[str]] = defaultdict(list)

    def record_mood(
        self,
        user_id: int,
        mood: MoodLevel,
        intensity: int,
        triggers: List[MoodTrigger] = None,
        notes: str = None,
        activities: List[str] = None,
        sleep_hours: float = None,
        physical_symptoms: List[str] = None
    ) -> MoodRecord:
        """记录情绪"""
        record_id = f"mood_{user_id}_{int(datetime.now().timestamp())}"

        record = MoodRecord(
            record_id=record_id,
            user_id=user_id,
            mood=mood,
            intensity=min(max(intensity, 1), 10),
            triggers=triggers or [],
            notes=notes,
            activities=activities or [],
            sleep_hours=sleep_hours,
            physical_symptoms=physical_symptoms or []
        )

        self.records[record_id] = record
        self.user_records[user_id].append(record_id)

        logger.info(f"记录情绪: {mood.value} for user {user_id}")
        return record

    def get_user_records(
        self,
        user_id: int,
        days: int = 30,
        mood: MoodLevel = None
    ) -> List[MoodRecord]:
        """获取用户情绪记录"""
        cutoff = datetime.now() - timedelta(days=days)
        record_ids = self.user_records.get(user_id, [])

        records = [
            self.records[rid] for rid in record_ids
            if rid in self.records and self.records[rid].recorded_at >= cutoff
        ]

        if mood:
            records = [r for r in records if r.mood == mood]

        return sorted(records, key=lambda x: x.recorded_at, reverse=True)

    def get_mood_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取情绪统计"""
        records = self.get_user_records(user_id, days)

        if not records:
            return {
                "period_days": days,
                "total_records": 0,
                'message': '暂无情绪记录'
            }

        # 情绪分布
        mood_counts = defaultdict(int)
        total_score = 0
        trigger_counts = defaultdict(int)

        for record in records:
            mood_counts[record.mood.value] += 1
            total_score += self.MOOD_SCORES.get(record.mood, 3)
            for trigger in record.triggers:
                trigger_counts[trigger.value] += 1

        avg_score = total_score / len(records)

        # 情绪趋势
        recent_records = records[:7]
        recent_score = sum(self.MOOD_SCORES.get(r.mood, 3) for r in recent_records) / len(recent_records) if recent_records else 0

        trend = 'stable'
        if recent_score > avg_score + 0.5:
            trend = 'improving'
        elif recent_score < avg_score - 0.5:
            trend = "declining"

        return {
            "period_days": days,
            "total_records": len(records),
            "mood_distribution": dict(mood_counts),
            "average_score": round(avg_score, 2),
            "recent_score": round(recent_score, 2),
            'trend': trend,
            "top_triggers": dict(sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "recommendations": self._generate_recommendations(avg_score, trend, trigger_counts)
        }

    def _generate_recommendations(
        self,
        avg_score: float,
        trend: str,
        triggers: Dict[str, int]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if avg_score < 2.5:
            recommendations.append("您近期情绪偏低，建议多与家人朋友交流")
            recommendations.append("如果持续低落，建议咨询专业人士")

        if trend == "declining":
            recommendations.append("情绪有下降趋势，可以尝试放松训练")

        if 'lonely' in triggers or "social" in triggers:
            recommendations.append("可以多参加社区活动，增加社交")

        if "sleep" in triggers:
            recommendations.append("注意保持规律作息，改善睡眠质量")

        if not recommendations:
            recommendations.append("情绪状态良好，继续保持积极心态")

        return recommendations

    def get_today_mood(self, user_id: int) -> Optional[MoodRecord]:
        """获取今日情绪"""
        today = datetime.now().date()
        records = self.get_user_records(user_id, days=1)

        for record in records:
            if record.recorded_at.date() == today:
                return record

        return None


# ==================== 心理评估 ====================

@dataclass
class AssessmentQuestion:
    """评估问题"""
    question_id: str
    text: str
    options: List[Dict[str, Any]]  # {text, score}


@dataclass
class AssessmentResult:
    """评估结果"""
    result_id: str
    user_id: int
    assessment_type: AssessmentType
    score: int
    max_score: int
    level: str  # normal/mild/moderate/severe
    interpretation: str
    recommendations: List[str]
    answers: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            "assessment_type": self.assessment_type.value,
            'score': self.score,
            'max_score': self.max_score,
            'level': self.level,
            "interpretation": self.interpretation,
            "recommendations": self.recommendations,
            'created_at': self.created_at.isoformat()
        }


class PsychologicalAssessmentService:
    """心理评估服务"""

    # PHQ-2 抑郁筛查(简化版)
    DEPRESSION_QUESTIONS = [
        AssessmentQuestion(
            "dep_1",
            "过去两周，您是否经常感到心情低落、沮丧或绝望？",
            [
                {'text': '完全没有', 'score': 0},
                {'text': '有几天', 'score': 1},
                {'text': '一半以上的时间', 'score': 2},
                {'text': '几乎每天', 'score': 3}
            ]
        ),
        AssessmentQuestion(
            "dep_2",
            "过去两周，您是否对做事缺乏兴趣或乐趣？",
            [
                {'text': '完全没有', 'score': 0},
                {'text': '有几天', 'score': 1},
                {'text': '一半以上的时间', 'score': 2},
                {'text': '几乎每天', 'score': 3}
            ]
        )
    ]

    # GAD-2 焦虑筛查(简化版)
    ANXIETY_QUESTIONS = [
        AssessmentQuestion(
            "anx_1",
            "过去两周，您是否经常感到紧张、焦虑或烦躁？",
            [
                {'text': '完全没有', 'score': 0},
                {'text': '有几天', 'score': 1},
                {'text': '一半以上的时间', 'score': 2},
                {'text': '几乎每天', 'score': 3}
            ]
        ),
        AssessmentQuestion(
            "anx_2",
            "过去两周，您是否无法停止或控制担忧？",
            [
                {'text': '完全没有', 'score': 0},
                {'text': '有几天', 'score': 1},
                {'text': '一半以上的时间', 'score': 2},
                {'text': '几乎每天', 'score': 3}
            ]
        )
    ]

    # 孤独感评估
    LONELINESS_QUESTIONS = [
        AssessmentQuestion(
            "lone_1",
            "您多久会感到缺少陪伴？",
            [
                {'text': '几乎从不', 'score': 1},
                {'text': '有时', 'score': 2},
                {'text': '经常', 'score': 3}
            ]
        ),
        AssessmentQuestion(
            'lone_2',
            '您多久会感到被冷落？',
            [
                {'text': '几乎从不', 'score': 1},
                {'text': '有时', 'score': 2},
                {'text': '经常', 'score': 3}
            ]
        ),
        AssessmentQuestion(
            "lone_3",
            "您多久会感到与他人隔离？",
            [
                {'text': '几乎从不', 'score': 1},
                {'text': '有时', 'score': 2},
                {'text': '经常', 'score': 3}
            ]
        )
    ]

    # 生活满意度评估
    LIFE_SATISFACTION_QUESTIONS = [
        AssessmentQuestion(
            "life_1",
            "总体来说，您对目前的生活满意吗？",
            [
                {'text': '非常满意', 'score': 5},
                {'text': '比较满意', 'score': 4},
                {'text': '一般', 'score': 3},
                {'text': '不太满意', 'score': 2},
                {'text': '很不满意', 'score': 1}
            ]
        ),
        AssessmentQuestion(
            "life_2",
            "您觉得自己的生活接近理想状态吗？",
            [
                {'text': '非常接近', 'score': 5},
                {'text': '比较接近', 'score': 4},
                {'text': '一般', 'score': 3},
                {'text': '不太接近', 'score': 2},
                {'text': '差很远', 'score': 1}
            ]
        ),
        AssessmentQuestion(
            "life_3",
            "如果能重新来过，您会改变很多事情吗？",
            [
                {'text': '几乎不会', 'score': 5},
                {'text': '改变一点', 'score': 4},
                {'text': '会改变一些', 'score': 3},
                {'text': '会改变很多', 'score': 2},
                {'text': '完全改变', "score": 1}
            ]
        )
    ]

    def __init__(self):
        self.results: Dict[str, AssessmentResult] = {}
        self.user_results: Dict[int, List[str]] = defaultdict(list)
        self.assessments = {
            AssessmentType.DEPRESSION: self.DEPRESSION_QUESTIONS,
            AssessmentType.ANXIETY: self.ANXIETY_QUESTIONS,
            AssessmentType.LONELINESS: self.LONELINESS_QUESTIONS,
            AssessmentType.LIFE_SATISFACTION: self.LIFE_SATISFACTION_QUESTIONS
        }

    def get_assessment_questions(
        self,
        assessment_type: AssessmentType
    ) -> List[Dict[str, Any]]:
        """获取评估问题"""
        questions = self.assessments.get(assessment_type, [])
        return [
            {
                "question_id": q.question_id,
                'text': q.text,
                'options': q.options
            }
            for q in questions
        ]

    def submit_assessment(
        self,
        user_id: int,
        assessment_type: AssessmentType,
        answers: List[Dict[str, Any]]  # {question_id, score}
    ) -> AssessmentResult:
        """提交评估"""
        result_id = f"assess_{user_id}_{int(datetime.now().timestamp())}"

        questions = self.assessments.get(assessment_type, [])
        max_score = sum(max(opt['score'] for opt in q.options) for q in questions)
        total_score = sum(a.get('score', 0) for a in answers)

        # 计算等级和解释
        level, interpretation, recommendations = self._interpret_result(
            assessment_type, total_score, max_score
        )

        result = AssessmentResult(
            result_id=result_id,
            user_id=user_id,
            assessment_type=assessment_type,
            score=total_score,
            max_score=max_score,
            level=level,
            interpretation=interpretation,
            recommendations=recommendations,
            answers=answers
        )

        self.results[result_id] = result
        self.user_results[user_id].append(result_id)

        return result

    def _interpret_result(
        self,
        assessment_type: AssessmentType,
        score: int,
        max_score: int
    ) -> Tuple[str, str, List[str]]:
        """解释评估结果"""
        ratio = score / max_score if max_score > 0 else 0

        if assessment_type == AssessmentType.DEPRESSION:
            if score <= 2:
                return 'normal', '您的抑郁风险较低', ['保持积极心态', '维持健康作息']
            elif score <= 4:
                return "mild", "您可能存在轻度抑郁倾向", [
                    '建议多与家人朋友交流',
                    "可以尝试放松训练",
                    "如持续两周以上建议咨询医生"
                ]
            else:
                return "moderate", "您可能存在中度抑郁倾向", [
                    '建议尽快咨询专业人士',
                    '与家人沟通您的感受',
                    '保持规律作息和运动'
                ]

        elif assessment_type == AssessmentType.ANXIETY:
            if score <= 2:
                return 'normal', '您的焦虑水平较低', ['继续保持良好心态']
            elif score <= 4:
                return 'mild', '您可能存在轻度焦虑', [
                    '尝试深呼吸放松',
                    '适当运动可以缓解焦虑',
                    '注意睡眠质量'
                ]
            else:
                return 'moderate', '您可能存在中度焦虑', [
                    '建议咨询专业人士',
                    '学习放松技巧',
                    '减少压力来源'
                ]

        elif assessment_type == AssessmentType.LONELINESS:
            if score <= 4:
                return 'normal', '您的社交状态良好', ['继续保持社交活动']
            elif score <= 6:
                return 'mild', '您可能有些孤独感', [
                    '可以多参加社区活动',
                    '主动联系老朋友',
                    '培养新的兴趣爱好'
                ]
            else:
                return 'moderate', '您可能感到比较孤独', [
                    '建议增加社交活动',
                    '可以加入兴趣小组',
                    '与家人多交流'
                ]

        elif assessment_type == AssessmentType.LIFE_SATISFACTION:
            if score >= 12:
                return 'high', '您对生活非常满意', ['继续保持积极态度']
            elif score >= 8:
                return 'moderate', "您对生活比较满意", ["可以设定小目标增加成就感"]
            else:
                return 'low', '您对生活满意度较低', [
                    '思考什么能让您更快乐',
                    '与家人分享您的想法',
                    '尝试新的活动和兴趣'
                ]

        return 'unknown', "评估完成", []

    def get_user_assessments(
        self,
        user_id: int,
        assessment_type: AssessmentType = None
    ) -> List[AssessmentResult]:
        """获取用户评估历史"""
        result_ids = self.user_results.get(user_id, [])
        results = [self.results[rid] for rid in result_ids if rid in self.results]

        if assessment_type:
            results = [r for r in results if r.assessment_type == assessment_type]

        return sorted(results, key=lambda x: x.created_at, reverse=True)


# ==================== 放松训练 ====================

@dataclass
class RelaxationExercise:
    """放松练习"""
    exercise_id: str
    name: str
    exercise_type: RelaxationType
    description: str
    duration_minutes: int
    steps: List[str]
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    difficulty: int = 1  # 1-3
    benefits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exercise_id": self.exercise_id,
            'name': self.name,
            "exercise_type": self.exercise_type.value,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            'steps': self.steps,
            'audio_url': self.audio_url,
            'video_url': self.video_url,
            'difficulty': self.difficulty,
            'benefits': self.benefits
        }


@dataclass
class RelaxationSession:
    """放松训练记录"""
    session_id: str
    user_id: int
    exercise_id: str
    exercise_name: str
    duration_minutes: int
    mood_before: Optional[int] = None  # 1-5
    mood_after: Optional[int] = None
    notes: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "duration_minutes": self.duration_minutes,
            "mood_before": self.mood_before,
            'mood_after': self.mood_after,
            "mood_change": (self.mood_after - self.mood_before) if self.mood_before and self.mood_after else None,
            'notes': self.notes,
            "completed_at": self.completed_at.isoformat()
        }


class RelaxationService:
    """放松训练服务"""

    EXERCISES = [
        RelaxationExercise(
            'relax_breathing_1', "腹式呼吸", RelaxationType.BREATHING,
            "简单有效的腹式呼吸练习，帮助放松身心",
            5,
            [
                "找一个安静舒适的地方坐下或躺下",
                "将一只手放在胸口，另一只手放在腹部",
                "用鼻子慢慢吸气4秒，感受腹部鼓起",
                "屏住呼吸2秒",
                "用嘴慢慢呼气6秒，感受腹部收缩",
                "重复这个过程5-10次"
            ],
            difficulty=1,
            benefits=['缓解焦虑', '降低血压', '改善睡眠']
        ),
        RelaxationExercise(
            'relax_breathing_2', "4-7-8呼吸法", RelaxationType.BREATHING,
            "帮助快速入睡的呼吸技巧",
            3,
            [
                '舒适地坐好或躺好',
                '用鼻子吸气4秒',
                '屏住呼吸7秒',
                '用嘴缓慢呼气8秒',
                '重复3-4个循环'
            ],
            difficulty=2,
            benefits=['促进睡眠', '减轻压力', '平复心情']
        ),
        RelaxationExercise(
            'relax_meditation_1', "简单冥想", RelaxationType.MEDITATION,
            "适合初学者的基础冥想练习",
            10,
            [
                "找一个安静的地方，舒适地坐着",
                '闭上眼睛，放松身体',
                "将注意力集中在呼吸上",
                "当思绪飘走时，轻轻地把注意力拉回到呼吸",
                "不要评判自己的想法，只是观察",
                '保持10分钟'
            ],
            difficulty=1,
            benefits=['减轻压力', '提高专注力', '增加内心平静']
        ),
        RelaxationExercise(
            'relax_imagery_1', "美好回忆想象", RelaxationType.IMAGERY,
            "通过回忆美好场景来放松心情",
            10,
            [
                "闭上眼睛，做几次深呼吸",
                "回想一个让您感到快乐和平静的地方",
                "想象那里的景色、声音、气味",
                "感受那种平和与快乐",
                "在这个美好的场景中停留几分钟",
                "慢慢睁开眼睛，带着平静的心情回来"
            ],
            difficulty=1,
            benefits=['改善心情', '减少负面情绪', '增加幸福感']
        ),
        RelaxationExercise(
            'relax_muscle_1', "渐进式肌肉放松", RelaxationType.MUSCLE_RELAXATION,
            "通过有意识地紧张和放松肌肉来放松全身",
            15,
            [
                "躺下或舒适地坐着",
                "从脚部开始：紧绷脚趾5秒，然后放松",
                "向上移动到小腿：紧绷5秒，放松",
                "继续到大腿、腹部、手、手臂、肩膀、脸部",
                "每个部位都是紧绷5秒，然后完全放松",
                '感受紧张与放松的对比'
            ],
            difficulty=2,
            benefits=['缓解肌肉紧张', '改善睡眠', '减轻身体疲劳']
        ),
        RelaxationExercise(
            'relax_mindfulness_1', '正念觉察', RelaxationType.MINDFULNESS,
            "培养对当下的觉察能力",
            10,
            [
                "舒适地坐着，保持脊背挺直",
                '注意您现在的身体感觉',
                '注意您听到的声音',
                '注意您闻到的气味',
                '不要评判，只是觉察',
                '接受此刻的一切'
            ],
            difficulty=2,
            benefits=['减少焦虑', '提高自我认知', "活在当下"]
        )
    ]

    def __init__(self):
        self.exercises = {e.exercise_id: e for e in self.EXERCISES}
        self.sessions: Dict[str, RelaxationSession] = {}
        self.user_sessions: Dict[int, List[str]] = defaultdict(list)

    def get_exercises(
        self,
        exercise_type: RelaxationType = None,
        max_duration: int = None
    ) -> List[RelaxationExercise]:
        """获取放松练习"""
        exercises = list(self.exercises.values())

        if exercise_type:
            exercises = [e for e in exercises if e.exercise_type == exercise_type]

        if max_duration:
            exercises = [e for e in exercises if e.duration_minutes <= max_duration]

        return exercises

    def get_recommended_exercise(self, mood_score: int = None) -> RelaxationExercise:
        """根据情绪推荐练习"""
        if mood_score and mood_score <= 2:
            # 心情不好，推荐简单的呼吸练习
            return self.exercises.get("relax_breathing_1")
        elif mood_score and mood_score <= 3:
            # 心情一般，推荐冥想
            return self.exercises.get("relax_meditation_1")
        else:
            # 默认推荐美好回忆
            return self.exercises.get("relax_imagery_1")

    def record_session(
        self,
        user_id: int,
        exercise_id: str,
        duration_minutes: int,
        mood_before: int = None,
        mood_after: int = None,
        notes: str = None
    ) -> Optional[RelaxationSession]:
        """记录放松训练"""
        exercise = self.exercises.get(exercise_id)
        if not exercise:
            return None

        session_id = f"relax_{user_id}_{int(datetime.now().timestamp())}"

        session = RelaxationSession(
            session_id=session_id,
            user_id=user_id,
            exercise_id=exercise_id,
            exercise_name=exercise.name,
            duration_minutes=duration_minutes,
            mood_before=mood_before,
            mood_after=mood_after,
            notes=notes
        )

        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)

        return session

    def get_user_sessions(
        self,
        user_id: int,
        days: int = 30
    ) -> List[RelaxationSession]:
        """获取用户放松训练记录"""
        cutoff = datetime.now() - timedelta(days=days)
        session_ids = self.user_sessions.get(user_id, [])

        sessions = [
            self.sessions[sid] for sid in session_ids
            if sid in self.sessions and self.sessions[sid].completed_at >= cutoff
        ]

        return sorted(sessions, key=lambda x: x.completed_at, reverse=True)


# ==================== 心理支持资源 ====================

@dataclass
class SupportResource:
    """支持资源"""
    resource_id: str
    name: str
    resource_type: str  # hotline/article/video/app
    description: str
    contact: Optional[str] = None
    url: Optional[str] = None
    available_hours: Optional[str] = None
    is_free: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            'name': self.name,
            "resource_type": self.resource_type,
            "description": self.description,
            'contact': self.contact,
            'url': self.url,
            "available_hours": self.available_hours,
            'is_free': self.is_free
        }


class SupportResourceService:
    """心理支持资源服务"""

    RESOURCES = [
        SupportResource(
            'res_hotline_1', '北京心理危机研究与干预中心',
            'hotline', "24小时心理援助热线",
            contact="010-82951332", available_hours='24小时'
        ),
        SupportResource(
            'res_hotline_2', '全国心理援助热线',
            'hotline', "卫健委心理援助热线",
            contact="400-161-9995", available_hours='24小时'
        ),
        SupportResource(
            'res_hotline_3', '希望24热线',
            "hotline", "青少年心理危机干预热线",
            contact="400-161-9995", available_hours='24小时'
        ),
        SupportResource(
            'res_article_1', '如何应对孤独感',
            "article", "了解孤独感的来源和应对方法",
            url="/resources/loneliness-guide"
        ),
        SupportResource(
            'res_article_2', '老年人睡眠改善指南',
            "article", "改善睡眠质量的实用技巧",
            url="/resources/sleep-guide"
        ),
        SupportResource(
            'res_article_3', '与焦虑共处',
            'article', "理解焦虑并学会管理",
            url="/resources/anxiety-guide"
        )
    ]

    def __init__(self):
        self.resources = {r.resource_id: r for r in self.RESOURCES}

    def get_resources(
        self,
        resource_type: str = None
    ) -> List[SupportResource]:
        """获取支持资源"""
        resources = list(self.resources.values())

        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]

        return resources

    def get_emergency_hotlines(self) -> List[SupportResource]:
        """获取紧急求助热线"""
        return [r for r in self.resources.values() if r.resource_type == 'hotline']


# ==================== 统一心理健康服务 ====================

class MentalHealthService:
    """统一心理健康服务"""

    def __init__(self):
        self.mood_tracking = MoodTrackingService()
        self.assessment = PsychologicalAssessmentService()
        self.relaxation = RelaxationService()
        self.support = SupportResourceService()

    def get_mental_health_summary(self, user_id: int) -> Dict[str, Any]:
        """获取心理健康摘要"""
        # 情绪统计
        mood_stats = self.mood_tracking.get_mood_statistics(user_id, days=7)

        # 今日情绪
        today_mood = self.mood_tracking.get_today_mood(user_id)

        # 最近评估
        recent_assessments = []
        for assessment_type in AssessmentType:
            results = self.assessment.get_user_assessments(user_id, assessment_type)
            if results:
                recent_assessments.append(results[0].to_dict())

        # 放松训练统计
        relax_sessions = self.relaxation.get_user_sessions(user_id, days=7)

        return {
            'mood': {
                "today": today_mood.to_dict() if today_mood else None,
                "weekly_stats": mood_stats
            },
            "assessments": recent_assessments[:3],
            'relaxation': {
                "sessions_this_week": len(relax_sessions),
                "total_minutes": sum(s.duration_minutes for s in relax_sessions)
            },
            "recommendations": mood_stats.get("recommendations", [])
        }


# 全局服务实例
mental_health_service = MentalHealthService()
