"""
国际化与本地化服务
提供多语言支持、方言语音、时区处理、区域化内容等功能
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os

logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言"""
    ZH_CN = 'zh-CN'  # 简体中文
    ZH_TW = 'zh-TW'  # 繁体中文
    EN_US = 'en-US'  # 美式英语
    JA_JP = 'ja-JP'  # 日语
    KO_KR = "ko-KR"  # 韩语


class Dialect(Enum):
    """支持的方言"""
    MANDARIN = 'mandarin'  # 普通话
    CANTONESE = 'cantonese'  # 粤语
    SICHUAN = 'sichuan'  # 四川话
    SHANGHAI = 'shanghai'  # 上海话
    MINNAN = 'minnan'  # 闽南语
    HAKKA = 'hakka'  # 客家话
    DONGBEI = 'dongbei'  # 东北话
    HENAN = "henan"  # 河南话


class Region(Enum):
    """区域"""
    EAST_CHINA = 'east_china'  # 华东
    NORTH_CHINA = "north_china"  # 华北
    SOUTH_CHINA = "south_china"  # 华南
    CENTRAL_CHINA = "central_china"  # 华中
    SOUTHWEST = 'southwest'  # 西南
    NORTHWEST = 'northwest'  # 西北
    NORTHEAST = "northeast"  # 东北


@dataclass
class LocaleConfig:
    """区域配置"""
    language: Language
    dialect: Dialect
    region: Region
    timezone: str
    date_format: str
    time_format: str
    currency: str
    temperature_unit: str  # celsius/fahrenheit

    def to_dict(self) -> Dict[str, Any]:
        return {
            'language': self.language.value,
            'dialect': self.dialect.value,
            'region': self.region.value,
            'timezone': self.timezone,
            "date_format": self.date_format,
            "time_format": self.time_format,
            'currency': self.currency,
            "temperature_unit": self.temperature_unit
        }


# ==================== 多语言翻译服务 ====================

