"""
社交功能服务
为老年人提供朋友圈、活动、社群等社交功能
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date
import random

logger = logging.getLogger(__name__)


class PostType(Enum):
    """动态类型"""
    TEXT = 'text'  # 纯文字
    IMAGE = 'image'  # 图片
    VOICE = 'voice'  # 语音
    HEALTH = 'health'  # 健康打卡
    ACTIVITY = 'activity'  # 活动分享
    ACHIEVEMENT = "achievement"  # 成就展示


class ActivityType(Enum):
    """活动类型"""
    EXERCISE = 'exercise'  # 运动健身
    CULTURE = 'culture'  # 文化活动
    SOCIAL = 'social'  # 社交聚会
    LEARNING = 'learning'  # 学习课程
    ENTERTAINMENT = "entertainment"  # 娱乐活动
    VOLUNTEER = 'volunteer'  # 志愿服务


class ActivityStatus(Enum):
    """活动状态"""
    UPCOMING = 'upcoming'  # 即将开始
    ONGOING = 'ongoing'  # 进行中
    ENDED = 'ended'  # 已结束
    CANCELLED = 'cancelled'  # 已取消


@dataclass
class SocialPost:
    """社交动态"""
    post_id: str
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    post_type: PostType = PostType.TEXT
    content: str = ""
    images: List[str] = field(default_factory=list)
    voice_url: Optional[str] = None
    voice_duration: int = 0
    location: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    likes: List[int] = field(default_factory=list)  # 点赞用户ID
    comments: List[Dict] = field(default_factory=list)
    is_public: bool = True
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'post_id': self.post_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            "user_avatar": self.user_avatar,
            'post_type': self.post_type.value,
            'content': self.content,
            'images': self.images,
            'voice_url': self.voice_url,
            "voice_duration": self.voice_duration,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'like_count': len(self.likes),
            "comment_count": len(self.comments),
            'is_public': self.is_public,
            'tags': self.tags
        }


@dataclass
class Activity:
    """社交活动"""
    activity_id: str
    title: str
    description: str
    activity_type: ActivityType
    organizer_id: int
    organizer_name: str
    location: str
    start_time: datetime
    end_time: datetime
    max_participants: int = 0  # 0表示不限
    participants: List[int] = field(default_factory=list)
    status: ActivityStatus = ActivityStatus.UPCOMING
    cover_image: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    requirements: str = ""  # 参与要求
    fee: float = 0  # 费用

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            'title': self.title,
            "description": self.description,
            "activity_type": self.activity_type.value,
            "organizer_id": self.organizer_id,
            "organizer_name": self.organizer_name,
            'location': self.location,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            "max_participants": self.max_participants,
            "participant_count": len(self.participants),
            'is_full': self.max_participants > 0 and len(self.participants) >= self.max_participants,
            'status': self.status.value,
            "cover_image": self.cover_image,
            'tags': self.tags,
            "requirements": self.requirements,
            'fee': self.fee
        }


@dataclass
class Friend:
    """好友关系"""
    user_id: int
    friend_id: int
    friend_name: str
    friend_avatar: Optional[str] = None
    nickname: str = ""  # 备注名
    created_at: datetime = field(default_factory=datetime.now)
    is_favorite: bool = False  # 特别关注

    def to_dict(self) -> Dict[str, Any]:
        return {
            'friend_id': self.friend_id,
            "friend_name": self.friend_name,
            "friend_avatar": self.friend_avatar,
            'nickname': self.nickname,
            "is_favorite": self.is_favorite,
            'added_at': self.created_at.isoformat()
        }


@dataclass
class HealthCheckIn:
    """健康打卡"""
    checkin_id: str
    user_id: int
    user_name: str
    checkin_date: date
    checkin_type: str  # exercise/diet/medication/sleep
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    streak_days: int = 1  # 连续打卡天数
    likes: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'checkin_id': self.checkin_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            "checkin_date": self.checkin_date.isoformat(),
            "checkin_type": self.checkin_type,
            'content': self.content,
            "streak_days": self.streak_days,
            'like_count': len(self.likes)
        }


# ==================== 社交服务 ====================

class SocialService:
    """社交服务"""

    def __init__(self):
        self.posts: Dict[str, SocialPost] = {}
        self.user_posts: Dict[int, List[str]] = {}
        self.activities: Dict[str, Activity] = {}
        self.friends: Dict[int, List[Friend]] = {}
        self.checkins: Dict[str, HealthCheckIn] = {}
        self.user_checkins: Dict[int, List[str]] = {}

    # ==================== 动态管理 ====================

    def create_post(
        self,
        user_id: int,
        user_name: str,
        content: str,
        post_type: PostType = PostType.TEXT,
        images: List[str] = None,
        voice_url: str = None,
        voice_duration: int = 0,
        location: str = None,
        tags: List[str] = None,
        is_public: bool = True
    ) -> SocialPost:
        """创建动态"""
        post_id = f"post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        post = SocialPost(
            post_id=post_id,
            user_id=user_id,
            user_name=user_name,
            post_type=post_type,
            content=content,
            images=images or [],
            voice_url=voice_url,
            voice_duration=voice_duration,
            location=location,
            tags=tags or [],
            is_public=is_public
        )

        self.posts[post_id] = post

        if user_id not in self.user_posts:
            self.user_posts[user_id] = []
        self.user_posts[user_id].append(post_id)

        logger.info(f"用户 {user_id} 发布动态: {post_id}")
        return post

    def delete_post(self, post_id: str, user_id: int) -> bool:
        """删除动态"""
        post = self.posts.get(post_id)
        if not post or post.user_id != user_id:
            return False

        del self.posts[post_id]
        if user_id in self.user_posts:
            self.user_posts[user_id].remove(post_id)

        return True

    def like_post(self, post_id: str, user_id: int) -> bool:
        """点赞动态"""
        post = self.posts.get(post_id)
        if not post:
            return False

        if user_id not in post.likes:
            post.likes.append(user_id)
        return True

    def unlike_post(self, post_id: str, user_id: int) -> bool:
        """取消点赞"""
        post = self.posts.get(post_id)
        if not post:
            return False

        if user_id in post.likes:
            post.likes.remove(user_id)
        return True

    def comment_post(
        self,
        post_id: str,
        user_id: int,
        user_name: str,
        content: str
    ) -> Optional[Dict]:
        """评论动态"""
        post = self.posts.get(post_id)
        if not post:
            return None

        comment = {
            'comment_id': f'comment_{len(post.comments)}',
            'user_id': user_id,
            'user_name': user_name,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        post.comments.append(comment)

        return comment

    def get_post(self, post_id: str) -> Optional[SocialPost]:
        """获取动态详情"""
        return self.posts.get(post_id)

    def get_user_posts(self, user_id: int, limit: int = 20) -> List[SocialPost]:
        """获取用户动态"""
        post_ids = self.user_posts.get(user_id, [])
        posts = [self.posts[pid] for pid in post_ids if pid in self.posts]
        posts.sort(key=lambda p: p.created_at, reverse=True)
        return posts[:limit]

    def get_feed(self, user_id: int, limit: int = 20) -> List[SocialPost]:
        """获取动态流（好友+自己的动态）"""
        friend_ids = [f.friend_id for f in self.friends.get(user_id, [])]
        friend_ids.append(user_id)

        all_posts = []
        for fid in friend_ids:
            posts = self.get_user_posts(fid, limit)
            all_posts.extend([p for p in posts if p.is_public or p.user_id == user_id])

        all_posts.sort(key=lambda p: p.created_at, reverse=True)
        return all_posts[:limit]

    # ==================== 好友管理 ====================

    def add_friend(
        self,
        user_id: int,
        friend_id: int,
        friend_name: str,
        nickname: str = ""
    ) -> Friend:
        """添加好友"""
        friend = Friend(
            user_id=user_id,
            friend_id=friend_id,
            friend_name=friend_name,
            nickname=nickname
        )

        if user_id not in self.friends:
            self.friends[user_id] = []

        # 检查是否已是好友
        existing = [f for f in self.friends[user_id] if f.friend_id == friend_id]
        if not existing:
            self.friends[user_id].append(friend)

        logger.info(f"用户 {user_id} 添加好友: {friend_id}")
        return friend

    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """删除好友"""
        if user_id not in self.friends:
            return False

        self.friends[user_id] = [
            f for f in self.friends[user_id]
            if f.friend_id != friend_id
        ]
        return True

    def get_friends(self, user_id: int) -> List[Friend]:
        """获取好友列表"""
        friends = self.friends.get(user_id, [])
        # 特别关注的排前面
        return sorted(friends, key=lambda f: (not f.is_favorite, f.friend_name))

    def set_favorite_friend(self, user_id: int, friend_id: int, is_favorite: bool) -> bool:
        """设置特别关注"""
        if user_id not in self.friends:
            return False

        for friend in self.friends[user_id]:
            if friend.friend_id == friend_id:
                friend.is_favorite = is_favorite
                return True
        return False

    # ==================== 活动管理 ====================

    def create_activity(
        self,
        organizer_id: int,
        organizer_name: str,
        title: str,
        description: str,
        activity_type: ActivityType,
        location: str,
        start_time: datetime,
        end_time: datetime,
        max_participants: int = 0,
        requirements: str = "",
        fee: float = 0,
        tags: List[str] = None
    ) -> Activity:
        """创建活动"""
        activity_id = f"activity_{organizer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        activity = Activity(
            activity_id=activity_id,
            title=title,
            description=description,
            activity_type=activity_type,
            organizer_id=organizer_id,
            organizer_name=organizer_name,
            location=location,
            start_time=start_time,
            end_time=end_time,
            max_participants=max_participants,
            requirements=requirements,
            fee=fee,
            tags=tags or []
        )

        self.activities[activity_id] = activity
        logger.info(f"活动创建: {title} by {organizer_name}")
        return activity

    def join_activity(self, activity_id: str, user_id: int) -> Dict[str, Any]:
        """参加活动"""
        activity = self.activities.get(activity_id)
        if not activity:
            return {'success': False, 'error': '活动不存在'}

        if activity.status != ActivityStatus.UPCOMING:
            return {'success': False, 'error': '活动已结束或取消'}

        if activity.max_participants > 0 and len(activity.participants) >= activity.max_participants:
            return {'success': False, 'error': '活动已满员'}

        if user_id in activity.participants:
            return {'success': False, 'error': '已报名'}

        activity.participants.append(user_id)
        return {'success': True, 'message': '报名成功'}

    def leave_activity(self, activity_id: str, user_id: int) -> bool:
        """退出活动"""
        activity = self.activities.get(activity_id)
        if not activity:
            return False

        if user_id in activity.participants:
            activity.participants.remove(user_id)
            return True
        return False

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """获取活动详情"""
        return self.activities.get(activity_id)

    def get_activities(
        self,
        activity_type: Optional[ActivityType] = None,
        status: Optional[ActivityStatus] = None,
        limit: int = 20
    ) -> List[Activity]:
        """获取活动列表"""
        activities = list(self.activities.values())

        if activity_type:
            activities = [a for a in activities if a.activity_type == activity_type]

        if status:
            activities = [a for a in activities if a.status == status]

        # 按开始时间排序
        activities.sort(key=lambda a: a.start_time)
        return activities[:limit]

    def get_user_activities(self, user_id: int) -> List[Activity]:
        """获取用户参与的活动"""
        return [
            a for a in self.activities.values()
            if user_id in a.participants or a.organizer_id == user_id
        ]

    # ==================== 健康打卡 ====================

    def create_checkin(
        self,
        user_id: int,
        user_name: str,
        checkin_type: str,
        content: str
    ) -> HealthCheckIn:
        """健康打卡"""
        today = date.today()
        checkin_id = f'checkin_{user_id}_{today.isoformat()}'

        # 计算连续打卡天数
        streak = self._calculate_streak(user_id, today)

        checkin = HealthCheckIn(
            checkin_id=checkin_id,
            user_id=user_id,
            user_name=user_name,
            checkin_date=today,
            checkin_type=checkin_type,
            content=content,
            streak_days=streak
        )

        self.checkins[checkin_id] = checkin

        if user_id not in self.user_checkins:
            self.user_checkins[user_id] = []
        self.user_checkins[user_id].append(checkin_id)

        logger.info(f"用户 {user_id} 健康打卡: {checkin_type}")
        return checkin

    def _calculate_streak(self, user_id: int, today: date) -> int:
        """计算连续打卡天数"""
        checkin_ids = self.user_checkins.get(user_id, [])
        if not checkin_ids:
            return 1

        # 检查昨天是否打卡
        from datetime import timedelta
        yesterday = today - timedelta(days=1)

        for cid in reversed(checkin_ids):
            checkin = self.checkins.get(cid)
            if checkin and checkin.checkin_date == yesterday:
                return checkin.streak_days + 1

        return 1

    def get_user_checkins(
        self,
        user_id: int,
        days: int = 30
    ) -> List[HealthCheckIn]:
        """获取用户打卡记录"""
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=days)

        checkin_ids = self.user_checkins.get(user_id, [])
        checkins = [
            self.checkins[cid] for cid in checkin_ids
            if cid in self.checkins and self.checkins[cid].checkin_date >= cutoff
        ]

        checkins.sort(key=lambda c: c.checkin_date, reverse=True)
        return checkins

    def get_checkin_leaderboard(self, limit: int = 10) -> List[Dict]:
        """获取打卡排行榜"""
        user_streaks = {}

        for checkin in self.checkins.values():
            if checkin.user_id not in user_streaks:
                user_streaks[checkin.user_id] = {
                    'user_id': checkin.user_id,
                    'user_name': checkin.user_name,
                    "streak_days": 0,
                    "total_checkins": 0
                }

            user_streaks[checkin.user_id]["total_checkins"] += 1
            if checkin.streak_days > user_streaks[checkin.user_id]["streak_days"]:
                user_streaks[checkin.user_id]["streak_days"] = checkin.streak_days

        leaderboard = list(user_streaks.values())
        leaderboard.sort(key=lambda x: (-x["streak_days"], -x['total_checkins']))
        return leaderboard[:limit]

    # ==================== 互动统计 ====================

    def get_user_social_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户社交统计"""
        posts = self.get_user_posts(user_id, 100)
        friends = self.get_friends(user_id)
        checkins = self.get_user_checkins(user_id, 30)
        activities = self.get_user_activities(user_id)

        total_likes = sum(len(p.likes) for p in posts)
        total_comments = sum(len(p.comments) for p in posts)

        return {
            'post_count': len(posts),
            "friend_count": len(friends),
            "activity_count": len(activities),
            "checkin_count": len(checkins),
            "total_likes_received": total_likes,
            "total_comments_received": total_comments,
            "current_streak": checkins[0].streak_days if checkins else 0
        }


