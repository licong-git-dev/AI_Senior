"""
个性化配置服务
为老年用户提供全面的个性化设置管理
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, time
import json

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """主题模式"""
    LIGHT = 'light'  # 浅色
    DARK = 'dark'  # 深色
    AUTO = "auto"  # 自动
    HIGH_CONTRAST = "high_contrast"  # 高对比度


class FontSize(Enum):
    """字体大小"""
    SMALL = 'small'  # 小
    MEDIUM = 'medium'  # 中
    LARGE = "large"  # 大
    EXTRA_LARGE = "extra_large"  # 特大


class LayoutMode(Enum):
    """布局模式"""
    STANDARD = 'standard'  # 标准
    SIMPLIFIED = 'simplified'  # 简化
    LARGE_ICON = "large_icon"  # 大图标


class NotificationMode(Enum):
    """通知模式"""
    ALL = 'all'  # 全部通知
    IMPORTANT = 'important'  # 仅重要
    EMERGENCY = 'emergency'  # 仅紧急
    NONE = "none"  # 静音


@dataclass
class DisplaySettings:
    """显示设置"""
    theme: ThemeMode = ThemeMode.LIGHT
    font_size: FontSize = FontSize.LARGE
    layout: LayoutMode = LayoutMode.STANDARD
    brightness: int = 80  # 0-100
    color_blind_mode: bool = False
    animations_enabled: bool = True
    large_buttons: bool = True
    show_hints: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'theme': self.theme.value,
            'font_size': self.font_size.value,
            'layout': self.layout.value,
            'brightness': self.brightness,
            "color_blind_mode": self.color_blind_mode,
            "animations_enabled": self.animations_enabled,
            "large_buttons": self.large_buttons,
            'show_hints': self.show_hints
        }


@dataclass
class AudioSettings:
    """音频设置"""
    master_volume: int = 80  # 0-100
    voice_volume: int = 90
    music_volume: int = 70
    alert_volume: int = 100
    voice_speed: float = 0.9
    voice_pitch: float = 1.0
    voice_gender: str = "female"
    enable_haptic: bool = True  # 触觉反馈
    ring_tone: str = "gentle"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "master_volume": self.master_volume,
            "voice_volume": self.voice_volume,
            "music_volume": self.music_volume,
            "alert_volume": self.alert_volume,
            "voice_speed": self.voice_speed,
            "voice_pitch": self.voice_pitch,
            "voice_gender": self.voice_gender,
            "enable_haptic": self.enable_haptic,
            'ring_tone': self.ring_tone
        }


@dataclass
class NotificationSettings:
    """通知设置"""
    mode: NotificationMode = NotificationMode.IMPORTANT
    quiet_start: Optional[time] = None
    quiet_end: Optional[time] = None
    voice_announcements: bool = True
    show_previews: bool = True
    vibrate: bool = True
    led_indicator: bool = True
    repeat_alerts: bool = True
    repeat_interval_minutes: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mode': self.mode.value,
            "quiet_start": self.quiet_start.isoformat() if self.quiet_start else None,
            'quiet_end': self.quiet_end.isoformat() if self.quiet_end else None,
            "voice_announcements": self.voice_announcements,
            "show_previews": self.show_previews,
            'vibrate': self.vibrate,
            "led_indicator": self.led_indicator,
            "repeat_alerts": self.repeat_alerts,
            "repeat_interval_minutes": self.repeat_interval_minutes
        }


@dataclass
class PrivacySettings:
    """隐私设置"""
    share_location: bool = True
    share_health_data: bool = True
    share_activity_status: bool = True
    allow_family_view: bool = True
    public_profile: bool = False
    data_collection: bool = True
    crash_reports: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "share_location": self.share_location,
            "share_health_data": self.share_health_data,
            "share_activity_status": self.share_activity_status,
            "allow_family_view": self.allow_family_view,
            "public_profile": self.public_profile,
            "data_collection": self.data_collection,
            "crash_reports": self.crash_reports
        }


@dataclass
class HealthSettings:
    """健康设置"""
    enable_reminders: bool = True
    medication_reminders: bool = True
    exercise_reminders: bool = True
    water_reminders: bool = True
    sleep_tracking: bool = True
    auto_health_check: bool = True
    health_report_frequency: str = 'daily'  # daily/weekly/monthly
    abnormal_alerts: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_reminders": self.enable_reminders,
            "medication_reminders": self.medication_reminders,
            "exercise_reminders": self.exercise_reminders,
            "water_reminders": self.water_reminders,
            "sleep_tracking": self.sleep_tracking,
            "auto_health_check": self.auto_health_check,
            "health_report_frequency": self.health_report_frequency,
            "abnormal_alerts": self.abnormal_alerts
        }


@dataclass
class ContentPreferences:
    """内容偏好"""
    preferred_music_genres: List[str] = field(default_factory=lambda: ['经典老歌', '戏曲'])
    preferred_news_categories: List[str] = field(default_factory=lambda: ['健康', '养生'])
    preferred_activities: List[str] = field(default_factory=lambda: ['太极', '广场舞'])
    language: str = 'zh-CN'
    dialect: str = 'mandarin'
    content_filter_level: str = "moderate"  # strict/moderate/none

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preferred_music_genres": self.preferred_music_genres,
            "preferred_news_categories": self.preferred_news_categories,
            "preferred_activities": self.preferred_activities,
            'language': self.language,
            'dialect': self.dialect,
            "content_filter_level": self.content_filter_level
        }


@dataclass
class QuickAccessSettings:
    """快捷访问设置"""
    home_shortcuts: List[str] = field(default_factory=lambda: [
        'health_check', 'call_family', 'entertainment', 'sos'
    ])
    voice_shortcuts: Dict[str, str] = field(default_factory=dict)
    favorite_contacts: List[int] = field(default_factory=list)
    pinned_features: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "home_shortcuts": self.home_shortcuts,
            "voice_shortcuts": self.voice_shortcuts,
            "favorite_contacts": self.favorite_contacts,
            "pinned_features": self.pinned_features
        }


@dataclass
class UserPreferences:
    """用户偏好（完整配置）"""
    user_id: int
    display: DisplaySettings = field(default_factory=DisplaySettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    notification: NotificationSettings = field(default_factory=NotificationSettings)
    privacy: PrivacySettings = field(default_factory=PrivacySettings)
    health: HealthSettings = field(default_factory=HealthSettings)
    content: ContentPreferences = field(default_factory=ContentPreferences)
    quick_access: QuickAccessSettings = field(default_factory=QuickAccessSettings)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'display': self.display.to_dict(),
            'audio': self.audio.to_dict(),
            "notification": self.notification.to_dict(),
            'privacy': self.privacy.to_dict(),
            'health': self.health.to_dict(),
            'content': self.content.to_dict(),
            "quick_access": self.quick_access.to_dict(),
            "custom_settings": self.custom_settings,
            'updated_at': self.updated_at.isoformat()
        }


# ==================== 预设配置 ====================

class PresetConfigurations:
    """预设配置方案"""

    @staticmethod
    def default_elderly() -> UserPreferences:
        """默认老年人配置"""
        prefs = UserPreferences(user_id=0)
        prefs.display.font_size = FontSize.LARGE
        prefs.display.large_buttons = True
        prefs.display.show_hints = True
        prefs.audio.voice_speed = 0.85
        prefs.audio.voice_volume = 90
        return prefs

    @staticmethod
    def vision_impaired() -> UserPreferences:
        """视力障碍配置"""
        prefs = UserPreferences(user_id=0)
        prefs.display.font_size = FontSize.EXTRA_LARGE
        prefs.display.theme = ThemeMode.HIGH_CONTRAST
        prefs.display.large_buttons = True
        prefs.audio.voice_volume = 100
        prefs.audio.voice_speed = 0.8
        prefs.notification.voice_announcements = True
        return prefs

    @staticmethod
    def hearing_impaired() -> UserPreferences:
        """听力障碍配置"""
        prefs = UserPreferences(user_id=0)
        prefs.display.font_size = FontSize.EXTRA_LARGE
        prefs.audio.master_volume = 100
        prefs.audio.enable_haptic = True
        prefs.notification.vibrate = True
        prefs.notification.led_indicator = True
        prefs.notification.voice_announcements = False
        return prefs

    @staticmethod
    def simplified() -> UserPreferences:
        """极简配置"""
        prefs = UserPreferences(user_id=0)
        prefs.display.layout = LayoutMode.SIMPLIFIED
        prefs.display.font_size = FontSize.EXTRA_LARGE
        prefs.display.large_buttons = True
        prefs.display.animations_enabled = False
        prefs.notification.mode = NotificationMode.EMERGENCY
        prefs.quick_access.home_shortcuts = ['call_family', 'sos']
        return prefs

    @staticmethod
    def tech_savvy() -> UserPreferences:
        """科技熟练配置"""
        prefs = UserPreferences(user_id=0)
        prefs.display.font_size = FontSize.MEDIUM
        prefs.display.layout = LayoutMode.STANDARD
        prefs.display.animations_enabled = True
        prefs.audio.voice_speed = 1.0
        prefs.notification.mode = NotificationMode.ALL
        return prefs


# ==================== 个性化服务 ====================

class PersonalizationService:
    """个性化配置服务"""

    def __init__(self):
        self.user_preferences: Dict[int, UserPreferences] = {}
        self.presets = PresetConfigurations()

    def get_preferences(self, user_id: int) -> UserPreferences:
        """获取用户偏好配置"""
        if user_id not in self.user_preferences:
            # 创建默认配置
            prefs = PresetConfigurations.default_elderly()
            prefs.user_id = user_id
            self.user_preferences[user_id] = prefs
        return self.user_preferences[user_id]

    def update_preferences(
        self,
        user_id: int,
        category: str,
        settings: Dict[str, Any]
    ) -> UserPreferences:
        """更新指定类别的配置"""
        prefs = self.get_preferences(user_id)

        if category == 'display':
            self._update_display(prefs.display, settings)
        elif category == 'audio':
            self._update_audio(prefs.audio, settings)
        elif category == "notification":
            self._update_notification(prefs.notification, settings)
        elif category == 'privacy':
            self._update_privacy(prefs.privacy, settings)
        elif category == 'health':
            self._update_health(prefs.health, settings)
        elif category == 'content':
            self._update_content(prefs.content, settings)
        elif category == "quick_access":
            self._update_quick_access(prefs.quick_access, settings)
        elif category == 'custom':
            prefs.custom_settings.update(settings)

        prefs.updated_at = datetime.now()
        logger.info(f'用户 {user_id} 更新 {category} 配置')
        return prefs

    def _update_display(self, display: DisplaySettings, settings: Dict):
        if 'theme' in settings:
            display.theme = ThemeMode(settings['theme'])
        if 'font_size' in settings:
            display.font_size = FontSize(settings['font_size'])
        if 'layout' in settings:
            display.layout = LayoutMode(settings['layout'])
        if 'brightness' in settings:
            display.brightness = max(0, min(100, settings["brightness"]))
        if "color_blind_mode" in settings:
            display.color_blind_mode = settings["color_blind_mode"]
        if "animations_enabled" in settings:
            display.animations_enabled = settings["animations_enabled"]
        if "large_buttons" in settings:
            display.large_buttons = settings["large_buttons"]
        if 'show_hints' in settings:
            display.show_hints = settings['show_hints']

    def _update_audio(self, audio: AudioSettings, settings: Dict):
        if "master_volume" in settings:
            audio.master_volume = max(0, min(100, settings["master_volume"]))
        if "voice_volume" in settings:
            audio.voice_volume = max(0, min(100, settings["voice_volume"]))
        if "music_volume" in settings:
            audio.music_volume = max(0, min(100, settings["music_volume"]))
        if "alert_volume" in settings:
            audio.alert_volume = max(0, min(100, settings["alert_volume"]))
        if "voice_speed" in settings:
            audio.voice_speed = max(0.5, min(2.0, settings["voice_speed"]))
        if "voice_pitch" in settings:
            audio.voice_pitch = max(0.5, min(2.0, settings["voice_pitch"]))
        if "voice_gender" in settings:
            audio.voice_gender = settings["voice_gender"]
        if "enable_haptic" in settings:
            audio.enable_haptic = settings["enable_haptic"]
        if 'ring_tone' in settings:
            audio.ring_tone = settings['ring_tone']

    def _update_notification(self, notification: NotificationSettings, settings: Dict):
        if 'mode' in settings:
            notification.mode = NotificationMode(settings['mode'])
        if "quiet_start" in settings:
            notification.quiet_start = time.fromisoformat(settings["quiet_start"]) if settings["quiet_start"] else None
        if 'quiet_end' in settings:
            notification.quiet_end = time.fromisoformat(settings['quiet_end']) if settings['quiet_end'] else None
        if "voice_announcements" in settings:
            notification.voice_announcements = settings["voice_announcements"]
        if "show_previews" in settings:
            notification.show_previews = settings["show_previews"]
        if 'vibrate' in settings:
            notification.vibrate = settings['vibrate']
        if "led_indicator" in settings:
            notification.led_indicator = settings["led_indicator"]
        if "repeat_alerts" in settings:
            notification.repeat_alerts = settings["repeat_alerts"]
        if "repeat_interval_minutes" in settings:
            notification.repeat_interval_minutes = settings["repeat_interval_minutes"]

    def _update_privacy(self, privacy: PrivacySettings, settings: Dict):
        for key in ['share_location', 'share_health_data', 'share_activity_status',
                    'allow_family_view', 'public_profile', 'data_collection', 'crash_reports']:
            if key in settings:
                setattr(privacy, key, settings[key])

    def _update_health(self, health: HealthSettings, settings: Dict):
        for key in ['enable_reminders', 'medication_reminders', 'exercise_reminders',
                    'water_reminders', 'sleep_tracking', 'auto_health_check',
                    'health_report_frequency', 'abnormal_alerts']:
            if key in settings:
                setattr(health, key, settings[key])

    def _update_content(self, content: ContentPreferences, settings: Dict):
        if "preferred_music_genres" in settings:
            content.preferred_music_genres = settings["preferred_music_genres"]
        if "preferred_news_categories" in settings:
            content.preferred_news_categories = settings["preferred_news_categories"]
        if "preferred_activities" in settings:
            content.preferred_activities = settings["preferred_activities"]
        if 'language' in settings:
            content.language = settings['language']
        if 'dialect' in settings:
            content.dialect = settings['dialect']
        if "content_filter_level" in settings:
            content.content_filter_level = settings["content_filter_level"]

    def _update_quick_access(self, quick_access: QuickAccessSettings, settings: Dict):
        if "home_shortcuts" in settings:
            quick_access.home_shortcuts = settings["home_shortcuts"]
        if "voice_shortcuts" in settings:
            quick_access.voice_shortcuts = settings["voice_shortcuts"]
        if "favorite_contacts" in settings:
            quick_access.favorite_contacts = settings["favorite_contacts"]
        if "pinned_features" in settings:
            quick_access.pinned_features = settings["pinned_features"]

    def apply_preset(self, user_id: int, preset_name: str) -> Optional[UserPreferences]:
        """应用预设配置"""
        preset_methods = {
            "default_elderly": self.presets.default_elderly,
            "vision_impaired": self.presets.vision_impaired,
            "hearing_impaired": self.presets.hearing_impaired,
            'simplified': self.presets.simplified,
            'tech_savvy': self.presets.tech_savvy
        }

        preset_method = preset_methods.get(preset_name)
        if not preset_method:
            return None

        prefs = preset_method()
        prefs.user_id = user_id
        self.user_preferences[user_id] = prefs

        logger.info(f"用户 {user_id} 应用预设: {preset_name}")
        return prefs

    def get_available_presets(self) -> List[Dict]:
        """获取可用预设列表"""
        return [
            {
                'name': "default_elderly",
                'title': '标准老年模式',
                'description': "适合大多数老年用户，字体较大，语速较慢",
                "recommended": True
            },
            {
                'name': "vision_impaired",
                'title': '视力辅助模式',
                'description': "超大字体，高对比度，强化语音播报",
                "recommended": False
            },
            {
                'name': "hearing_impaired",
                'title': '听力辅助模式',
                'description': "最大音量，强化振动和视觉提示",
                "recommended": False
            },
            {
                'name': 'simplified',
                'title': '极简模式',
                'description': "最简化的界面，只保留核心功能",
                "recommended": False
            },
            {
                'name': 'tech_savvy',
                'title': '标准模式',
                'description': "适合熟悉智能设备的用户",
                "recommended": False
            }
        ]

    def reset_preferences(self, user_id: int) -> UserPreferences:
        """重置为默认配置"""
        return self.apply_preset(user_id, "default_elderly")

    def export_preferences(self, user_id: int) -> str:
        """导出配置为JSON"""
        prefs = self.get_preferences(user_id)
        return json.dumps(prefs.to_dict(), ensure_ascii=False, indent=2)

    def import_preferences(self, user_id: int, json_data: str) -> bool:
        """从JSON导入配置"""
        try:
            data = json.loads(json_data)
            prefs = self.get_preferences(user_id)

            for category, settings in data.items():
                if category in ['display', 'audio', 'notification', 'privacy',
                               'health', 'content', 'quick_access', 'custom']:
                    self.update_preferences(user_id, category, settings)

            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False


# 全局服务实例
personalization_service = PersonalizationService()
