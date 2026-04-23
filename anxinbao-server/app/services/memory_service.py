"""
回忆录系统服务
提供照片相册、人生故事、时光记忆、家族传承等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class AlbumType(Enum):
    """相册类型"""
    FAMILY = 'family'  # 家庭相册
    TRAVEL = "travel"  # 旅行回忆
    CELEBRATION = "celebration"  # 节日庆典
    CHILDHOOD = 'childhood'  # 童年记忆
    YOUTH = 'youth'  # 青春岁月
    WEDDING = 'wedding'  # 婚礼纪念
    CAREER = "career"  # 职业生涯
    GRANDCHILDREN = "grandchildren"  # 儿孙成长
    GENERAL = "general"  # 一般相册


class StoryCategory(Enum):
    """故事分类"""
    CHILDHOOD_MEMORY = "childhood_memory"  # 童年回忆
    SCHOOL_DAYS = "school_days"  # 求学时光
    FIRST_JOB = 'first_job'  # 第一份工作
    LOVE_STORY = 'love_story'  # 爱情故事
    PARENTING = "parenting"  # 育儿经历
    LIFE_LESSON = "life_lesson"  # 人生感悟
    HISTORICAL_EVENT = "historical_event"  # 历史见证
    TRADITION = 'tradition'  # 家族传统
    HOBBY = "hobby"  # 兴趣爱好
    ACHIEVEMENT = "achievement"  # 人生成就


class MemoryMood(Enum):
    """记忆情绪"""
    HAPPY = 'happy'  # 快乐
    NOSTALGIC = 'nostalgic'  # 怀旧
    PROUD = 'proud'  # 自豪
    GRATEFUL = 'grateful'  # 感恩
    PEACEFUL = "peaceful"  # 平静
    BITTERSWEET = "bittersweet"  # 苦中带甜
    EXCITED = "excited"  # 兴奋


# ==================== 照片相册 ====================

@dataclass
class Photo:
    """照片"""
    photo_id: str
    user_id: int
    album_id: str
    url: str
    thumbnail_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    taken_date: Optional[date] = None
    location: Optional[str] = None
    people_tags: List[str] = field(default_factory=list)  # 照片中的人
    is_favorite: bool = False
    view_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'photo_id': self.photo_id,
            'album_id': self.album_id,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            'title': self.title,
            "description": self.description,
            'taken_date': self.taken_date.isoformat() if self.taken_date else None,
            'location': self.location,
            "people_tags": self.people_tags,
            "is_favorite": self.is_favorite,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Album:
    """相册"""
    album_id: str
    user_id: int
    name: str
    album_type: AlbumType
    description: Optional[str] = None
    cover_photo_id: Optional[str] = None
    cover_url: Optional[str] = None
    photo_count: int = 0
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    is_shared: bool = False  # 是否与家人共享
    shared_with: List[int] = field(default_factory=list)  # 共享给谁
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'album_id': self.album_id,
            'name': self.name,
            "album_type": self.album_type.value,
            "description": self.description,
            'cover_url': self.cover_url,
            "photo_count": self.photo_count,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            'is_shared': self.is_shared,
            'created_at': self.created_at.isoformat()
        }


class PhotoAlbumService:
    """照片相册服务"""

    def __init__(self):
        self.albums: Dict[str, Album] = {}
        self.user_albums: Dict[int, List[str]] = defaultdict(list)
        self.photos: Dict[str, Photo] = {}
        self.album_photos: Dict[str, List[str]] = defaultdict(list)

    def create_album(
        self,
        user_id: int,
        name: str,
        album_type: AlbumType,
        description: str = None
    ) -> Album:
        """创建相册"""
        album_id = f"album_{user_id}_{secrets.token_hex(4)}"

        album = Album(
            album_id=album_id,
            user_id=user_id,
            name=name,
            album_type=album_type,
            description=description
        )

        self.albums[album_id] = album
        self.user_albums[user_id].append(album_id)

        logger.info(f"创建相册: {name} for user {user_id}")
        return album

    def get_user_albums(
        self,
        user_id: int,
        album_type: AlbumType = None
    ) -> List[Album]:
        """获取用户相册"""
        album_ids = self.user_albums.get(user_id, [])
        albums = [self.albums[aid] for aid in album_ids if aid in self.albums]

        if album_type:
            albums = [a for a in albums if a.album_type == album_type]

        return sorted(albums, key=lambda x: x.created_at, reverse=True)

    def add_photo(
        self,
        user_id: int,
        album_id: str,
        url: str,
        thumbnail_url: str = None,
        title: str = None,
        description: str = None,
        taken_date: date = None,
        location: str = None,
        people_tags: List[str] = None
    ) -> Optional[Photo]:
        """添加照片"""
        album = self.albums.get(album_id)
        if not album or album.user_id != user_id:
            return None

        photo_id = f"photo_{user_id}_{int(datetime.now().timestamp())}"

        photo = Photo(
            photo_id=photo_id,
            user_id=user_id,
            album_id=album_id,
            url=url,
            thumbnail_url=thumbnail_url,
            title=title,
            description=description,
            taken_date=taken_date,
            location=location,
            people_tags=people_tags or []
        )

        self.photos[photo_id] = photo
        self.album_photos[album_id].append(photo_id)

        # 更新相册统计
        album.photo_count += 1
        if not album.cover_photo_id:
            album.cover_photo_id = photo_id
            album.cover_url = thumbnail_url or url

        return photo

    def get_album_photos(
        self,
        album_id: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Photo], int]:
        """获取相册照片"""
        album = self.albums.get(album_id)
        if not album:
            return [], 0

        # 检查权限
        if album.user_id != user_id and user_id not in album.shared_with:
            return [], 0

        photo_ids = self.album_photos.get(album_id, [])
        photos = [self.photos[pid] for pid in photo_ids if pid in self.photos]

        # 按日期排序
        photos = sorted(photos, key=lambda x: x.taken_date or x.created_at, reverse=True)

        total = len(photos)
        photos = photos[offset:offset + limit]

        return photos, total

    def toggle_favorite(self, photo_id: str, user_id: int) -> bool:
        """切换收藏状态"""
        photo = self.photos.get(photo_id)
        if not photo or photo.user_id != user_id:
            return False

        photo.is_favorite = not photo.is_favorite
        return True

    def get_favorites(self, user_id: int) -> List[Photo]:
        """获取收藏照片"""
        favorites = [
            p for p in self.photos.values()
            if p.user_id == user_id and p.is_favorite
        ]
        return sorted(favorites, key=lambda x: x.created_at, reverse=True)

    def share_album(
        self,
        album_id: str,
        user_id: int,
        share_with: List[int]
    ) -> bool:
        """共享相册给家人"""
        album = self.albums.get(album_id)
        if not album or album.user_id != user_id:
            return False

        album.is_shared = True
        album.shared_with = list(set(album.shared_with + share_with))
        return True

    def get_shared_albums(self, user_id: int) -> List[Album]:
        """获取别人共享给我的相册"""
        shared = [
            a for a in self.albums.values()
            if user_id in a.shared_with and a.user_id != user_id
        ]
        return sorted(shared, key=lambda x: x.created_at, reverse=True)

    def search_photos(
        self,
        user_id: int,
        keyword: str = None,
        person: str = None,
        location: str = None,
        year: int = None
    ) -> List[Photo]:
        """搜索照片"""
        photos = [p for p in self.photos.values() if p.user_id == user_id]

        if keyword:
            keyword_lower = keyword.lower()
            photos = [
                p for p in photos
                if (p.title and keyword_lower in p.title.lower()) or
                   (p.description and keyword_lower in p.description.lower())
            ]

        if person:
            photos = [p for p in photos if person in p.people_tags]

        if location:
            location_lower = location.lower()
            photos = [
                p for p in photos
                if p.location and location_lower in p.location.lower()
            ]

        if year:
            photos = [
                p for p in photos
                if p.taken_date and p.taken_date.year == year
            ]

        return sorted(photos, key=lambda x: x.taken_date or x.created_at, reverse=True)


# ==================== 人生故事 ====================

@dataclass
class LifeStory:
    """人生故事"""
    story_id: str
    user_id: int
    title: str
    content: str
    category: StoryCategory
    mood: MemoryMood
    time_period: Optional[str] = None  # 例如 '1960年代', '童年'
    specific_date: Optional[date] = None
    location: Optional[str] = None
    people_involved: List[str] = field(default_factory=list)
    related_photos: List[str] = field(default_factory=list)
    audio_url: Optional[str] = None  # 语音版本
    is_published: bool = False  # 是否发布给家人看
    view_count: int = 0
    likes: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'story_id': self.story_id,
            'title': self.title,
            'content': self.content,
            'category': self.category.value,
            "mood": self.mood.value,
            "time_period": self.time_period,
            "specific_date": self.specific_date.isoformat() if self.specific_date else None,
            'location': self.location,
            "people_involved": self.people_involved,
            "related_photos": self.related_photos,
            'audio_url': self.audio_url,
            "is_published": self.is_published,
            'view_count': self.view_count,
            'likes': self.likes,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class StoryComment:
    """故事评论"""
    comment_id: str
    story_id: str
    user_id: int
    user_name: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'comment_id': self.comment_id,
            'story_id': self.story_id,
            'user_name': self.user_name,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


class LifeStoryService:
    """人生故事服务"""

    # 故事写作提示
    STORY_PROMPTS = {
        StoryCategory.CHILDHOOD_MEMORY: [
            "您记得小时候最喜欢玩什么游戏吗？",
            "您童年的家是什么样子的？",
            "小时候最难忘的一件事是什么？",
            "您最喜欢的童年食物是什么？"
        ],
        StoryCategory.SCHOOL_DAYS: [
            "您还记得您的第一位老师吗？",
            "学生时代最要好的朋友是谁？",
            "学校里发生过什么有趣的事？",
            "您最喜欢什么科目？"
        ],
        StoryCategory.FIRST_JOB: [
            "您的第一份工作是什么？",
            "第一次领工资是什么感觉？",
            "工作中遇到过什么印象深刻的人？",
            "您是如何找到这份工作的？"
        ],
        StoryCategory.LOVE_STORY: [
            "您和爱人是怎么认识的？",
            "您们的第一次约会是什么样的？",
            "结婚那天有什么特别的回忆？",
            "这些年来最感动的瞬间是什么？"
        ],
        StoryCategory.PARENTING: [
            "孩子出生时是什么感觉？",
            "育儿过程中最有趣的事是什么？",
            "您是如何教育孩子的？",
            "孩子让您最骄傲的时刻？"
        ],
        StoryCategory.LIFE_LESSON: [
            "这一生最重要的人生经验是什么？",
            "您想对年轻人说些什么？",
            "如果能重来，您会改变什么？",
            "什么事情让您感到最满足？"
        ]
    }

    def __init__(self):
        self.stories: Dict[str, LifeStory] = {}
        self.user_stories: Dict[int, List[str]] = defaultdict(list)
        self.comments: Dict[str, StoryComment] = {}
        self.story_comments: Dict[str, List[str]] = defaultdict(list)

    def create_story(
        self,
        user_id: int,
        title: str,
        content: str,
        category: StoryCategory,
        mood: MemoryMood,
        time_period: str = None,
        specific_date: date = None,
        location: str = None,
        people_involved: List[str] = None,
        related_photos: List[str] = None,
        audio_url: str = None,
        tags: List[str] = None
    ) -> LifeStory:
        """创建人生故事"""
        story_id = f"story_{user_id}_{secrets.token_hex(4)}"

        story = LifeStory(
            story_id=story_id,
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            mood=mood,
            time_period=time_period,
            specific_date=specific_date,
            location=location,
            people_involved=people_involved or [],
            related_photos=related_photos or [],
            audio_url=audio_url,
            tags=tags or []
        )

        self.stories[story_id] = story
        self.user_stories[user_id].append(story_id)

        logger.info(f"创建人生故事: {title} for user {user_id}")
        return story

    def update_story(
        self,
        story_id: str,
        user_id: int,
        title: str = None,
        content: str = None,
        time_period: str = None,
        location: str = None,
        people_involved: List[str] = None,
        related_photos: List[str] = None,
        tags: List[str] = None
    ) -> Optional[LifeStory]:
        """更新故事"""
        story = self.stories.get(story_id)
        if not story or story.user_id != user_id:
            return None

        if title:
            story.title = title
        if content:
            story.content = content
        if time_period:
            story.time_period = time_period
        if location:
            story.location = location
        if people_involved is not None:
            story.people_involved = people_involved
        if related_photos is not None:
            story.related_photos = related_photos
        if tags is not None:
            story.tags = tags

        story.updated_at = datetime.now()
        return story

    def get_user_stories(
        self,
        user_id: int,
        category: StoryCategory = None,
        published_only: bool = False
    ) -> List[LifeStory]:
        """获取用户故事"""
        story_ids = self.user_stories.get(user_id, [])
        stories = [self.stories[sid] for sid in story_ids if sid in self.stories]

        if category:
            stories = [s for s in stories if s.category == category]

        if published_only:
            stories = [s for s in stories if s.is_published]

        return sorted(stories, key=lambda x: x.created_at, reverse=True)

    def publish_story(self, story_id: str, user_id: int) -> bool:
        """发布故事给家人"""
        story = self.stories.get(story_id)
        if not story or story.user_id != user_id:
            return False

        story.is_published = True
        return True

    def get_writing_prompts(self, category: StoryCategory = None) -> List[str]:
        """获取写作提示"""
        if category and category in self.STORY_PROMPTS:
            return self.STORY_PROMPTS[category]

        # 返回所有提示
        all_prompts = []
        for prompts in self.STORY_PROMPTS.values():
            all_prompts.extend(prompts)
        return all_prompts

    def add_comment(
        self,
        story_id: str,
        user_id: int,
        user_name: str,
        content: str
    ) -> Optional[StoryComment]:
        """添加评论"""
        story = self.stories.get(story_id)
        if not story or not story.is_published:
            return None

        comment_id = f"comment_{story_id}_{int(datetime.now().timestamp())}"

        comment = StoryComment(
            comment_id=comment_id,
            story_id=story_id,
            user_id=user_id,
            user_name=user_name,
            content=content
        )

        self.comments[comment_id] = comment
        self.story_comments[story_id].append(comment_id)

        return comment

    def get_story_comments(self, story_id: str) -> List[StoryComment]:
        """获取故事评论"""
        comment_ids = self.story_comments.get(story_id, [])
        comments = [self.comments[cid] for cid in comment_ids if cid in self.comments]
        return sorted(comments, key=lambda x: x.created_at)

    def like_story(self, story_id: str) -> bool:
        """点赞故事"""
        story = self.stories.get(story_id)
        if not story:
            return False

        story.likes += 1
        return True

    def search_stories(
        self,
        user_id: int,
        keyword: str = None,
        category: StoryCategory = None,
        person: str = None
    ) -> List[LifeStory]:
        """搜索故事"""
        stories = self.get_user_stories(user_id)

        if keyword:
            keyword_lower = keyword.lower()
            stories = [
                s for s in stories
                if keyword_lower in s.title.lower() or keyword_lower in s.content.lower()
            ]

        if category:
            stories = [s for s in stories if s.category == category]

        if person:
            stories = [s for s in stories if person in s.people_involved]

        return stories


# ==================== 时光记忆 ====================

@dataclass
class TimelineEvent:
    """时间线事件"""
    event_id: str
    user_id: int
    title: str
    description: Optional[str] = None
    event_date: date = None
    event_type: str = 'milestone'  # milestone/memory/achievement
    related_stories: List[str] = field(default_factory=list)
    related_photos: List[str] = field(default_factory=list)
    icon: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'title': self.title,
            "description": self.description,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'event_type': self.event_type,
            "related_stories": self.related_stories,
            "related_photos": self.related_photos,
            'icon': self.icon
        }


class TimelineService:
    """时间线服务"""

    def __init__(self):
        self.events: Dict[str, TimelineEvent] = {}
        self.user_events: Dict[int, List[str]] = defaultdict(list)

    def add_event(
        self,
        user_id: int,
        title: str,
        event_date: date,
        description: str = None,
        event_type: str = 'milestone',
        related_stories: List[str] = None,
        related_photos: List[str] = None,
        icon: str = None
    ) -> TimelineEvent:
        """添加时间线事件"""
        event_id = f"event_{user_id}_{secrets.token_hex(4)}"

        event = TimelineEvent(
            event_id=event_id,
            user_id=user_id,
            title=title,
            description=description,
            event_date=event_date,
            event_type=event_type,
            related_stories=related_stories or [],
            related_photos=related_photos or [],
            icon=icon
        )

        self.events[event_id] = event
        self.user_events[user_id].append(event_id)

        return event

    def get_user_timeline(
        self,
        user_id: int,
        start_year: int = None,
        end_year: int = None
    ) -> List[TimelineEvent]:
        """获取用户时间线"""
        event_ids = self.user_events.get(user_id, [])
        events = [self.events[eid] for eid in event_ids if eid in self.events]

        if start_year:
            events = [e for e in events if e.event_date and e.event_date.year >= start_year]

        if end_year:
            events = [e for e in events if e.event_date and e.event_date.year <= end_year]

        return sorted(events, key=lambda x: x.event_date or date.min)

    def get_timeline_by_decade(self, user_id: int) -> Dict[str, List[TimelineEvent]]:
        """按年代获取时间线"""
        events = self.get_user_timeline(user_id)
        by_decade = defaultdict(list)

        for event in events:
            if event.event_date:
                decade = (event.event_date.year // 10) * 10
                decade_key = f"{decade}年代"
                by_decade[decade_key].append(event)

        return dict(by_decade)


# ==================== 家族传承 ====================

@dataclass
class FamilyMember:
    """家族成员"""
    member_id: str
    user_id: int  # 创建者
    name: str
    relationship: str  # 与创建者的关系
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    birthplace: Optional[str] = None
    occupation: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    parent_id: Optional[str] = None  # 父节点ID(用于家谱)
    generation: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'member_id': self.member_id,
            "name": self.name,
            "relationship": self.relationship,
            'birth_year': self.birth_year,
            'death_year': self.death_year,
            'birthplace': self.birthplace,
            'occupation': self.occupation,
            'bio': self.bio,
            'photo_url': self.photo_url,
            'parent_id': self.parent_id,
            'generation': self.generation
        }


@dataclass
class FamilyTradition:
    """家族传统"""
    tradition_id: str
    user_id: int
    name: str
    description: str
    origin_story: Optional[str] = None
    related_holiday: Optional[str] = None
    photos: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tradition_id": self.tradition_id,
            'name': self.name,
            "description": self.description,
            "origin_story": self.origin_story,
            "related_holiday": self.related_holiday,
            'photos': self.photos
        }


class FamilyLegacyService:
    """家族传承服务"""

    def __init__(self):
        self.members: Dict[str, FamilyMember] = {}
        self.user_members: Dict[int, List[str]] = defaultdict(list)
        self.traditions: Dict[str, FamilyTradition] = {}
        self.user_traditions: Dict[int, List[str]] = defaultdict(list)

    def add_family_member(
        self,
        user_id: int,
        name: str,
        relationship: str,
        birth_year: int = None,
        death_year: int = None,
        birthplace: str = None,
        occupation: str = None,
        bio: str = None,
        photo_url: str = None,
        parent_id: str = None,
        generation: int = 0
    ) -> FamilyMember:
        """添加家族成员"""
        member_id = f"member_{user_id}_{secrets.token_hex(4)}"

        member = FamilyMember(
            member_id=member_id,
            user_id=user_id,
            name=name,
            relationship=relationship,
            birth_year=birth_year,
            death_year=death_year,
            birthplace=birthplace,
            occupation=occupation,
            bio=bio,
            photo_url=photo_url,
            parent_id=parent_id,
            generation=generation
        )

        self.members[member_id] = member
        self.user_members[user_id].append(member_id)

        return member

    def get_family_tree(self, user_id: int) -> List[FamilyMember]:
        """获取家谱"""
        member_ids = self.user_members.get(user_id, [])
        members = [self.members[mid] for mid in member_ids if mid in self.members]
        return sorted(members, key=lambda x: (x.generation, x.birth_year or 0))

    def get_family_tree_structured(self, user_id: int) -> Dict[str, Any]:
        """获取结构化家谱"""
        members = self.get_family_tree(user_id)

        # 按代分组
        by_generation = defaultdict(list)
        for member in members:
            by_generation[member.generation].append(member.to_dict())

        return {
            "total_members": len(members),
            "generations": dict(by_generation)
        }

    def add_tradition(
        self,
        user_id: int,
        name: str,
        description: str,
        origin_story: str = None,
        related_holiday: str = None,
        photos: List[str] = None
    ) -> FamilyTradition:
        """添加家族传统"""
        tradition_id = f"tradition_{user_id}_{secrets.token_hex(4)}"

        tradition = FamilyTradition(
            tradition_id=tradition_id,
            user_id=user_id,
            name=name,
            description=description,
            origin_story=origin_story,
            related_holiday=related_holiday,
            photos=photos or []
        )

        self.traditions[tradition_id] = tradition
        self.user_traditions[user_id].append(tradition_id)

        return tradition

    def get_traditions(self, user_id: int) -> List[FamilyTradition]:
        """获取家族传统"""
        tradition_ids = self.user_traditions.get(user_id, [])
        traditions = [self.traditions[tid] for tid in tradition_ids if tid in self.traditions]
        return traditions


# ==================== 统一回忆录服务 ====================

class MemoryService:
    """统一回忆录服务"""

    def __init__(self):
        self.photo_album = PhotoAlbumService()
        self.life_story = LifeStoryService()
        self.timeline = TimelineService()
        self.family_legacy = FamilyLegacyService()

    def get_memory_overview(self, user_id: int) -> Dict[str, Any]:
        """获取回忆录概览"""
        albums = self.photo_album.get_user_albums(user_id)
        stories = self.life_story.get_user_stories(user_id)
        timeline = self.timeline.get_user_timeline(user_id)
        family = self.family_legacy.get_family_tree(user_id)

        total_photos = sum(a.photo_count for a in albums)

        return {
            'albums': {
                'count': len(albums),
                "total_photos": total_photos
            },
            'stories': {
                'count': len(stories),
                'published': sum(1 for s in stories if s.is_published),
                'categories': list(set(s.category.value for s in stories))
            },
            'timeline': {
                "events_count": len(timeline),
                "earliest_year": min((e.event_date.year for e in timeline if e.event_date), default=None),
                "latest_year": max((e.event_date.year for e in timeline if e.event_date), default=None)
            },
            'family': {
                "members_count": len(family),
                "traditions_count": len(self.family_legacy.get_traditions(user_id))
            }
        }


# 全局服务实例
memory_service = MemoryService()
