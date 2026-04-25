"""
老人主动语音 API（r25 · Insight #12）

7 个端点:
- POST   /api/voice-message/                 老人录音 → 入库
- POST   /api/voice-message/{id}/transcript  STT 回填（内部用）
- POST   /api/voice-message/{id}/caption     摘要回填（内部用）
- GET    /api/voice-message/inbox            家属拉收件箱
- POST   /api/voice-message/{id}/delivered   家属端标记送达
- POST   /api/voice-message/{id}/read        家属端标记已读
- POST   /api/voice-message/{id}/reply       家属语音回复
- GET    /api/voice-message/stats            老人维度统计
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db
from app.core.security import get_current_user, UserInfo
from app.services.voice_message_service import (
    MessageNotFoundError,
    NotRecipientError,
    RecipientNotFoundError,
    VoiceMessageError,
    voice_message_service,
)


router = APIRouter(prefix="/api/voice-message", tags=["老人主动语音"])


# ===== 请求模型 =====


class RecordRequest(BaseModel):
    sender_user_id: int = Field(..., description="老人的 User.id（注意不是 user_auth.id）")
    recipient_user_auth_id: int = Field(..., description="收件家属的 user_auth.id")
    audio_url: str = Field(..., min_length=1, max_length=500)
    duration_sec: int = Field(..., ge=1, le=120)


class TranscriptRequest(BaseModel):
    transcript: str = Field(..., max_length=1000)


class CaptionRequest(BaseModel):
    caption: str = Field(..., max_length=200)
    emotion: Optional[str] = Field(None, max_length=20)


class ReplyRequest(BaseModel):
    audio_url: str = Field(..., min_length=1, max_length=500)
    duration_sec: int = Field(..., ge=1, le=120)


# ===== 工具：异常翻译 =====


def _handle(fn):
    from functools import wraps

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except RecipientNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except NotRecipientError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except MessageNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except VoiceMessageError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return wrapper


def _user_auth_id(current_user: UserInfo) -> int:
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="JWT user_id 非数字")


def _serialize(msg) -> dict:
    return {
        "id": msg.id,
        "sender_user_id": msg.sender_user_id,
        "recipient_user_auth_id": msg.recipient_user_auth_id,
        "audio_url": msg.audio_url,
        "duration_sec": msg.duration_sec,
        "transcript": msg.transcript,
        "ai_caption": msg.ai_caption,
        "emotion": msg.emotion,
        "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
        "read_at": msg.read_at.isoformat() if msg.read_at else None,
        "reply_voice_message_id": msg.reply_voice_message_id,
        "created_at": msg.created_at.isoformat(),
    }


# ===== 端点 =====


@router.post("/", status_code=201)
@_handle
async def record(
    body: RecordRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """老人录音入库"""
    msg = voice_message_service.record(
        db=db,
        sender_user_id=body.sender_user_id,
        recipient_user_auth_id=body.recipient_user_auth_id,
        audio_url=body.audio_url,
        duration_sec=body.duration_sec,
    )
    return _serialize(msg)


@router.post("/{message_id}/transcript")
@_handle
async def attach_transcript(
    message_id: int,
    body: TranscriptRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """STT 完成后回填（通常由后台任务触发）"""
    msg = voice_message_service.attach_transcript(db, message_id, body.transcript)
    return _serialize(msg)


@router.post("/{message_id}/caption")
@_handle
async def attach_caption(
    message_id: int,
    body: CaptionRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """qwen 摘要回填（通常由后台任务触发）"""
    msg = voice_message_service.attach_caption(
        db, message_id, body.caption, emotion=body.emotion
    )
    return _serialize(msg)


@router.get("/inbox")
@_handle
async def list_inbox(
    unread_only: bool = False,
    limit: int = 30,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家属拉收件箱"""
    ua_id = _user_auth_id(current_user)
    msgs = voice_message_service.list_inbox(
        db, ua_id, unread_only=unread_only, limit=limit
    )
    return {"items": [_serialize(m) for m in msgs]}


@router.post("/{message_id}/delivered")
@_handle
async def mark_delivered(
    message_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """前端列表展示后标记送达"""
    ua_id = _user_auth_id(current_user)
    ok = voice_message_service.mark_delivered(db, message_id, ua_id)
    return {"ok": ok}


@router.post("/{message_id}/read")
@_handle
async def mark_read(
    message_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家属点开播放后标记已读"""
    ua_id = _user_auth_id(current_user)
    ok = voice_message_service.mark_read(db, message_id, ua_id)
    return {"ok": ok}


@router.post("/{message_id}/reply", status_code=201)
@_handle
async def reply_voice(
    message_id: int,
    body: ReplyRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家属语音回复老人"""
    ua_id = _user_auth_id(current_user)
    msg = voice_message_service.reply_voice(
        db=db,
        original_message_id=message_id,
        replier_user_auth_id=ua_id,
        audio_url=body.audio_url,
        duration_sec=body.duration_sec,
    )
    return _serialize(msg)


@router.get("/stats/{elder_user_id}")
@_handle
async def stats_for_elder(
    elder_user_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """老人维度的语音统计（子女端展示用）"""
    return voice_message_service.stats_for_elder(db, elder_user_id)
