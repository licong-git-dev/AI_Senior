"""
回忆录API
提供照片相册、人生故事、时光记忆、家族传承等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date

from app.services.memory_service import (
    memory_service,
    AlbumType,
    StoryCategory,
    MemoryMood
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/memory", tags=["回忆录"])


# ==================== 请求模型 ====================

class CreateAlbumRequest(BaseModel):
    """创建相册请求"""
    name: str = Field(..., max_length=100, description='相册名称')
    album_type: str = Field('general', description='相册类型')
    description: Optional[str] = Field(None, max_length=500, description="相册描述")


class AddPhotoRequest(BaseModel):
    """添加照片请求"""
    album_id: str = Field(..., description='相册ID')
    url: str = Field(..., description='照片URL')
    thumbnail_url: Optional[str] = Field(None, description='缩略图URL')
    title: Optional[str] = Field(None, max_length=100, description='照片标题')
    description: Optional[str] = Field(None, max_length=500, description='照片描述')
    taken_date: Optional[date] = Field(None, description='拍摄日期')
    location: Optional[str] = Field(None, max_length=100, description='拍摄地点')
    people_tags: Optional[List[str]] = Field(None, description="照片中的人")


class ShareAlbumRequest(BaseModel):
    """共享相册请求"""
    share_with: List[int] = Field(..., description="共享给的用户ID列表")


class CreateStoryRequest(BaseModel):
    """创建故事请求"""
    title: str = Field(..., max_length=200, description='故事标题')
    content: str = Field(..., min_length=10, description='故事内容')
    category: str = Field(..., description='故事分类')
    mood: str = Field('nostalgic', description='情绪基调')
    time_period: Optional[str] = Field(None, description='时间段')
    specific_date: Optional[date] = Field(None, description='具体日期')
    location: Optional[str] = Field(None, description='地点')
    people_involved: Optional[List[str]] = Field(None, description='相关人物')
    related_photos: Optional[List[str]] = Field(None, description='相关照片ID')
    audio_url: Optional[str] = Field(None, description='语音版本URL')
    tags: Optional[List[str]] = Field(None, description="标签")


class UpdateStoryRequest(BaseModel):
    """更新故事请求"""
    title: Optional[str] = Field(None, max_length=200, description='故事标题')
    content: Optional[str] = Field(None, min_length=10, description='故事内容')
    time_period: Optional[str] = Field(None, description='时间段')
    location: Optional[str] = Field(None, description='地点')
    people_involved: Optional[List[str]] = Field(None, description='相关人物')
    related_photos: Optional[List[str]] = Field(None, description='相关照片ID')
    tags: Optional[List[str]] = Field(None, description="标签")


class AddCommentRequest(BaseModel):
    """添加评论请求"""
    content: str = Field(..., min_length=1, max_length=500, description="评论内容")


class AddTimelineEventRequest(BaseModel):
    """添加时间线事件请求"""
    title: str = Field(..., max_length=100, description='事件标题')
    event_date: date = Field(..., description='事件日期')
    description: Optional[str] = Field(None, max_length=500, description='事件描述')
    event_type: str = Field("milestone", description="事件类型: milestone/memory/achievement")
    related_stories: Optional[List[str]] = Field(None, description='相关故事ID')
    related_photos: Optional[List[str]] = Field(None, description='相关照片ID')
    icon: Optional[str] = Field(None, description="图标")


class AddFamilyMemberRequest(BaseModel):
    """添加家族成员请求"""
    name: str = Field(..., max_length=50, description='姓名')
    relationship: str = Field(..., max_length=50, description='关系')
    birth_year: Optional[int] = Field(None, ge=1800, le=2100, description='出生年份')
    death_year: Optional[int] = Field(None, ge=1800, le=2100, description='去世年份')
    birthplace: Optional[str] = Field(None, max_length=100, description='出生地')
    occupation: Optional[str] = Field(None, max_length=100, description='职业')
    bio: Optional[str] = Field(None, max_length=1000, description='简介')
    photo_url: Optional[str] = Field(None, description='照片URL')
    parent_id: Optional[str] = Field(None, description='父节点ID')
    generation: int = Field(0, description="代数")


class AddTraditionRequest(BaseModel):
    """添加家族传统请求"""
    name: str = Field(..., max_length=100, description='传统名称')
    description: str = Field(..., max_length=1000, description='传统描述')
    origin_story: Optional[str] = Field(None, description='来源故事')
    related_holiday: Optional[str] = Field(None, description='相关节日')
    photos: Optional[List[str]] = Field(None, description='相关照片')


# ==================== 照片相册API ====================

@router.post("/albums")
async def create_album(
    request: CreateAlbumRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建相册

    创建新的照片相册
    """
    user_id = int(current_user['sub'])

    try:
        album_type = AlbumType(request.album_type)
    except ValueError:
        valid_types = [t.value for t in AlbumType]
        raise HTTPException(status_code=400, detail=f"无效的相册类型，可选: {valid_types}")

    album = memory_service.photo_album.create_album(
        user_id,
        request.name,
        album_type,
        request.description
    )

    return {
        'success': True,
        'album': album.to_dict(),
        "message": f"相册 {request.name} 创建成功"
    }


