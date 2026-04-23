"""
社交功能API
提供朋友圈、活动、好友、健康打卡等社交功能接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.social_service import (
    social_service,
    social_recommendation,
    PostType,
    ActivityType,
    ActivityStatus
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/social", tags=["社交功能"])


# ==================== 请求/响应模型 ====================

class CreatePostRequest(BaseModel):
    """发布动态请求"""
    content: str = Field(..., min_length=1, max_length=2000, description='动态内容')
    post_type: str = Field(default="text", description="类型: text/image/voice/health")
    images: Optional[List[str]] = Field(default=None, description='图片URL列表')
    voice_url: Optional[str] = Field(default=None, description='语音URL')
    voice_duration: int = Field(default=0, description='语音时长（秒）')
    location: Optional[str] = Field(default=None, description='位置')
    tags: Optional[List[str]] = Field(default=None, description='标签')
    is_public: bool = Field(default=True, description="是否公开")


class CommentRequest(BaseModel):
    """评论请求"""
    content: str = Field(..., min_length=1, max_length=500, description="评论内容")


class AddFriendRequest(BaseModel):
    """添加好友请求"""
    friend_id: int = Field(..., description='好友用户ID')
    friend_name: str = Field(..., description="好友名称")
    nickname: Optional[str] = Field(default="", description="备注名")


class CreateActivityRequest(BaseModel):
    """创建活动请求"""
    title: str = Field(..., min_length=1, max_length=100, description='活动标题')
    description: str = Field(..., min_length=1, max_length=2000, description="活动描述")
    activity_type: str = Field(..., description="类型: exercise/culture/social/learning/entertainment/volunteer")
    location: str = Field(..., description='活动地点')
    start_time: str = Field(..., description='开始时间 ISO格式')
    end_time: str = Field(..., description='结束时间 ISO格式')
    max_participants: int = Field(default=0, ge=0, description="最大人数，0不限")
    requirements: str = Field(default="", description='参与要求')
    fee: float = Field(default=0, ge=0, description='费用')
    tags: Optional[List[str]] = Field(default=None, description="标签")


class CheckInRequest(BaseModel):
    """健康打卡请求"""
    checkin_type: str = Field(..., description="类型: exercise/diet/medication/sleep")
    content: str = Field(..., min_length=1, max_length=500, description="打卡内容")


class PostResponse(BaseModel):
    """动态响应"""
    post_id: str
    user_id: int
    user_name: str
    post_type: str
    content: str
    images: List[str]
    voice_url: Optional[str]
    voice_duration: int
    location: Optional[str]
    created_at: str
    like_count: int
    comment_count: int
    is_public: bool
    tags: List[str]


class ActivityResponse(BaseModel):
    """活动响应"""
    activity_id: str
    title: str
    description: str
    activity_type: str
    organizer_id: int
    organizer_name: str
    location: str
    start_time: str
    end_time: str
    max_participants: int
    participant_count: int
    is_full: bool
    status: str
    tags: List[str]
    requirements: str
    fee: float


# ==================== 动态API ====================

@router.post("/posts", response_model=PostResponse)
async def create_post(
    request: CreatePostRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    发布动态

    支持的动态类型:
    - text: 纯文字
    - image: 图片动态
    - voice: 语音动态
    - health: 健康打卡分享
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', f'用户{user_id}')

    # 验证动态类型
    try:
        post_type = PostType(request.post_type)
    except ValueError:
        valid_types = [t.value for t in PostType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的动态类型，可选: {valid_types}"
        )

    post = social_service.create_post(
        user_id=user_id,
        user_name=user_name,
        content=request.content,
        post_type=post_type,
        images=request.images,
        voice_url=request.voice_url,
        voice_duration=request.voice_duration,
        location=request.location,
        tags=request.tags,
        is_public=request.is_public
    )

    return PostResponse(**post.to_dict())


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除动态
    """
    user_id = int(current_user['sub'])
    success = social_service.delete_post(post_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='动态不存在或无权删除')

    return {'success': True, 'message': "动态已删除"}


