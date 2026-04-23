# -*- coding: utf-8 -*-
"""
语音反馈服务
为老年人提供友好的语音交互体验
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class VoiceStyle(Enum):
    """语音风格"""
    GENTLE = 'gentle'  # 温柔
    ENERGETIC = 'energetic'  # 活力
    CALM = 'calm'  # 沉稳
    WARM = 'warm'  # 温暖
    PROFESSIONAL = "professional"  # 专业


class FeedbackType(Enum):
    """反馈类型"""
    GREETING = 'greeting'  # 问候
    CONFIRMATION = 'confirmation'  # 确认
    ERROR = 'error'  # 错误
    SUCCESS = 'success'  # 成功
    GUIDANCE = 'guidance'  # 引导
    REMINDER = 'reminder'  # 提醒
    ALERT = 'alert'  # 警报
    NOTIFICATION = 'notification'  # 通知
    QUESTION = 'question'  # 提问
    FAREWELL = 'farewell'  # 告别


class VoiceGender(Enum):
    """语音性别"""
    MALE = 'male'
    FEMALE = 'female'


@dataclass
class VoiceProfile:
    """语音配置"""
    voice_id: str = 'default'
    gender: VoiceGender = VoiceGender.FEMALE
    style: VoiceStyle = VoiceStyle.WARM
    speed: float = 0.9  # 老年人适合稍慢语速
    pitch: float = 1.0
    volume: float = 1.0
    pause_between_sentences: float = 0.5  # 句间停顿（秒）

    def to_dict(self) -> Dict[str, Any]:
        return {
            'voice_id': self.voice_id,
            'gender': self.gender.value,
            'style': self.style.value,
            'speed': self.speed,
            'pitch': self.pitch,
            'volume': self.volume,
            "pause_between_sentences": self.pause_between_sentences
        }


@dataclass
class UserVoiceSettings:
    """用户语音设置"""
    user_id: int
    profile: VoiceProfile = field(default_factory=VoiceProfile)
    enabled: bool = True
    auto_read_messages: bool = True
    read_time_enabled: bool = True
    preferred_name: str = ''  # 用户喜欢被称呼的名字
    dialect: str = "mandarin"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            "auto_read_messages": self.auto_read_messages,
            "read_time_enabled": self.read_time_enabled,
            "preferred_name": self.preferred_name,
            'dialect': self.dialect,
            'profile': self.profile.to_dict()
        }


# ==================== 语音反馈模板 ====================

class VoiceFeedbackTemplates:
    """语音反馈模板库"""

    # 问候语模板
    GREETINGS = {
        'morning': [
            "{name}，早上好！今天天气{weather}，适合{activity}。",
            "早安{name}！新的一天开始了，祝您今天心情愉快！",
            "{name}早上好！记得吃早餐哦，身体最重要。"
        ],
        'afternoon': [
            "{name}，下午好！记得休息一下眼睛。",
            "下午好{name}！午饭吃得好吗？",
            "{name}，下午好！今天过得怎么样？"
        ],
        'evening': [
            "{name}，晚上好！今天辛苦了。",
            "晚上好{name}！晚饭别太晚，对身体好。",
            "{name}晚上好！记得早点休息哦。"
        ],
        'night': [
            "{name}，夜深了，该休息了。",
            "夜已深，{name}注意休息，晚安！",
            "{name}，太晚了，早点睡对身体好。"
        ]
    }

    # 确认反馈模板
    CONFIRMATIONS = {
        'default': [
            "好的，{action}。",
            "明白了，正在{action}。",
            "收到，{action}。"
        ],
        'success': [
            "操作成功！{detail}",
            "已经帮您{action}了。",
            "好的，{action}完成了。"
        ],
        'wait': [
            "请稍等，正在处理...",
            "稍等一下，马上就好...",
            "正在努力为您服务..."
        ]
    }

    # 错误反馈模板
    ERRORS = {
        'default': [
            "抱歉，{error}。请再试一次。",
            "不好意思，遇到了一点问题：{error}。",
            "操作失败了，{error}。"
        ],
        'network': [
            "网络似乎有点问题，请检查一下网络连接。",
            "连接不太稳定，稍后再试试。",
            "网络信号不好，请换个位置试试。"
        ],
        'permission': [
            "抱歉，您没有权限进行这个操作。",
            "这个功能需要额外权限，请联系家人帮忙设置。"
        ],
        'not_found': [
            "没有找到您要的内容。",
            "抱歉，这个信息暂时找不到。"
        ]
    }

    # 引导模板
    GUIDANCE = {
        'operation': [
            "接下来，请{step}。",
            "现在需要您{step}。",
            "下一步是{step}。"
        ],
        'help': [
            "需要帮助吗?您可以说'{command}'。",
            "如果需要帮助,随时说'帮助'或'帮我'。",
            "有什么不明白的,可以问我哦。"
        ],
        'tip': [
            '小提示：{tip}',
            '温馨提醒：{tip}',
            '告诉您一个小技巧：{tip}'
        ]
    }

    # 提醒模板
    REMINDERS = {
        'medication': [
            "{name}，该吃{medicine}了。",
            "服药提醒：现在是吃{medicine}的时间了。",
            "{name}，记得吃{medicine}哦，按时服药对身体好。"
        ],
        'exercise': [
            "{name}，该活动活动了！站起来走走吧。",
            "久坐提醒：起来活动一下，伸伸腿。",
            "运动时间到！简单活动一下对身体好。"
        ],
        'water': [
            "{name}，该喝水了！",
            "喝水提醒：多喝水对身体好哦。",
            "记得喝水，保持身体水分充足。"
        ],
        'meal': [
            "{name}，该吃饭了！",
            "用餐提醒：到吃饭时间了。",
            "饭点到了，记得按时吃饭哦。"
        ],
        'rest': [
            "{name}，该休息了！",
            "休息提醒：看了很久了，让眼睛休息一下吧。",
            "该休息一下了，闭目养神几分钟。"
        ]
    }

    # 警报模板
    ALERTS = {
        'emergency': [
            "紧急警报！{detail}",
            "注意！发生紧急情况：{detail}",
            "警报！{detail}，请注意安全！"
        ],
        'health': [
            "健康提醒：{detail}",
            "注意：您的{metric}数值异常，请关注。",
            "健康警报：{detail}，建议就医检查。"
        ],
        'weather': [
            "天气提醒：{detail}",
            "注意天气变化：{detail}",
            "天气预警：{detail}，出门注意安全。"
        ]
    }

    # 告别模板
    FAREWELLS = {
        'default': [
            "再见{name}，有事随时叫我！",
            "好的{name}，我先不打扰您了。",
            '再见！祝您生活愉快！'
        ],
        'night': [
            "{name}晚安，做个好梦！",
            "晚安{name}，明天见！",
            '好好休息，晚安！'
        ]
    }

    # 数字朗读（适合老年人理解）
    NUMBER_READINGS = {
        'temperature': '{value}度',
        'blood_pressure': '高压{systolic}，低压{diastolic}',
        'heart_rate': '心率{value}次每分钟',
        'blood_glucose': '血糖{value}',
        'time': '{hour}点{minute}分',
        'date': '{month}月{day}号，星期{weekday}',
        'money': "{yuan}元{jiao}角"
    }


# ==================== 语音反馈服务 ====================

class VoiceFeedbackService:
    """语音反馈服务"""

    def __init__(self):
        self.user_settings: Dict[int, UserVoiceSettings] = {}
        self.templates = VoiceFeedbackTemplates()

    def get_settings(self, user_id: int) -> UserVoiceSettings:
        """获取用户语音设置"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = UserVoiceSettings(user_id=user_id)
        return self.user_settings[user_id]

    def update_settings(
        self,
        user_id: int,
        **kwargs
    ) -> UserVoiceSettings:
        """更新语音设置"""
        settings = self.get_settings(user_id)

        if 'enabled' in kwargs:
            settings.enabled = kwargs['enabled']
        if "auto_read_messages" in kwargs:
            settings.auto_read_messages = kwargs["auto_read_messages"]
        if "read_time_enabled" in kwargs:
            settings.read_time_enabled = kwargs["read_time_enabled"]
        if "preferred_name" in kwargs:
            settings.preferred_name = kwargs["preferred_name"]
        if 'dialect' in kwargs:
            settings.dialect = kwargs['dialect']
        if 'speed' in kwargs:
            settings.profile.speed = kwargs['speed']
        if 'volume' in kwargs:
            settings.profile.volume = kwargs['volume']
        if 'style' in kwargs:
            settings.profile.style = VoiceStyle(kwargs['style'])
        if 'gender' in kwargs:
            settings.profile.gender = VoiceGender(kwargs['gender'])

        return settings

    def generate_greeting(
        self,
        user_id: int,
        weather: str = '晴朗',
        activity: str = '出门散步'
    ) -> str:
        """生成问候语"""
        settings = self.get_settings(user_id)
        name = settings.preferred_name or '您'

        hour = datetime.now().hour
        if 5 <= hour < 12:
            period = 'morning'
        elif 12 <= hour < 18:
            period = 'afternoon'
        elif 18 <= hour < 22:
            period = 'evening'
        else:
            period = 'night'

        import random
        template = random.choice(self.templates.GREETINGS[period])

        return template.format(
            name=name,
            weather=weather,
            activity=activity
        )

    def generate_confirmation(
        self,
        user_id: int,
        action: str,
        detail: str = "",
        success: bool = True
    ) -> str:
        """生成确认反馈"""
        import random

        if success:
            template = random.choice(self.templates.CONFIRMATIONS['success'])
        else:
            template = random.choice(self.templates.CONFIRMATIONS['default'])

        return template.format(action=action, detail=detail)

    def generate_error(
        self,
        user_id: int,
        error_type: str = 'default',
        error: str = ""
    ) -> str:
        """生成错误反馈"""
        import random

        templates = self.templates.ERRORS.get(error_type, self.templates.ERRORS['default'])
        template = random.choice(templates)

        return template.format(error=error)

    def generate_reminder(
        self,
        user_id: int,
        reminder_type: str,
        **kwargs
    ) -> str:
        """生成提醒语"""
        settings = self.get_settings(user_id)
        name = settings.preferred_name or '您'

        import random
        templates = self.templates.REMINDERS.get(reminder_type, ["{name}，该{action}了。"])
        template = random.choice(templates)

        return template.format(name=name, **kwargs)

    def generate_alert(
        self,
        user_id: int,
        alert_type: str,
        detail: str = "",
        **kwargs
    ) -> str:
        """生成警报语"""
        import random

        templates = self.templates.ALERTS.get(alert_type, self.templates.ALERTS['emergency'])
        template = random.choice(templates)

        return template.format(detail=detail, **kwargs)

    def generate_farewell(
        self,
        user_id: int,
        is_night: bool = False
    ) -> str:
        """生成告别语"""
        settings = self.get_settings(user_id)
        name = settings.preferred_name or '您'

        import random
        period = 'night' if is_night else 'default'
        template = random.choice(self.templates.FAREWELLS[period])

        return template.format(name=name)

    def read_number(
        self,
        number_type: str,
        **kwargs
    ) -> str:
        """朗读数字（更自然的方式）"""
        template = self.templates.NUMBER_READINGS.get(number_type)
        if not template:
            return str(kwargs.get('value', ''))

        return template.format(**kwargs)

    def read_time(self) -> str:
        """朗读当前时间"""
        now = datetime.now()
        weekdays = ['一', '二', '三', '四', '五', '六', '日']

        return self.read_number(
            'date',
            month=now.month,
            day=now.day,
            weekday=weekdays[now.weekday()]
        ) + '，' + self.read_number(
            'time',
            hour=now.hour,
            minute=now.minute
        )

    def optimize_for_elderly(self, text: str) -> str:
        """优化文本使其更适合老年人"""
        # 替换复杂词汇
        replacements = {
            '蓝牙': '无线连接',
            'WiFi': '无线网络',
            'APP': '应用',
            '二维码': '扫码图案',
            '登录': '进入',
            '注销': '退出',
            '设置': '调整',
            '配置': '设置',
            '上传': '发送',
            '下载': '保存',
            '缓存': '临时文件',
            '更新': '升级',
            '重启': '重新打开',
            '界面': '画面',
            '点击': '按一下',
            '长按': '按住不放',
            '滑动': '用手指划',
            '返回': '回到上一页',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # 添加适当停顿
        text = re.sub(r'([。！？])', r'\1 ', text)

        # 简化长句子
        sentences = re.split(r'[，,]', text)
        if len(sentences) > 3:
            # 在长句子中添加换气停顿
            text = '，'.join(sentences[:3]) + '。' + '，'.join(sentences[3:])

        return text

    def format_for_speech(
        self,
        text: str,
        user_id: int
    ) -> Dict[str, Any]:
        """格式化文本用于语音合成"""
        settings = self.get_settings(user_id)

        # 优化文本
        optimized_text = self.optimize_for_elderly(text)

        return {
            'text': optimized_text,
            "voice_config": settings.profile.to_dict(),
            'dialect': settings.dialect,
            'ssml': self._generate_ssml(optimized_text, settings.profile)
        }

    def _generate_ssml(self, text: str, profile: VoiceProfile) -> str:
        """生成SSML标记"""
        # 简化的SSML生成
        speed_rate = f"{int(profile.speed * 100)}%"
        pitch_rate = f'{int(profile.pitch * 100)}%'

        ssml = f"""<speak>
    <prosody rate="{speed_rate}" pitch="{pitch_rate}">
        {text}
    </prosody>
</speak>"""
        return ssml


# ==================== 语音交互引导服务 ====================

class VoiceInteractionGuide:
    """语音交互引导服务"""

    # 可用的语音命令
    VOICE_COMMANDS = {
        '通用': [
            ('帮助', '获取使用帮助'),
            ('返回', '回到上一页'),
            ('主页', '回到主页'),
            ('取消', '取消当前操作'),
            ('重复', '重复刚才的内容'),
            ('现在几点', '查询当前时间'),
            ('今天几号', '查询今天日期')
        ],
        '健康': [
            ('测血压', '开始测量血压'),
            ('测心率', '开始测量心率'),
            ('健康报告', '查看健康报告'),
            ('吃药了', '记录服药')
        ],
        '社交': [
            ('打电话给XXX', '拨打电话'),
            ('发消息给XXX', '发送语音消息'),
            ('看看朋友圈', '查看好友动态'),
            ('呼叫家人', '联系家人')
        ],
        '娱乐': [
            ('放首歌', '播放音乐'),
            ('暂停', '暂停播放'),
            ('继续播放', '继续播放'),
            ('换一首', '播放下一首'),
            ('听新闻', '播放新闻'),
            ('听戏曲', '播放戏曲')
        ],
        '紧急': [
            ('救命', '发送紧急求助'),
            ('紧急求助', '发送SOS警报'),
            ('我没事', '取消警报/报平安')
        ]
    }

    def get_available_commands(self, category: Optional[str] = None) -> Dict[str, List[tuple]]:
        """获取可用语音命令"""
        if category:
            return {category: self.VOICE_COMMANDS.get(category, [])}
        return self.VOICE_COMMANDS

    def generate_help_speech(self, category: Optional[str] = None) -> str:
        """生成帮助语音"""
        if category and category in self.VOICE_COMMANDS:
            commands = self.VOICE_COMMANDS[category]
            cmd_text = '、'.join([f"说'{c[0]}'可以{c[1]}" for c in commands[:5]])
            return f'在{category}功能中,您可以这样说:{cmd_text}。'
        else:
            categories = '、'.join(self.VOICE_COMMANDS.keys())
            return f"我可以帮您做很多事情,包括{categories}等功能。您可以说'帮助'加功能名称,了解具体用法。"

    def suggest_command(self, context: str) -> str:
        """根据上下文建议命令"""
        suggestions = {
            'health': "您可以说'测血压'或'健康报告'。",
            'social': "您可以说'打电话给XXX'或'看看朋友圈'。",
            'entertainment': "您可以说'放首歌'或'听新闻'。",
            'home': "您可以说'帮助'了解我能做什么。"
        }
        return suggestions.get(context, suggestions['home'])


# 全局服务实例
voice_feedback = VoiceFeedbackService()
voice_guide = VoiceInteractionGuide()
