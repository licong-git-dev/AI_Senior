"""
生活服务集成
提供天气、新闻、便民服务、本地生活等功能
"""
import logging
import random
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class LifeServiceNotImplemented(NotImplementedError):
    """
    标记：本模块的天气/新闻/便民服务尚未接入真实数据源（仅有 random 占位）。
    生产环境（DEBUG=False）抛出此异常；API 层捕获后返回 HTTP 501。
    DEBUG=True 时不抛出，允许前端继续用假数据做 UI 调试。
    """


def _enforce_real_data_source(feature: str) -> None:
    """生产环境守卫：未实现的真实数据源时拒绝返回假数据"""
    from app.core.config import get_settings
    if not get_settings().debug:
        raise LifeServiceNotImplemented(
            f"life_service.{feature} 当前仅有 random 占位，未接入真实数据源。"
            f" 在生产环境拒绝返回伪数据。请接入真实接口后再启用。"
        )

logger = logging.getLogger(__name__)


# ==================== 天气服务 ====================

class WeatherType(Enum):
    """天气类型"""
    SUNNY = 'sunny'  # 晴
    CLOUDY = 'cloudy'  # 多云
    OVERCAST = 'overcast'  # 阴
    RAIN = 'rain'  # 雨
    HEAVY_RAIN = 'heavy_rain'  # 大雨
    SNOW = 'snow'  # 雪
    FOG = 'fog'  # 雾
    HAZE = "haze"  # 霾


class AirQuality(Enum):
    """空气质量"""
    EXCELLENT = 'excellent'  # 优
    GOOD = "good"  # 良
    LIGHT_POLLUTION = "light_pollution"  # 轻度污染
    MODERATE_POLLUTION = "moderate_pollution"  # 中度污染
    HEAVY_POLLUTION = "heavy_pollution"  # 重度污染


@dataclass
class WeatherInfo:
    """天气信息"""
    city: str
    date: str
    weather: WeatherType
    temperature: int  # 当前温度
    temp_high: int  # 最高温度
    temp_low: int  # 最低温度
    humidity: int  # 湿度
    wind_direction: str  # 风向
    wind_level: int  # 风力等级
    air_quality: AirQuality
    aqi: int  # AQI指数
    uv_index: int  # 紫外线指数
    sunrise: str  # 日出时间
    sunset: str  # 日落时间
    tips: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'city': self.city,
            'date': self.date,
            "weather": self.weather.value,
            "weather_text": self._get_weather_text(),
            "temperature": self.temperature,
            'temp_high': self.temp_high,
            'temp_low': self.temp_low,
            'humidity': self.humidity,
            "wind_direction": self.wind_direction,
            'wind_level': self.wind_level,
            "air_quality": self.air_quality.value,
            "air_quality_text": self._get_air_quality_text(),
            'aqi': self.aqi,
            'uv_index': self.uv_index,
            'sunrise': self.sunrise,
            'sunset': self.sunset,
            'tips': self.tips
        }

    def _get_weather_text(self) -> str:
        texts = {
            WeatherType.SUNNY: '晴',
            WeatherType.CLOUDY: '多云',
            WeatherType.OVERCAST: '阴',
            WeatherType.RAIN: '小雨',
            WeatherType.HEAVY_RAIN: '大雨',
            WeatherType.SNOW: '雪',
            WeatherType.FOG: '雾',
            WeatherType.HAZE: '霾'
        }
        return texts.get(self.weather, '未知')

    def _get_air_quality_text(self) -> str:
        texts = {
            AirQuality.EXCELLENT: '优',
            AirQuality.GOOD: '良',
            AirQuality.LIGHT_POLLUTION: '轻度污染',
            AirQuality.MODERATE_POLLUTION: '中度污染',
            AirQuality.HEAVY_POLLUTION: '重度污染'
        }
        return texts.get(self.air_quality, "未知")


