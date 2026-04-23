"""
社区服务系统
提供社区活动、志愿者服务、邻里互助、社区资源等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class ActivityType(Enum):
    """活动类型"""
    HEALTH_TALK = "health_talk"  # 健康讲座
    EXERCISE_CLASS = "exercise_class"  # 运动课程
    CULTURAL = 'cultural'  # 文化活动
    SOCIAL = 'social'  # 社交聚会
    LEARNING = "learning"  # 学习班
    ENTERTAINMENT = "entertainment"  # 娱乐活动
    VOLUNTEER = 'volunteer'  # 志愿活动
    FESTIVAL = "festival"  # 节日活动


class ActivityStatus(Enum):
    """活动状态"""
    UPCOMING = 'upcoming'  # 即将开始
    ONGOING = 'ongoing'  # 进行中
    COMPLETED = 'completed'  # 已结束
    CANCELLED = "cancelled"  # 已取消


class ServiceType(Enum):
    """服务类型"""
    ACCOMPANY = 'accompany'  # 陪伴服务
    SHOPPING = 'shopping'  # 代购服务
    ESCORT = 'escort'  # 陪同就医
    HOUSEWORK = 'housework'  # 家务帮助
    TECH_HELP = 'tech_help'  # 技术帮助
    CHAT = 'chat'  # 聊天陪伴
    ERRANDS = "errands"  # 跑腿服务


class RequestStatus(Enum):
    """请求状态"""
    PENDING = 'pending'  # 待接单
    ACCEPTED = "accepted"  # 已接单
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = 'completed'  # 已完成
    CANCELLED = "cancelled"  # 已取消


# ==================== 社区活动 ====================

@dataclass
class CommunityActivity:
    """社区活动"""
    activity_id: str
    title: str
    activity_type: ActivityType
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    organizer: str
    max_participants: int
    current_participants: int = 0
    requirements: Optional[str] = None
    fee: float = 0  # 费用
    image_url: Optional[str] = None
    contact_phone: Optional[str] = None
    status: ActivityStatus = ActivityStatus.UPCOMING
    registered_users: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            'title': self.title,
            "activity_type": self.activity_type.value,
            "description": self.description,
            'location': self.location,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'organizer': self.organizer,
            "max_participants": self.max_participants,
            "current_participants": self.current_participants,
            "spots_available": self.max_participants - self.current_participants,
            "requirements": self.requirements,
            'fee': self.fee,
            'image_url': self.image_url,
            "contact_phone": self.contact_phone,
            'status': self.status.value
        }


@dataclass
class ActivityRegistration:
    """活动报名"""
    registration_id: str
    activity_id: str
    user_id: int
    registered_at: datetime = field(default_factory=datetime.now)
    attended: bool = False
    feedback: Optional[str] = None
    rating: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "registration_id": self.registration_id,
            "activity_id": self.activity_id,
            "registered_at": self.registered_at.isoformat(),
            'attended': self.attended,
            'feedback': self.feedback,
            'rating': self.rating
        }


class CommunityActivityService:
    """社区活动服务"""

    def __init__(self):
        self.activities: Dict[str, CommunityActivity] = {}
        self.registrations: Dict[str, ActivityRegistration] = {}
        self.user_registrations: Dict[int, List[str]] = defaultdict(list)
        self._init_sample_activities()

    def _init_sample_activities(self):
        """初始化示例活动"""
        now = datetime.now()
        activities = [
            CommunityActivity(
                'act_001', "老年人健康讲座", ActivityType.HEALTH_TALK,
                "邀请社区医院专家讲解老年人常见疾病预防和保健知识",
                "社区活动中心一楼会议室",
                now + timedelta(days=3, hours=9),
                now + timedelta(days=3, hours=11),
                '社区卫生服务中心', 50,
                requirements="建议携带笔记本",
                contact_phone="010-12345678"
            ),
            CommunityActivity(
                'act_002', "太极拳晨练班", ActivityType.EXERCISE_CLASS,
                "由资深教练带领，适合各年龄段老年人参加",
                '社区公园太极广场',
                now + timedelta(days=1, hours=6),
                now + timedelta(days=1, hours=7),
                '社区体育协会', 30,
                requirements='穿舒适运动服装',
                fee=0
            ),
            CommunityActivity(
                'act_003', "智能手机使用培训", ActivityType.LEARNING,
                "学习使用智能手机的基本功能，包括微信、视频通话等",
                '社区活动中心电脑室',
                now + timedelta(days=5, hours=14),
                now + timedelta(days=5, hours=16),
                '社区志愿者服务队', 20,
                requirements='请自带智能手机'
            ),
            CommunityActivity(
                'act_004', "重阳节联欢会", ActivityType.FESTIVAL,
                "庆祝重阳节，文艺表演、茶话会",
                '社区大礼堂',
                now + timedelta(days=10, hours=9),
                now + timedelta(days=10, hours=12),
                '社区居委会', 100,
                fee=0
            ),
            CommunityActivity(
                'act_005', "书法兴趣班", ActivityType.CULTURAL,
                "学习书法基础，修身养性",
                '社区文化站书画室',
                now + timedelta(days=2, hours=14),
                now + timedelta(days=2, hours=16),
                '社区老年大学', 15,
                requirements="材料费20元",
                fee=20
            )
        ]

        for activity in activities:
            self.activities[activity.activity_id] = activity

    def get_activities(
        self,
        activity_type: ActivityType = None,
        status: ActivityStatus = None,
        upcoming_only: bool = True
    ) -> List[CommunityActivity]:
        """获取活动列表"""
        activities = list(self.activities.values())

        # 更新状态
        now = datetime.now()
        for act in activities:
            if act.status != ActivityStatus.CANCELLED:
                if now >= act.end_time:
                    act.status = ActivityStatus.COMPLETED
                elif now >= act.start_time:
                    act.status = ActivityStatus.ONGOING
                else:
                    act.status = ActivityStatus.UPCOMING

        if activity_type:
            activities = [a for a in activities if a.activity_type == activity_type]

        if status:
            activities = [a for a in activities if a.status == status]

        if upcoming_only:
            activities = [a for a in activities if a.status == ActivityStatus.UPCOMING]

        return sorted(activities, key=lambda x: x.start_time)

    def register_activity(
        self,
        user_id: int,
        activity_id: str
    ) -> Tuple[bool, str]:
        """报名活动"""
        activity = self.activities.get(activity_id)
        if not activity:
            return False, '活动不存在'

        if activity.status != ActivityStatus.UPCOMING:
            return False, '活动已结束或取消'

        if user_id in activity.registered_users:
            return False, '您已报名该活动'

        if activity.current_participants >= activity.max_participants:
            return False, '报名已满'

        # 创建报名记录
        reg_id = f"reg_{user_id}_{activity_id}"
        registration = ActivityRegistration(
            registration_id=reg_id,
            activity_id=activity_id,
            user_id=user_id
        )

        self.registrations[reg_id] = registration
        self.user_registrations[user_id].append(reg_id)

        activity.registered_users.append(user_id)
        activity.current_participants += 1

        return True, "报名成功"

    def cancel_registration(
        self,
        user_id: int,
        activity_id: str
    ) -> Tuple[bool, str]:
        """取消报名"""
        activity = self.activities.get(activity_id)
        if not activity:
            return False, '活动不存在'

        if user_id not in activity.registered_users:
            return False, '您未报名该活动'

        reg_id = f"reg_{user_id}_{activity_id}"
        if reg_id in self.registrations:
            del self.registrations[reg_id]

        if reg_id in self.user_registrations[user_id]:
            self.user_registrations[user_id].remove(reg_id)

        activity.registered_users.remove(user_id)
        activity.current_participants -= 1

        return True, "已取消报名"

    def get_user_registrations(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户报名的活动"""
        reg_ids = self.user_registrations.get(user_id, [])
        result = []

        for reg_id in reg_ids:
            reg = self.registrations.get(reg_id)
            if reg:
                activity = self.activities.get(reg.activity_id)
                if activity:
                    result.append({
                        "registration": reg.to_dict(),
                        'activity': activity.to_dict()
                    })

        return result

    def submit_feedback(
        self,
        user_id: int,
        activity_id: str,
        rating: int,
        feedback: str = None
    ) -> bool:
        """提交活动反馈"""
        reg_id = f"reg_{user_id}_{activity_id}"
        reg = self.registrations.get(reg_id)
        if not reg:
            return False

        reg.rating = rating
        reg.feedback = feedback
        reg.attended = True
        return True


