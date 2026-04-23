"""
社区服务API
提供社区活动、志愿者服务、邻里互助、社区资源等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.community_service import (
    community_service,
    ActivityType,
    ActivityStatus,
    ServiceType,
    RequestStatus
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/community", tags=["社区服务"])


# ==================== 请求模型 ====================

class RegisterActivityRequest(BaseModel):
    """报名活动请求"""
    activity_id: str = Field(..., description="活动ID")


class ActivityFeedbackRequest(BaseModel):
    """活动反馈请求"""
    activity_id: str = Field(..., description='活动ID')
    rating: int = Field(..., ge=1, le=5, description='评分(1-5)')
    feedback: Optional[str] = Field(None, max_length=500, description="反馈内容")


class RegisterVolunteerRequest(BaseModel):
    """注册志愿者请求"""
    name: str = Field(..., max_length=50, description='姓名')
    phone: str = Field(..., max_length=20, description='联系电话')
    skills: List[str] = Field(..., description='技能特长')
    available_services: List[str] = Field(..., description='可提供的服务类型')
    available_times: List[str] = Field(..., description='可服务时间段')
    service_area: str = Field(..., max_length=100, description="服务区域")


class CreateServiceRequestRequest(BaseModel):
    """创建服务请求"""
    service_type: str = Field(..., description='服务类型')
    description: str = Field(..., max_length=500, description='服务描述')
    preferred_time: datetime = Field(..., description='期望服务时间')
    location: str = Field(..., max_length=200, description='服务地点')
    phone: str = Field(..., max_length=20, description="联系电话")


class RateServiceRequest(BaseModel):
    """评价服务请求"""
    rating: int = Field(..., ge=1, le=5, description='评分(1-5)')
    feedback: Optional[str] = Field(None, max_length=500, description="反馈内容")


class CreateNeighborPostRequest(BaseModel):
    """创建邻里帖子请求"""
    post_type: str = Field(..., description="帖子类型: help_needed/offer_help/share/lost_found")
    title: str = Field(..., max_length=100, description='标题')
    content: str = Field(..., max_length=2000, description='内容')
    images: Optional[List[str]] = Field(None, description='图片URL列表')
    location: Optional[str] = Field(None, max_length=100, description='位置')
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")


class AddReplyRequest(BaseModel):
    """添加回复请求"""
    content: str = Field(..., min_length=1, max_length=500, description="回复内容")


# ==================== 社区活动API ====================

@router.get("/activities")
async def get_activities(
    activity_type: Optional[str] = Query(None, description='活动类型'),
    upcoming_only: bool = Query(True, description="仅显示即将开始的活动"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取社区活动列表
    """
    type_filter = None
    if activity_type:
        try:
            type_filter = ActivityType(activity_type)
        except ValueError:
            pass

    activities = community_service.activity.get_activities(
        activity_type=type_filter,
        upcoming_only=upcoming_only
    )

    return {
        'activities': [a.to_dict() for a in activities],
        'count': len(activities)
    }


