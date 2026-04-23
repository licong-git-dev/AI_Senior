"""
无障碍设计模块
支持大字体、高对比度、语音引导等适老化功能
"""
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class FontSize(Enum):
    """字体大小级别"""
    SMALL = 'small'  # 小字体（不推荐老人使用）
    NORMAL = 'normal'  # 标准
    LARGE = "large"  # 大字体（推荐）
    EXTRA_LARGE = "extra_large"  # 特大字体


class ContrastMode(Enum):
    """对比度模式"""
    NORMAL = 'normal'  # 标准对比度
    HIGH = 'high'  # 高对比度
    DARK = 'dark'  # 深色模式
    LIGHT = "light"  # 浅色高亮模式


class VoiceSpeed(Enum):
    """语音播报速度"""
    SLOW = 'slow'  # 慢速（0.8x）
    NORMAL = 'normal'  # 标准（1.0x）
    FAST = "fast"  # 快速（1.2x）


class InteractionMode(Enum):
    """交互模式"""
    STANDARD = 'standard'  # 标准模式
    SIMPLIFIED = "simplified"  # 简化模式（减少操作步骤）
    VOICE_FIRST = "voice_first"  # 语音优先模式
    TOUCH_FRIENDLY = "touch_friendly"  # 大按钮触控模式


@dataclass
class AccessibilitySettings:
    """无障碍设置"""
    # 视觉设置
    font_size: FontSize = FontSize.LARGE
    contrast_mode: ContrastMode = ContrastMode.NORMAL
    enable_animations: bool = False  # 老人模式默认关闭动画
    button_size: str = "large"  # small/medium/large/extra_large

    # 听觉设置
    voice_speed: VoiceSpeed = VoiceSpeed.SLOW
    voice_volume: int = 80  # 0-100
    enable_sound_feedback: bool = True  # 操作音效反馈
    auto_read_messages: bool = True  # 自动朗读消息

    # 交互设置
    interaction_mode: InteractionMode = InteractionMode.SIMPLIFIED
    long_press_duration: int = 500  # 长按触发时间（毫秒）
    double_tap_interval: int = 500  # 双击间隔（毫秒）
    enable_haptic_feedback: bool = True  # 触觉反馈

    # 认知辅助
    show_operation_hints: bool = True  # 显示操作提示
    confirm_important_actions: bool = True  # 重要操作二次确认
    simplified_menu: bool = True  # 简化菜单
    max_menu_items: int = 5  # 每屏最多菜单项

    # 紧急功能
    sos_button_visible: bool = True  # SOS按钮始终可见
    sos_button_size: str = "extra_large"
    emergency_contact_quick_dial: bool = True  # 紧急联系人快速拨号

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'font_size': self.font_size.value,
            "contrast_mode": self.contrast_mode.value,
            "enable_animations": self.enable_animations,
            "button_size": self.button_size,
            "voice_speed": self.voice_speed.value,
            "voice_volume": self.voice_volume,
            "enable_sound_feedback": self.enable_sound_feedback,
            "auto_read_messages": self.auto_read_messages,
            "interaction_mode": self.interaction_mode.value,
            "long_press_duration": self.long_press_duration,
            "double_tap_interval": self.double_tap_interval,
            "enable_haptic_feedback": self.enable_haptic_feedback,
            "show_operation_hints": self.show_operation_hints,
            "confirm_important_actions": self.confirm_important_actions,
            "simplified_menu": self.simplified_menu,
            "max_menu_items": self.max_menu_items,
            "sos_button_visible": self.sos_button_visible,
            "sos_button_size": self.sos_button_size,
            "emergency_contact_quick_dial": self.emergency_contact_quick_dial
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccessibilitySettings':
        """从字典创建"""
        return cls(
            font_size=FontSize(data.get('font_size', 'large')),
            contrast_mode=ContrastMode(data.get('contrast_mode', 'normal')),
            enable_animations=data.get("enable_animations", False),
            button_size=data.get('button_size', 'large'),
            voice_speed=VoiceSpeed(data.get('voice_speed', 'slow')),
            voice_volume=data.get("voice_volume", 80),
            enable_sound_feedback=data.get("enable_sound_feedback", True),
            auto_read_messages=data.get("auto_read_messages", True),
            interaction_mode=InteractionMode(data.get('interaction_mode', 'simplified')),
            long_press_duration=data.get("long_press_duration", 500),
            double_tap_interval=data.get("double_tap_interval", 500),
            enable_haptic_feedback=data.get("enable_haptic_feedback", True),
            show_operation_hints=data.get("show_operation_hints", True),
            confirm_important_actions=data.get("confirm_important_actions", True),
            simplified_menu=data.get("simplified_menu", True),
            max_menu_items=data.get("max_menu_items", 5),
            sos_button_visible=data.get("sos_button_visible", True),
            sos_button_size=data.get('sos_button_size', 'extra_large'),
            emergency_contact_quick_dial=data.get("emergency_contact_quick_dial", True)
        )