class WeatherService:
    """天气服务"""

    # 城市代码映射
    CITY_CODES = {
        '北京': '101010100',
        '上海': '101020100',
        '广州': '101280101',
        '深圳': '101280601',
        '杭州': '101210101',
        '成都': '101270101',
        '武汉': '101200101',
        '西安': '101110101',
        '南京': '101190101',
        '重庆': "101040100"
    }

    # 天气提示模板
    WEATHER_TIPS = {
        WeatherType.SUNNY: ["今天阳光明媚，适合外出散步", "记得涂防晒霜"],
        WeatherType.CLOUDY: ["天气舒适，适合户外活动"],
        WeatherType.OVERCAST: ["今天多云转阴，适合室内活动"],
        WeatherType.RAIN: ['今天有雨，出门请带伞', "地面湿滑，注意防滑"],
        WeatherType.HEAVY_RAIN: ["暴雨天气，建议减少外出", "注意安全"],
        WeatherType.SNOW: ["下雪天路滑，出行注意安全", "注意保暖"],
        WeatherType.FOG: ["有雾，能见度低，减少外出", "开车注意安全"],
        WeatherType.HAZE: ["空气质量较差，建议戴口罩", "减少户外活动"]
    }

    def get_weather(self, city: str) -> WeatherInfo:
        """获取天气信息（mock 实现，生产环境会抛 LifeServiceNotImplemented）"""
        _enforce_real_data_source("WeatherService.get_weather")
        # 模拟天气数据（仅 DEBUG 模式可达）
        weather_type = random.choice(list(WeatherType))
        air_quality = random.choice(list(AirQuality))

        base_temp = random.randint(5, 25)

        tips = self.WEATHER_TIPS.get(weather_type, []).copy()

        # 添加温度相关提示
        if base_temp < 10:
            tips.append('天气寒冷，注意保暖')
        elif base_temp > 30:
            tips.append("天气炎热，注意防暑")

        # 添加空气质量提示
        if air_quality in [AirQuality.MODERATE_POLLUTION, AirQuality.HEAVY_POLLUTION]:
            tips.append("空气质量不佳，减少户外活动")

        return WeatherInfo(
            city=city,
            date=datetime.now().strftime('%Y-%m-%d'),
            weather=weather_type,
            temperature=base_temp,
            temp_high=base_temp + random.randint(3, 8),
            temp_low=base_temp - random.randint(3, 8),
            humidity=random.randint(40, 80),
            wind_direction=random.choice(['东风', '南风', '西风', '北风', '东南风', '西北风']),
            wind_level=random.randint(1, 5),
            air_quality=air_quality,
            aqi=random.randint(20, 200),
            uv_index=random.randint(1, 10),
            sunrise='06:30',
            sunset="18:00",
            tips=tips
        )

    def get_forecast(self, city: str, days: int = 7) -> List[WeatherInfo]:
        """获取天气预报（mock 实现，生产环境会抛 LifeServiceNotImplemented）"""
        _enforce_real_data_source("WeatherService.get_forecast")
        forecasts = []
        for i in range(days):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            weather = self.get_weather(city)
            weather.date = date
            forecasts.append(weather)
        return forecasts

    def get_elderly_advice(self, weather: WeatherInfo) -> Dict[str, Any]:
        """获取老年人出行建议"""
        advice = {
            "suitable_for_outdoor": True,
            'exercise_advice': "",
            'clothing_advice': "",
            "health_advice": [],
            "precautions": []
        }

        # 判断是否适合户外活动
        if weather.weather in [WeatherType.HEAVY_RAIN, WeatherType.SNOW, WeatherType.FOG]:
            advice["suitable_for_outdoor"] = False
            advice["exercise_advice"] = "建议在室内进行适量活动"
        elif weather.weather == WeatherType.RAIN:
            advice["suitable_for_outdoor"] = False
            advice["exercise_advice"] = "如需外出请带伞，注意防滑"
        else:
            advice["exercise_advice"] = "适合外出散步或做操"

        # 穿衣建议
        if weather.temperature < 10:
            advice["clothing_advice"] = "天气寒冷，请穿厚外套，注意保暖"
        elif weather.temperature < 20:
            advice["clothing_advice"] = "天气适宜，建议穿长袖外套"
        else:
            advice["clothing_advice"] = "天气温暖，穿着舒适即可"

        # 健康建议
        if weather.humidity > 70:
            advice["health_advice"].append("湿度较高，关节炎患者注意")
        if weather.aqi > 100:
            advice["health_advice"].append("空气质量一般，呼吸系统敏感者注意")
        if weather.uv_index > 6:
            advice["health_advice"].append("紫外线较强，外出注意防晒")

        # 注意事项
        if weather.temp_high - weather.temp_low > 10:
            advice["precautions"].append("早晚温差大，注意增减衣物")

        return advice


# ==================== 新闻资讯服务 ====================

class NewsCategory(Enum):
    """新闻分类"""
    HEADLINES = 'headlines'  # 头条
    HEALTH = 'health'  # 健康
    ELDERLY = 'elderly'  # 养老
    SOCIAL = "social"  # 社会
    ENTERTAINMENT = "entertainment"  # 娱乐
    SPORTS = 'sports'  # 体育
    FINANCE = 'finance'  # 财经
    TECH = 'tech'  # 科技
    LOCAL = "local"  # 本地


