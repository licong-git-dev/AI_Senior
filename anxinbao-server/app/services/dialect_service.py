"""
方言与地区语言支持模块
支持多种中国方言识别与合成
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class DialectType(Enum):
    """方言类型"""
    # 官话区
    MANDARIN = 'mandarin'  # 普通话
    BEIJING = 'beijing'  # 北京话
    NORTHEAST = 'northeast'  # 东北话
    SICHUAN = 'sichuan'  # 四川话
    HENAN = 'henan'  # 河南话
    SHAANXI = 'shaanxi'  # 陕西话
    SHANDONG = 'shandong'  # 山东话

    # 吴语区
    SHANGHAI = 'shanghai'  # 上海话
    SUZHOU = 'suzhou'  # 苏州话
    NINGBO = 'ningbo'  # 宁波话
    WENZHOU = 'wenzhou'  # 温州话

    # 粤语区
    CANTONESE = 'cantonese'  # 广东话（粤语）
    HAKKA = 'hakka'  # 客家话

    # 闽语区
    MINNAN = 'minnan'  # 闽南话
    FUZHOU = 'fuzhou'  # 福州话
    CHAOZHOU = 'chaozhou'  # 潮州话
    TAIWANESE = 'taiwanese'  # 台湾闽南语

    # 其他
    HUNAN = 'hunan'  # 湖南话
    JIANGXI = 'jiangxi'  # 江西话
    ANHUI = "anhui"  # 安徽话


class LanguageMode(Enum):
    """语言模式"""
    STANDARD = 'standard'  # 标准普通话
    DIALECT_RECOGNITION = "dialect_recognition"  # 方言识别
    DIALECT_SYNTHESIS = "dialect_synthesis"  # 方言合成
    BILINGUAL = "bilingual"  # 双语模式


@dataclass
class DialectProfile:
    """方言配置"""
    dialect_type: DialectType
    display_name: str
    region: str
    description: str
    tts_voice_id: Optional[str] = None  # TTS语音ID
    asr_model_id: Optional[str] = None  # ASR模型ID
    is_supported_tts: bool = False  # 是否支持TTS
    is_supported_asr: bool = False  # 是否支持ASR
    sample_phrases: List[str] = None  # 示例短语

    def __post_init__(self):
        if self.sample_phrases is None:
            self.sample_phrases = []


# ==================== 方言配置库 ====================

DIALECT_PROFILES: Dict[DialectType, DialectProfile] = {
    DialectType.MANDARIN: DialectProfile(
        dialect_type=DialectType.MANDARIN,
        display_name='普通话',
        region='全国通用',
        description="标准普通话，全国通用",
        tts_voice_id="zh-CN-XiaoxiaoNeural",
        asr_model_id="paraformer-zh",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['您好', '今天天气怎么样', '我想和您聊聊天']
    ),

    DialectType.CANTONESE: DialectProfile(
        dialect_type=DialectType.CANTONESE,
        display_name='粤语（广东话）',
        region="广东、香港、澳门",
        description="粤语，主要在广东省、香港和澳门使用",
        tts_voice_id="zh-HK-HiuMaanNeural",
        asr_model_id="paraformer-cantonese",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['你好', '今日天氣點呀', '我想同你傾下偈']
    ),

    DialectType.SICHUAN: DialectProfile(
        dialect_type=DialectType.SICHUAN,
        display_name='四川话',
        region="四川、重庆",
        description="四川话，西南官话的代表",
        tts_voice_id="zh-CN-sichuan",
        asr_model_id="paraformer-sichuan",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['你好哇', '今天天气咋个样', '摆哈龙门阵嘛']
    ),

    DialectType.SHANGHAI: DialectProfile(
        dialect_type=DialectType.SHANGHAI,
        display_name='上海话',
        region="上海",
        description="上海话，吴语的代表方言",
        tts_voice_id="zh-CN-shanghai",
        asr_model_id="paraformer-wuyu",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['侬好', '今朝天气哪能', '阿拉来白相相']
    ),

    DialectType.MINNAN: DialectProfile(
        dialect_type=DialectType.MINNAN,
        display_name='闽南话',
        region="福建南部、台湾",
        description="闽南话，在福建南部、台湾广泛使用",
        tts_voice_id="zh-TW-HsiaoChenNeural",
        asr_model_id="paraformer-minnan",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['汝好', '今仔日天氣按怎', '來開講']
    ),

    DialectType.NORTHEAST: DialectProfile(
        dialect_type=DialectType.NORTHEAST,
        display_name='东北话',
        region="黑龙江、吉林、辽宁",
        description="东北话，东北官话的代表",
        tts_voice_id="zh-CN-northeast",
        asr_model_id="paraformer-zh",
        is_supported_tts=False,
        is_supported_asr=True,
        sample_phrases=['咋地了', '今儿个天儿咋样', '唠嗑唠嗑']
    ),

    DialectType.HENAN: DialectProfile(
        dialect_type=DialectType.HENAN,
        display_name='河南话',
        region="河南",
        description="河南话，中原官话的代表",
        tts_voice_id=None,
        asr_model_id="paraformer-zh",
        is_supported_tts=False,
        is_supported_asr=True,
        sample_phrases=['中不中', '今儿天咋样', '说说话']
    ),

    DialectType.HAKKA: DialectProfile(
        dialect_type=DialectType.HAKKA,
        display_name="客家话",
        region="广东梅州、江西、福建等",
        description="客家话，客家人使用的方言",
        tts_voice_id=None,
        asr_model_id="paraformer-hakka",
        is_supported_tts=False,
        is_supported_asr=True,
        sample_phrases=['你好', '今日天時仰般', '來講話']
    ),

    DialectType.BEIJING: DialectProfile(
        dialect_type=DialectType.BEIJING,
        display_name='北京话',
        region="北京",
        description="北京话，带有北京特色的普通话",
        tts_voice_id="zh-CN-YunxiNeural",
        asr_model_id="paraformer-zh",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['您吃了吗', '今儿天儿不错', '咱聊聊']
    ),

    DialectType.TAIWANESE: DialectProfile(
        dialect_type=DialectType.TAIWANESE,
        display_name='台湾国语',
        region="台湾",
        description="台湾地区的普通话，带有台湾特色",
        tts_voice_id="zh-TW-HsiaoChenNeural",
        asr_model_id="paraformer-tw",
        is_supported_tts=True,
        is_supported_asr=True,
        sample_phrases=['你好啊', '今天天气怎么样', '聊聊天吧']
    )
}


# ==================== 常用方言词汇映射 ====================

DIALECT_VOCABULARY: Dict[DialectType, Dict[str, str]] = {
    DialectType.CANTONESE: {
        # 粤语 -> 普通话
        '唔该': '谢谢/请问',
        '点解': '为什么',
        '几多': '多少',
        '边度': '哪里',
        '咩嘢': '什么',
        '靓仔': '帅哥',
        '靓女': '美女',
        '食饭': '吃饭',
        '饮茶': '喝茶',
        '冇问题': '没问题',
        '好攰': '很累',
        '唔舒服': '不舒服'
    },

    DialectType.SICHUAN: {
        # 四川话 -> 普通话
        '巴适': '舒服/很好',
        '要得': '可以/好的',
        '啷个': '怎么',
        '啥子': '什么',
        '龙门阵': '聊天',
        '耍朋友': '谈恋爱',
        '瓜娃子': '傻瓜',
        '撇脱': '轻松',
        '安逸': '舒服'
    },

    DialectType.SHANGHAI: {
        # 上海话 -> 普通话
        '侬好': '你好',
        '阿拉': '我们',
        '伊': '他/她',
        '勿晓得': '不知道',
        '老灵额': '很好',
        '老嗲': '很棒',
        '白相': '玩',
        '轧朋友': '交朋友',
        '搭界': '有关系'
    },

    DialectType.NORTHEAST: {
        # 东北话 -> 普通话
        '咋整': '怎么办',
        '嘎哈呢': '干什么呢',
        '贼': '非常/很',
        '得瑟': '炫耀/显摆',
        '唠嗑': '聊天',
        '嗯哪': '是的',
        '埋汰': '脏/侮辱',
        '磨叽': '磨蹭',
        '秃噜': "说话"
    }
}


# ==================== 方言服务 ====================

class DialectService:
    """方言服务"""

    def __init__(self):
        self.profiles = DIALECT_PROFILES
        self.vocabulary = DIALECT_VOCABULARY
        self.user_preferences: Dict[int, DialectType] = {}

    def get_all_dialects(self) -> List[Dict[str, Any]]:
        """获取所有支持的方言列表"""
        dialects = []
        for dt, profile in self.profiles.items():
            dialects.append({
                'type': dt.value,
                'name': profile.display_name,
                'region': profile.region,
                "description": profile.description,
                "is_supported_tts": profile.is_supported_tts,
                "is_supported_asr": profile.is_supported_asr,
                "sample_phrases": profile.sample_phrases
            })
        return dialects

    def get_dialect_profile(self, dialect_type: DialectType) -> Optional[DialectProfile]:
        """获取方言配置"""
        return self.profiles.get(dialect_type)

    def set_user_dialect(self, user_id: int, dialect_type: DialectType):
        """设置用户方言偏好"""
        self.user_preferences[user_id] = dialect_type
        logger.info(f"用户 {user_id} 方言设为: {dialect_type.value}")

    def get_user_dialect(self, user_id: int) -> DialectType:
        """获取用户方言偏好"""
        return self.user_preferences.get(user_id, DialectType.MANDARIN)

    def get_tts_config(self, dialect_type: DialectType) -> Dict[str, Any]:
        """获取TTS配置"""
        profile = self.profiles.get(dialect_type)
        if not profile or not profile.is_supported_tts:
            # 回退到普通话
            profile = self.profiles[DialectType.MANDARIN]

        return {
            'voice_id': profile.tts_voice_id,
            "dialect": profile.dialect_type.value,
            "display_name": profile.display_name
        }

    def get_asr_config(self, dialect_type: DialectType) -> Dict[str, Any]:
        """获取ASR配置"""
        profile = self.profiles.get(dialect_type)
        if not profile or not profile.is_supported_asr:
            # 回退到普通话
            profile = self.profiles[DialectType.MANDARIN]

        return {
            'model_id': profile.asr_model_id,
            "dialect": profile.dialect_type.value,
            "display_name": profile.display_name
        }

    def translate_dialect_words(
        self,
        text: str,
        from_dialect: DialectType
    ) -> str:
        """
        将方言词汇转换为普通话

        Args:
            text: 输入文本
            from_dialect: 源方言

        Returns:
            转换后的文本
        """
        vocab = self.vocabulary.get(from_dialect, {})
        result = text

        for dialect_word, standard_word in vocab.items():
            if dialect_word in result:
                result = result.replace(dialect_word, f"【{standard_word}】")
                logger.debug(f"方言转换: {dialect_word} -> {standard_word}")

        return result

    def detect_dialect(self, text: str) -> Optional[DialectType]:
        """
        简单的方言检测（基于词汇特征）

        实际应用中应使用专门的方言识别模型
        """
        for dialect_type, vocab in self.vocabulary.items():
            match_count = sum(1 for word in vocab.keys() if word in text)
            if match_count >= 2:
                logger.info(f"检测到方言: {dialect_type.value}")
                return dialect_type

        return None

    def get_dialect_greeting(self, dialect_type: DialectType) -> str:
        """获取方言问候语"""
        greetings = {
            DialectType.MANDARIN: "您好！有什么可以帮您的吗？",
            DialectType.CANTONESE: "你好呀！有咩可以帮到你？",
            DialectType.SICHUAN: "你好嘛！有啥子事找我？",
            DialectType.SHANGHAI: '侬好！有啥好帮忙的？',
            DialectType.NORTHEAST: '你好啊！有啥事儿吗？',
            DialectType.BEIJING: '您好！有什么事儿吗？',
            DialectType.MINNAN: "汝好！有啥代志？",
            DialectType.TAIWANESE: "你好！有什么需要帮忙的吗？"
        }
        return greetings.get(dialect_type, greetings[DialectType.MANDARIN])


# ==================== 地区文化适配 ====================

class RegionalCultureAdapter:
    """地区文化适配器"""

    # 地区特色内容
    REGIONAL_CONTENT: Dict[str, Dict[str, Any]] = {
        '广东': {
            'diet_preferences': ['粤菜', '煲汤', '早茶', "糖水"],
            "health_tips": [
                "广东天气炎热潮湿，注意防暑祛湿",
                "煲汤养生是广东人的传统",
                "饮早茶时注意控制糖分摄入"
            ],
            'festivals': ['迎春花市', '龙舟节', '中秋赏月'],
            'common_topics': ['饮茶', '煲汤', '养生']
        },
        '四川': {
            'diet_preferences': ['川菜', '火锅', "麻辣"],
            "health_tips": [
                "麻辣食物虽好，但要适量",
                "四川盆地潮湿，注意防潮",
                '多吃清淡食物平衡辛辣'
            ],
            'festivals': ['春节庙会', '灯会'],
            'common_topics': ['火锅', '麻将', '川剧']
        },
        '上海': {
            'diet_preferences': ['本帮菜', '小笼包', "糕点"],
            "health_tips": [
                "上海梅雨季节注意防潮防霉",
                '甜食适量，注意血糖',
                '多活动筋骨，不要久坐'
            ],
            'festivals': ['城隍庙灯会', '豫园新春'],
            'common_topics': ['股票', '养生', '广场舞']
        },
        '东北': {
            'diet_preferences': ['东北菜', '炖菜', "饺子"],
            "health_tips": [
                "东北冬天寒冷，注意保暖",
                '多吃热乎的食物驱寒',
                '注意心脑血管保护'
            ],
            'festivals': ['冰雪节', '秧歌会'],
            'common_topics': ['养生', '二人转', '跳舞']
        },
        '北京': {
            'diet_preferences': ['京菜', '涮羊肉', "烤鸭"],
            "health_tips": [
                "北京春天多风沙，注意防护",
                '冬天干燥，多喝水润燥',
                '雾霾天气减少外出'
            ],
            'festivals': ['庙会', '元宵灯会'],
            'common_topics': ['京剧', '遛鸟', "下棋"]
        }
    }

    @classmethod
    def get_regional_content(cls, region: str) -> Dict[str, Any]:
        """获取地区特色内容"""
        # 模糊匹配
        for key, content in cls.REGIONAL_CONTENT.items():
            if key in region or region in key:
                return content

        # 默认返回通用内容
        return {
            'diet_preferences': ['家常菜', '清淡饮食'],
            'health_tips': ['注意饮食均衡', '适当运动', '保持心情愉快'],
            'festivals': ['春节', '中秋节', '重阳节'],
            'common_topics': ['健康', '家常', "天气"]
        }

    @classmethod
    def adapt_response(
        cls,
        response: str,
        dialect_type: DialectType,
        region: str
    ) -> str:
        """适配回复内容"""
        regional_content = cls.get_regional_content(region)

        # 根据地区特色调整回复
        # 实际应用中可以使用更复杂的适配逻辑

        return response


# 全局方言服务实例
dialect_service = DialectService()
regional_adapter = RegionalCultureAdapter()