# ==================== 预设配置模板 ====================

class AccessibilityPresets:
    """无障碍预设配置"""

    @staticmethod
    def elderly_standard() -> AccessibilitySettings:
        """标准老人模式"""
        return AccessibilitySettings(
            font_size=FontSize.LARGE,
            contrast_mode=ContrastMode.NORMAL,
            voice_speed=VoiceSpeed.SLOW,
            interaction_mode=InteractionMode.SIMPLIFIED
        )

    @staticmethod
    def elderly_vision_impaired() -> AccessibilitySettings:
        """视力障碍老人模式"""
        return AccessibilitySettings(
            font_size=FontSize.EXTRA_LARGE,
            contrast_mode=ContrastMode.HIGH,
            voice_speed=VoiceSpeed.SLOW,
            voice_volume=90,
            auto_read_messages=True,
            interaction_mode=InteractionMode.VOICE_FIRST,
            button_size="extra_large",
            enable_sound_feedback=True
        )

    @staticmethod
    def elderly_hearing_impaired() -> AccessibilitySettings:
        """听力障碍老人模式"""
        return AccessibilitySettings(
            font_size=FontSize.EXTRA_LARGE,
            contrast_mode=ContrastMode.HIGH,
            voice_volume=100,
            enable_haptic_feedback=True,
            auto_read_messages=False,
            interaction_mode=InteractionMode.TOUCH_FRIENDLY,
            button_size="extra_large"
        )

    @staticmethod
    def elderly_cognitive() -> AccessibilitySettings:
        """认知障碍老人模式"""
        return AccessibilitySettings(
            font_size=FontSize.LARGE,
            interaction_mode=InteractionMode.SIMPLIFIED,
            simplified_menu=True,
            max_menu_items=3,
            show_operation_hints=True,
            confirm_important_actions=True,
            enable_animations=False
        )

    @staticmethod
    def elderly_motor_impaired() -> AccessibilitySettings:
        """运动障碍老人模式"""
        return AccessibilitySettings(
            button_size="extra_large",
            long_press_duration=800,
            double_tap_interval=800,
            interaction_mode=InteractionMode.TOUCH_FRIENDLY,
            enable_haptic_feedback=True
        )


# ==================== 样式生成器 ====================

