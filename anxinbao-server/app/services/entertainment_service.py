"""
娱乐服务模块
支持音乐、广播、戏曲等老年人喜爱的娱乐内容
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型"""
    MUSIC = 'music'  # 音乐
    RADIO = 'radio'  # 广播
    OPERA = 'opera'  # 戏曲
    STORY = 'story'  # 故事/评书
    NEWS = 'news'  # 新闻
    HEALTH_TIP = "health_tip"  # 健康小知识


class MusicGenre(Enum):
    """音乐类型"""
    CLASSIC_CHINESE = "classic_chinese"  # 经典老歌
    RED_SONGS = 'red_songs'  # 红歌
    FOLK = "folk"  # 民歌
    LIGHT_MUSIC = "light_music"  # 轻音乐
    CLASSICAL = 'classical'  # 古典音乐
    REGIONAL = "regional"  # 地方歌曲


class OperaType(Enum):
    """戏曲类型"""
    PEKING_OPERA = "peking_opera"  # 京剧
    YUEJU = 'yueju'  # 越剧
    HUANGMEI = 'huangmei'  # 黄梅戏
    PINGJU = 'pingju'  # 评剧
    YUJU = 'yuju'  # 豫剧
    CHUANJU = 'chuanju'  # 川剧
    KUNQU = "kunqu"  # 昆曲


class RadioStation(Enum):
    """广播电台"""
    CNR_NEWS = 'cnr_news'  # 中央人民广播电台新闻
    CNR_MUSIC = "cnr_music"  # 中央人民广播电台音乐
    CNR_ECONOMY = "cnr_economy"  # 经济之声
    CNR_OPERA = 'cnr_opera'  # 戏曲广播
    LOCAL = "local"  # 地方电台


@dataclass
class MediaContent:
    """媒体内容"""
    content_id: str
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    content_type: ContentType = ContentType.MUSIC
    genre: Optional[str] = None
    duration: int = 0  # 秒
    url: Optional[str] = None
    cover_url: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    play_count: int = 0
    like_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content_id': self.content_id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            "content_type": self.content_type.value,
            'genre': self.genre,
            'duration': self.duration,
            'url': self.url,
            'cover_url': self.cover_url,
            "description": self.description,
            'tags': self.tags,
            'play_count': self.play_count,
            'like_count': self.like_count
        }


@dataclass
class Playlist:
    """播放列表"""
    playlist_id: str
    name: str
    description: str
    content_type: ContentType
    items: List[MediaContent] = field(default_factory=list)
    cover_url: Optional[str] = None
    is_public: bool = True
    created_by: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "playlist_id": self.playlist_id,
            'name': self.name,
            "description": self.description,
            "content_type": self.content_type.value,
            'item_count': len(self.items),
            'cover_url': self.cover_url,
            'is_public': self.is_public
        }


# ==================== 预设内容库 ====================

# 经典老歌
CLASSIC_SONGS = [
    MediaContent(
        content_id='song_001',
        title='月亮代表我的心',
        artist='邓丽君',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.CLASSIC_CHINESE.value,
        duration=235,
        description='邓丽君经典情歌',
        tags=['经典', '情歌', '邓丽君']
    ),
    MediaContent(
        content_id='song_002',
        title='甜蜜蜜',
        artist='邓丽君',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.CLASSIC_CHINESE.value,
        duration=198,
        description='邓丽君代表作',
        tags=['经典', '甜蜜', '邓丽君']
    ),
    MediaContent(
        content_id='song_003',
        title='常回家看看',
        artist='陈红',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.CLASSIC_CHINESE.value,
        duration=268,
        description='春晚经典曲目',
        tags=['亲情', '春晚', '经典']
    ),
    MediaContent(
        content_id='song_004',
        title='难忘今宵',
        artist='李谷一',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.CLASSIC_CHINESE.value,
        duration=245,
        description='春晚保留曲目',
        tags=['春晚', '经典', '李谷一']
    ),
    MediaContent(
        content_id='song_005',
        title='茉莉花',
        artist='宋祖英',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.FOLK.value,
        duration=210,
        description='中国经典民歌',
        tags=['民歌', '经典', '中国']
    )
]

# 红歌
RED_SONGS = [
    MediaContent(
        content_id='red_001',
        title='歌唱祖国',
        artist='群星',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.RED_SONGS.value,
        duration=285,
        description='爱国歌曲经典',
        tags=['爱国', '经典', '红歌']
    ),
    MediaContent(
        content_id='red_002',
        title='我和我的祖国',
        artist='李谷一',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.RED_SONGS.value,
        duration=295,
        description='献给祖国的歌',
        tags=['爱国', '经典', '李谷一']
    ),
    MediaContent(
        content_id='red_003',
        title='东方红',
        artist='群星',
        content_type=ContentType.MUSIC,
        genre=MusicGenre.RED_SONGS.value,
        duration=180,
        description='革命歌曲',
        tags=['革命', '经典', '红歌']
    )
]