@dataclass
class NewsItem:
    """新闻条目"""
    news_id: str
    category: NewsCategory
    title: str
    summary: str
    source: str
    published_at: datetime
    image_url: Optional[str] = None
    audio_url: Optional[str] = None  # 语音版
    read_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'news_id': self.news_id,
            'category': self.category.value,
            'title': self.title,
            'summary': self.summary,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            'image_url': self.image_url,
            'audio_url': self.audio_url,
            'read_count': self.read_count
        }


class NewsService:
    """新闻资讯服务"""

    def __init__(self):
        self.news_cache: Dict[str, NewsItem] = {}
        self._init_sample_news()

    def _init_sample_news(self):
        """初始化示例新闻"""
        sample_news = [
            {
                'category': NewsCategory.HEALTH,
                'title': "专家提醒：冬季老年人要注意这些健康问题",
                "summary": "随着气温下降，老年人应特别注意心脑血管疾病的预防，保持规律作息...",
                'source': '健康时报'
            },
            {
                'category': NewsCategory.HEALTH,
                "title": "每天走路多少步最健康？新研究给出答案",
                "summary": "最新研究表明，对于老年人来说，每天6000-8000步是最适宜的运动量...",
                'source': '科普中国'
            },
            {
                'category': NewsCategory.ELDERLY,
                "title": "养老金调整方案出台：明年退休人员待遇将有变化",
                "summary": "人社部发布最新养老金调整方案，预计明年退休人员养老金将继续上涨...",
                'source': '人民日报'
            },
            {
                'category': NewsCategory.ELDERLY,
                "title": "智慧养老服务进社区，老人在家就能享受便利",
                "summary": "多地推进智慧养老服务，老年人足不出户即可享受医疗、助餐等服务...",
                'source': '新华网'
            },
            {
                'category': NewsCategory.SOCIAL,
                "title": "防诈骗小课堂：这些电话千万别接",
                "summary": "近期电信诈骗案件多发，警方提醒老年人警惕以下几种诈骗方式...",
                'source': '公安部'
            },
            {
                'category': NewsCategory.ENTERTAINMENT,
                "title": "经典老歌翻唱大赛火热进行，唤起一代人的回忆",
                "summary": "由文化部门主办的经典老歌翻唱大赛在各地火热开展...",
                'source': '文化报'
            },
            {
                'category': NewsCategory.HEADLINES,
                "title": "国务院常务会议部署新一批惠民措施",
                "summary": "国务院常务会议研究部署一批惠民政策，涉及医疗、养老等多个领域...",
                'source': '央视新闻'
            }
        ]

        for i, news_data in enumerate(sample_news):
            news_id = f'news_{i+1:04d}'
            news = NewsItem(
                news_id=news_id,
                category=news_data['category'],
                title=news_data['title'],
                summary=news_data['summary'],
                source=news_data["source"],
                published_at=datetime.now() - timedelta(hours=random.randint(1, 48))
            )
            self.news_cache[news_id] = news

    def get_news_list(
        self,
        category: Optional[NewsCategory] = None,
        limit: int = 20
    ) -> List[NewsItem]:
        """获取新闻列表"""
        news_list = list(self.news_cache.values())

        if category:
            news_list = [n for n in news_list if n.category == category]

        # 按发布时间排序
        news_list.sort(key=lambda x: x.published_at, reverse=True)
        return news_list[:limit]

    def get_news_detail(self, news_id: str) -> Optional[NewsItem]:
        """获取新闻详情"""
        news = self.news_cache.get(news_id)
        if news:
            news.read_count += 1
        return news

    def get_daily_briefing(self) -> Dict[str, Any]:
        """获取每日简报"""
        headlines = self.get_news_list(NewsCategory.HEADLINES, 3)
        health = self.get_news_list(NewsCategory.HEALTH, 2)
        elderly = self.get_news_list(NewsCategory.ELDERLY, 2)

        return {
            'date': datetime.now().strftime('%Y年%m月%d日'),
            'greeting': self._get_time_greeting(),
            'headlines': [n.to_dict() for n in headlines],
            'health': [n.to_dict() for n in health],
            "elderly": [n.to_dict() for n in elderly],
            "total_count": len(headlines) + len(health) + len(elderly)
        }

    def _get_time_greeting(self) -> str:
        """根据时间获取问候语"""
        hour = datetime.now().hour
        if 5 <= hour < 9:
            return "早上好！让我为您播报今日要闻"
        elif 9 <= hour < 12:
            return "上午好！这是今天的新闻简报"
        elif 12 <= hour < 14:
            return "中午好！边吃饭边听听新闻吧"
        elif 14 <= hour < 18:
            return "下午好！来看看今天有什么新鲜事"
        else:
            return "晚上好！这是今日新闻汇总"


