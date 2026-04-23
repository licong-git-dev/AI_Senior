"""
运动康复系统服务
提供运动计划、康复训练、运动数据分析等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class ExerciseType(Enum):
    """运动类型"""
    WALKING = 'walking'  # 散步
    TAI_CHI = 'tai_chi'  # 太极拳
    YOGA = 'yoga'  # 瑜伽
    STRETCHING = 'stretching'  # 拉伸
    STRENGTH = 'strength'  # 力量训练
    BALANCE = 'balance'  # 平衡训练
    SWIMMING = 'swimming'  # 游泳
    CYCLING = 'cycling'  # 骑车
    DANCING = 'dancing'  # 跳舞
    QIGONG = "qigong"  # 气功


class ExerciseIntensity(Enum):
    """运动强度"""
    LIGHT = 'light'  # 轻度
    MODERATE = 'moderate'  # 中度
    VIGOROUS = "vigorous"  # 高强度


class RehabilitationType(Enum):
    """康复类型"""
    POST_SURGERY = "post_surgery"  # 术后康复
    JOINT = 'joint'  # 关节康复
    STROKE = 'stroke'  # 中风康复
    CARDIAC = 'cardiac'  # 心脏康复
    PULMONARY = "pulmonary"  # 肺康复
    FALL_PREVENTION = "fall_prevention"  # 防跌倒训练
    COGNITIVE = "cognitive"  # 认知康复


class BodyPart(Enum):
    """身体部位"""
    NECK = 'neck'  # 颈部
    SHOULDER = 'shoulder'  # 肩部
    ARM = 'arm'  # 手臂
    WRIST = 'wrist'  # 手腕
    BACK = 'back'  # 背部
    WAIST = 'waist'  # 腰部
    HIP = 'hip'  # 髋部
    KNEE = 'knee'  # 膝盖
    ANKLE = 'ankle'  # 脚踝
    FULL_BODY = "full_body"  # 全身


@dataclass
class ExerciseMove:
    """运动动作"""
    move_id: str
    name: str
    description: str
    body_parts: List[BodyPart]
    duration_seconds: int
    repetitions: Optional[int] = None
    sets: int = 1
    rest_between_sets: int = 30
    difficulty: int = 1  # 1-5
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    precautions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'move_id': self.move_id,
            'name': self.name,
            "description": self.description,
            'body_parts': [p.value for p in self.body_parts],
            "duration_seconds": self.duration_seconds,
            "repetitions": self.repetitions,
            'sets': self.sets,
            "rest_between_sets": self.rest_between_sets,
            'difficulty': self.difficulty,
            'video_url': self.video_url,
            'image_url': self.image_url,
            "precautions": self.precautions
        }


# ==================== 运动计划 ====================

@dataclass
class ExercisePlan:
    """运动计划"""
    plan_id: str
    user_id: int
    name: str
    exercise_type: ExerciseType
    intensity: ExerciseIntensity
    frequency_per_week: int
    duration_minutes: int
    moves: List[str]  # move_ids
    goals: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'name': self.name,
            "exercise_type": self.exercise_type.value,
            'intensity': self.intensity.value,
            "frequency_per_week": self.frequency_per_week,
            "duration_minutes": self.duration_minutes,
            'moves': self.moves,
            'goals': self.goals,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes,
            'enabled': self.enabled
        }


@dataclass
class ExerciseSession:
    """运动记录"""
    session_id: str
    user_id: int
    plan_id: Optional[str]
    exercise_type: ExerciseType
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: int = 0
    calories_burned: int = 0
    distance_meters: Optional[int] = None
    steps: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    feeling: Optional[str] = None  # good/normal/tired/pain
    notes: Optional[str] = None
    completed_moves: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'plan_id': self.plan_id,
            "exercise_type": self.exercise_type.value,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            "duration_minutes": self.duration_minutes,
            "calories_burned": self.calories_burned,
            "distance_meters": self.distance_meters,
            'steps': self.steps,
            "heart_rate_avg": self.heart_rate_avg,
            "heart_rate_max": self.heart_rate_max,
            'feeling': self.feeling,
            'notes': self.notes,
            "completed_moves": self.completed_moves
        }


# ==================== 康复训练 ====================

@dataclass
class RehabProgram:
    """康复训练计划"""
    program_id: str
    user_id: int
    name: str
    rehab_type: RehabilitationType
    target_body_parts: List[BodyPart]
    phases: List[Dict[str, Any]]  # 康复阶段
    current_phase: int = 0
    start_date: datetime = field(default_factory=datetime.now)
    prescribed_by: Optional[str] = None  # 医生/治疗师
    hospital: Optional[str] = None
    notes: Optional[str] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'program_id': self.program_id,
            'name': self.name,
            "rehab_type": self.rehab_type.value,
            "target_body_parts": [p.value for p in self.target_body_parts],
            'phases': self.phases,
            "current_phase": self.current_phase,
            'start_date': self.start_date.isoformat(),
            "prescribed_by": self.prescribed_by,
            'hospital': self.hospital,
            'notes': self.notes,
            'enabled': self.enabled
        }


@dataclass
class RehabSession:
    """康复训练记录"""
    session_id: str
    user_id: int
    program_id: str
    phase: int
    exercises_completed: List[Dict[str, Any]]
    pain_level: int = 0  # 0-10
    mobility_score: Optional[int] = None  # 活动度评分
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    notes: Optional[str] = None
    therapist_feedback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'program_id': self.program_id,
            "phase": self.phase,
            "exercises_completed": self.exercises_completed,
            'pain_level': self.pain_level,
            "mobility_score": self.mobility_score,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'notes': self.notes,
            "therapist_feedback": self.therapist_feedback
        }


# ==================== 运动计划服务 ====================

class ExercisePlanService:
    """运动计划服务"""

    # 预设运动动作库
    EXERCISE_MOVES = {
        # 散步热身
        "move_warmup_neck": ExerciseMove(
            'move_warmup_neck', "颈部转动",
            "缓慢转动头部，左右各转5圈",
            [BodyPart.NECK], 60, repetitions=5, difficulty=1,
            precautions=['动作要慢', "如有头晕立即停止"]
        ),
        "move_warmup_shoulder": ExerciseMove(
            'move_warmup_shoulder', "肩部环绕",
            "双肩向前、向后各转动10次",
            [BodyPart.SHOULDER], 60, repetitions=10, difficulty=1
        ),
        "move_warmup_waist": ExerciseMove(
            'move_warmup_waist', "腰部扭转",
            "双手叉腰，左右扭转腰部",
            [BodyPart.WAIST], 60, repetitions=10, difficulty=1,
            precautions=["腰部有问题者慎做"]
        ),
        # 太极拳
        "move_taichi_start": ExerciseMove(
            'move_taichi_start', "起势",
            "双脚与肩同宽，双手缓缓上提至胸前",
            [BodyPart.FULL_BODY], 30, difficulty=2
        ),
        "move_taichi_cloud": ExerciseMove(
            'move_taichi_cloud', "云手",
            "双手如拨云般左右移动，配合重心转移",
            [BodyPart.ARM, BodyPart.WAIST], 120, difficulty=3
        ),
        # 平衡训练
        "move_balance_single": ExerciseMove(
            'move_balance_single', "单脚站立",
            "扶墙单脚站立，每侧30秒",
            [BodyPart.ANKLE, BodyPart.HIP], 60, sets=2, difficulty=2,
            precautions=['务必扶墙或有人陪伴', "站不稳立即放下"]
        ),
        "move_balance_heel": ExerciseMove(
            'move_balance_heel', '脚跟脚尖走',
            '脚跟紧贴脚尖走直线',
            [BodyPart.ANKLE, BodyPart.HIP], 120, difficulty=3,
            precautions=['需要有人陪伴', "旁边要有扶手"]
        ),
        # 拉伸
        "move_stretch_hamstring": ExerciseMove(
            'move_stretch_hamstring', "大腿后侧拉伸",
            "坐姿，一腿伸直，身体前倾触脚尖",
            [BodyPart.HIP, BodyPart.KNEE], 60, sets=2, difficulty=1,
            precautions=['不要勉强', '感到轻微拉伸即可']
        ),
        'move_stretch_calf': ExerciseMove(
            'move_stretch_calf', "小腿拉伸",
            "面墙站立，一腿后撤，保持脚跟着地",
            [BodyPart.ANKLE], 60, sets=2, difficulty=1
        ),
        # 力量训练
        "move_strength_squat": ExerciseMove(
            'move_strength_squat', "扶椅深蹲",
            "双手扶椅背，缓慢下蹲至大腿与地面平行",
            [BodyPart.HIP, BodyPart.KNEE], 90, repetitions=10, sets=2, difficulty=2,
            precautions=['膝盖不要超过脚尖', "下蹲幅度量力而行"]
        ),
        "move_strength_wall_push": ExerciseMove(
            'move_strength_wall_push', "扶墙俯卧撑",
            "面墙站立，双手扶墙做推墙动作",
            [BodyPart.ARM, BodyPart.SHOULDER], 90, repetitions=10, sets=2, difficulty=2
        ),
    }

    def __init__(self):
        self.plans: Dict[str, ExercisePlan] = {}
        self.user_plans: Dict[int, List[str]] = defaultdict(list)
        self.sessions: Dict[str, ExerciseSession] = {}
        self.user_sessions: Dict[int, List[str]] = defaultdict(list)

    def create_plan(
        self,
        user_id: int,
        name: str,
        exercise_type: ExerciseType,
        intensity: ExerciseIntensity,
        frequency_per_week: int,
        duration_minutes: int,
        moves: List[str] = None,
        goals: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        notes: str = None
    ) -> ExercisePlan:
        """创建运动计划"""
        plan_id = f"plan_{user_id}_{secrets.token_hex(4)}"

        plan = ExercisePlan(
            plan_id=plan_id,
            user_id=user_id,
            name=name,
            exercise_type=exercise_type,
            intensity=intensity,
            frequency_per_week=frequency_per_week,
            duration_minutes=duration_minutes,
            moves=moves or [],
            goals=goals or [],
            start_date=start_date or datetime.now(),
            end_date=end_date,
            notes=notes
        )

        self.plans[plan_id] = plan
        self.user_plans[user_id].append(plan_id)

        logger.info(f"创建运动计划: {name} for user {user_id}")
        return plan

    def get_user_plans(
        self,
        user_id: int,
        enabled_only: bool = True
    ) -> List[ExercisePlan]:
        """获取用户运动计划"""
        plan_ids = self.user_plans.get(user_id, [])
        plans = [self.plans[pid] for pid in plan_ids if pid in self.plans]

        if enabled_only:
            plans = [p for p in plans if p.enabled]

        return plans

    def start_session(
        self,
        user_id: int,
        exercise_type: ExerciseType,
        plan_id: str = None
    ) -> ExerciseSession:
        """开始运动记录"""
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"

        session = ExerciseSession(
            session_id=session_id,
            user_id=user_id,
            plan_id=plan_id,
            exercise_type=exercise_type,
            started_at=datetime.now()
        )

        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)

        return session

    def end_session(
        self,
        session_id: str,
        user_id: int,
        duration_minutes: int,
        calories_burned: int = 0,
        distance_meters: int = None,
        steps: int = None,
        heart_rate_avg: int = None,
        heart_rate_max: int = None,
        feeling: str = None,
        notes: str = None,
        completed_moves: List[str] = None
    ) -> Optional[ExerciseSession]:
        """结束运动记录"""
        session = self.sessions.get(session_id)
        if not session or session.user_id != user_id:
            return None

        session.ended_at = datetime.now()
        session.duration_minutes = duration_minutes
        session.calories_burned = calories_burned or self._estimate_calories(
            session.exercise_type, duration_minutes
        )
        session.distance_meters = distance_meters
        session.steps = steps
        session.heart_rate_avg = heart_rate_avg
        session.heart_rate_max = heart_rate_max
        session.feeling = feeling
        session.notes = notes
        session.completed_moves = completed_moves or []

        return session

    def _estimate_calories(
        self,
        exercise_type: ExerciseType,
        duration_minutes: int
    ) -> int:
        """估算消耗卡路里"""
        # 每分钟消耗卡路里(老年人估算)
        calories_per_minute = {
            ExerciseType.WALKING: 3,
            ExerciseType.TAI_CHI: 3,
            ExerciseType.YOGA: 2.5,
            ExerciseType.STRETCHING: 2,
            ExerciseType.STRENGTH: 4,
            ExerciseType.BALANCE: 2,
            ExerciseType.SWIMMING: 5,
            ExerciseType.CYCLING: 4,
            ExerciseType.DANCING: 4,
            ExerciseType.QIGONG: 2
        }

        rate = calories_per_minute.get(exercise_type, 3)
        return int(rate * duration_minutes)

    def get_user_sessions(
        self,
        user_id: int,
        days: int = 30,
        exercise_type: ExerciseType = None
    ) -> List[ExerciseSession]:
        """获取用户运动记录"""
        cutoff = datetime.now() - timedelta(days=days)
        session_ids = self.user_sessions.get(user_id, [])

        sessions = [
            self.sessions[sid] for sid in session_ids
            if sid in self.sessions and self.sessions[sid].started_at >= cutoff
        ]

        if exercise_type:
            sessions = [s for s in sessions if s.exercise_type == exercise_type]

        return sorted(sessions, key=lambda x: x.started_at, reverse=True)

    def get_weekly_stats(self, user_id: int) -> Dict[str, Any]:
        """获取每周运动统计"""
        sessions = self.get_user_sessions(user_id, days=7)

        total_minutes = sum(s.duration_minutes for s in sessions)
        total_calories = sum(s.calories_burned for s in sessions)
        total_sessions = len(sessions)

        # 按类型统计
        by_type = defaultdict(int)
        for s in sessions:
            by_type[s.exercise_type.value] += s.duration_minutes

        return {
            'period': "最近7天",
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "total_calories": total_calories,
            'by_type': dict(by_type),
            "daily_average": round(total_minutes / 7, 1),
            'goal_status': '达标' if total_minutes >= 150 else "未达标",
            "recommendation": self._generate_recommendation(total_minutes, total_sessions)
        }

    def _generate_recommendation(
        self,
        weekly_minutes: int,
        weekly_sessions: int
    ) -> str:
        """生成运动建议"""
        if weekly_minutes < 60:
            return "运动量偏少，建议每天至少进行15-20分钟轻度运动"
        elif weekly_minutes < 150:
            return "继续加油！建议增加运动频率，每周至少150分钟中等强度运动"
        else:
            return "运动习惯良好，请继续保持！注意运动与休息的平衡"

    def get_move_library(
        self,
        body_part: BodyPart = None,
        max_difficulty: int = 5
    ) -> List[ExerciseMove]:
        """获取动作库"""
        moves = list(self.EXERCISE_MOVES.values())

        if body_part:
            moves = [m for m in moves if body_part in m.body_parts]

        moves = [m for m in moves if m.difficulty <= max_difficulty]

        return moves


# ==================== 康复训练服务 ====================

class RehabilitationService:
    """康复训练服务"""

    # 预设康复计划模板
    REHAB_TEMPLATES = {
        "knee_replacement": {
            'name': '膝关节置换术后康复',
            "rehab_type": RehabilitationType.JOINT,
            "target_body_parts": [BodyPart.KNEE, BodyPart.HIP],
            'phases': [
                {
                    'phase': 1,
                    'name': "早期康复(术后1-2周)",
                    'goals': ['控制肿胀', '恢复膝关节屈曲'],
                    'exercises': ['踝泵运动', '股四头肌等长收缩', '直腿抬高'],
                    'frequency': "每天3-4次",
                    "duration_weeks": 2
                },
                {
                    'phase': 2,
                    'name': "中期康复(术后2-6周)",
                    'goals': ['增加活动范围', '加强肌力'],
                    'exercises': ['坐位屈膝', '站立支撑', '平衡训练'],
                    'frequency': "每天2-3次",
                    "duration_weeks": 4
                },
                {
                    'phase': 3,
                    'name': "后期康复(术后6-12周)",
                    'goals': ['恢复正常步态', '回归日常活动'],
                    'exercises': ['行走训练', '上下楼梯', '功能性活动'],
                    'frequency': "每天1-2次",
                    "duration_weeks": 6
                }
            ]
        },
        "stroke_recovery": {
            'name': '中风康复训练',
            "rehab_type": RehabilitationType.STROKE,
            "target_body_parts": [BodyPart.ARM, BodyPart.FULL_BODY],
            'phases': [
                {
                    'phase': 1,
                    'name': "急性期(发病1-2周)",
                    'goals': ['预防并发症', '维持关节活动度'],
                    'exercises': ['被动关节活动', '体位转换', '深呼吸'],
                    'frequency': "每天多次",
                    "duration_weeks": 2
                },
                {
                    'phase': 2,
                    'name': "恢复期(发病2周-3月)",
                    'goals': ['促进运动功能恢复', '提高ADL能力'],
                    'exercises': ['主动辅助运动', '坐位平衡', '转移训练'],
                    'frequency': "每天2-3次",
                    "duration_weeks": 10
                },
                {
                    'phase': 3,
                    'name': '后遗症期',
                    'goals': ['巩固功能', '代偿训练'],
                    'exercises': ['强化训练', '精细动作', '日常活动训练'],
                    'frequency': "每天1-2次",
                    "duration_weeks": 12
                }
            ]
        },
        "fall_prevention": {
            'name': '防跌倒训练计划',
            "rehab_type": RehabilitationType.FALL_PREVENTION,
            "target_body_parts": [BodyPart.ANKLE, BodyPart.HIP, BodyPart.KNEE],
            'phases': [
                {
                    'phase': 1,
                    'name': "基础阶段(第1-4周)",
                    'goals': ['增强下肢力量', '改善平衡感'],
                    'exercises': ['扶椅站立', '踮脚练习', '侧向移步'],
                    'frequency': "每天1次",
                    "duration_weeks": 4
                },
                {
                    'phase': 2,
                    'name': "进阶阶段(第5-8周)",
                    'goals': ['动态平衡', '反应能力'],
                    'exercises': ['单脚站立', '脚跟脚尖走', '转向练习'],
                    'frequency': "每天1次",
                    "duration_weeks": 4
                },
                {
                    'phase': 3,
                    'name': '维持阶段',
                    'goals': ['保持能力', '融入日常'],
                    'exercises': ['太极拳', '散步', '家务活动'],
                    'frequency': "每周3-5次",
                    "duration_weeks": 0  # 持续
                }
            ]
        }
    }

    def __init__(self):
        self.programs: Dict[str, RehabProgram] = {}
        self.user_programs: Dict[int, List[str]] = defaultdict(list)
        self.rehab_sessions: Dict[str, RehabSession] = {}
        self.user_rehab_sessions: Dict[int, List[str]] = defaultdict(list)

    def create_program(
        self,
        user_id: int,
        name: str,
        rehab_type: RehabilitationType,
        target_body_parts: List[BodyPart],
        phases: List[Dict[str, Any]] = None,
        prescribed_by: str = None,
        hospital: str = None,
        notes: str = None
    ) -> RehabProgram:
        """创建康复计划"""
        program_id = f"rehab_{user_id}_{secrets.token_hex(4)}"

        program = RehabProgram(
            program_id=program_id,
            user_id=user_id,
            name=name,
            rehab_type=rehab_type,
            target_body_parts=target_body_parts,
            phases=phases or [],
            prescribed_by=prescribed_by,
            hospital=hospital,
            notes=notes
        )

        self.programs[program_id] = program
        self.user_programs[user_id].append(program_id)

        logger.info(f"创建康复计划: {name} for user {user_id}")
        return program

    def create_from_template(
        self,
        user_id: int,
        template_key: str,
        prescribed_by: str = None,
        hospital: str = None
    ) -> Optional[RehabProgram]:
        """从模板创建康复计划"""
        template = self.REHAB_TEMPLATES.get(template_key)
        if not template:
            return None

        return self.create_program(
            user_id,
            template['name'],
            template['rehab_type'],
            template["target_body_parts"],
            template['phases'],
            prescribed_by,
            hospital
        )

    def get_user_programs(
        self,
        user_id: int,
        enabled_only: bool = True
    ) -> List[RehabProgram]:
        """获取用户康复计划"""
        program_ids = self.user_programs.get(user_id, [])
        programs = [self.programs[pid] for pid in program_ids if pid in self.programs]

        if enabled_only:
            programs = [p for p in programs if p.enabled]

        return programs

    def advance_phase(self, program_id: str, user_id: int) -> bool:
        """进入下一康复阶段"""
        program = self.programs.get(program_id)
        if not program or program.user_id != user_id:
            return False

        if program.current_phase < len(program.phases) - 1:
            program.current_phase += 1
            return True

        return False

    def record_rehab_session(
        self,
        user_id: int,
        program_id: str,
        exercises_completed: List[Dict[str, Any]],
        pain_level: int = 0,
        mobility_score: int = None,
        notes: str = None
    ) -> Optional[RehabSession]:
        """记录康复训练"""
        program = self.programs.get(program_id)
        if not program or program.user_id != user_id:
            return None

        session_id = f"rehab_session_{user_id}_{int(datetime.now().timestamp())}"

        session = RehabSession(
            session_id=session_id,
            user_id=user_id,
            program_id=program_id,
            phase=program.current_phase,
            exercises_completed=exercises_completed,
            pain_level=pain_level,
            mobility_score=mobility_score,
            notes=notes
        )

        self.rehab_sessions[session_id] = session
        self.user_rehab_sessions[user_id].append(session_id)

        return session

    def get_rehab_progress(
        self,
        user_id: int,
        program_id: str
    ) -> Dict[str, Any]:
        """获取康复进度"""
        program = self.programs.get(program_id)
        if not program or program.user_id != user_id:
            return {}

        session_ids = self.user_rehab_sessions.get(user_id, [])
        sessions = [
            self.rehab_sessions[sid] for sid in session_ids
            if sid in self.rehab_sessions and self.rehab_sessions[sid].program_id == program_id
        ]

        # 按阶段统计
        phase_stats = defaultdict(lambda: {'count': 0, "avg_pain": 0, "pain_scores": []})
        for s in sessions:
            phase_stats[s.phase]['count'] += 1
            phase_stats[s.phase]["pain_scores"].append(s.pain_level)

        for phase, stats in phase_stats.items():
            if stats["pain_scores"]:
                stats['avg_pain'] = round(sum(stats["pain_scores"]) / len(stats["pain_scores"]), 1)
            del stats["pain_scores"]

        current_phase_info = None
        if program.current_phase < len(program.phases):
            current_phase_info = program.phases[program.current_phase]

        return {
            'program_id': program_id,
            "program_name": program.name,
            "current_phase": program.current_phase,
            "total_phases": len(program.phases),
            "current_phase_info": current_phase_info,
            "total_sessions": len(sessions),
            "phase_stats": dict(phase_stats),
            "days_since_start": (datetime.now() - program.start_date).days
        }

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """获取可用康复模板"""
        templates = []
        for key, template in self.REHAB_TEMPLATES.items():
            templates.append({
                'key': key,
                'name': template['name'],
                'rehab_type': template['rehab_type'].value,
                "phases_count": len(template['phases']),
                "target_parts": [p.value for p in template["target_body_parts"]]
            })
        return templates


# ==================== 统一运动康复服务 ====================

class ExerciseService:
    """统一运动康复服务"""

    def __init__(self):
        self.exercise_plan = ExercisePlanService()
        self.rehabilitation = RehabilitationService()


# 全局服务实例
exercise_service = ExerciseService()