# ==================== 志愿者服务 ====================

@dataclass
class Volunteer:
    """志愿者"""
    volunteer_id: str
    user_id: int
    name: str
    phone: str
    skills: List[str]
    available_services: List[ServiceType]
    available_times: List[str]  # 可服务时间段
    service_area: str  # 服务区域
    total_service_hours: float = 0
    total_services: int = 0
    rating: float = 5.0
    is_active: bool = True
    registered_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "volunteer_id": self.volunteer_id,
            'name': self.name,
            'skills': self.skills,
            "available_services": [s.value for s in self.available_services],
            "available_times": self.available_times,
            "service_area": self.service_area,
            "total_service_hours": self.total_service_hours,
            "total_services": self.total_services,
            'rating': self.rating,
            'is_active': self.is_active
        }


@dataclass
class ServiceRequest:
    """服务请求"""
    request_id: str
    user_id: int
    user_name: str
    service_type: ServiceType
    description: str
    preferred_time: datetime
    location: str
    phone: str
    status: RequestStatus = RequestStatus.PENDING
    volunteer_id: Optional[str] = None
    volunteer_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            "service_type": self.service_type.value,
            "description": self.description,
            "preferred_time": self.preferred_time.isoformat(),
            'location': self.location,
            'status': self.status.value,
            "volunteer_name": self.volunteer_name,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            'rating': self.rating,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat()
        }