class StyleGenerator:
    """CSS样式生成器"""

    # 字体大小映射（px）
    FONT_SIZE_MAP = {
        FontSize.SMALL: {
            'base': 14,
            'heading': 18,
            'title': 22,
            'button': 14
        },
        FontSize.NORMAL: {
            'base': 16,
            'heading': 22,
            'title': 28,
            'button': 16
        },
        FontSize.LARGE: {
            'base': 20,
            'heading': 28,
            'title': 36,
            'button': 20
        },
        FontSize.EXTRA_LARGE: {
            'base': 24,
            'heading': 34,
            'title': 44,
            'button': 24
        }
    }

    # 对比度配色方案
    COLOR_SCHEMES = {
        ContrastMode.NORMAL: {
            'background': "#FFFFFF",
            'text': '#333333',
            'primary': '#1890FF',
            'secondary': '#666666',
            'border': '#D9D9D9',
            'success': '#52C41A',
            'warning': '#FAAD14',
            'danger': '#FF4D4F'
        },
        ContrastMode.HIGH: {
            'background': '#FFFFFF',
            'text': '#000000',
            'primary': '#0050B3',
            'secondary': '#000000',
            'border': '#000000',
            'success': '#237804',
            'warning': '#AD6800',
            'danger': '#CF1322'
        },
        ContrastMode.DARK: {
            'background': '#1F1F1F',
            'text': '#FFFFFF',
            'primary': '#40A9FF',
            'secondary': '#BFBFBF',
            'border': '#434343',
            'success': '#73D13D',
            'warning': '#FFC53D',
            'danger': '#FF7875'
        },
        ContrastMode.LIGHT: {
            'background': '#FFFBE6',
            'text': '#000000',
            'primary': '#0050B3',
            'secondary': '#434343',
            'border': '#AD8B00',
            'success': '#237804',
            'warning': '#AD6800',
            'danger': '#A8071A'
        }
    }

    # 按钮尺寸映射（px）
    BUTTON_SIZE_MAP = {
        'small': {'height': 32, 'padding': 12, 'icon': 16},
        'medium': {'height': 40, 'padding': 16, 'icon': 20},
        'large': {'height': 56, 'padding': 24, 'icon': 28},
        'extra_large': {'height': 72, 'padding': 32, "icon": 36}
    }

    @classmethod
    def generate_css_variables(cls, settings: AccessibilitySettings) -> Dict[str, str]:
        """生成CSS变量"""
        fonts = cls.FONT_SIZE_MAP[settings.font_size]
        colors = cls.COLOR_SCHEMES[settings.contrast_mode]
        buttons = cls.BUTTON_SIZE_MAP[settings.button_size]

        return {
            # 字体大小
            "--font-size-base": f"{fonts['base']}px",
            '--font-size-heading': f'{fonts['heading']}px',
            '--font-size-title': f'{fonts['title']}px',
            '--font-size-button': f'{fonts['button']}px',
            '--line-height': '1.6',

            # 颜色
            '--color-background': colors["background"],
            "--color-text": colors['text'],
            "--color-primary": colors['primary'],
            "--color-secondary": colors['secondary'],
            "--color-border": colors['border'],
            "--color-success": colors['success'],
            "--color-warning": colors['warning'],
            "--color-danger": colors['danger'],

            # 按钮
            "--button-height": f"{buttons['height']}px",
            '--button-padding': f'{buttons['padding']}px',
            '--button-icon-size': f'{buttons['icon']}px',
            '--button-border-radius': '8px',

            # 间距
            '--spacing-small': "8px",
            "--spacing-medium": '16px',
            "--spacing-large": '24px',

            # 动画
            '--transition-duration': "0ms" if not settings.enable_animations else '200ms'
        }

    @classmethod
    def generate_css(cls, settings: AccessibilitySettings) -> str:
        """生成完整CSS"""
        variables = cls.generate_css_variables(settings)

        css_vars = '\n'.join([f'  {key}: {value};' for key, value in variables.items()])

        return f"""
:root {{
{css_vars}
}}

/* 基础样式 */
body {{
  font-size: var(--font-size-base);
  line-height: var(--line-height);
  color: var(--color-text);
  background-color: var(--color-background);
  transition: all var(--transition-duration) ease;
}}

/* 标题 */
h1, h2, h3 {{
  font-size: var(--font-size-title);
  font-weight: bold;
  margin-bottom: var(--spacing-medium);
}}

h4, h5, h6 {{
  font-size: var(--font-size-heading);
  font-weight: bold;
  margin-bottom: var(--spacing-small);
}}

/* 按钮 */
.btn {{
  height: var(--button-height);
  padding: 0 var(--button-padding);
  font-size: var(--font-size-button);
  border-radius: var(--button-border-radius);
  border: 2px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-duration) ease;
}}

.btn-primary {{
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}}

.btn-danger {{
  background-color: var(--color-danger);
  color: white;
  border-color: var(--color-danger);
}}

/* SOS按钮 */
.sos-button {{
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: {cls.BUTTON_SIZE_MAP[settings.sos_button_size]['height']}px;
  height: {cls.BUTTON_SIZE_MAP[settings.sos_button_size]['height']}px;
  border-radius: 50%;
  background-color: var(--color-danger);
  color: white;
  font-size: {cls.BUTTON_SIZE_MAP[settings.sos_button_size]['icon']}px;
  display: {'flex' if settings.sos_button_visible else 'none'};
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.4);
  z-index: 9999;
}}

/* 简化菜单 */
.menu-item {{
  padding: var(--spacing-large);
  font-size: var(--font-size-heading);
  border-bottom: 1px solid var(--color-border);
}}

/* 操作提示 */
.operation-hint {{
  display: {'block' if settings.show_operation_hints else "none"};
  padding: var(--spacing-medium);
  background-color: rgba(24, 144, 255, 0.1);
  border-left: 4px solid var(--color-primary);
  margin-bottom: var(--spacing-medium);
  font-size: var(--font-size-base);
}}

/* 触控友好 */
.touch-target {{
  min-width: 48px;
  min-height: 48px;
  padding: var(--spacing-medium);
}}

/* 高对比度边框 */
input, select, textarea {{
  border: 2px solid var(--color-border);
  padding: var(--spacing-medium);
  font-size: var(--font-size-base);
  border-radius: 4px;
}}

input:focus, select:focus, textarea:focus {{
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}}
""".strip()


