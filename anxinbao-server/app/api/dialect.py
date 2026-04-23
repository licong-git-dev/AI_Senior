"""
方言服务API
支持方言选择、配置和区域文化适配
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.dialect_service import (
    dialect_service,
    regional_adapter,
    DialectType,
    LanguageMode
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/dialect", tags=["方言服务"])


# ==================== 请求/响应模型 ====================

class DialectInfo(BaseModel):
    """方言信息"""
    type: str
    name: str
    region: str
    description: str
    is_supported_tts: bool
    is_supported_asr: bool
    sample_phrases: List[str]


class SetDialectRequest(BaseModel):
    """设置方言请求"""
    dialect_type: str = Field(..., description="方言类型")


class TranslateRequest(BaseModel):
    """方言翻译请求"""
    text: str = Field(..., description='待翻译文本')
    from_dialect: str = Field(..., description="源方言类型")


class TTSConfigResponse(BaseModel):
    """TTS配置响应"""
    voice_id: Optional[str]
    dialect: str
    display_name: str


class ASRConfigResponse(BaseModel):
    """ASR配置响应"""
    model_id: Optional[str]
    dialect: str
    display_name: str


class RegionalContentResponse(BaseModel):
    """地区内容响应"""
    diet_preferences: List[str]
    health_tips: List[str]
    festivals: List[str]
    common_topics: List[str]


# ==================== API端点 ====================

@router.get("/list", response_model=List[DialectInfo])
async def get_dialect_list():
    """
    获取支持的方言列表

    返回所有可用的方言及其支持情况
    """
    dialects = dialect_service.get_all_dialects()
    return [DialectInfo(**d) for d in dialects]


@router.get("/supported")
async def get_supported_dialects():
    """
    获取完全支持的方言（同时支持TTS和ASR）
    """
    all_dialects = dialect_service.get_all_dialects()
    fully_supported = [
        d for d in all_dialects
        if d["is_supported_tts"] and d['is_supported_asr']
    ]
    return {
        "fully_supported": fully_supported,
        "total_count": len(all_dialects),
        "supported_count": len(fully_supported)
    }


@router.get("/current")
async def get_current_dialect(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户的方言设置
    """
    user_id = int(current_user['sub'])
    dialect_type = dialect_service.get_user_dialect(user_id)
    profile = dialect_service.get_dialect_profile(dialect_type)

    return {
        "dialect_type": dialect_type.value,
        "display_name": profile.display_name if profile else '普通话',
        'region': profile.region if profile else '全国通用'
    }


@router.post("/set")
async def set_dialect(
    request: SetDialectRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    设置用户方言偏好

    可选方言类型:
    - mandarin: 普通话
    - cantonese: 粤语
    - sichuan: 四川话
    - shanghai: 上海话
    - minnan: 闽南话
    - northeast: 东北话
    - beijing: 北京话
    - taiwanese: 台湾国语
    """
    user_id = int(current_user['sub'])

    try:
        dialect_type = DialectType(request.dialect_type)
    except ValueError:
        valid_types = [dt.value for dt in DialectType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的方言类型，可选: {valid_types}"
        )

    dialect_service.set_user_dialect(user_id, dialect_type)
    profile = dialect_service.get_dialect_profile(dialect_type)

    return {
        "success": True,
        "dialect_type": dialect_type.value,
        "display_name": profile.display_name if profile else dialect_type.value,
        'greeting': dialect_service.get_dialect_greeting(dialect_type)
    }


@router.get("/tts-config", response_model=TTSConfigResponse)
async def get_tts_config(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户的TTS（文字转语音）配置
    """
    user_id = int(current_user['sub'])
    dialect_type = dialect_service.get_user_dialect(user_id)
    config = dialect_service.get_tts_config(dialect_type)
    return TTSConfigResponse(**config)


@router.get("/asr-config", response_model=ASRConfigResponse)
async def get_asr_config(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户的ASR（语音识别）配置
    """
    user_id = int(current_user['sub'])
    dialect_type = dialect_service.get_user_dialect(user_id)
    config = dialect_service.get_asr_config(dialect_type)
    return ASRConfigResponse(**config)


@router.post("/translate")
async def translate_dialect(request: TranslateRequest):
    """
    方言词汇翻译（转为普通话）

    将方言特有词汇标注并解释
    """
    try:
        from_dialect = DialectType(request.from_dialect)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的源方言类型')

    translated = dialect_service.translate_dialect_words(
        request.text,
        from_dialect
    )

    return {
        'original': request.text,
        "translated": translated,
        "from_dialect": from_dialect.value
    }


@router.post("/detect")
async def detect_dialect(text: str):
    """
    检测文本中的方言特征

    基于词汇特征进行简单检测
    """
    detected = dialect_service.detect_dialect(text)

    if detected:
        profile = dialect_service.get_dialect_profile(detected)
        return {
            'detected': True,
            "dialect_type": detected.value,
            "display_name": profile.display_name if profile else detected.value,
            'confidence': 'medium'  # 基于词汇的检测置信度较低
        }

    return {
        "detected": False,
        "dialect_type": None,
        'message': "未检测到明显的方言特征"
    }


@router.get("/greeting")
async def get_dialect_greeting(current_user: dict = Depends(get_current_user)):
    """
    获取当前方言的问候语
    """
    user_id = int(current_user['sub'])
    dialect_type = dialect_service.get_user_dialect(user_id)
    greeting = dialect_service.get_dialect_greeting(dialect_type)

    return {
        "dialect_type": dialect_type.value,
        'greeting': greeting
    }


@router.get("/greetings/all")
async def get_all_greetings():
    """
    获取所有方言的问候语
    """
    greetings = {}
    for dt in DialectType:
        profile = dialect_service.get_dialect_profile(dt)
        if profile:
            greetings[dt.value] = {
                'name': profile.display_name,
                'greeting': dialect_service.get_dialect_greeting(dt)
            }
    return {'greetings': greetings}


# ==================== 地区文化API ====================

@router.get("/regional/{region}", response_model=RegionalContentResponse)
async def get_regional_content(region: str):
    """
    获取地区特色内容

    支持的地区: 广东、四川、上海、东北、北京等
    """
    content = regional_adapter.get_regional_content(region)
    return RegionalContentResponse(**content)


@router.get("/regional/{region}/health-tips")
async def get_regional_health_tips(region: str):
    """
    获取地区健康建议
    """
    content = regional_adapter.get_regional_content(region)
    return {'region': region, "health_tips": content.get("health_tips", [])}


@router.get("/regional/{region}/diet")
async def get_regional_diet(region: str):
    """
    获取地区饮食偏好
    """
    content = regional_adapter.get_regional_content(region)
    return {'region': region, "diet_preferences": content.get("diet_preferences", [])}


@router.get("/regional/{region}/topics")
async def get_regional_topics(region: str):
    """
    获取地区常见话题
    """
    content = regional_adapter.get_regional_content(region)
    return {'region': region, "common_topics": content.get("common_topics", [])}