class VolunteerService:
    """志愿者服务"""

    def __init__(self):
        self.volunteers: Dict[str, Volunteer] = {}
        self.user_volunteer: Dict[int, str] = {}  # user_id -> volunteer_id
        self.requests: Dict[str, ServiceRequest] = {}
        self.user_requests: Dict[int, List[str]] = defaultdict(list)

    def register_volunteer(
        self,
        user_id: int,
        name: str,
        phone: str,
        skills: List[str],
        available_services: List[ServiceType],
        available_times: List[str],
        service_area: str
    ) -> Volunteer:
        """注册志愿者"""
        volunteer_id = f"vol_{user_id}"

        volunteer = Volunteer(
            volunteer_id=volunteer_id,
            user_id=user_id,
            name=name,
            phone=phone,
            skills=skills,
            available_services=available_services,
            available_times=available_times,
            service_area=service_area
        )

        self.volunteers[volunteer_id] = volunteer
        self.user_volunteer[user_id] = volunteer_id

        logger.info(f"注册志愿者: {name}")
        return volunteer

    def get_volunteers(
        self,
        service_type: ServiceType = None,
        service_area: str = None
    ) -> List[Volunteer]:
        """获取志愿者列表"""
        volunteers = [v for v in self.volunteers.values() if v.is_active]

        if service_type:
            volunteers = [v for v in volunteers if service_type in v.available_services]

        if service_area:
            volunteers = [v for v in volunteers if service_area in v.service_area]

        return sorted(volunteers, key=lambda x: x.rating, reverse=True)

    def create_service_request(
        self,
        user_id: int,
        user_name: str,
        service_type: ServiceType,
        description: str,
        preferred_time: datetime,
        location: str,
        phone: str
    ) -> ServiceRequest:
        """创建服务请求"""
        request_id = f"req_{user_id}_{int(datetime.now().timestamp())}"

        request = ServiceRequest(
            request_id=request_id,
            user_id=user_id,
            user_name=user_name,
            service_type=service_type,
            description=description,
            preferred_time=preferred_time,
            location=location,
            phone=phone
        )

        self.requests[request_id] = request
        self.user_requests[user_id].append(request_id)

        return request

    def accept_request(
        self,
        request_id: str,
        volunteer_id: str
    ) -> bool:
        """接受服务请求"""
        request = self.requests.get(request_id)
        volunteer = self.volunteers.get(volunteer_id)

        if not request or not volunteer:
            return False

        if request.status != RequestStatus.PENDING:
            return False

        request.volunteer_id = volunteer_id
        request.volunteer_name = volunteer.name
        request.status = RequestStatus.ACCEPTED

        return True

    def complete_request(
        self,
        request_id: str,
        volunteer_id: str,
        service_hours: float
    ) -> bool:
        """完成服务"""
        request = self.requests.get(request_id)
        volunteer = self.volunteers.get(volunteer_id)

        if not request or not volunteer:
            return False

        if request.volunteer_id != volunteer_id:
            return False

        request.status = RequestStatus.COMPLETED
        request.completed_at = datetime.now()

        # 更新志愿者统计
        volunteer.total_services += 1
        volunteer.total_service_hours += service_hours

        return True

    def rate_service(
        self,
        request_id: str,
        user_id: int,
        rating: int,
        feedback: str = None
    ) -> bool:
        """评价服务"""
        request = self.requests.get(request_id)
        if not request or request.user_id != user_id:
            return False

        if request.status != RequestStatus.COMPLETED:
            return False

        request.rating = rating
        request.feedback = feedback

        # 更新志愿者评分
        volunteer = self.volunteers.get(request.volunteer_id)
        if volunteer:
            total_ratings = volunteer.total_services
            volunteer.rating = (volunteer.rating * (total_ratings - 1) + rating) / total_ratings

        return True

    def get_user_requests(
        self,
        user_id: int,
        status: RequestStatus = None
    ) -> List[ServiceRequest]:
        """获取用户的服务请求"""
        request_ids = self.user_requests.get(user_id, [])
        requests = [self.requests[rid] for rid in request_ids if rid in self.requests]

        if status:
            requests = [r for r in requests if r.status == status]

        return sorted(requests, key=lambda x: x.created_at, reverse=True)

    def get_pending_requests(
        self,
        service_type: ServiceType = None
    ) -> List[ServiceRequest]:
        """获取待接单的请求"""
        requests = [r for r in self.requests.values() if r.status == RequestStatus.PENDING]

        if service_type:
            requests = [r for r in requests if r.service_type == service_type]

        return sorted(requests, key=lambda x: x.preferred_time)