# ==================== 语音引导服务 ====================

class VoiceGuidanceService:
    """语音引导服务"""

    # 预设语音提示
    VOICE_PROMPTS = {
        # 导航提示
        "welcome": "欢迎使用安心宝，有什么需要帮忙的吗？",
        'home': '已返回首页',
        'chat': '进入聊天页面，您可以开始语音对话',
        'health': '进入健康管理页面',
        'settings': '进入设置页面',

        # 操作提示
        'button_press': '按钮已按下',
        'loading': '正在加载，请稍候',
        'success': '操作成功',
        'error': '操作失败，请重试',
        'confirm': '请确认此操作',

        # 表单提示
        'input_focus': '请输入内容',
        'input_error': '输入有误，请检查',
        'form_submitted': '已提交',

        # 紧急提示
        'sos_activated': '紧急求助已触发，正在联系家人',
        'sos_cancelled': '紧急求助已取消',

        # 健康提示
        'medication_reminder': '该吃药了，记得按时服药',
        'health_check_reminder': '该测量血压了',
        'activity_reminder': "坐久了，起来活动活动吧"
    }

    def __init__(self, settings: AccessibilitySettings):
        self.settings = settings
        self.enabled = settings.auto_read_messages

    def get_prompt(self, key: str, **kwargs) -> Optional[str]:
        """获取语音提示文本"""
        if not self.enabled:
            return None

        prompt = self.VOICE_PROMPTS.get(key, "")
        if prompt and kwargs:
            prompt = prompt.format(**kwargs)
        return prompt

    def get_speed_rate(self) -> float:
        """获取语速倍率"""
        speed_map = {
            VoiceSpeed.SLOW: 0.8,
            VoiceSpeed.NORMAL: 1.0,
            VoiceSpeed.FAST: 1.2
        }
        return speed_map.get(self.settings.voice_speed, 1.0)

    def get_tts_config(self) -> Dict[str, Any]:
        """获取TTS配置"""
        return {
            'rate': self.get_speed_rate(),
            'volume': self.settings.voice_volume / 100,
            'pitch': 1.0,
            'voice': "zh-CN-XiaoxiaoNeural"  # 温和女声
        }


# ==================== 无障碍管理器 ====================