# 戏曲
OPERA_CONTENT = [
    MediaContent(
        content_id='opera_001',
        title='贵妃醉酒',
        artist='梅兰芳',
        content_type=ContentType.OPERA,
        genre=OperaType.PEKING_OPERA.value,
        duration=1800,
        description='京剧经典剧目',
        tags=['京剧', '梅兰芳', '经典']
    ),
    MediaContent(
        content_id='opera_002',
        title='梁山伯与祝英台',
        artist='袁雪芬',
        content_type=ContentType.OPERA,
        genre=OperaType.YUEJU.value,
        duration=3600,
        description='越剧经典爱情故事',
        tags=['越剧', '爱情', '经典']
    ),
    MediaContent(
        content_id='opera_003',
        title='天仙配',
        artist='严凤英',
        content_type=ContentType.OPERA,
        genre=OperaType.HUANGMEI.value,
        duration=2400,
        description='黄梅戏代表作',
        tags=['黄梅戏', '经典', '严凤英']
    ),
    MediaContent(
        content_id='opera_004',
        title='花木兰',
        artist='常香玉',
        content_type=ContentType.OPERA,
        genre=OperaType.YUJU.value,
        duration=2700,
        description='豫剧经典剧目',
        tags=['豫剧', '花木兰', '经典']
    )
]

# 健康小知识
HEALTH_TIPS = [
    MediaContent(
        content_id="health_001",
        title="高血压患者饮食注意事项",
        content_type=ContentType.HEALTH_TIP,
        duration=180,
        description="高血压患者应低盐低脂饮食",
        tags=['高血压', '饮食', '健康']
    ),
    MediaContent(
        content_id='health_002',
        title='老年人运动指南',
        content_type=ContentType.HEALTH_TIP,
        duration=200,
        description='适合老年人的运动方式',
        tags=['运动', '老年人', '健康']
    ),
    MediaContent(
        content_id='health_003',
        title="睡眠质量改善方法",
        content_type=ContentType.HEALTH_TIP,
        duration=160,
        description="提高老年人睡眠质量的方法",
        tags=['睡眠', '老年人', "健康"]
    )
]


# ==================== 预设播放列表 ====================

PRESET_PLAYLISTS = {
    "classic_hits": Playlist(
        playlist_id="classic_hits",
        name="经典老歌精选",
        description="怀旧金曲，重温美好时光",
        content_type=ContentType.MUSIC,
        items=CLASSIC_SONGS
    ),
    "red_classics": Playlist(
        playlist_id="red_classics",
        name='红歌精选',
        description="爱国歌曲，永恒记忆",
        content_type=ContentType.MUSIC,
        items=RED_SONGS
    ),
    "opera_collection": Playlist(
        playlist_id="opera_collection",
        name='戏曲精选',
        description="各大剧种经典剧目",
        content_type=ContentType.OPERA,
        items=OPERA_CONTENT
    ),
    "health_tips": Playlist(
        playlist_id="health_tips",
        name='健康小知识',
        description="每日健康小贴士",
        content_type=ContentType.HEALTH_TIP,
        items=HEALTH_TIPS
    )
}


# ==================== 娱乐服务 ====================