# ==================== 邻里互助 ====================

@dataclass
class NeighborPost:
    """邻里帖子"""
    post_id: str
    user_id: int
    user_name: str
    post_type: str  # help_needed/offer_help/share/lost_found
    title: str
    content: str
    images: List[str] = field(default_factory=list)
    location: Optional[str] = None
    contact_phone: Optional[str] = None
    is_resolved: bool = False
    view_count: int = 0
    reply_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'post_id': self.post_id,
            'user_name': self.user_name,
            'post_type': self.post_type,
            'title': self.title,
            'content': self.content,
            'images': self.images,
            'location': self.location,
            "is_resolved": self.is_resolved,
            'view_count': self.view_count,
            "reply_count": self.reply_count,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class PostReply:
    """帖子回复"""
    reply_id: str
    post_id: str
    user_id: int
    user_name: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'reply_id': self.reply_id,
            'user_name': self.user_name,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


class NeighborService:
    """邻里互助服务"""

    def __init__(self):
        self.posts: Dict[str, NeighborPost] = {}
        self.user_posts: Dict[int, List[str]] = defaultdict(list)
        self.replies: Dict[str, PostReply] = {}
        self.post_replies: Dict[str, List[str]] = defaultdict(list)

    def create_post(
        self,
        user_id: int,
        user_name: str,
        post_type: str,
        title: str,
        content: str,
        images: List[str] = None,
        location: str = None,
        contact_phone: str = None
    ) -> NeighborPost:
        """创建帖子"""
        post_id = f"post_{user_id}_{int(datetime.now().timestamp())}"

        post = NeighborPost(
            post_id=post_id,
            user_id=user_id,
            user_name=user_name,
            post_type=post_type,
            title=title,
            content=content,
            images=images or [],
            location=location,
            contact_phone=contact_phone
        )

        self.posts[post_id] = post
        self.user_posts[user_id].append(post_id)

        return post

    def get_posts(
        self,
        post_type: str = None,
        resolved: bool = None,
        limit: int = 50
    ) -> List[NeighborPost]:
        """获取帖子列表"""
        posts = list(self.posts.values())

        if post_type:
            posts = [p for p in posts if p.post_type == post_type]

        if resolved is not None:
            posts = [p for p in posts if p.is_resolved == resolved]

        posts = sorted(posts, key=lambda x: x.created_at, reverse=True)
        return posts[:limit]

    def add_reply(
        self,
        post_id: str,
        user_id: int,
        user_name: str,
        content: str
    ) -> Optional[PostReply]:
        """添加回复"""
        post = self.posts.get(post_id)
        if not post:
            return None

        reply_id = f"reply_{post_id}_{int(datetime.now().timestamp())}"

        reply = PostReply(
            reply_id=reply_id,
            post_id=post_id,
            user_id=user_id,
            user_name=user_name,
            content=content
        )

        self.replies[reply_id] = reply
        self.post_replies[post_id].append(reply_id)
        post.reply_count += 1

        return reply

    def get_post_replies(self, post_id: str) -> List[PostReply]:
        """获取帖子回复"""
        reply_ids = self.post_replies.get(post_id, [])
        replies = [self.replies[rid] for rid in reply_ids if rid in self.replies]
        return sorted(replies, key=lambda x: x.created_at)

    def mark_resolved(self, post_id: str, user_id: int) -> bool:
        """标记已解决"""
        post = self.posts.get(post_id)
        if not post or post.user_id != user_id:
            return False

        post.is_resolved = True
        return True


