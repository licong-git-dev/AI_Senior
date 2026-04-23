"""
API路由 - 情感记忆系统
实现用户画像管理、记忆提取存储、重要日期、人生故事等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, date
import json

from app.core.deps import get_db
from app.models.database import (
    UserProfile,
    UserMemory,
    ImportantDate,
    LifeStory,
    User,
    Conversation
)
from app.schemas.memory import (
    MemoryType,
    DateType,
    StoryCateogry,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserMemoryCreate,
    UserMemoryUpdate,
    UserMemoryResponse,
    ExtractMemoryRequest,
    RetrieveMemoryRequest,
    ImportantDateCreate,
    ImportantDateUpdate,
    ImportantDateResponse,
    LifeStoryCreate,
    LifeStoryUpdate,
    LifeStoryResponse,
    PersonalizationContext,
    GeneratePersonalizedResponseRequest
)

router = APIRouter(prefix="/api/memory", tags=["情感记忆"])


# ==================== 工具函数 ====================

def parse_json_field(value: Optional[str]) -> Optional[List]:
    """解析JSON字段"""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def serialize_json(value) -> str:
    """序列化为JSON"""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def profile_to_response(profile: UserProfile) -> dict:
    """将UserProfile转换为响应格式"""
    return {
        'id': profile.id,
        'user_id': profile.user_id,
        'nickname': profile.nickname,
        'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
        'zodiac': profile.zodiac,
        "constellation": profile.constellation,
        'hometown': profile.hometown,
        "current_city": profile.current_city,
        "family_info": parse_json_field(profile.family_info),
        'hobbies': parse_json_field(profile.hobbies),
        "favorite_music": parse_json_field(profile.favorite_music),
        "favorite_foods": parse_json_field(profile.favorite_foods),
        "disliked_foods": parse_json_field(profile.disliked_foods),
        "chronic_conditions": parse_json_field(profile.chronic_conditions),
        'allergies': parse_json_field(profile.allergies),
        "dietary_restrictions": parse_json_field(profile.dietary_restrictions),
        "personality_traits": parse_json_field(profile.personality_traits),
        "communication_style": profile.communication_style,
        "preferred_topics": parse_json_field(profile.preferred_topics),
        'ai_persona': profile.ai_persona,
        "response_speed": profile.response_speed,
        'verbosity': profile.verbosity,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat()
    }


# ==================== 用户画像 ====================

@router.post("/profile", response_model=dict)
def create_user_profile(
    request: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """创建用户画像"""
    # 检查用户是否存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已有画像
    existing = db.query(UserProfile).filter(UserProfile.user_id == request.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户画像已存在，请使用更新接口")

    profile = UserProfile(
        user_id=request.user_id,
        nickname=request.nickname,
        birth_date=request.birth_date,
        hometown=request.hometown,
        current_city=request.current_city
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        'success': True,
        'profile_id': profile.id,
        'message': "用户画像创建成功"
    }


@router.get("/profile/{user_id}", response_model=dict)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户画像"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        # 如果没有画像，返回基本信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail='用户不存在')
        return {
            'exists': False,
            'user_id': user_id,
            'user_name': user.name,
            'message': '用户画像尚未创建'
        }

    return {
        'exists': True,
        "profile": profile_to_response(profile)
    }


@router.put("/profile/{user_id}", response_model=dict)
def update_user_profile(
    user_id: int,
    request: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """更新用户画像"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        # 自动创建
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    update_data = request.model_dump(exclude_unset=True)

    # 处理JSON字段
    json_fields = [
        'family_info', 'hobbies', 'favorite_music', 'favorite_foods',
        'disliked_foods', 'chronic_conditions', 'allergies',
        'dietary_restrictions', 'personality_traits', 'preferred_topics'
    ]

    for key, value in update_data.items():
        if key in json_fields and value is not None:
            setattr(profile, key, serialize_json(value))
        elif key == 'communication_style' and value:
            setattr(profile, key, value.value if hasattr(value, 'value') else value)
        elif key == 'ai_persona' and value:
            setattr(profile, key, value.value if hasattr(value, 'value') else value)
        else:
            setattr(profile, key, value)

    db.commit()
    return {'success': True, 'message': '用户画像更新成功'}


# ==================== 用户记忆 ====================

