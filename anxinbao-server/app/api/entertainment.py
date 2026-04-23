"""
娱乐服务API
支持音乐、广播、戏曲等内容播放
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.entertainment_service import (
    entertainment_service,
    radio_service,
    health_broadcast,
    ContentType,
    MusicGenre,
    OperaType,
    RadioStation
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/entertainment", tags=["娱乐服务"])


# ==================== 请求/响应模型 ====================

class ContentResponse(BaseModel):
    """内容响应"""
    content_id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    content_type: str
    genre: Optional[str]
    duration: int
    url: Optional[str]
    cover_url: Optional[str]
    description: str
    tags: List[str]


class PlaylistResponse(BaseModel):
    """播放列表响应"""
    playlist_id: str
    name: str
    description: str
    content_type: str
    item_count: int
    cover_url: Optional[str]
    is_public: bool


class StationResponse(BaseModel):
    """电台响应"""
    station_id: str
    name: str
    description: str
    frequency: str
    stream_url: str


class FavoriteRequest(BaseModel):
    """收藏请求"""
    content_id: str = Field(..., description="内容ID")


class PlayRequest(BaseModel):
    """播放请求"""
    content_id: str = Field(..., description='内容ID')


# ==================== 播放列表API ====================

@router.get("/playlists", response_model=List[PlaylistResponse])
async def get_playlists():
    """
    获取所有播放列表
    """
    playlists = entertainment_service.get_all_playlists()
    return playlists


@router.get("/playlists/{playlist_id}")
async def get_playlist_detail(playlist_id: str):
    """
    获取播放列表详情
    """
    playlist = entertainment_service.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail='播放列表不存在')

    return {
        **playlist.to_dict(),
        "items": [item.to_dict() for item in playlist.items]
    }


@router.get("/playlists/{playlist_id}/items", response_model=List[ContentResponse])
async def get_playlist_items(playlist_id: str):
    """
    获取播放列表内容
    """
    items = entertainment_service.get_playlist_items(playlist_id)
    if not items:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    return items


# ==================== 内容API ====================

@router.get("/content/music", response_model=List[ContentResponse])
async def get_music_content():
    """
    获取所有音乐内容
    """
    return entertainment_service.get_content_by_type(ContentType.MUSIC)


@router.get("/content/opera", response_model=List[ContentResponse])
async def get_opera_content():
    """
    获取所有戏曲内容
    """
    return entertainment_service.get_content_by_type(ContentType.OPERA)


@router.get("/content/health-tips", response_model=List[ContentResponse])
async def get_health_tip_content():
    """
    获取健康小知识
    """
    return entertainment_service.get_content_by_type(ContentType.HEALTH_TIP)


@router.get("/content/search")
async def search_content(
    q: str = Query(..., min_length=1, description='搜索关键词'),
    content_type: Optional[str] = Query(None, description="内容类型过滤")
):
    """
    搜索内容

    支持搜索标题、艺术家、描述、标签
    """
    ct = None
    if content_type:
        try:
            ct = ContentType(content_type)
        except ValueError:
            raise HTTPException(status_code=400, detail='无效的内容类型')

    results = entertainment_service.search(q, ct)
    return {'query': q, 'count': len(results), "results": results}


# ==================== 推荐API ====================

@router.get("/recommendations")
async def get_recommendations(
    content_type: Optional[str] = Query(None, description='内容类型'),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取个性化推荐
    """
    user_id = int(current_user['sub'])

    ct = None
    if content_type:
        try:
            ct = ContentType(content_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的内容类型")

    recommendations = entertainment_service.get_recommendations(user_id, ct, limit)
    return {"recommendations": recommendations}


# ==================== 收藏API ====================

@router.get("/favorites", response_model=List[ContentResponse])
async def get_favorites(current_user: dict = Depends(get_current_user)):
    """
    获取用户收藏
    """
    user_id = int(current_user['sub'])
    return entertainment_service.get_favorites(user_id)


@router.post("/favorites")
async def add_favorite(
    request: FavoriteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加收藏
    """
    user_id = int(current_user['sub'])
    entertainment_service.add_to_favorites(user_id, request.content_id)
    return {'success': True, 'message': "已添加到收藏"}


@router.delete("/favorites/{content_id}")
async def remove_favorite(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    取消收藏
    """
    user_id = int(current_user['sub'])
    entertainment_service.remove_from_favorites(user_id, content_id)
    return {'success': True, 'message': '已取消收藏'}


# ==================== 播放历史API ====================

@router.get("/history")
async def get_play_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取播放历史
    """
    user_id = int(current_user['sub'])
    history = entertainment_service.get_history(user_id, limit)
    return {'history': history}


# ==================== 播放控制API ====================

@router.post("/play")
async def start_play(
    request: PlayRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    开始播放
    """
    user_id = int(current_user['sub'])
    entertainment_service.set_current_playing(user_id, request.content_id)

    return {
        'success': True,
        'message': '开始播放',
        "content_id": request.content_id
    }


@router.get("/now-playing")
async def get_now_playing(current_user: dict = Depends(get_current_user)):
    """
    获取当前播放
    """
    user_id = int(current_user['sub'])
    current = entertainment_service.get_current_playing(user_id)

    if current:
        return {'playing': True, 'content': current}
    return {'playing': False, 'content': None}


# ==================== 广播电台API ====================

@router.get("/radio/stations", response_model=List[StationResponse])
async def get_radio_stations():
    """
    获取所有广播电台
    """
    return radio_service.get_all_stations()


@router.get("/radio/stations/{station_id}", response_model=StationResponse)
async def get_radio_station(station_id: str):
    """
    获取电台详情
    """
    station = radio_service.get_station(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="电台不存在")
    return station


@router.post("/radio/play/{station_id}")
async def play_radio(
    station_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    播放广播电台
    """
    station = radio_service.get_station(station_id)
    if not station:
        raise HTTPException(status_code=404, detail='电台不存在')

    return {
        'success': True,
        'message': f"正在播放: {station['name']}",
        "station": station
    }


# ==================== 健康广播API ====================

@router.get("/health/daily-tip")
async def get_daily_health_tip():
    """
    获取每日健康提示
    """
    tip = health_broadcast.get_daily_tip()
    return {
        'tip': tip,
        'type': 'daily'
    }


@router.get("/health/random-tip")
async def get_random_health_tip():
    """
    获取随机健康提示
    """
    tip = health_broadcast.get_random_tip()
    return {
        'tip': tip,
        'type': 'random'
    }


# ==================== 分类信息API ====================

@router.get("/categories/music")
async def get_music_genres():
    """
    获取音乐类型列表
    """
    genres = [
        {'value': g.value, 'name': _get_genre_name(g)}
        for g in MusicGenre
    ]
    return {'genres': genres}


@router.get("/categories/opera")
async def get_opera_types():
    """
    获取戏曲类型列表
    """
    types = [
        {'value': t.value, 'name': _get_opera_name(t)}
        for t in OperaType
    ]
    return {'types': types}


@router.get("/categories/content")
async def get_content_types():
    """
    获取内容类型列表
    """
    types = [
        {'value': t.value, 'name': _get_content_type_name(t)}
        for t in ContentType
    ]
    return {'types': types}


def _get_genre_name(genre: MusicGenre) -> str:
    """获取音乐类型中文名"""
    names = {
        MusicGenre.CLASSIC_CHINESE: '经典老歌',
        MusicGenre.RED_SONGS: '红歌',
        MusicGenre.FOLK: '民歌',
        MusicGenre.LIGHT_MUSIC: '轻音乐',
        MusicGenre.CLASSICAL: '古典音乐',
        MusicGenre.REGIONAL: "地方歌曲"
    }
    return names.get(genre, genre.value)


def _get_opera_name(opera: OperaType) -> str:
    """获取戏曲类型中文名"""
    names = {
        OperaType.PEKING_OPERA: '京剧',
        OperaType.YUEJU: '越剧',
        OperaType.HUANGMEI: '黄梅戏',
        OperaType.PINGJU: '评剧',
        OperaType.YUJU: '豫剧',
        OperaType.CHUANJU: '川剧',
        OperaType.KUNQU: "昆曲"
    }
    return names.get(opera, opera.value)


def _get_content_type_name(ct: ContentType) -> str:
    """获取内容类型中文名"""
    names = {
        ContentType.MUSIC: '音乐',
        ContentType.RADIO: '广播',
        ContentType.OPERA: '戏曲',
        ContentType.STORY: '故事/评书',
        ContentType.NEWS: '新闻',
        ContentType.HEALTH_TIP: "健康小知识"
    }
    return names.get(ct, ct.value)