@router.get("/activities/{activity_id}")
async def get_activity_detail(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取活动详情
    """
    activity = community_service.activity.activities.get(activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail='活动不存在')

    user_id = int(current_user['sub'])
    is_registered = user_id in activity.registered_users

    return {
        "activity": activity.to_dict(),
        "is_registered": is_registered
    }


@router.post("/activities/register")
async def register_activity(
    request: RegisterActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    报名社区活动
    """
    user_id = int(current_user['sub'])

    success, message = community_service.activity.register_activity(
        user_id, request.activity_id
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'message': message
    }


@router.post("/activities/cancel")
async def cancel_activity_registration(
    request: RegisterActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    取消活动报名
    """
    user_id = int(current_user['sub'])

    success, message = community_service.activity.cancel_registration(
        user_id, request.activity_id
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'message': message
    }


@router.get("/activities/my-registrations")
async def get_my_registrations(current_user: dict = Depends(get_current_user)):
    """
    获取我报名的活动
    """
    user_id = int(current_user['sub'])

    registrations = community_service.activity.get_user_registrations(user_id)

    return {
        "registrations": registrations,
        'count': len(registrations)
    }


@router.post("/activities/feedback")
async def submit_activity_feedback(
    request: ActivityFeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交活动反馈
    """
    user_id = int(current_user['sub'])

    success = community_service.activity.submit_feedback(
        user_id, request.activity_id, request.rating, request.feedback
    )

    if not success:
        raise HTTPException(status_code=400, detail="无法提交反馈，请确认您已报名该活动")

    return {
        'success': True,
        'message': "感谢您的反馈"
    }


@router.get("/activities/types")
async def get_activity_types(current_user: dict = Depends(get_current_user)):
    """
    获取活动类型列表
    """
    types = [{'value': t.value, 'label': t.value} for t in ActivityType]

    return {'types': types}


# ==================== 志愿者服务API ====================

@router.post("/volunteers/register")
async def register_as_volunteer(
    request: RegisterVolunteerRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    注册成为志愿者
    """
    user_id = int(current_user['sub'])

    available_services = []
    for service in request.available_services:
        try:
            available_services.append(ServiceType(service))
        except ValueError:
            pass

    if not available_services:
        raise HTTPException(status_code=400, detail="请选择至少一种服务类型")

    volunteer = community_service.volunteer.register_volunteer(
        user_id,
        request.name,
        request.phone,
        request.skills,
        available_services,
        request.available_times,
        request.service_area
    )

    return {
        'success': True,
        'volunteer': volunteer.to_dict(),
        "message": "志愿者注册成功，感谢您的爱心"
    }


@router.get("/volunteers")
async def get_volunteers(
    service_type: Optional[str] = Query(None, description='服务类型'),
    service_area: Optional[str] = Query(None, description="服务区域"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取志愿者列表
    """
    type_filter = None
    if service_type:
        try:
            type_filter = ServiceType(service_type)
        except ValueError:
            pass

    volunteers = community_service.volunteer.get_volunteers(type_filter, service_area)

    return {
        'volunteers': [v.to_dict() for v in volunteers],
        'count': len(volunteers)
    }


@router.post("/services/request")
async def create_service_request(
    request: CreateServiceRequestRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建服务请求

    向志愿者请求帮助
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', "用户")

    try:
        service_type = ServiceType(request.service_type)
    except ValueError:
        valid_types = [t.value for t in ServiceType]
        raise HTTPException(status_code=400, detail=f"无效的服务类型，可选: {valid_types}")

    service_request = community_service.volunteer.create_service_request(
        user_id,
        user_name,
        service_type,
        request.description,
        request.preferred_time,
        request.location,
        request.phone
    )

    return {
        'success': True,
        'request': service_request.to_dict(),
        "message": "服务请求已发布，等待志愿者接单"
    }


@router.get("/services/my-requests")
async def get_my_service_requests(
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的服务请求
    """
    user_id = int(current_user['sub'])

    status_filter = None
    if status:
        try:
            status_filter = RequestStatus(status)
        except ValueError:
            pass

    requests = community_service.volunteer.get_user_requests(user_id, status_filter)

    return {
        'requests': [r.to_dict() for r in requests],
        'count': len(requests)
    }


@router.get("/services/pending")
async def get_pending_requests(
    service_type: Optional[str] = Query(None, description="服务类型"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取待接单的服务请求

    志愿者查看可接单的请求
    """
    type_filter = None
    if service_type:
        try:
            type_filter = ServiceType(service_type)
        except ValueError:
            pass

    requests = community_service.volunteer.get_pending_requests(type_filter)

    return {
        'requests': [r.to_dict() for r in requests],
        'count': len(requests)
    }


@router.post("/services/{request_id}/accept")
async def accept_service_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    接受服务请求

    志愿者接单
    """
    user_id = int(current_user['sub'])
    volunteer_id = f"vol_{user_id}"

    success = community_service.volunteer.accept_request(request_id, volunteer_id)

    if not success:
        raise HTTPException(status_code=400, detail='无法接单，请确认您已注册为志愿者')

    return {
        'success': True,
        "message": "接单成功，请及时联系服务对象"
    }


@router.post("/services/{request_id}/complete")
async def complete_service_request(
    request_id: str,
    service_hours: float = Query(..., ge=0.5, description="服务时长(小时)"),
    current_user: dict = Depends(get_current_user)
):
    """
    完成服务

    志愿者确认服务完成
    """
    user_id = int(current_user['sub'])
    volunteer_id = f"vol_{user_id}"

    success = community_service.volunteer.complete_request(
        request_id, volunteer_id, service_hours
    )

    if not success:
        raise HTTPException(status_code=400, detail='无法完成，请确认是您接的单')

    return {
        'success': True,
        "message": "服务已完成，感谢您的付出"
    }


@router.post("/services/{request_id}/rate")
async def rate_service(
    request_id: str,
    request: RateServiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    评价服务
    """
    user_id = int(current_user['sub'])

    success = community_service.volunteer.rate_service(
        request_id, user_id, request.rating, request.feedback
    )

    if not success:
        raise HTTPException(status_code=400, detail='无法评价')

    return {
        'success': True,
        'message': "感谢您的评价"
    }


@router.get("/services/types")
async def get_service_types(current_user: dict = Depends(get_current_user)):
    """
    获取服务类型列表
    """
    types = [{'value': t.value, 'label': t.value} for t in ServiceType]

    return {'types': types}


# ==================== 邻里互助API ====================

@router.post("/neighbor/posts")
async def create_neighbor_post(
    request: CreateNeighborPostRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发布邻里帖子
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', '邻居')

    post = community_service.neighbor.create_post(
        user_id,
        user_name,
        request.post_type,
        request.title,
        request.content,
        request.images,
        request.location,
        request.contact_phone
    )

    return {
        'success': True,
        'post': post.to_dict(),
        'message': "帖子发布成功"
    }


@router.get("/neighbor/posts")
async def get_neighbor_posts(
    post_type: Optional[str] = Query(None, description='帖子类型'),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取邻里帖子列表
    """
    posts = community_service.neighbor.get_posts(post_type, resolved, limit)

    return {
        'posts': [p.to_dict() for p in posts],
        'count': len(posts)
    }


@router.get("/neighbor/posts/{post_id}")
async def get_neighbor_post_detail(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取帖子详情
    """
    post = community_service.neighbor.posts.get(post_id)

    if not post:
        raise HTTPException(status_code=404, detail='帖子不存在')

    # 增加浏览量
    post.view_count += 1

    # 获取回复
    replies = community_service.neighbor.get_post_replies(post_id)

    return {
        'post': post.to_dict(),
        "replies": [r.to_dict() for r in replies]
    }


@router.post("/neighbor/posts/{post_id}/reply")
async def add_post_reply(
    post_id: str,
    request: AddReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    回复帖子
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', '邻居')

    reply = community_service.neighbor.add_reply(
        post_id, user_id, user_name, request.content
    )

    if not reply:
        raise HTTPException(status_code=404, detail='帖子不存在')

    return {
        'success': True,
        'reply': reply.to_dict(),
        'message': "回复成功"
    }


@router.post("/neighbor/posts/{post_id}/resolve")
async def resolve_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    标记帖子已解决
    """
    user_id = int(current_user['sub'])

    success = community_service.neighbor.mark_resolved(post_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail="无法标记，请确认是您发布的帖子")

    return {
        'success': True,
        'message': '已标记为已解决'
    }


# ==================== 社区资源API ====================

@router.get('/resources')
async def get_community_resources(
    category: Optional[str] = Query(None, description="资源分类"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取社区资源

    查看周边便民服务资源
    """
    resources = community_service.resource.get_resources(category)

    return {
        'resources': [r.to_dict() for r in resources],
        'count': len(resources)
    }


@router.get("/resources/search")
async def search_resources(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    """
    搜索社区资源
    """
    resources = community_service.resource.search_resources(keyword)

    return {
        'resources': [r.to_dict() for r in resources],
        'count': len(resources)
    }


@router.get("/resources/categories")
async def get_resource_categories(current_user: dict = Depends(get_current_user)):
    """
    获取资源分类
    """
    categories = [
        {'value': 'medical', 'label': '医疗健康'},
        {'value': 'shopping', 'label': '购物超市'},
        {'value': 'service', 'label': '便民服务'},
        {'value': 'recreation', 'label': '文化娱乐'},
        {'value': 'government', 'label': '政务服务'}
    ]

    return {'categories': categories}


# ==================== 社区仪表板API ====================

@router.get("/dashboard")
async def get_community_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取社区服务仪表板

    综合展示社区服务信息
    """
    user_id = int(current_user['sub'])

    overview = community_service.get_community_overview(user_id)

    return overview


@router.get("/overview")
async def get_community_overview(current_user: dict = Depends(get_current_user)):
    """
    获取社区概览
    """
    user_id = int(current_user['sub'])

    overview = community_service.get_community_overview(user_id)

    return overview