@router.get("/posts/{post_id}")
async def get_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取动态详情
    """
    post = social_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail='动态不存在')

    user_id = int(current_user['sub'])
    post_dict = post.to_dict()
    post_dict['is_liked'] = user_id in post.likes
    post_dict["comments"] = post.comments

    return post_dict


@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    点赞动态
    """
    user_id = int(current_user['sub'])
    success = social_service.like_post(post_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='动态不存在')

    return {'success': True, 'message': "已点赞"}


@router.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    取消点赞
    """
    user_id = int(current_user['sub'])
    success = social_service.unlike_post(post_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='动态不存在')

    return {'success': True, 'message': "已取消点赞"}


@router.post("/posts/{post_id}/comments")
async def comment_post(
    post_id: str,
    request: CommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    评论动态
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', f'用户{user_id}')

    comment = social_service.comment_post(
        post_id=post_id,
        user_id=user_id,
        user_name=user_name,
        content=request.content
    )

    if not comment:
        raise HTTPException(status_code=404, detail='动态不存在')

    return {'success': True, 'comment': comment}


@router.get("/feed")
async def get_feed(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取动态流（好友+自己的动态）
    """
    user_id = int(current_user['sub'])
    posts = social_service.get_feed(user_id, limit)

    feed = []
    for post in posts:
        post_dict = post.to_dict()
        post_dict['is_liked'] = user_id in post.likes
        feed.append(post_dict)

    return {'posts': feed, 'count': len(feed)}