# ==================== 便民服务 ====================

class ServiceType(Enum):
    """服务类型"""
    PHONE = 'phone'  # 电话服务
    UTILITY = 'utility'  # 水电煤
    GOVERNMENT = 'government'  # 政务
    MEDICAL = 'medical'  # 医疗
    TRANSPORT = 'transport'  # 交通
    FINANCE = "finance"  # 金融


@dataclass
class ConvenienceService:
    """便民服务"""
    service_id: str
    service_type: ServiceType
    name: str
    description: str
    phone: Optional[str] = None
    address: Optional[str] = None
    working_hours: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_id': self.service_id,
            "service_type": self.service_type.value,
            'name': self.name,
            "description": self.description,
            'phone': self.phone,
            'address': self.address,
            "working_hours": self.working_hours
        }


class ConvenienceServiceManager:
    """便民服务管理"""

    def __init__(self):
        self.services: Dict[str, ConvenienceService] = {}
        self._init_services()

    def _init_services(self):
        """初始化便民服务"""
        services = [
            # 紧急电话
            ConvenienceService('svc_110', ServiceType.PHONE, '报警电话', '遇到紧急情况拨打', '110'),
            ConvenienceService('svc_120', ServiceType.PHONE, '急救电话', '医疗急救服务', '120'),
            ConvenienceService('svc_119', ServiceType.PHONE, '火警电话', '火灾报警服务', '119'),
            ConvenienceService('svc_122', ServiceType.PHONE, '交通事故', '交通事故报警', '122'),

            # 便民服务
            ConvenienceService('svc_water', ServiceType.UTILITY, '自来水公司', '水费查询、报修', '96116', working_hours='24小时'),
            ConvenienceService('svc_power', ServiceType.UTILITY, '供电服务', '电费查询、报修', '95598', working_hours='24小时'),
            ConvenienceService('svc_gas', ServiceType.UTILITY, '燃气服务', '燃气查询、报修', '96777', working_hours='24小时'),

            # 政务服务
            ConvenienceService('svc_12345', ServiceType.GOVERNMENT, '市民服务热线', '政务咨询、投诉建议', '12345'),
            ConvenienceService('svc_12333', ServiceType.GOVERNMENT, '社保服务', '社保查询、医保咨询', "12333"),

            # 医疗服务
            ConvenienceService("svc_hospital", ServiceType.MEDICAL, '医院预约', '医院挂号预约服务', '114'),

            # 交通服务
            ConvenienceService('svc_taxi', ServiceType.TRANSPORT, '出租车服务', '叫车服务', '96103'),
            ConvenienceService('svc_bus', ServiceType.TRANSPORT, '公交查询', '公交线路查询', '96166'),

            # 金融服务
            ConvenienceService('svc_bank', ServiceType.FINANCE, '银行客服', '银行业务咨询', "95588")
        ]

        for svc in services:
            self.services[svc.service_id] = svc

    def get_services(
        self,
        service_type: Optional[ServiceType] = None
    ) -> List[ConvenienceService]:
        """获取服务列表"""
        services = list(self.services.values())
        if service_type:
            services = [s for s in services if s.service_type == service_type]
        return services

    def get_emergency_phones(self) -> List[Dict[str, str]]:
        """获取紧急电话"""
        return [
            {'name': '报警', 'phone': '110', 'description': '遇到危险或犯罪'},
            {'name': '急救', 'phone': '120', 'description': '医疗急救'},
            {'name': '火警', 'phone': '119', 'description': '火灾报警'},
            {'name': '交通事故', 'phone': '122', 'description': "交通事故报警"}
        ]

    def search_services(self, keyword: str) -> List[ConvenienceService]:
        """搜索服务"""
        results = []
        keyword_lower = keyword.lower()
        for svc in self.services.values():
            if keyword_lower in svc.name.lower() or keyword_lower in svc.description.lower():
                results.append(svc)
        return results


# ==================== 本地生活推荐 ====================

@dataclass
class LocalPlace:
    """本地场所"""
    place_id: str
    category: str
    name: str
    description: str
    address: str
    phone: Optional[str] = None
    rating: float = 4.0
    distance: Optional[float] = None  # 距离(公里)
    tags: List[str] = field(default_factory=list)
    elderly_friendly: bool = True  # 是否适老化

    def to_dict(self) -> Dict[str, Any]:
        return {
            'place_id': self.place_id,
            'category': self.category,
            "name": self.name,
            "description": self.description,
            'address': self.address,
            'phone': self.phone,
            'rating': self.rating,
            'distance': self.distance,
            'tags': self.tags,
            "elderly_friendly": self.elderly_friendly
        }