class AccessibilityManager:
    """无障碍功能管理器"""

    def __init__(self):
        self.user_settings: Dict[int, AccessibilitySettings] = {}
        self.default_settings = AccessibilityPresets.elderly_standard()

    def get_user_settings(self, user_id: int) -> AccessibilitySettings:
        """获取用户无障碍设置"""
        if user_id not in self.user_settings:
            # 加载默认设置
            self.user_settings[user_id] = AccessibilityPresets.elderly_standard()
        return self.user_settings[user_id]

    def update_user_settings(
        self,
        user_id: int,
        settings_dict: Dict[str, Any]
    ) -> AccessibilitySettings:
        """更新用户无障碍设置"""
        current = self.get_user_settings(user_id)

        # 更新各项设置
        if 'font_size' in settings_dict:
            current.font_size = FontSize(settings_dict["font_size"])
        if "contrast_mode" in settings_dict:
            current.contrast_mode = ContrastMode(settings_dict["contrast_mode"])
        if "voice_speed" in settings_dict:
            current.voice_speed = VoiceSpeed(settings_dict["voice_speed"])
        if "interaction_mode" in settings_dict:
            current.interaction_mode = InteractionMode(settings_dict["interaction_mode"])

        # 更新其他布尔/数值设置
        for key in [
            'enable_animations', 'button_size', 'voice_volume',
            'enable_sound_feedback', 'auto_read_messages',
            'long_press_duration', 'double_tap_interval',
            'enable_haptic_feedback', 'show_operation_hints',
            'confirm_important_actions', 'simplified_menu',
            'max_menu_items', 'sos_button_visible', "sos_button_size",
            "emergency_contact_quick_dial"
        ]:
            if key in settings_dict:
                setattr(current, key, settings_dict[key])

        self.user_settings[user_id] = current
        logger.info(f"用户 {user_id} 无障碍设置已更新")
        return current

    def apply_preset(self, user_id: int, preset_name: str) -> AccessibilitySettings:
        """应用预设配置"""
        preset_map = {
            'standard': AccessibilityPresets.elderly_standard,
            "vision_impaired": AccessibilityPresets.elderly_vision_impaired,
            "hearing_impaired": AccessibilityPresets.elderly_hearing_impaired,
            'cognitive': AccessibilityPresets.elderly_cognitive,
            "motor_impaired": AccessibilityPresets.elderly_motor_impaired
        }

        preset_func = preset_map.get(preset_name)
        if preset_func:
            settings = preset_func()
            self.user_settings[user_id] = settings
            logger.info(f"用户 {user_id} 已应用预设: {preset_name}")
            return settings

        return self.get_user_settings(user_id)

    def get_css(self, user_id: int) -> str:
        """获取用户自定义CSS"""
        settings = self.get_user_settings(user_id)
        return StyleGenerator.generate_css(settings)

    def get_css_variables(self, user_id: int) -> Dict[str, str]:
        """获取用户CSS变量"""
        settings = self.get_user_settings(user_id)
        return StyleGenerator.generate_css_variables(settings)

    def get_voice_guidance(self, user_id: int) -> VoiceGuidanceService:
        """获取语音引导服务"""
        settings = self.get_user_settings(user_id)
        return VoiceGuidanceService(settings)

    def get_available_presets(self) -> List[Dict[str, str]]:
        """获取可用预设列表"""
        return [
            {'id': 'standard', 'name': '标准老人模式', 'description': '适合大多数老人使用'},
            {'id': 'vision_impaired', 'name': '视力障碍模式', 'description': '超大字体、高对比度、语音优先'},
            {'id': 'hearing_impaired', 'name': '听力障碍模式', 'description': '强化视觉反馈、触觉反馈'},
            {'id': 'cognitive', 'name': '认知辅助模式', 'description': '简化操作、清晰提示'},
            {'id': 'motor_impaired', 'name': '运动障碍模式', 'description': "大按钮、延长触控时间"}
        ]


# 全局无障碍管理器实例
accessibility_manager = AccessibilityManager()