@router.get("/posts/user/{target_user_id}")
async def get_user_posts(
    target_user_id: int,
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定用户的动态
    """
    posts = social_service.get_user_posts(target_user_id, limit)

    user_id = int(current_user['sub'])
    result = []
    for post in posts:
        # 非公开动态只有自己可见
        if not post.is_public and post.user_id != user_id:
            continue
        post_dict = post.to_dict()
        post_dict['is_liked'] = user_id in post.likes
        result.append(post_dict)

    return {'posts': result, 'count': len(result)}


# ==================== 好友API ====================

@router.get("/friends")
async def get_friends(current_user: dict = Depends(get_current_user)):
    """
    获取好友列表
    """
    user_id = int(current_user['sub'])
    friends = social_service.get_friends(user_id)

    return {
        'friends': [f.to_dict() for f in friends],
        'count': len(friends)
    }


@router.post("/friends")
async def add_friend(
    request: AddFriendRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加好友
    """
    user_id = int(current_user['sub'])

    if request.friend_id == user_id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    friend = social_service.add_friend(
        user_id=user_id,
        friend_id=request.friend_id,
        friend_name=request.friend_name,
        nickname=request.nickname or ""
    )

    return {'success': True, 'friend': friend.to_dict()}


@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    删除好友
    """
    user_id = int(current_user['sub'])
    success = social_service.remove_friend(user_id, friend_id)

    if not success:
        raise HTTPException(status_code=404, detail='好友不存在')

    return {'success': True, 'message': "已删除好友"}


@router.put("/friends/{friend_id}/favorite")
async def set_favorite_friend(
    friend_id: int,
    is_favorite: bool = Query(True),
    current_user: dict = Depends(get_current_user)
):
    """
    设置/取消特别关注
    """
    user_id = int(current_user['sub'])
    success = social_service.set_favorite_friend(user_id, friend_id, is_favorite)

    if not success:
        raise HTTPException(status_code=404, detail='好友不存在')

    return {
        'success': True,
        'message': '已设为特别关注' if is_favorite else "已取消特别关注"
    }


# ==================== 活动API ====================

@router.get("/activities")
async def get_activities(
    activity_type: Optional[str] = Query(None, description='活动类型过滤'),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取活动列表
    """
    type_filter = None
    if activity_type:
        try:
            type_filter = ActivityType(activity_type)
        except ValueError:
            pass

    status_filter = None
    if status:
        try:
            status_filter = ActivityStatus(status)
        except ValueError:
            pass

    activities = social_service.get_activities(
        activity_type=type_filter,
        status=status_filter,
        limit=limit
    )

    return {
        'activities': [a.to_dict() for a in activities],
        'count': len(activities)
    }


@router.post("/activities", response_model=ActivityResponse)
async def create_activity(
    request: CreateActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建活动
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', f'用户{user_id}')

    # 验证活动类型
    try:
        activity_type = ActivityType(request.activity_type)
    except ValueError:
        valid_types = [t.value for t in ActivityType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的活动类型，可选: {valid_types}"
        )

    # 解析时间
    from datetime import datetime
    try:
        start_time = datetime.fromisoformat(request.start_time)
        end_time = datetime.fromisoformat(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误，请使用ISO格式")

    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

    activity = social_service.create_activity(
        organizer_id=user_id,
        organizer_name=user_name,
        title=request.title,
        description=request.description,
        activity_type=activity_type,
        location=request.location,
        start_time=start_time,
        end_time=end_time,
        max_participants=request.max_participants,
        requirements=request.requirements,
        fee=request.fee,
        tags=request.tags
    )

    return ActivityResponse(**activity.to_dict())


@router.get("/activities/{activity_id}")
async def get_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取活动详情
    """
    activity = social_service.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail='活动不存在')

    user_id = int(current_user['sub'])
    result = activity.to_dict()
    result["is_joined"] = user_id in activity.participants
    result["is_organizer"] = user_id == activity.organizer_id

    return result


@router.post("/activities/{activity_id}/join")
async def join_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    报名参加活动
    """
    user_id = int(current_user['sub'])
    result = social_service.join_activity(activity_id, user_id)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/activities/{activity_id}/leave")
async def leave_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    退出活动
    """
    user_id = int(current_user['sub'])
    success = social_service.leave_activity(activity_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='活动不存在或未参加')

    return {'success': True, 'message': "已退出活动"}


@router.get("/activities/my/list")
async def get_my_activities(current_user: dict = Depends(get_current_user)):
    """
    获取我参与的活动
    """
    user_id = int(current_user['sub'])
    activities = social_service.get_user_activities(user_id)

    result = []
    for activity in activities:
        act_dict = activity.to_dict()
        act_dict["is_organizer"] = activity.organizer_id == user_id
        result.append(act_dict)

    return {'activities': result, 'count': len(result)}


# ==================== 健康打卡API ====================

@router.post("/checkin")
async def create_checkin(
    request: CheckInRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    健康打卡

    打卡类型:
    - exercise: 运动打卡
    - diet: 饮食打卡
    - medication: 服药打卡
    - sleep: 睡眠打卡
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', f'用户{user_id}')

    valid_types = ['exercise', 'diet', 'medication', "sleep"]
    if request.checkin_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的打卡类型，可选: {valid_types}"
        )

    checkin = social_service.create_checkin(
        user_id=user_id,
        user_name=user_name,
        checkin_type=request.checkin_type,
        content=request.content
    )

    return {
        'success': True,
        'checkin': checkin.to_dict(),
        "message": f"打卡成功！已连续打卡{checkin.streak_days}天"
    }


@router.get("/checkin/history")
async def get_checkin_history(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    获取打卡历史
    """
    user_id = int(current_user['sub'])
    checkins = social_service.get_user_checkins(user_id, days)

    return {
        'checkins': [c.to_dict() for c in checkins],
        'count': len(checkins)
    }


@router.get("/checkin/leaderboard")
async def get_checkin_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取打卡排行榜
    """
    leaderboard = social_service.get_checkin_leaderboard(limit)

    user_id = int(current_user['sub'])
    my_rank = None
    for i, item in enumerate(leaderboard):
        if item['user_id'] == user_id:
            my_rank = i + 1
            break

    return {
        "leaderboard": leaderboard,
        'my_rank': my_rank
    }


# ==================== 统计与推荐 ====================

@router.get("/stats")
async def get_social_stats(current_user: dict = Depends(get_current_user)):
    """
    获取社交统计
    """
    user_id = int(current_user['sub'])
    stats = social_service.get_user_social_stats(user_id)
    return stats


@router.get("/recommendations/friends")
async def get_friend_recommendations(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """
    获取好友推荐
    """
    user_id = int(current_user['sub'])
    recommendations = social_recommendation.recommend_friends(user_id, limit)
    return {"recommendations": recommendations}


@router.get("/recommendations/activities")
async def get_activity_recommendations(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """
    获取活动推荐
    """
    user_id = int(current_user['sub'])
    activities = social_recommendation.recommend_activities(user_id, limit)

    return {
        "recommendations": [a.to_dict() for a in activities]
    }