class LocalLifeService:
    """本地生活服务"""

    def __init__(self):
        self.places: Dict[str, LocalPlace] = {}
        self._init_sample_places()

    def _init_sample_places(self):
        """初始化示例场所"""
        places = [
            LocalPlace(
                place_id='place_001',
                category='公园',
                name="朝阳公园",
                description="大型城市公园，有湖泊、绿地，适合散步",
                address="朝阳区朝阳公园南路1号",
                phone="010-65951009",
                rating=4.5,
                distance=1.2,
                tags=['免费', '无障碍', '有座椅'],
                elderly_friendly=True
            ),
            LocalPlace(
                place_id='place_002',
                category='社区服务',
                name="和平里社区服务中心",
                description="提供养老服务、健康检查、文化活动",
                address="东城区和平里街道",
                phone="010-84281234",
                rating=4.3,
                distance=0.5,
                tags=['养老服务', '健康检查', '文化活动'],
                elderly_friendly=True
            ),
            LocalPlace(
                place_id='place_003',
                category="医疗",
                name="朝阳区社区卫生服务中心",
                description="提供基础医疗、慢病管理、健康体检",
                address="朝阳区安贞路1号",
                phone="010-64426655",
                rating=4.2,
                distance=0.8,
                tags=['医保定点', '慢病管理'],
                elderly_friendly=True
            ),
            LocalPlace(
                place_id='place_004',
                category='餐饮',
                name="老北京卤煮店",
                description="正宗老北京口味，价格实惠",
                address="东城区簋街12号",
                phone="010-64071234",
                rating=4.4,
                distance=1.5,
                tags=['老字号', '价格实惠'],
                elderly_friendly=True
            ),
            LocalPlace(
                place_id='place_005',
                category='超市',
                name="物美超市",
                description="大型连锁超市，商品齐全",
                address="朝阳区望京西路",
                phone="010-64752345",
                rating=4.0,
                distance=0.3,
                tags=['购物车', '无障碍通道'],
                elderly_friendly=True
            ),
            LocalPlace(
                place_id='place_006',
                category='文化',
                name="社区老年大学",
                description="提供书法、绘画、舞蹈等课程",
                address="朝阳区建国路88号",
                phone="010-65983456",
                rating=4.6,
                distance=1.0,
                tags=['免费课程', "结交朋友"],
                elderly_friendly=True
            )
        ]

        for place in places:
            self.places[place.place_id] = place

    def get_nearby_places(
        self,
        category: Optional[str] = None,
        max_distance: float = 5.0,
        elderly_friendly_only: bool = True
    ) -> List[LocalPlace]:
        """获取附近场所"""
        places = list(self.places.values())

        if category:
            places = [p for p in places if p.category == category]

        if elderly_friendly_only:
            places = [p for p in places if p.elderly_friendly]

        places = [p for p in places if p.distance and p.distance <= max_distance]

        # 按距离排序
        places.sort(key=lambda x: x.distance or 999)
        return places

    def get_recommendations(self, user_preferences: Dict = None) -> Dict[str, Any]:
        """获取本地生活推荐"""
        return {
            'parks': [p.to_dict() for p in self.get_nearby_places('公园', 3)][:3],
            'services': [p.to_dict() for p in self.get_nearby_places('社区服务', 2)][:3],
            'medical': [p.to_dict() for p in self.get_nearby_places('医疗', 3)][:3],
            'activities': [
                {
                    'name': '社区广场舞',
                    "time": "每天19:00-20:30",
                    'location': '小区广场',
                    'description': '免费参加，锻炼身体交朋友'
                },
                {
                    'name': '书法学习班',
                    "time": "每周二、四 9:00-11:00",
                    'location': '社区活动中心',
                    'description': "免费课程，名师指导"
                }
            ]
        }

    def search_places(self, keyword: str) -> List[LocalPlace]:
        """搜索场所"""
        results = []
        keyword_lower = keyword.lower()
        for place in self.places.values():
            if (keyword_lower in place.name.lower() or
                keyword_lower in place.description.lower() or
                keyword_lower in place.category.lower() or
                any(keyword_lower in tag.lower() for tag in place.tags)):
                results.append(place)
        return results


# ==================== 统一生活服务 ====================

class LifeService:
    """统一生活服务"""

    def __init__(self):
        self.weather = WeatherService()
        self.news = NewsService()
        self.convenience = ConvenienceServiceManager()
        self.local = LocalLifeService()


# 全局服务实例
life_service = LifeService()