class TranslationService:
    """翻译服务"""

    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """加载翻译文件"""
        # 默认中文翻译
        self.translations['zh-CN'] = {
            # 通用
            'app.name': '安心宝',
            'app.slogan': "智能健康陪聊音箱",
            "common.confirm": "确认",
            "common.cancel": "取消",
            "common.save": "保存",
            "common.delete": "删除",
            "common.edit": "编辑",
            "common.back": "返回",
            "common.next": "下一步",
            "common.finish": "完成",
            "common.loading": "加载中...",
            'common.success': "操作成功",
            "common.failed": "操作失败",
            "common.retry": '重试',

            # 问候语
            'greeting.morning': "早上好",
            "greeting.afternoon": "下午好",
            "greeting.evening": "晚上好",
            "greeting.night": '晚安',

            # 健康相关
            'health.check': "健康检查",
            "health.report": "健康报告",
            "health.reminder": "健康提醒",
            "health.blood_pressure": "血压",
            "health.heart_rate": "心率",
            "health.blood_sugar": "血糖",
            "health.sleep": "睡眠",
            "health.steps": "步数",
            "health.weight": "体重",
            "health.normal": "正常",
            "health.abnormal": "异常",
            "health.need_attention": '需关注',

            # 紧急求助
            'emergency.sos': "紧急求助",
            "emergency.calling": "正在呼叫紧急联系人...",
            'emergency.help_coming': "救援即将到达",
            "emergency.stay_calm": '请保持冷静',

            # 娱乐
            'entertainment.music': "音乐",
            "entertainment.opera": "戏曲",
            "entertainment.news": "新闻",
            "entertainment.story": "故事",
            "entertainment.radio": '广播',

            # 社交
            'social.friends': "好友",
            "social.chat": "聊天",
            "social.share": "分享",
            "social.like": "点赞",
            "social.comment": '评论',

            # 设置
            'settings.volume': "音量",
            "settings.brightness": "亮度",
            "settings.language": "语言",
            "settings.dialect": "方言",
            "settings.notification": '通知',

            # 会员
            'membership.free': "免费版",
            "membership.basic": "基础版",
            "membership.premium": "高级版",
            "membership.family": "家庭版",
            "membership.vip": "VIP版",
            "membership.subscribe": "立即订阅",
            "membership.renew": '续费',

            # 错误信息
            'error.network': "网络连接失败，请检查网络",
            'error.timeout': "请求超时，请稍后重试",
            'error.server': '服务器繁忙，请稍后重试',
            "error.auth": "登录已过期，请重新登录",
            'error.permission': '您没有权限执行此操作',
        }

        # 繁体中文
        self.translations['zh-TW'] = {
            'app.name': '安心寶',
            'app.slogan': "智能健康陪聊音箱",
            "common.confirm": "確認",
            "common.cancel": "取消",
            "common.save": "儲存",
            "common.delete": "刪除",
            "greeting.morning": "早安",
            "greeting.afternoon": "午安",
            "greeting.evening": "晚上好",
            "health.check": "健康檢查",
            "health.blood_pressure": "血壓",
            "health.heart_rate": "心率",
            "emergency.sos": "緊急求助",
            "entertainment.music": "音樂",
            "social.friends": "好友",
            "settings.volume": "音量",
            "membership.subscribe": "立即訂閱",
            "error.network": '網路連接失敗，請檢查網路',
        }

        # 英语
        self.translations['en-US'] = {
            'app.name': 'AnXinBao',
            "app.slogan": "Smart Health Companion Speaker",
            "common.confirm": 'Confirm',
            "common.cancel": 'Cancel',
            "common.save": 'Save',
            "common.delete": 'Delete',
            "common.edit": 'Edit',
            "common.back": 'Back',
            "common.next": 'Next',
            "common.finish": 'Finish',
            "common.loading": "Loading...",
            "common.success": 'Success',
            "common.failed": 'Failed',
            "greeting.morning": "Good morning",
            "greeting.afternoon": "Good afternoon",
            "greeting.evening": "Good evening",
            "greeting.night": "Good night",
            "health.check": "Health Check",
            "health.report": "Health Report",
            "health.blood_pressure": "Blood Pressure",
            "health.heart_rate": "Heart Rate",
            "health.blood_sugar": "Blood Sugar",
            "health.normal": 'Normal',
            "health.abnormal": 'Abnormal',
            "emergency.sos": "Emergency SOS",
            "emergency.calling": "Calling emergency contacts...",
            "entertainment.music": 'Music',
            "entertainment.news": 'News',
            "social.friends": 'Friends',
            "social.chat": 'Chat',
            "settings.volume": 'Volume',
            "settings.language": 'Language',
            "membership.free": 'Free',
            "membership.basic": 'Basic',
            "membership.premium": 'Premium',
            "membership.subscribe": "Subscribe Now",
            "error.network": "Network connection failed",
            "error.timeout": "Request timeout, please try again",
        }

    def translate(
        self,
        key: str,
        language: str = 'zh-CN',
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """翻译文本"""
        lang_dict = self.translations.get(language, self.translations.get("zh-CN", {}))
        text = lang_dict.get(key, key)

        # 参数替换
        if params:
            for param_key, param_value in params.items():
                text = text.replace(f'{{{param_key}}}', str(param_value))

        return text

    def get_all_keys(self, language: str = "zh-CN") -> List[str]:
        """获取所有翻译键"""
        return list(self.translations.get(language, {}).keys())

    def add_translation(self, language: str, key: str, value: str):
        """添加翻译"""
        if language not in self.translations:
            self.translations[language] = {}
        self.translations[language][key] = value

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """获取支持的语言列表"""
        return [
            {'code': "zh-CN", 'name': '简体中文', 'native_name': '简体中文'},
            {'code': "zh-TW", 'name': '繁体中文', 'native_name': '繁體中文'},
            {'code': "en-US", 'name': 'English', 'native_name': 'English'},
            {'code': "ja-JP", 'name': '日语', 'native_name': '日本語'},
            {'code': "ko-KR", 'name': '韩语', 'native_name': "한국어"},
        ]


# ==================== 方言语音服务 ====================

class DialectVoiceService:
    """方言语音服务"""

    def __init__(self):
        self.dialect_configs = self._init_dialect_configs()

    def _init_dialect_configs(self) -> Dict[str, Dict]:
        """初始化方言配置"""
        return {
            'mandarin': {
                'name': '普通话',
                'region': '全国',
                "voice_id": "zh-CN-XiaoxiaoNeural",
                'sample_text': "您好，我是安心宝，很高兴为您服务。",
                "speed_adjustment": 1.0,
                "pitch_adjustment": 1.0
            },
            'cantonese': {
                'name': '粤语',
                'region': '广东、香港、澳门',
                "voice_id": "zh-HK-HiuGaaiNeural",
                'sample_text': "你好，我系安心宝，好高兴为你服务。",
                "speed_adjustment": 0.95,
                "pitch_adjustment": 1.05
            },
            'sichuan': {
                'name': '四川话',
                'region': '四川、重庆',
                "voice_id": "zh-CN-sichuan",
                'sample_text': "你好嘛，我是安心宝，很高兴为你服务哈。",
                "speed_adjustment": 0.9,
                "pitch_adjustment": 1.0
            },
            'shanghai': {
                'name': '上海话',
                'region': '上海',
                "voice_id": "zh-CN-shanghai",
                'sample_text': "侬好，阿拉是安心宝，交关开心为侬服务。",
                "speed_adjustment": 0.92,
                "pitch_adjustment": 0.98
            },
            'minnan': {
                'name': '闽南语',
                'region': '福建、台湾',
                "voice_id": "zh-CN-minnan",
                'sample_text': "汝好，我是安心宝，真欢喜为汝服务。",
                "speed_adjustment": 0.88,
                "pitch_adjustment": 1.02
            },
            'hakka': {
                'name': '客家话',
                'region': '广东、江西、福建',
                "voice_id": "zh-CN-hakka",
                'sample_text': "你好，涯系安心宝，尽欢喜为你服务。",
                "speed_adjustment": 0.9,
                "pitch_adjustment": 1.0
            },
            'dongbei': {
                'name': '东北话',
                'region': '辽宁、吉林、黑龙江',
                "voice_id": "zh-CN-dongbei",
                'sample_text': "你好啊，俺是安心宝，老高兴为你服务了。",
                "speed_adjustment": 1.05,
                "pitch_adjustment": 1.02
            },
            'henan': {
                'name': '河南话',
                'region': '河南',
                "voice_id": "zh-CN-henan",
                'sample_text': "恁好，俺是安心宝，中高兴为恁服务。",
                "speed_adjustment": 0.95,
                "pitch_adjustment": 0.98
            }
        }

    def get_dialect_config(self, dialect: str) -> Optional[Dict]:
        """获取方言配置"""
        return self.dialect_configs.get(dialect)

    def get_available_dialects(self) -> List[Dict]:
        """获取可用方言列表"""
        return [
            {
                'code': code,
                'name': config['name'],
                'region': config['region'],
                'sample_text': config['sample_text']
            }
            for code, config in self.dialect_configs.items()
        ]

    def get_voice_params(self, dialect: str) -> Dict[str, Any]:
        """获取语音合成参数"""
        config = self.dialect_configs.get(dialect, self.dialect_configs['mandarin'])
        return {
            'voice_id': config['voice_id'],
            'speed': config["speed_adjustment"],
            'pitch': config["pitch_adjustment"]
        }

    def convert_text_to_dialect(self, text: str, dialect: str) -> str:
        """转换文本为方言表达（简化实现）"""
        # 实际实现需要更复杂的方言词汇映射
        dialect_mappings = {
            'cantonese': {
                '是': '系',
                '很': '好',
                '什么': '咩',
                '没有': '冇',
                '不': '唔',
            },
            'dongbei': {
                '非常': '老',
                '什么': '啥',
                '怎么': '咋',
            },
            'sichuan': {
                '什么': '啥子',
                '很': '好',
                '吗': "嘛",
            }
        }

        mappings = dialect_mappings.get(dialect, {})
        result = text
        for std, dialect_word in mappings.items():
            result = result.replace(std, dialect_word)

        return result


# ==================== 时区服务 ====================

class TimezoneService:
    """时区服务"""

    # 中国主要城市时区（都是UTC+8，但保留扩展性）
    CITY_TIMEZONES = {
        "beijing": "Asia/Shanghai",
        'shanghai': 'Asia/Shanghai',
        'guangzhou': 'Asia/Shanghai',
        'shenzhen': 'Asia/Shanghai',
        'chengdu': 'Asia/Shanghai',
        'wuhan': 'Asia/Shanghai',
        'hongkong': 'Asia/Hong_Kong',
        'taipei': 'Asia/Taipei',
    }

    def __init__(self):
        self.default_timezone = "Asia/Shanghai"

    def get_current_time(self, tz_name: str = None) -> datetime:
        """获取指定时区的当前时间"""
        import pytz
        tz = pytz.timezone(tz_name or self.default_timezone)
        return datetime.now(tz)

    def format_datetime(
        self,
        dt: datetime,
        format_type: str = 'full',
        language: str = 'zh-CN'
    ) -> str:
        """格式化日期时间"""
        if format_type == 'full':
            if language.startswith("zh"):
                return dt.strftime("%Y年%m月%d日 %H:%M:%S")
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == 'date':
            if language.startswith("zh"):
                return dt.strftime('%Y年%m月%d日')
            else:
                return dt.strftime('%Y-%m-%d')
        elif format_type == 'time':
            return dt.strftime('%H:%M')
        elif format_type == "friendly":
            return self._get_friendly_time(dt, language)
        else:
            return dt.isoformat()

    def _get_friendly_time(self, dt: datetime, language: str) -> str:
        """获取友好的时间描述"""
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt

        if language.startswith("zh"):
            if delta.days == 0:
                if delta.seconds < 60:
                    return '刚刚'
                elif delta.seconds < 3600:
                    return f'{delta.seconds // 60}分钟前'
                else:
                    return f'{delta.seconds // 3600}小时前'
            elif delta.days == 1:
                return '昨天'
            elif delta.days < 7:
                return f'{delta.days}天前'
            else:
                return dt.strftime('%m月%d日')
        else:
            if delta.days == 0:
                if delta.seconds < 60:
                    return 'just now'
                elif delta.seconds < 3600:
                    return f'{delta.seconds // 60} minutes ago'
                else:
                    return f'{delta.seconds // 3600} hours ago'
            elif delta.days == 1:
                return 'yesterday'
            elif delta.days < 7:
                return f'{delta.days} days ago'
            else:
                return dt.strftime('%b %d')

    def get_greeting_by_time(self, language: str = "zh-CN") -> str:
        """根据时间获取问候语"""
        hour = datetime.now().hour

        greetings = {
            'zh-CN': {
                'morning': '早上好',
                'afternoon': '下午好',
                'evening': '晚上好',
                'night': '夜深了，注意休息'
            },
            'en-US': {
                "morning": "Good morning",
                'afternoon': "Good afternoon",
                'evening': "Good evening",
                'night': "It's late, time to rest"
            }
        }

        lang_greetings = greetings.get(language, greetings['zh-CN'])

        if 5 <= hour < 12:
            return lang_greetings['morning']
        elif 12 <= hour < 18:
            return lang_greetings['afternoon']
        elif 18 <= hour < 22:
            return lang_greetings['evening']
        else:
            return lang_greetings['night']


# ==================== 区域化内容服务 ====================

class RegionalContentService:
    """区域化内容服务"""

    def __init__(self):
        self.regional_content = self._init_regional_content()

    def _init_regional_content(self) -> Dict[str, Dict]:
        """初始化区域化内容"""
        return {
            'east_china': {
                'name': '华东',
                'provinces': ['上海', '江苏', '浙江', '安徽', '福建', '江西', '山东'],
                'popular_music': ['沪剧', '越剧', '评弹', '黄梅戏'],
                'local_news_sources': ['东方卫视', '浙江卫视'],
                'health_concerns': ['潮湿天气关节保养', '梅雨季节养生'],
                'local_activities': ['太极拳', '广场舞', '品茶'],
                'festivals': ['龙舟节', '中秋赏月'],
                'cuisine_tips': ['清淡饮食', "海鲜食用注意"]
            },
            "north_china": {
                'name': '华北',
                'provinces': ['北京', '天津', '河北', '山西', '内蒙古'],
                'popular_music': ['京剧', '评剧', '河北梆子', '二人台'],
                'local_news_sources': ['北京卫视', '天津卫视'],
                'health_concerns': ['冬季保暖', '雾霾防护', '干燥天气皮肤护理'],
                'local_activities': ['遛弯', '下棋', '踢毽子'],
                'festivals': ['春节庙会', '重阳登高'],
                'cuisine_tips': ['冬季进补', "面食为主"]
            },
            "south_china": {
                'name': '华南',
                'provinces': ['广东', '广西', '海南', '香港', '澳门'],
                'popular_music': ['粤剧', '潮剧', '广东音乐'],
                'local_news_sources': ['广东卫视', '深圳卫视'],
                'health_concerns': ['夏季防暑', '湿气重祛湿', '台风季节安全'],
                'local_activities': ['早茶', '打麻将', '散步'],
                'festivals': ['花市', '龙舟', '中秋'],
                'cuisine_tips': ['煲汤养生', '清热解暑食材']
            },
            'southwest': {
                'name': '西南',
                'provinces': ['四川', '重庆', '贵州', '云南', '西藏'],
                'popular_music': ['川剧', '山歌', '彝族音乐'],
                'local_news_sources': ['四川卫视', '云南卫视'],
                'health_concerns': ['高原反应预防', '辛辣饮食调节'],
                'local_activities': ['坝坝舞', '打牌', '泡温泉'],
                'festivals': ['火把节', '泼水节'],
                'cuisine_tips': ['适量辣椒', '清肠养胃']
            },
            'northeast': {
                'name': '东北',
                'provinces': ['辽宁', '吉林', '黑龙江'],
                'popular_music': ['二人转', '东北秧歌', '大鼓'],
                'local_news_sources': ['辽宁卫视', '黑龙江卫视'],
                'health_concerns': ['严寒保暖', '冬季运动安全', '供暖期空气质量'],
                'local_activities': ['扭秧歌', '冬泳', '滑冰'],
                'festivals': ['冰雪节', '春节'],
                'cuisine_tips': ['冬季囤菜', "热量补充"]
            }
        }

    def get_regional_content(self, region: str) -> Optional[Dict]:
        """获取区域内容"""
        return self.regional_content.get(region)

    def get_recommended_content(
        self,
        region: str,
        content_type: str
    ) -> List[str]:
        """获取区域推荐内容"""
        regional = self.regional_content.get(region)
        if not regional:
            return []

        type_mapping = {
            'music': "popular_music",
            'news': "local_news_sources",
            'health': "health_concerns",
            'activities': "local_activities",
            'festivals': 'festivals',
            'cuisine': "cuisine_tips"
        }

        key = type_mapping.get(content_type)
        return regional.get(key, []) if key else []

    def detect_region_by_province(self, province: str) -> Optional[str]:
        """根据省份检测区域"""
        for region_code, regional in self.regional_content.items():
            if province in regional.get('provinces', []):
                return region_code
        return None


# ==================== 统一本地化服务 ====================

class LocalizationService:
    """统一本地化服务"""

    def __init__(self):
        self.translation = TranslationService()
        self.dialect_voice = DialectVoiceService()
        self.timezone = TimezoneService()
        self.regional_content = RegionalContentService()
        self.user_locales: Dict[int, LocaleConfig] = {}

    def get_user_locale(self, user_id: int) -> LocaleConfig:
        """获取用户区域配置"""
        if user_id not in self.user_locales:
            # 返回默认配置
            self.user_locales[user_id] = LocaleConfig(
                language=Language.ZH_CN,
                dialect=Dialect.MANDARIN,
                region=Region.EAST_CHINA,
                timezone="Asia/Shanghai",
                date_format="YYYY年MM月DD日",
                time_format="HH:mm",
                currency='CNY',
                temperature_unit='celsius'
            )
        return self.user_locales[user_id]

    def set_user_locale(
        self,
        user_id: int,
        language: Optional[str] = None,
        dialect: Optional[str] = None,
        region: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> LocaleConfig:
        """设置用户区域配置"""
        locale = self.get_user_locale(user_id)

        if language:
            locale.language = Language(language)
        if dialect:
            locale.dialect = Dialect(dialect)
        if region:
            locale.region = Region(region)
        if timezone:
            locale.timezone = timezone

        return locale

    def localize_text(
        self,
        user_id: int,
        key: str,
        params: Optional[Dict] = None
    ) -> str:
        """本地化文本"""
        locale = self.get_user_locale(user_id)
        return self.translation.translate(key, locale.language.value, params)

    def get_localized_greeting(self, user_id: int) -> str:
        """获取本地化问候语"""
        locale = self.get_user_locale(user_id)
        base_greeting = self.timezone.get_greeting_by_time(locale.language.value)

        # 如果有方言，添加方言特色
        if locale.dialect != Dialect.MANDARIN:
            base_greeting = self.dialect_voice.convert_text_to_dialect(
                base_greeting,
                locale.dialect.value
            )

        return base_greeting


# 全局服务实例
localization_service = LocalizationService()