class EntertainmentService:
    """娱乐服务"""

    def __init__(self):
        self.playlists = PRESET_PLAYLISTS
        self.user_favorites: Dict[int, List[str]] = {}  # 用户收藏
        self.user_history: Dict[int, List[str]] = {}  # 播放历史
        self.current_playing: Dict[int, Optional[str]] = {}  # 当前播放

    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """获取所有播放列表"""
        return [p.to_dict() for p in self.playlists.values()]

    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """获取播放列表详情"""
        return self.playlists.get(playlist_id)

    def get_playlist_items(self, playlist_id: str) -> List[Dict[str, Any]]:
        """获取播放列表内容"""
        playlist = self.playlists.get(playlist_id)
        if playlist:
            return [item.to_dict() for item in playlist.items]
        return []

    def get_content_by_type(self, content_type: ContentType) -> List[Dict[str, Any]]:
        """按类型获取内容"""
        contents = []
        for playlist in self.playlists.values():
            if playlist.content_type == content_type:
                contents.extend([item.to_dict() for item in playlist.items])
        return contents

    def get_recommendations(
        self,
        user_id: int,
        content_type: Optional[ContentType] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取推荐内容"""
        all_items = []

        for playlist in self.playlists.values():
            if content_type is None or playlist.content_type == content_type:
                all_items.extend(playlist.items)

        # 简单随机推荐（实际应用中可以基于用户偏好）
        random.shuffle(all_items)
        return [item.to_dict() for item in all_items[:limit]]

    def add_to_favorites(self, user_id: int, content_id: str):
        """添加收藏"""
        if user_id not in self.user_favorites:
            self.user_favorites[user_id] = []
        if content_id not in self.user_favorites[user_id]:
            self.user_favorites[user_id].append(content_id)
            logger.info(f"用户 {user_id} 收藏: {content_id}")

    def remove_from_favorites(self, user_id: int, content_id: str):
        """取消收藏"""
        if user_id in self.user_favorites:
            if content_id in self.user_favorites[user_id]:
                self.user_favorites[user_id].remove(content_id)

    def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户收藏"""
        favorite_ids = self.user_favorites.get(user_id, [])
        favorites = []

        for playlist in self.playlists.values():
            for item in playlist.items:
                if item.content_id in favorite_ids:
                    favorites.append(item.to_dict())

        return favorites

    def record_play(self, user_id: int, content_id: str):
        """记录播放历史"""
        if user_id not in self.user_history:
            self.user_history[user_id] = []

        # 移除重复，保持最近的在前面
        if content_id in self.user_history[user_id]:
            self.user_history[user_id].remove(content_id)

        self.user_history[user_id].insert(0, content_id)

        # 只保留最近50条
        self.user_history[user_id] = self.user_history[user_id][:50]

    def get_history(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """获取播放历史"""
        history_ids = self.user_history.get(user_id, [])[:limit]
        history = []

        for playlist in self.playlists.values():
            for item in playlist.items:
                if item.content_id in history_ids:
                    history.append(item.to_dict())

        return history

    def set_current_playing(self, user_id: int, content_id: str):
        """设置当前播放"""
        self.current_playing[user_id] = content_id
        self.record_play(user_id, content_id)

    def get_current_playing(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取当前播放"""
        content_id = self.current_playing.get(user_id)
        if not content_id:
            return None

        for playlist in self.playlists.values():
            for item in playlist.items:
                if item.content_id == content_id:
                    return item.to_dict()
        return None

    def search(
        self,
        query: str,
        content_type: Optional[ContentType] = None
    ) -> List[Dict[str, Any]]:
        """搜索内容"""
        results = []
        query_lower = query.lower()

        for playlist in self.playlists.values():
            if content_type and playlist.content_type != content_type:
                continue

            for item in playlist.items:
                # 搜索标题、艺术家、描述、标签
                if (query_lower in item.title.lower() or
                    (item.artist and query_lower in item.artist.lower()) or
                    query_lower in item.description.lower() or
                    any(query_lower in tag.lower() for tag in item.tags)):
                    results.append(item.to_dict())

        return results


# ==================== 广播服务 ====================

class RadioService:
    """广播服务"""

    # 广播电台信息
    STATIONS = {
        RadioStation.CNR_NEWS: {
            "name": "中央人民广播电台新闻频道",
            'description': '国内国际新闻资讯',
            'frequency': 'FM106.1',
            "stream_url": "http://example.com/cnr_news.m3u8"
        },
        RadioStation.CNR_MUSIC: {
            'name': "中央人民广播电台音乐之声",
            'description': '流行音乐、经典老歌',
            'frequency': 'FM90.0',
            "stream_url": "http://example.com/cnr_music.m3u8"
        },
        RadioStation.CNR_OPERA: {
            'name': "中央人民广播电台戏曲频道",
            'description': '各类戏曲节目',
            'frequency': 'FM11.4',
            "stream_url": "http://example.com/cnr_opera.m3u8"
        },
        RadioStation.CNR_ECONOMY: {
            'name': "中央人民广播电台经济之声",
            'description': '财经新闻、市场资讯',
            'frequency': 'FM96.6',
            "stream_url": "http://example.com/cnr_economy.m3u8"
        }
    }

    @classmethod
    def get_all_stations(cls) -> List[Dict[str, Any]]:
        """获取所有电台"""
        return [
            {
                'station_id': station.value,
                **info
            }
            for station, info in cls.STATIONS.items()
        ]

    @classmethod
    def get_station(cls, station_id: str) -> Optional[Dict[str, Any]]:
        """获取电台详情"""
        try:
            station = RadioStation(station_id)
            info = cls.STATIONS.get(station)
            if info:
                return {'station_id': station_id, **info}
        except ValueError:
            pass
        return None


# ==================== 健康广播 ====================

class HealthBroadcastService:
    """健康广播服务"""

    # 每日健康提示
    DAILY_TIPS = [
        "今天记得多喝水，保持身体水分充足。",
        '适当运动有益健康，建议每天散步30分钟。',
        '保持良好的作息，早睡早起身体好。',
        '饮食要均衡，多吃蔬菜水果。',
        '心情愉快很重要，多和家人朋友聊天。',
        '定期测量血压，关注身体健康。',
        '天气变化注意增减衣物，预防感冒。',
        '适当晒太阳有助于补充维生素D。',
        '保持良好的卫生习惯，勤洗手。',
        "阅读、下棋等活动有助于保持大脑活力。"
    ]

    @classmethod
    def get_daily_tip(cls) -> str:
        """获取每日健康提示"""
        # 根据日期选择提示
        day = datetime.now().day
        index = day % len(cls.DAILY_TIPS)
        return cls.DAILY_TIPS[index]

    @classmethod
    def get_random_tip(cls) -> str:
        """获取随机健康提示"""
        return random.choice(cls.DAILY_TIPS)


# 全局服务实例
entertainment_service = EntertainmentService()
radio_service = RadioService()
health_broadcast = HealthBroadcastService()