@router.get("/albums")
async def get_albums(
    album_type: Optional[str] = Query(None, description="相册类型筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取相册列表
    """
    user_id = int(current_user['sub'])

    type_filter = None
    if album_type:
        try:
            type_filter = AlbumType(album_type)
        except ValueError:
            pass

    albums = memory_service.photo_album.get_user_albums(user_id, type_filter)

    return {
        'albums': [a.to_dict() for a in albums],
        'count': len(albums)
    }


@router.get("/albums/shared")
async def get_shared_albums(current_user: dict = Depends(get_current_user)):
    """
    获取共享给我的相册
    """
    user_id = int(current_user['sub'])

    albums = memory_service.photo_album.get_shared_albums(user_id)

    return {
        'albums': [a.to_dict() for a in albums],
        'count': len(albums)
    }


@router.post("/albums/{album_id}/share")
async def share_album(
    album_id: str,
    request: ShareAlbumRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    共享相册给家人
    """
    user_id = int(current_user['sub'])

    success = memory_service.photo_album.share_album(album_id, user_id, request.share_with)

    if not success:
        raise HTTPException(status_code=404, detail='相册不存在')

    return {
        'success': True,
        'message': '相册已共享给家人'
    }


@router.post("/photos")
async def add_photo(
    request: AddPhotoRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加照片

    向相册添加新照片
    """
    user_id = int(current_user['sub'])

    photo = memory_service.photo_album.add_photo(
        user_id,
        request.album_id,
        request.url,
        request.thumbnail_url,
        request.title,
        request.description,
        request.taken_date,
        request.location,
        request.people_tags
    )

    if not photo:
        raise HTTPException(status_code=404, detail='相册不存在')

    return {
        'success': True,
        'photo': photo.to_dict(),
        'message': "照片添加成功"
    }


@router.get("/albums/{album_id}/photos")
async def get_album_photos(
    album_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    获取相册照片
    """
    user_id = int(current_user['sub'])

    photos, total = memory_service.photo_album.get_album_photos(
        album_id, user_id, limit, offset
    )

    return {
        'photos': [p.to_dict() for p in photos],
        'total': total,
        'limit': limit,
        'offset': offset
    }


@router.post("/photos/{photo_id}/favorite")
async def toggle_photo_favorite(
    photo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    切换照片收藏状态
    """
    user_id = int(current_user['sub'])

    success = memory_service.photo_album.toggle_favorite(photo_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='照片不存在')

    return {
        'success': True,
        'message': "收藏状态已更新"
    }


@router.get("/photos/favorites")
async def get_favorite_photos(current_user: dict = Depends(get_current_user)):
    """
    获取收藏的照片
    """
    user_id = int(current_user['sub'])

    photos = memory_service.photo_album.get_favorites(user_id)

    return {
        'photos': [p.to_dict() for p in photos],
        'count': len(photos)
    }


@router.get("/photos/search")
async def search_photos(
    keyword: Optional[str] = Query(None, description='关键词'),
    person: Optional[str] = Query(None, description='人物'),
    location: Optional[str] = Query(None, description='地点'),
    year: Optional[int] = Query(None, description="年份"),
    current_user: dict = Depends(get_current_user)
):
    """
    搜索照片
    """
    user_id = int(current_user['sub'])

    photos = memory_service.photo_album.search_photos(
        user_id, keyword, person, location, year
    )

    return {
        'photos': [p.to_dict() for p in photos],
        'count': len(photos)
    }


# ==================== 人生故事API ====================

@router.post("/stories")
async def create_story(
    request: CreateStoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建人生故事

    记录您的人生经历和回忆
    """
    user_id = int(current_user['sub'])

    try:
        category = StoryCategory(request.category)
    except ValueError:
        valid_categories = [c.value for c in StoryCategory]
        raise HTTPException(status_code=400, detail=f'无效的故事分类，可选: {valid_categories}')

    try:
        mood = MemoryMood(request.mood)
    except ValueError:
        valid_moods = [m.value for m in MemoryMood]
        raise HTTPException(status_code=400, detail=f'无效的情绪，可选: {valid_moods}')

    story = memory_service.life_story.create_story(
        user_id,
        request.title,
        request.content,
        category,
        mood,
        request.time_period,
        request.specific_date,
        request.location,
        request.people_involved,
        request.related_photos,
        request.audio_url,
        request.tags
    )

    return {
        'success': True,
        'story': story.to_dict(),
        "message": "故事创建成功，珍贵的回忆已保存"
    }


@router.put("/stories/{story_id}")
async def update_story(
    story_id: str,
    request: UpdateStoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    更新故事
    """
    user_id = int(current_user['sub'])

    story = memory_service.life_story.update_story(
        story_id,
        user_id,
        request.title,
        request.content,
        request.time_period,
        request.location,
        request.people_involved,
        request.related_photos,
        request.tags
    )

    if not story:
        raise HTTPException(status_code=404, detail='故事不存在')

    return {
        'success': True,
        'story': story.to_dict(),
        'message': '故事已更新'
    }


@router.get('/stories')
async def get_stories(
    category: Optional[str] = Query(None, description='故事分类'),
    published_only: bool = Query(False, description="仅显示已发布"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取故事列表
    """
    user_id = int(current_user['sub'])

    category_filter = None
    if category:
        try:
            category_filter = StoryCategory(category)
        except ValueError:
            pass

    stories = memory_service.life_story.get_user_stories(
        user_id, category_filter, published_only
    )

    return {
        'stories': [s.to_dict() for s in stories],
        'count': len(stories)
    }


@router.get("/stories/{story_id}")
async def get_story_detail(
    story_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取故事详情
    """
    story = memory_service.life_story.stories.get(story_id)

    if not story:
        raise HTTPException(status_code=404, detail='故事不存在')

    # 增加浏览次数
    story.view_count += 1

    # 获取评论
    comments = memory_service.life_story.get_story_comments(story_id)

    return {
        'story': story.to_dict(),
        "comments": [c.to_dict() for c in comments]
    }


@router.post("/stories/{story_id}/publish")
async def publish_story(
    story_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    发布故事给家人
    """
    user_id = int(current_user['sub'])

    success = memory_service.life_story.publish_story(story_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail='故事不存在')

    return {
        'success': True,
        'message': "故事已发布给家人"
    }


@router.post("/stories/{story_id}/like")
async def like_story(
    story_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    点赞故事
    """
    success = memory_service.life_story.like_story(story_id)

    if not success:
        raise HTTPException(status_code=404, detail='故事不存在')

    return {
        'success': True,
        'message': "点赞成功"
    }


@router.post("/stories/{story_id}/comments")
async def add_story_comment(
    story_id: str,
    request: AddCommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加故事评论
    """
    user_id = int(current_user['sub'])
    user_name = current_user.get('name', '家人')

    comment = memory_service.life_story.add_comment(
        story_id, user_id, user_name, request.content
    )

    if not comment:
        raise HTTPException(status_code=404, detail='故事不存在或未发布')

    return {
        'success': True,
        'comment': comment.to_dict(),
        'message': "评论发送成功"
    }


@router.get("/stories/prompts")
async def get_story_prompts(
    category: Optional[str] = Query(None, description="故事分类"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取写作提示

    获取帮助您回忆的问题提示
    """
    category_filter = None
    if category:
        try:
            category_filter = StoryCategory(category)
        except ValueError:
            pass

    prompts = memory_service.life_story.get_writing_prompts(category_filter)

    return {
        'prompts': prompts,
        'count': len(prompts),
        'tip': "选择一个问题，慢慢回忆，记录下您的故事"
    }


@router.get("/stories/search")
async def search_stories(
    keyword: Optional[str] = Query(None, description='关键词'),
    category: Optional[str] = Query(None, description='分类'),
    person: Optional[str] = Query(None, description="相关人物"),
    current_user: dict = Depends(get_current_user)
):
    """
    搜索故事
    """
    user_id = int(current_user['sub'])

    category_filter = None
    if category:
        try:
            category_filter = StoryCategory(category)
        except ValueError:
            pass

    stories = memory_service.life_story.search_stories(
        user_id, keyword, category_filter, person
    )

    return {
        'stories': [s.to_dict() for s in stories],
        'count': len(stories)
    }


# ==================== 时间线API ====================

@router.post("/timeline/events")
async def add_timeline_event(
    request: AddTimelineEventRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加时间线事件

    记录人生中的重要时刻
    """
    user_id = int(current_user['sub'])

    event = memory_service.timeline.add_event(
        user_id,
        request.title,
        request.event_date,
        request.description,
        request.event_type,
        request.related_stories,
        request.related_photos,
        request.icon
    )

    return {
        'success': True,
        'event': event.to_dict(),
        'message': '时间线事件已添加'
    }


@router.get('/timeline')
async def get_timeline(
    start_year: Optional[int] = Query(None, description='起始年份'),
    end_year: Optional[int] = Query(None, description="结束年份"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取时间线
    """
    user_id = int(current_user['sub'])

    events = memory_service.timeline.get_user_timeline(user_id, start_year, end_year)

    return {
        'events': [e.to_dict() for e in events],
        'count': len(events)
    }


@router.get("/timeline/by-decade")
async def get_timeline_by_decade(current_user: dict = Depends(get_current_user)):
    """
    按年代获取时间线
    """
    user_id = int(current_user['sub'])

    by_decade = memory_service.timeline.get_timeline_by_decade(user_id)

    return {
        'decades': {
            decade: [e.to_dict() for e in events]
            for decade, events in by_decade.items()
        }
    }


# ==================== 家族传承API ====================

@router.post("/family/members")
async def add_family_member(
    request: AddFamilyMemberRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加家族成员

    构建您的家谱
    """
    user_id = int(current_user['sub'])

    member = memory_service.family_legacy.add_family_member(
        user_id,
        request.name,
        request.relationship,
        request.birth_year,
        request.death_year,
        request.birthplace,
        request.occupation,
        request.bio,
        request.photo_url,
        request.parent_id,
        request.generation
    )

    return {
        'success': True,
        'member': member.to_dict(),
        'message': f"家族成员 {request.name} 已添加"
    }


@router.get("/family/tree")
async def get_family_tree(current_user: dict = Depends(get_current_user)):
    """
    获取家谱

    查看完整家族树
    """
    user_id = int(current_user['sub'])

    tree = memory_service.family_legacy.get_family_tree_structured(user_id)

    return tree


@router.get("/family/members")
async def get_family_members(current_user: dict = Depends(get_current_user)):
    """
    获取家族成员列表
    """
    user_id = int(current_user['sub'])

    members = memory_service.family_legacy.get_family_tree(user_id)

    return {
        'members': [m.to_dict() for m in members],
        'count': len(members)
    }


@router.post("/family/traditions")
async def add_family_tradition(
    request: AddTraditionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加家族传统

    记录您的家族传统习俗
    """
    user_id = int(current_user['sub'])

    tradition = memory_service.family_legacy.add_tradition(
        user_id,
        request.name,
        request.description,
        request.origin_story,
        request.related_holiday,
        request.photos
    )

    return {
        'success': True,
        'tradition': tradition.to_dict(),
        'message': f"家族传统 {request.name} 已记录"
    }


@router.get("/family/traditions")
async def get_family_traditions(current_user: dict = Depends(get_current_user)):
    """
    获取家族传统
    """
    user_id = int(current_user['sub'])

    traditions = memory_service.family_legacy.get_traditions(user_id)

    return {
        'traditions': [t.to_dict() for t in traditions],
        'count': len(traditions)
    }


# ==================== 回忆录仪表板API ====================

@router.get("/dashboard")
async def get_memory_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取回忆录仪表板

    综合展示回忆录各项数据
    """
    user_id = int(current_user['sub'])

    overview = memory_service.get_memory_overview(user_id)

    # 最近故事
    recent_stories = memory_service.life_story.get_user_stories(user_id)[:5]

    # 最近相册
    recent_albums = memory_service.photo_album.get_user_albums(user_id)[:5]

    # 写作提示
    prompts = memory_service.life_story.get_writing_prompts()[:3]

    return {
        "overview": overview,
        "recent_stories": [s.to_dict() for s in recent_stories],
        "recent_albums": [a.to_dict() for a in recent_albums],
        "writing_prompts": prompts,
        'encouragement': "记录您的故事，让珍贵的回忆永远流传"
    }


@router.get("/categories")
async def get_all_categories(current_user: dict = Depends(get_current_user)):
    """
    获取所有分类选项
    """
    return {
        'album_types': [{'value': t.value, 'label': t.value} for t in AlbumType],
        'story_categories': [{'value': c.value, 'label': c.value} for c in StoryCategory],
        'moods': [{'value': m.value, 'label': m.value} for m in MemoryMood]
    }