@router.post("/memories", response_model=dict)
def create_memory(
    request: UserMemoryCreate,
    db: Session = Depends(get_db)
):
    """创建用户记忆"""
    memory = UserMemory(
        user_id=request.user_id,
        memory_type=request.memory_type.value,
        category=request.category,
        key=request.key,
        value=request.value,
        context=request.context,
        source_conversation_id=request.source_conversation_id,
        importance=request.importance,
        confidence=request.confidence,
        extracted_at=datetime.now()
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    return {
        'success': True,
        'memory_id': memory.id,
        'message': "记忆创建成功"
    }


@router.get("/memories/{user_id}", response_model=dict)
def get_memories(
    user_id: int,
    memory_type: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取用户记忆列表"""
    query = db.query(UserMemory).filter(
        UserMemory.user_id == user_id,
        UserMemory.is_active == True
    )

    if memory_type:
        query = query.filter(UserMemory.memory_type == memory_type)
    if category:
        query = query.filter(UserMemory.category == category)
    if keyword:
        query = query.filter(
            or_(
                UserMemory.key.contains(keyword),
                UserMemory.value.contains(keyword)
            )
        )

    memories = query.order_by(
        UserMemory.importance.desc(),
        UserMemory.reference_count.desc()
    ).limit(limit).all()

    return {
        'user_id': user_id,
        'memories': [
            {
                'id': m.id,
                "memory_type": m.memory_type,
                'category': m.category,
                'key': m.key,
                'value': m.value,
                'context': m.context,
                'importance': m.importance,
                'confidence': m.confidence,
                "reference_count": m.reference_count,
                "last_referenced_at": m.last_referenced_at.isoformat() if m.last_referenced_at else None,
                "is_verified": m.is_verified,
                "extracted_at": m.extracted_at.isoformat()
            }
            for m in memories
        ],
        'total': len(memories)
    }


@router.get("/memories/{user_id}/by-key/{key}", response_model=dict)
def get_memory_by_key(
    user_id: int,
    key: str,
    db: Session = Depends(get_db)
):
    """通过key获取特定记忆"""
    memory = db.query(UserMemory).filter(
        UserMemory.user_id == user_id,
        UserMemory.key == key,
        UserMemory.is_active == True
    ).first()

    if not memory:
        return {'found': False, 'key': key}

    # 更新引用计数
    memory.reference_count += 1
    memory.last_referenced_at = datetime.now()
    db.commit()

    return {
        'found': True,
        'memory': {
            "id": memory.id,
            "memory_type": memory.memory_type,
            'key': memory.key,
            'value': memory.value,
            'context': memory.context,
            'importance': memory.importance,
            'confidence': memory.confidence
        }
    }


@router.put("/memories/{memory_id}", response_model=dict)
def update_memory(
    memory_id: int,
    request: UserMemoryUpdate,
    db: Session = Depends(get_db)
):
    """更新用户记忆"""
    memory = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail='记忆不存在')

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(memory, key, value)

    db.commit()
    return {'success': True, 'message': "记忆更新成功"}


@router.delete("/memories/{memory_id}", response_model=dict)
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):
    """删除用户记忆（软删除）"""
    memory = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail='记忆不存在')

    memory.is_active = False
    db.commit()
    return {'success': True, 'message': "记忆已删除"}


@router.post("/memories/extract", response_model=dict)
def extract_memories_from_conversation(
    request: ExtractMemoryRequest,
    db: Session = Depends(get_db)
):
    """从对话中提取记忆（模拟AI提取）"""
    # 这里是简化的规则提取，实际应该调用AI服务
    extracted = []
    content = request.conversation_content.lower()

    # 简单的关键词匹配规则
    extraction_rules = [
        # 家人相关
        {'keywords': ['儿子', '女儿', '孙子', '孙女'], 'type': 'family', 'category': 'children'},
        {'keywords': ['老伴', '老公', '老婆', '爱人'], 'type': 'family', 'category': 'spouse'},
        # 喜好相关
        {'keywords': ['喜欢吃', '爱吃', '最爱'], 'type': 'preference', 'category': 'food'},
        {'keywords': ['喜欢听', '爱听', '想听'], 'type': 'preference', 'category': 'music'},
        # 健康相关
        {'keywords': ['高血压', '糖尿病', '心脏病'], 'type': 'health', 'category': 'chronic'},
        # 地点相关
        {'keywords': ['老家', '家乡', '出生'], 'type': 'event', 'category': 'hometown'},
    ]

    for rule in extraction_rules:
        for keyword in rule['keywords']:
            if keyword in content:
                # 提取包含关键词的句子作为记忆
                memory = UserMemory(
                    user_id=request.user_id,
                    memory_type=rule['type'],
                    category=rule['category'],
                    key=f'{rule['category']}_{len(extracted)}',
                    value=f'用户提到了{keyword}相关的内容',
                    context=request.conversation_content[:200],
                    source_conversation_id=request.conversation_id,
                    importance=5,
                    confidence=0.7,
                    extracted_at=datetime.now()
                )
                db.add(memory)
                extracted.append({
                    'type': rule['type'],
                    'category': rule["category"],
                    "keyword_matched": keyword
                })
                break  # 每个规则只匹配一次

    db.commit()

    return {
        "success": True,
        "extracted_count": len(extracted),
        "extracted_memories": extracted,
        'message': f"从对话中提取了{len(extracted)}条记忆"
    }


@router.post("/memories/retrieve", response_model=dict)
def retrieve_relevant_memories(
    request: RetrieveMemoryRequest,
    db: Session = Depends(get_db)
):
    """检索相关记忆"""
    query = db.query(UserMemory).filter(
        UserMemory.user_id == request.user_id,
        UserMemory.is_active == True
    )

    if request.memory_types:
        type_values = [t.value for t in request.memory_types]
        query = query.filter(UserMemory.memory_type.in_(type_values))

    if request.keywords:
        keyword_filters = []
        for kw in request.keywords:
            keyword_filters.append(UserMemory.key.contains(kw))
            keyword_filters.append(UserMemory.value.contains(kw))
        query = query.filter(or_(*keyword_filters))

    memories = query.order_by(
        UserMemory.importance.desc(),
        UserMemory.confidence.desc()
    ).limit(request.limit).all()

    # 更新引用计数
    for m in memories:
        m.reference_count += 1
        m.last_referenced_at = datetime.now()
    db.commit()

    return {
        'user_id': request.user_id,
        'memories': [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                'key': m.key,
                'value': m.value,
                'importance': m.importance,
                'confidence': m.confidence
            }
            for m in memories
        ],
        'total': len(memories)
    }


# ==================== 重要日期 ====================

@router.post("/important-dates", response_model=dict)
def create_important_date(
    request: ImportantDateCreate,
    db: Session = Depends(get_db)
):
    """创建重要日期"""
    important_date = ImportantDate(
        user_id=request.user_id,
        date_type=request.date_type.value,
        title=request.title,
        description=request.description,
        month=request.month,
        day=request.day,
        is_lunar=request.is_lunar,
        year=request.year,
        reminder_days_before=request.reminder_days_before,
        reminder_enabled=request.reminder_enabled,
        related_person=request.related_person
    )
    db.add(important_date)
    db.commit()
    db.refresh(important_date)

    return {
        'success': True,
        'date_id': important_date.id,
        'message': "重要日期创建成功"
    }


@router.get("/important-dates/{user_id}", response_model=dict)
def get_important_dates(
    user_id: int,
    date_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取重要日期列表"""
    query = db.query(ImportantDate).filter(
        ImportantDate.user_id == user_id,
        ImportantDate.is_active == True
    )

    if date_type:
        query = query.filter(ImportantDate.date_type == date_type)

    dates = query.order_by(ImportantDate.month, ImportantDate.day).all()

    return {
        'user_id': user_id,
        'dates': [
            {
                'id': d.id,
                'date_type': d.date_type,
                'title': d.title,
                "description": d.description,
                'month': d.month,
                'day': d.day,
                'is_lunar': d.is_lunar,
                'year': d.year,
                "reminder_days_before": d.reminder_days_before,
                "reminder_enabled": d.reminder_enabled,
                "related_person": d.related_person
            }
            for d in dates
        ],
        'total': len(dates)
    }


@router.get("/important-dates/{user_id}/upcoming", response_model=dict)
def get_upcoming_dates(
    user_id: int,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """获取即将到来的重要日期"""
    today = date.today()
    current_month = today.month
    current_day = today.day

    dates = db.query(ImportantDate).filter(
        ImportantDate.user_id == user_id,
        ImportantDate.is_active == True,
        ImportantDate.is_lunar == False  # 暂时只处理公历
    ).all()

    upcoming = []
    today_dates = []

    for d in dates:
        # 计算今年和明年的日期
        try:
            this_year_date = date(today.year, d.month, d.day)
            next_year_date = date(today.year + 1, d.month, d.day)
        except ValueError:
            continue  # 跳过无效日期（如2月30日）

        # 判断是否在范围内
        target_date = this_year_date if this_year_date >= today else next_year_date
        days_until = (target_date - today).days

        if days_until == 0:
            today_dates.append({
                'id': d.id,
                'title': d.title,
                "date_type": d.date_type,
                "related_person": d.related_person,
                'date': target_date.isoformat()
            })
        elif 0 < days_until <= days:
            upcoming.append({
                'id': d.id,
                'title': d.title,
                'date_type': d.date_type,
                "related_person": d.related_person,
                'date': target_date.isoformat(),
                'days_until': days_until
            })

    # 按距离天数排序
    upcoming.sort(key=lambda x: x['days_until'])

    return {
        'user_id': user_id,
        "today": today.isoformat(),
        "today_dates": today_dates,
        "upcoming_dates": upcoming,
        "total_upcoming": len(upcoming)
    }


@router.put("/important-dates/{date_id}", response_model=dict)
def update_important_date(
    date_id: int,
    request: ImportantDateUpdate,
    db: Session = Depends(get_db)
):
    """更新重要日期"""
    important_date = db.query(ImportantDate).filter(ImportantDate.id == date_id).first()
    if not important_date:
        raise HTTPException(status_code=404, detail='重要日期不存在')

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(important_date, key, value)

    db.commit()
    return {'success': True, 'message': "更新成功"}


@router.delete("/important-dates/{date_id}", response_model=dict)
def delete_important_date(
    date_id: int,
    db: Session = Depends(get_db)
):
    """删除重要日期"""
    important_date = db.query(ImportantDate).filter(ImportantDate.id == date_id).first()
    if not important_date:
        raise HTTPException(status_code=404, detail='重要日期不存在')

    important_date.is_active = False
    db.commit()
    return {'success': True, 'message': "删除成功"}


# ==================== 人生故事 ====================

@router.post("/life-stories", response_model=dict)
def create_life_story(
    request: LifeStoryCreate,
    db: Session = Depends(get_db)
):
    """创建人生故事"""
    story = LifeStory(
        user_id=request.user_id,
        title=request.title,
        content=request.content,
        category=request.category.value if request.category else None,
        era=request.era,
        location=request.location,
        related_people=serialize_json(request.related_people),
        audio_url=request.audio_url,
        photo_urls=serialize_json(request.photo_urls),
        emotion_tags=serialize_json(request.emotion_tags),
        source=request.source,
        recorded_at=request.recorded_at or datetime.now()
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    return {
        'success': True,
        'story_id': story.id,
        'message': "人生故事创建成功"
    }


@router.get("/life-stories/{user_id}", response_model=dict)
def get_life_stories(
    user_id: int,
    category: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """获取人生故事列表"""
    query = db.query(LifeStory).filter(LifeStory.user_id == user_id)

    if category:
        query = query.filter(LifeStory.category == category)

    total = query.count()
    stories = query.order_by(LifeStory.recorded_at.desc()).offset(offset).limit(limit).all()

    return {
        'user_id': user_id,
        'stories': [
            {
                'id': s.id,
                'title': s.title,
                'content': s.content[:200] + '...' if len(s.content) > 200 else s.content,
                'category': s.category,
                'era': s.era,
                'location': s.location,
                "related_people": parse_json_field(s.related_people),
                "emotion_tags": parse_json_field(s.emotion_tags),
                'has_audio': bool(s.audio_url),
                "photo_count": len(parse_json_field(s.photo_urls) or []),
                "recorded_at": s.recorded_at.isoformat()
            }
            for s in stories
        ],
        'total': total,
        'has_more': offset + limit < total
    }


@router.get("/life-stories/detail/{story_id}", response_model=dict)
def get_life_story_detail(
    story_id: int,
    db: Session = Depends(get_db)
):
    """获取人生故事详情"""
    story = db.query(LifeStory).filter(LifeStory.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail='故事不存在')

    return {
        'story': {
            'id': story.id,
            'user_id': story.user_id,
            'title': story.title,
            'content': story.content,
            'category': story.category,
            'era': story.era,
            "location": story.location,
            "related_people": parse_json_field(story.related_people),
            'audio_url': story.audio_url,
            'photo_urls': parse_json_field(story.photo_urls),
            "emotion_tags": parse_json_field(story.emotion_tags),
            'source': story.source,
            "recorded_at": story.recorded_at.isoformat(),
            'created_at': story.created_at.isoformat()
        }
    }


@router.put("/life-stories/{story_id}", response_model=dict)
def update_life_story(
    story_id: int,
    request: LifeStoryUpdate,
    db: Session = Depends(get_db)
):
    """更新人生故事"""
    story = db.query(LifeStory).filter(LifeStory.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail='故事不存在')

    update_data = request.model_dump(exclude_unset=True)

    json_fields = ['related_people', 'photo_urls', 'emotion_tags']
    for key, value in update_data.items():
        if key in json_fields and value is not None:
            setattr(story, key, serialize_json(value))
        elif key == 'category' and value:
            setattr(story, key, value.value if hasattr(value, 'value') else value)
        else:
            setattr(story, key, value)

    db.commit()
    return {'success': True, 'message': "更新成功"}


@router.delete("/life-stories/{story_id}", response_model=dict)
def delete_life_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    """删除人生故事"""
    story = db.query(LifeStory).filter(LifeStory.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail='故事不存在')

    db.delete(story)
    db.commit()
    return {'success': True, 'message': "删除成功"}


# ==================== 个性化上下文 ====================

@router.get("/personalization-context/{user_id}", response_model=dict)
def get_personalization_context(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取对话个性化上下文"""
    # 获取用户画像
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    # 获取相关记忆（按重要性和最近引用排序）
    memories = db.query(UserMemory).filter(
        UserMemory.user_id == user_id,
        UserMemory.is_active == True
    ).order_by(
        UserMemory.importance.desc()
    ).limit(10).all()

    # 获取即将到来的重要日期（7天内）
    today = date.today()
    upcoming_dates_raw = db.query(ImportantDate).filter(
        ImportantDate.user_id == user_id,
        ImportantDate.is_active == True
    ).all()

    upcoming_dates = []
    for d in upcoming_dates_raw:
        try:
            this_year_date = date(today.year, d.month, d.day)
            if 0 <= (this_year_date - today).days <= 7:
                upcoming_dates.append({
                    'title': d.title,
                    'date': this_year_date.isoformat(),
                    'days_until': (this_year_date - today).days
                })
        except ValueError:
            continue

    # 获取最近交互情况
    recent_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == user_id,
        Conversation.created_at >= datetime.now() - timedelta(days=1)
    ).scalar()

    return {
        'user_id': user_id,
        "profile": profile_to_response(profile) if profile else None,
        "relevant_memories": [
            {
                'type': m.memory_type,
                'key': m.key,
                'value': m.value
            }
            for m in memories
        ],
        "upcoming_dates": upcoming_dates,
        "recent_interactions": recent_conversations,
        "context_generated_at": datetime.now().isoformat()
    }


# ==================== 统计 ====================

@router.get("/stats/{user_id}", response_model=dict)
def get_memory_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取记忆系统统计"""
    # 记忆统计
    memories_by_type = db.query(
        UserMemory.memory_type,
        func.count(UserMemory.id)
    ).filter(
        UserMemory.user_id == user_id,
        UserMemory.is_active == True
    ).group_by(UserMemory.memory_type).all()

    total_memories = sum(c for _, c in memories_by_type)

    # 重要日期统计
    dates_count = db.query(func.count(ImportantDate.id)).filter(
        ImportantDate.user_id == user_id,
        ImportantDate.is_active == True
    ).scalar()

    # 人生故事统计
    stories_count = db.query(func.count(LifeStory.id)).filter(
        LifeStory.user_id == user_id
    ).scalar()

    # 画像完整度
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    profile_completeness = 0
    if profile:
        profile_fields = [
            profile.nickname, profile.birth_date, profile.hometown,
            profile.hobbies, profile.favorite_music, profile.chronic_conditions
        ]
        filled_fields = sum(1 for f in profile_fields if f)
        profile_completeness = int(filled_fields / len(profile_fields) * 100)

    return {
        "user_id": user_id,
        "total_memories": total_memories,
        "memories_by_type": {t: c for t, c in memories_by_type},
        "important_dates_count": dates_count,
        "life_stories_count": stories_count,
        "profile_completeness": profile_completeness
    }
