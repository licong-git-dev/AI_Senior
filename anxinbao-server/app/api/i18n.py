"""
国际化与本地化API
提供多语言、方言、时区、区域化内容等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.localization_service import (
    localization_service,
    Language,
    Dialect,
    Region
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/i18n", tags=["国际化"])


# ==================== 请求模型 ====================

class SetLocaleRequest(BaseModel):
    """设置区域配置请求"""
    language: Optional[str] = Field(None, description="语言: zh-CN/zh-TW/en-US")
    dialect: Optional[str] = Field(None, description="方言: mandarin/cantonese/sichuan等")
    region: Optional[str] = Field(None, description="区域: east_china/north_china等")
    timezone: Optional[str] = Field(None, description="时区: Asia/Shanghai等")


class TranslateRequest(BaseModel):
    """翻译请求"""
    keys: List[str] = Field(..., description="翻译键列表")
    language: Optional[str] = Field(None, description="目标语言，默认使用用户设置")
    params: Optional[Dict[str, Any]] = Field(None, description='替换参数')


# ==================== 语言API ====================

@router.get("/languages")
async def get_supported_languages():
    """
    获取支持的语言列表
    """
    languages = localization_service.translation.get_supported_languages()
    return {
        'languages': languages,
        'default': "zh-CN"
    }


@router.get("/translations/{language}")
async def get_translations(
    language: str,
    category: Optional[str] = Query(None, description="分类筛选: common/health/emergency等")
):
    """
    获取指定语言的翻译文本
    """
    translations = localization_service.translation.translations.get(language)
    if not translations:
        raise HTTPException(status_code=404, detail="不支持的语言")

    if category:
        filtered = {k: v for k, v in translations.items() if k.startswith(f"{category}.")}
        return {'language': language, "translations": filtered}

    return {'language': language, "translations": translations}


@router.post("/translate")
async def translate_texts(
    request: TranslateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    批量翻译文本
    """
    user_id = int(current_user['sub'])
    locale = localization_service.get_user_locale(user_id)
    language = request.language or locale.language.value

    results = {}
    for key in request.keys:
        results[key] = localization_service.translation.translate(
            key, language, request.params
        )

    return {"translations": results, 'language': language}


# ==================== 方言API ====================

@router.get("/dialects")
async def get_available_dialects():
    """
    获取可用的方言列表
    """
    dialects = localization_service.dialect_voice.get_available_dialects()
    return {
        'dialects': dialects,
        'default': 'mandarin'
    }


@router.get("/dialects/{dialect}")
async def get_dialect_detail(dialect: str):
    """
    获取方言详情
    """
    config = localization_service.dialect_voice.get_dialect_config(dialect)
    if not config:
        raise HTTPException(status_code=404, detail='不支持的方言')

    return {
        "dialect": dialect,
        **config
    }


@router.get("/dialects/{dialect}/voice-params")
async def get_dialect_voice_params(dialect: str):
    """
    获取方言语音合成参数
    """
    params = localization_service.dialect_voice.get_voice_params(dialect)
    return params


@router.post("/dialects/{dialect}/convert")
async def convert_to_dialect(
    dialect: str,
    text: str = Query(..., description="要转换的文本")
):
    """
    将文本转换为方言表达
    """
    converted = localization_service.dialect_voice.convert_text_to_dialect(text, dialect)
    return {
        'original': text,
        'converted': converted,
        'dialect': dialect
    }


# ==================== 时区API ====================

@router.get("/time/current")
async def get_current_time(
    timezone: Optional[str] = Query(None, description="时区")
):
    """
    获取当前时间
    """
    current = localization_service.timezone.get_current_time(timezone)
    return {
        'datetime': current.isoformat(),
        'timezone': timezone or "Asia/Shanghai",
        'formatted': {
            'full': localization_service.timezone.format_datetime(current, "full"),
            'date': localization_service.timezone.format_datetime(current, 'date'),
            'time': localization_service.timezone.format_datetime(current, 'time')
        }
    }


