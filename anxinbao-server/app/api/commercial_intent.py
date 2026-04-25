"""
商业意图 API · payer-only 视角（r27 · Insight #13）

5 端点（全部需 payer 角色）:
- GET    /api/companion/intents               拉本人 family 老人的 intent 列表
- GET    /api/companion/intents/stats         分类分布
- POST   /api/companion/intents/{id}/review   标记已查看
- POST   /api/companion/intents/{id}/dismiss  关闭
- POST   /api/companion/intents/detect        手动触发识别（debug / 主动场景）

老人**永远看不到**自己的 intent（避免被推销心智）。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db
from app.core.security import get_current_user, UserInfo
from app.services.commercial_intent_service import (
    CommercialIntentError,
    NotPayerError,
    commercial_intent_service,
)


router = APIRouter(prefix="/api/companion/intents", tags=["商业意图（GMV）"])


def _user_auth_id(current_user: UserInfo) -> int:
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="JWT 中 user_id 非数字")


def _handle_errors(fn):
    from functools import wraps

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except NotPayerError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except CommercialIntentError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return wrapper


# ===== 请求模型 =====


class DetectIntentRequest(BaseModel):
    elder_user_id: int = Field(..., description="老人 User.id")
    text: str = Field(..., max_length=500)
    source_type: str = Field("manual", description="chat / proactive_ack / manual")
    source_object_id: Optional[str] = None


# ===== 端点 =====


@router.get("/")
@_handle_errors
async def list_intents(
    elder_user_id: int = Query(..., description="老人 User.id"),
    status: Optional[str] = Query(None, description="filter: detected / reviewed_by_family / ordered / dismissed"),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """payer 拉某老人的商业意图列表"""
    ua_id = _user_auth_id(current_user)
    items = commercial_intent_service.list_intents(
        db, elder_user_id, ua_id, status=status, limit=limit,
    )
    return {
        "items": [
            {
                "id": it.id,
                "category": it.category,
                "keyword": it.keyword,
                "suggested_title": it.suggested_title,
                "confidence": it.confidence,
                "status": it.status,
                "detected_at": it.detected_at.isoformat(),
                "reviewed_at": it.reviewed_at.isoformat() if it.reviewed_at else None,
                "expires_at": it.expires_at.isoformat() if it.expires_at else None,
                "source_text": it.source_text,
            }
            for it in items
        ]
    }


@router.get("/stats")
@_handle_errors
async def get_stats(
    elder_user_id: int = Query(..., description="老人 User.id"),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """payer 看分类分布"""
    ua_id = _user_auth_id(current_user)
    return commercial_intent_service.stats(db, elder_user_id, ua_id)


@router.post("/{intent_id}/review")
@_handle_errors
async def mark_reviewed(
    intent_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """payer 标"已查看"（不下单也不关闭，仅表示我看到了）"""
    ua_id = _user_auth_id(current_user)
    intent = commercial_intent_service.mark_reviewed(db, intent_id, ua_id)
    return {"id": intent.id, "status": intent.status}


@router.post("/{intent_id}/dismiss")
@_handle_errors
async def dismiss_intent(
    intent_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """payer 关闭这条意图（"妈妈说说而已不用买"）"""
    ua_id = _user_auth_id(current_user)
    intent = commercial_intent_service.dismiss(db, intent_id, ua_id)
    return {"id": intent.id, "status": intent.status}


@router.post("/detect")
@_handle_errors
async def detect_intent(
    body: DetectIntentRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    手动触发识别（debug / 主动场景；正常通过 Hermes 异步钩子触发）。
    payer-only。
    """
    ua_id = _user_auth_id(current_user)
    # 使用 service 内的 _require_payer_for_elder 检查权限（通过下面 detect_and_record 间接）
    # detect_and_record 不强校验 payer (因为 Hermes hook 不带 viewer)；这里需手动校
    commercial_intent_service._require_payer_for_elder(db, body.elder_user_id, ua_id)

    records = commercial_intent_service.detect_and_record(
        db, body.elder_user_id, body.text,
        source_type=body.source_type,
        source_object_id=body.source_object_id,
    )
    return {
        "detected_count": len(records),
        "items": [
            {"id": r.id, "category": r.category, "keyword": r.keyword,
             "confidence": r.confidence, "suggested_title": r.suggested_title}
            for r in records
        ]
    }