# ==================== 社区资源 ====================

@dataclass
class CommunityResource:
    """社区资源"""
    resource_id: str
    name: str
    category: str  # medical/shopping/service/recreation/government
    description: str
    address: str
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    is_elder_friendly: bool = True
    special_services: List[str] = field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            'name': self.name,
            'category': self.category,
            "description": self.description,
            'address': self.address,
            'phone': self.phone,
            "opening_hours": self.opening_hours,
            "is_elder_friendly": self.is_elder_friendly,
            "special_services": self.special_services
        }


class CommunityResourceService:
    """社区资源服务"""

    RESOURCES = [
        CommunityResource(
            'res_001', '社区卫生服务中心', "medical",
            "提供基本医疗、预防保健、健康管理等服务",
            "社区中心街123号",
            phone="010-12345678",
            opening_hours="周一至周五 8:00-17:00",
            special_services=['老年人体检', '慢病管理', '家庭医生签约']
        ),
        CommunityResource(
            'res_002', '阳光老年活动中心', "recreation",
            "老年人文化娱乐活动场所",
            "社区东路45号",
            phone="010-23456789",
            opening_hours="每天 8:00-18:00",
            special_services=['棋牌室', '书画室', '健身房', '舞蹈室']
        ),
        CommunityResource(
            'res_003', '便民服务站', "service",
            "提供水电费代缴、快递收发等便民服务",
            "社区中心街88号",
            phone="010-34567890",
            opening_hours="每天 7:00-20:00",
            special_services=['代缴费用', '快递代收', '打印复印']
        ),
        CommunityResource(
            'res_004', '街道办事处', 'government',
            '办理各类行政事务',
            "社区政务中心1号楼",
            phone="010-45678901",
            opening_hours="周一至周五 9:00-17:00",
            special_services=['老年证办理', '养老金咨询', '社保服务']
        ),
        CommunityResource(
            'res_005', '社区超市', 'shopping',
            '日常生活用品采购',
            "社区西路12号",
            phone="010-56789012",
            opening_hours="每天 7:00-22:00",
            special_services=['送货上门', "老年人优惠日"]
        )
    ]

    def __init__(self):
        self.resources = {r.resource_id: r for r in self.RESOURCES}

    def get_resources(
        self,
        category: str = None,
        elder_friendly: bool = None
    ) -> List[CommunityResource]:
        """获取社区资源"""
        resources = list(self.resources.values())

        if category:
            resources = [r for r in resources if r.category == category]

        if elder_friendly is not None:
            resources = [r for r in resources if r.is_elder_friendly == elder_friendly]

        return resources

    def search_resources(self, keyword: str) -> List[CommunityResource]:
        """搜索资源"""
        keyword_lower = keyword.lower()
        results = []

        for res in self.resources.values():
            if (keyword_lower in res.name.lower() or
                keyword_lower in res.description.lower() or
                any(keyword_lower in s.lower() for s in res.special_services)):
                results.append(res)

        return results


# ==================== 统一社区服务 ====================

class CommunityService:
    """统一社区服务"""

    def __init__(self):
        self.activity = CommunityActivityService()
        self.volunteer = VolunteerService()
        self.neighbor = NeighborService()
        self.resource = CommunityResourceService()

    def get_community_overview(self, user_id: int) -> Dict[str, Any]:
        """获取社区概览"""
        # 即将举行的活动
        upcoming = self.activity.get_activities(upcoming_only=True)[:5]

        # 用户报名的活动
        my_activities = self.activity.get_user_registrations(user_id)

        # 待接单的服务请求
        pending_requests = self.volunteer.get_pending_requests()[:5]

        # 最新邻里帖子
        recent_posts = self.neighbor.get_posts(limit=5)

        return {
            "upcoming_activities": [a.to_dict() for a in upcoming],
            "my_registrations": len(my_activities),
            "pending_service_requests": len(pending_requests),
            "recent_neighbor_posts": [p.to_dict() for p in recent_posts],
            'community_message': "参与社区活动，让生活更精彩"
        }


# 全局服务实例
community_service = CommunityService()