@router.get("/time/greeting")
async def get_time_based_greeting(
    language: str = Query('zh-CN', description="语言")
):
    """
    获取基于时间的问候语
    """
    greeting = localization_service.timezone.get_greeting_by_time(language)
    return {'greeting': greeting, 'language': language}


# ==================== 区域API ====================

@router.get("/regions")
async def get_available_regions():
    """
    获取可用的区域列表
    """
    regions = []
    for region in Region:
        content = localization_service.regional_content.get_regional_content(region.value)
        if content:
            regions.append({
                'code': region.value,
                'name': content['name'],
                'provinces': content['provinces']
            })
    return {'regions': regions}


@router.get("/regions/{region}")
async def get_region_detail(region: str):
    """
    获取区域详情
    """
    content = localization_service.regional_content.get_regional_content(region)
    if not content:
        raise HTTPException(status_code=404, detail='不支持的区域')

    return {"region": region, **content}


@router.get("/regions/{region}/recommendations")
async def get_regional_recommendations(
    region: str,
    content_type: str = Query(..., description="内容类型: music/news/health/activities/festivals/cuisine")
):
    """
    获取区域推荐内容
    """
    recommendations = localization_service.regional_content.get_recommended_content(
        region, content_type
    )

    if not recommendations:
        raise HTTPException(status_code=404, detail='未找到推荐内容')

    return {
        "region": region,
        "content_type": content_type,
        "recommendations": recommendations
    }


@router.get("/regions/detect")
async def detect_region(
    province: str = Query(..., description="省份名称")
):
    """
    根据省份检测区域
    """
    region = localization_service.regional_content.detect_region_by_province(province)

    if not region:
        return {'province': province, 'region': None, 'detected': False}

    content = localization_service.regional_content.get_regional_content(region)
    return {
        'province': province,
        'region': region,
        'region_name': content['name'] if content else None,
        'detected': True
    }


# ==================== 用户区域配置API ====================

@router.get("/locale")
async def get_user_locale(current_user: dict = Depends(get_current_user)):
    """
    获取我的区域配置
    """
    user_id = int(current_user['sub'])
    locale = localization_service.get_user_locale(user_id)

    return {
        'locale': locale.to_dict(),
        'options': {
            'languages': [l.value for l in Language],
            'dialects': [d.value for d in Dialect],
            'regions': [r.value for r in Region]
        }
    }


@router.put("/locale")
async def set_user_locale(
    request: SetLocaleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    设置我的区域配置
    """
    user_id = int(current_user['sub'])

    # 验证参数
    if request.language:
        try:
            Language(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail='不支持的语言')

    if request.dialect:
        try:
            Dialect(request.dialect)
        except ValueError:
            raise HTTPException(status_code=400, detail='不支持的方言')

    if request.region:
        try:
            Region(request.region)
        except ValueError:
            raise HTTPException(status_code=400, detail='不支持的区域')

    locale = localization_service.set_user_locale(
        user_id,
        language=request.language,
        dialect=request.dialect,
        region=request.region,
        timezone=request.timezone
    )

    return {
        'success': True,
        'locale': locale.to_dict(),
        'message': "区域配置已更新"
    }


@router.get("/locale/greeting")
async def get_localized_greeting(current_user: dict = Depends(get_current_user)):
    """
    获取本地化问候语
    """
    user_id = int(current_user['sub'])
    greeting = localization_service.get_localized_greeting(user_id)
    locale = localization_service.get_user_locale(user_id)

    return {
        'greeting': greeting,
        'language': locale.language.value,
        'dialect': locale.dialect.value
    }


# ==================== 工具API ====================

@router.get("/format/date")
async def format_date(
    timestamp: Optional[int] = Query(None, description='Unix时间戳'),
    format_type: str = Query("full", description="格式: full/date/time/friendly"),
    language: str = Query('zh-CN', description="语言")
):
    """
    格式化日期时间
    """
    from datetime import datetime

    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = datetime.now()

    formatted = localization_service.timezone.format_datetime(dt, format_type, language)

    return {
        'original': dt.isoformat(),
        'formatted': formatted,
        "format_type": format_type,
        'language': language
    }
