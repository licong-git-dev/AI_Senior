"""
新手引导服务
为老年用户提供友好的入门引导流程
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """引导步骤"""
    WELCOME = 'welcome'  # 欢迎
    PROFILE_SETUP = "profile_setup"  # 基本信息
    VOICE_SETUP = "voice_setup"  # 语音设置
    ACCESSIBILITY_SETUP = "accessibility_setup"  # 无障碍设置
    FAMILY_BINDING = "family_binding"  # 家庭绑定
    EMERGENCY_CONTACTS = "emergency_contacts"  # 紧急联系人
    HEALTH_PROFILE = "health_profile"  # 健康档案
    FEATURE_TOUR = "feature_tour"  # 功能介绍
    PRACTICE = 'practice'  # 练习使用
    COMPLETED = 'completed'  # 完成


class StepStatus(Enum):
    """步骤状态"""
    PENDING = 'pending'
    IN_PROGRESS = "in_progress"
    COMPLETED = 'completed'
    SKIPPED = 'skipped'


@dataclass
class OnboardingStepInfo:
    """引导步骤信息"""
    step: OnboardingStep
    title: str
    description: str
    voice_intro: str  # 语音介绍
    duration_minutes: int  # 预计时长
    is_required: bool = True
    help_tips: List[str] = field(default_factory=list)
    sub_steps: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'step': self.step.value,
            'title': self.title,
            "description": self.description,
            "voice_intro": self.voice_intro,
            "duration_minutes": self.duration_minutes,
            "is_required": self.is_required,
            'help_tips': self.help_tips,
            'sub_steps': self.sub_steps
        }


@dataclass
class UserOnboardingProgress:
    """用户引导进度"""
    user_id: int
    current_step: OnboardingStep = OnboardingStep.WELCOME
    completed_steps: List[str] = field(default_factory=list)
    skipped_steps: List[str] = field(default_factory=list)
    step_data: Dict[str, Any] = field(default_factory=dict)  # 每步收集的数据
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    is_completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_step": self.current_step.value,
            "completed_steps": self.completed_steps,
            "skipped_steps": self.skipped_steps,
            "progress_percent": self._calculate_progress(),
            'started_at': self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_completed": self.is_completed
        }

    def _calculate_progress(self) -> int:
        total_steps = len(OnboardingStep) - 1  # 不包括COMPLETED
        completed = len(self.completed_steps) + len(self.skipped_steps)
        return int((completed / total_steps) * 100)


# ==================== 引导步骤定义 ====================

ONBOARDING_STEPS: Dict[OnboardingStep, OnboardingStepInfo] = {
    OnboardingStep.WELCOME: OnboardingStepInfo(
        step=OnboardingStep.WELCOME,
        title='欢迎使用安心宝',
        description="让我们一起来了解安心宝，它会成为您生活中的好帮手。",
        voice_intro="您好！欢迎使用安心宝。我是您的智能助手，会陪伴您，帮助您更方便地生活。接下来，我会一步步引导您完成设置。不用担心，很简单的！",
        duration_minutes=2,
        help_tips=[
            "安心宝是专为您设计的智能助手",
            "您可以随时说'帮助'获取使用指导",
            "不要着急，我们会慢慢来"
        ]
    ),

    OnboardingStep.PROFILE_SETUP: OnboardingStepInfo(
        step=OnboardingStep.PROFILE_SETUP,
        title='基本信息设置',
        description="告诉我一些关于您的信息，这样我可以更好地为您服务。",
        voice_intro="现在，请告诉我一些关于您的信息。您希望我怎么称呼您呢？",
        duration_minutes=3,
        help_tips=[
            '您可以设置喜欢的称呼',
            "生日信息用于生日祝福",
            "这些信息只用于为您提供更好的服务"
        ],
        sub_steps=[
            {'id': 'name', 'label': '设置称呼', 'required': True},
            {'id': 'birthday', 'label': '设置生日', 'required': False},
            {'id': 'gender', 'label': '设置性别', 'required': False}
        ]
    ),

    OnboardingStep.VOICE_SETUP: OnboardingStepInfo(
        step=OnboardingStep.VOICE_SETUP,
        title='语音设置',
        description="调整语音的速度和音量，让您听得更清楚。",
        voice_intro="接下来，我们来调整语音。您觉得我说话的速度怎么样？太快还是太慢？",
        duration_minutes=2,
        help_tips=[
            "语速可以调慢一些，听得更清楚",
            "音量可以根据您的听力调整",
            '可以随时在设置中修改'
        ],
        sub_steps=[
            {'id': 'speed', 'label': '调整语速', 'required': True},
            {'id': 'volume', 'label': '调整音量', 'required': True},
            {'id': 'voice_style', 'label': '选择语音风格', 'required': False}
        ]
    ),

    OnboardingStep.ACCESSIBILITY_SETUP: OnboardingStepInfo(
        step=OnboardingStep.ACCESSIBILITY_SETUP,
        title='显示设置',
        description="调整字体大小和颜色，让您看得更清楚。",
        voice_intro="现在我们来调整屏幕显示。您觉得现在的字够大吗？颜色看得清楚吗？",
        duration_minutes=2,
        help_tips=[
            "字体可以调大,看得更清楚",
            "可以选择高对比度模式",
            "有多种预设方案可以选择"
        ],
        sub_steps=[
            {'id': 'font_size', 'label': '调整字体大小', 'required': True},
            {'id': 'contrast', 'label': '调整对比度', 'required': False},
            {'id': 'theme', 'label': '选择主题', 'required': False}
        ]
    ),

    OnboardingStep.FAMILY_BINDING: OnboardingStepInfo(
        step=OnboardingStep.FAMILY_BINDING,
        title='绑定家人',
        description="把家人添加进来，他们可以随时关心您的状况。",
        voice_intro="接下来是很重要的一步。请把您的子女或家人添加进来，这样他们可以通过手机关心您。",
        duration_minutes=5,
        is_required=False,
        help_tips=[
            "家人绑定后可以收到您的消息",
            "紧急情况时会自动通知家人",
            "可以稍后再设置，但建议现在完成"
        ],
        sub_steps=[
            {'id': 'create_group', 'label': '创建家庭组', 'required': True},
            {'id': 'invite_family', 'label': '邀请家人', 'required': False}
        ]
    ),

    OnboardingStep.EMERGENCY_CONTACTS: OnboardingStepInfo(
        step=OnboardingStep.EMERGENCY_CONTACTS,
        title='设置紧急联系人',
        description="添加紧急联系人，在需要帮助时可以快速联系到他们。",
        voice_intro="这一步非常重要。请添加您的紧急联系人，这样在您需要帮助时，我可以立刻通知他们。",
        duration_minutes=3,
        help_tips=[
            "建议至少添加2位紧急联系人",
            "可以是子女、亲戚或邻居",
            "紧急情况时会按顺序通知"
        ],
        sub_steps=[
            {'id': 'primary_contact', 'label': '添加主要联系人', 'required': True},
            {'id': 'secondary_contact', 'label': '添加备用联系人', 'required': False}
        ]
    ),

    OnboardingStep.HEALTH_PROFILE: OnboardingStepInfo(
        step=OnboardingStep.HEALTH_PROFILE,
        title='健康档案',
        description="记录您的基本健康信息，方便健康管理。",
        voice_intro="现在我们来记录一些健康信息。您有什么需要特别注意的健康问题吗？比如高血压、糖尿病？",
        duration_minutes=3,
        is_required=False,
        help_tips=[
            "记录慢性病有助于健康提醒",
            '可以设置服药提醒',
            '这些信息完全保密'
        ],
        sub_steps=[
            {'id': 'chronic_diseases', 'label': '慢性病记录', 'required': False},
            {'id': 'medications', 'label': '常用药物', 'required': False},
            {'id': 'allergies', 'label': '过敏信息', 'required': False}
        ]
    ),

    OnboardingStep.FEATURE_TOUR: OnboardingStepInfo(
        step=OnboardingStep.FEATURE_TOUR,
        title='功能介绍',
        description="了解安心宝可以帮您做什么。",
        voice_intro="设置差不多完成了。现在让我给您介绍一下安心宝都能做什么。",
        duration_minutes=5,
        help_tips=[
            "记不住没关系，随时可以问我",
            "常用功能会放在主页",
            "可以用语音控制大部分功能"
        ],
        sub_steps=[
            {'id': 'health_intro', 'label': '健康管理功能', 'required': True},
            {'id': 'social_intro', 'label': '社交功能', 'required': True},
            {'id': 'entertainment_intro', 'label': '娱乐功能', 'required': True},
            {'id': 'emergency_intro', 'label': '紧急求助', 'required': True}
        ]
    ),

    OnboardingStep.PRACTICE: OnboardingStepInfo(
        step=OnboardingStep.PRACTICE,
        title='练习使用',
        description="让我们来试试几个常用操作。",
        voice_intro="最后，我们来练习几个常用操作。不要紧张，做错了也没关系，我会一直帮助您。",
        duration_minutes=5,
        help_tips=[
            "不用担心做错，可以多试几次",
            "有问题随时说'帮助'",
            "熟能生巧，很快就会习惯"
        ],
        sub_steps=[
            {'id': 'voice_practice', 'label': '语音操作练习', 'required': True},
            {'id': 'button_practice', 'label': '按钮操作练习', 'required': True},
            {'id': 'sos_practice', 'label': '紧急求助练习', 'required': True}
        ]
    )
}


# ==================== 新手引导服务 ====================

class OnboardingService:
    """新手引导服务"""

    def __init__(self):
        self.user_progress: Dict[int, UserOnboardingProgress] = {}
        self.steps = ONBOARDING_STEPS

    def start_onboarding(self, user_id: int) -> UserOnboardingProgress:
        """开始引导流程"""
        progress = UserOnboardingProgress(user_id=user_id)
        self.user_progress[user_id] = progress

        logger.info(f"用户 {user_id} 开始新手引导")
        return progress

    def get_progress(self, user_id: int) -> Optional[UserOnboardingProgress]:
        """获取用户引导进度"""
        return self.user_progress.get(user_id)

    def get_current_step_info(self, user_id: int) -> Optional[OnboardingStepInfo]:
        """获取当前步骤信息"""
        progress = self.get_progress(user_id)
        if not progress:
            return None

        return self.steps.get(progress.current_step)

    def complete_step(
        self,
        user_id: int,
        step: OnboardingStep,
        data: Optional[Dict] = None
    ) -> Optional[UserOnboardingProgress]:
        """完成一个步骤"""
        progress = self.get_progress(user_id)
        if not progress:
            return None

        # 记录完成的步骤
        if step.value not in progress.completed_steps:
            progress.completed_steps.append(step.value)

        # 保存步骤数据
        if data:
            progress.step_data[step.value] = data

        # 移动到下一步
        next_step = self._get_next_step(step)
        if next_step:
            progress.current_step = next_step
        else:
            progress.current_step = OnboardingStep.COMPLETED
            progress.is_completed = True
            progress.completed_at = datetime.now()

        logger.info(f"用户 {user_id} 完成步骤: {step.value}")
        return progress

    def skip_step(
        self,
        user_id: int,
        step: OnboardingStep
    ) -> Optional[UserOnboardingProgress]:
        """跳过一个步骤"""
        progress = self.get_progress(user_id)
        if not progress:
            return None

        step_info = self.steps.get(step)
        if step_info and step_info.is_required:
            # 必需步骤不能跳过
            return None

        if step.value not in progress.skipped_steps:
            progress.skipped_steps.append(step.value)

        # 移动到下一步
        next_step = self._get_next_step(step)
        if next_step:
            progress.current_step = next_step
        else:
            progress.current_step = OnboardingStep.COMPLETED
            progress.is_completed = True
            progress.completed_at = datetime.now()

        logger.info(f"用户 {user_id} 跳过步骤: {step.value}")
        return progress

    def go_back(self, user_id: int) -> Optional[UserOnboardingProgress]:
        """返回上一步"""
        progress = self.get_progress(user_id)
        if not progress:
            return None

        prev_step = self._get_previous_step(progress.current_step)
        if prev_step:
            progress.current_step = prev_step

            # 从完成列表中移除
            if prev_step.value in progress.completed_steps:
                progress.completed_steps.remove(prev_step.value)

        return progress

    def _get_next_step(self, current: OnboardingStep) -> Optional[OnboardingStep]:
        """获取下一步"""
        steps = list(OnboardingStep)
        try:
            idx = steps.index(current)
            if idx < len(steps) - 1:
                return steps[idx + 1]
        except ValueError:
            pass
        return None

    def _get_previous_step(self, current: OnboardingStep) -> Optional[OnboardingStep]:
        """获取上一步"""
        steps = list(OnboardingStep)
        try:
            idx = steps.index(current)
            if idx > 0:
                return steps[idx - 1]
        except ValueError:
            pass
        return None

    def get_all_steps(self) -> List[OnboardingStepInfo]:
        """获取所有步骤信息"""
        return [self.steps[step] for step in OnboardingStep if step != OnboardingStep.COMPLETED]

    def get_step_status(self, user_id: int, step: OnboardingStep) -> StepStatus:
        """获取步骤状态"""
        progress = self.get_progress(user_id)
        if not progress:
            return StepStatus.PENDING

        if step.value in progress.completed_steps:
            return StepStatus.COMPLETED
        elif step.value in progress.skipped_steps:
            return StepStatus.SKIPPED
        elif progress.current_step == step:
            return StepStatus.IN_PROGRESS
        else:
            return StepStatus.PENDING

    def reset_onboarding(self, user_id: int) -> UserOnboardingProgress:
        """重置引导流程"""
        progress = UserOnboardingProgress(user_id=user_id)
        self.user_progress[user_id] = progress

        logger.info(f"用户 {user_id} 重置新手引导")
        return progress

    def generate_step_voice_guide(
        self,
        user_id: int,
        step: OnboardingStep
    ) -> Optional[str]:
        """生成步骤语音引导"""
        step_info = self.steps.get(step)
        if not step_info:
            return None

        return step_info.voice_intro

    def get_completion_message(self, user_id: int) -> str:
        """获取完成消息"""
        progress = self.get_progress(user_id)
        if not progress:
            return '欢迎使用安心宝！'

        if progress.is_completed:
            name = progress.step_data.get('profile_setup', {}).get('name', '您')
            return f"恭喜{name}！您已经完成了所有设置。现在可以开始使用安心宝的各项功能了。有任何问题随时说'帮助'，我会一直陪伴您！"

        return ""


# ==================== 互动练习服务 ====================

class PracticeService:
    """互动练习服务"""

    PRACTICE_TASKS = {
        "voice_practice": {
            'title': '语音操作练习',
            'instruction': "请对我说'你好'或'帮助'",
            'success_keywords': ['你好', '帮助', '助手'],
            'success_message': '太棒了！您已经学会用语音和我交流了！',
            'hint': "直接说出来就可以，我在听"
        },
        "button_practice": {
            'title': '按钮操作练习',
            'instruction': "请点击屏幕上的'健康'按钮",
            'success_action': 'click_health',
            'success_message': '做得好！点击按钮就是这么简单！',
            'hint': "用手指轻轻点一下按钮就可以"
        },
        "sos_practice": {
            'title': '紧急求助练习',
            'instruction': '这是紧急求助按钮，遇到危险时按住它3秒。现在我们来练习一下（这只是练习，不会真的发出警报）',
            'success_action': 'long_press_sos',
            'success_message': '很好！您已经知道怎么使用紧急求助了。真正遇到危险时，按住这个按钮就可以通知家人。',
            'hint': "用手指按住红色按钮，数1、2、3再松开"
        }
    }

    def get_practice_task(self, task_id: str) -> Optional[Dict]:
        """获取练习任务"""
        return self.PRACTICE_TASKS.get(task_id)

    def verify_voice_practice(self, spoken_text: str) -> bool:
        """验证语音练习"""
        task = self.PRACTICE_TASKS.get("voice_practice")
        if not task:
            return False

        keywords = task.get("success_keywords", [])
        return any(kw in spoken_text for kw in keywords)

    def get_all_practice_tasks(self) -> List[Dict]:
        """获取所有练习任务"""
        return [
            {'id': task_id, **task_info}
            for task_id, task_info in self.PRACTICE_TASKS.items()
        ]


# 全局服务实例
onboarding_service = OnboardingService()
practice_service = PracticeService()