# ==================== 推荐服务 ====================

class SocialRecommendationService:
    """社交推荐服务"""

    def __init__(self, social_service: SocialService):
        self.social = social_service

    def recommend_friends(self, user_id: int, limit: int = 5) -> List[Dict]:
        """推荐好友（基于共同好友）"""
        # 简化实现：随机推荐
        all_users = set()
        for friends in self.social.friends.values():
            for f in friends:
                all_users.add(f.friend_id)

        current_friends = {f.friend_id for f in self.social.get_friends(user_id)}
        current_friends.add(user_id)

        candidates = list(all_users - current_friends)
        random.shuffle(candidates)

        return [{'user_id': uid, 'reason': '可能认识'} for uid in candidates[:limit]]

    def recommend_activities(self, user_id: int, limit: int = 5) -> List[Activity]:
        """推荐活动"""
        # 获取即将开始的活动
        upcoming = self.social.get_activities(
            status=ActivityStatus.UPCOMING,
            limit=limit * 2
        )

        # 过滤已参加的
        user_activities = {a.activity_id for a in self.social.get_user_activities(user_id)}
        recommendations = [a for a in upcoming if a.activity_id not in user_activities]

        return recommendations[:limit]


# 全局服务实例
social_service = SocialService()
social_recommendation = SocialRecommendationService(social_service)
