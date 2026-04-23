"""
API路由 - 对话接口
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.services.qwen_service import chat_service
from app.services.health_evaluator import risk_evaluator
from app.services.dialect_companion import dialect_companion
from app.core.cache import conversation_store
from app.core.limiter import limiter
from app.core.security import get_current_user, UserInfo
from app.core.deps import get_db

router = APIRouter(prefix="/api/chat", tags=["对话"])


def _check_user_access(user_id: str, current_user: UserInfo, db: Session) -> None:
    """校验当前用户是否有权访问指定老人的健康摘要。"""
    if current_user.role == "admin":
        return

    from app.models.database import DeviceAuth, FamilyMember, UserAuth

    try:
        target_user_id = int(user_id)
        auth_id = int(current_user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户ID格式无效") from exc

    auth = db.query(UserAuth).filter(UserAuth.id == auth_id).first()
    if current_user.role == "elder" and auth and auth.user_id == target_user_id:
        return
    if current_user.role == "family" and auth and auth.family_id:
        family = db.query(FamilyMember).filter(FamilyMember.id == auth.family_id).first()
        if family and family.user_id == target_user_id:
            return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该用户的健康摘要")


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., max_length=2000, description="用户消息")
    session_id: Optional[str] = None
    dialect: Literal["mandarin", "wuhan", "ezhou"] = "mandarin"


class ChatResponse(BaseModel):
    """对话响应"""
    reply: str
    session_id: str
    risk_info: Dict
    food_therapy: Optional[Dict] = None
    timestamp: str


@router.post("/send", response_model=ChatResponse)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    chat_req: ChatRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    发送消息并获取AI回复

    - message: 用户消息
    - session_id: 会话ID（可选，不传则新建）
    - dialect: 方言类型
    """
    user_id = current_user.user_id

    # 获取或创建会话
    session_id = chat_req.session_id or str(uuid.uuid4())

    # 获取历史对话（通过ConversationStore，支持Redis和内存双模式）
    history = await conversation_store.get_history(user_id, session_id)

    # 调用AI对话服务（异步，避免阻塞事件循环）
    reply, ai_risk_info = await chat_service.chat_async(chat_req.message, history)

    # 健康风险评估
    risk_result = risk_evaluator.evaluate(
        user_id,
        chat_req.message,
        ai_risk_info
    )

    # 记录用户消息和AI回复到会话存储
    await conversation_store.add_message(
        user_id, session_id, "user", chat_req.message
    )
    await conversation_store.add_message(
        user_id, session_id, "assistant", reply,
        metadata={"risk_score": risk_result.get("risk_score", 0)}
    )

    # 如果是健康问题，生成食疗建议（含方言版）
    food_therapy = None
    if ai_risk_info.get("category") == "health" and risk_result["risk_score"] >= 3:
        food_therapy = await chat_service.generate_food_therapy_async(chat_req.message)
        # 附加方言食疗小贴士
        condition = "general"
        msg_lower = chat_req.message
        if any(w in msg_lower for w in ["血压", "头晕", "头疼"]):
            condition = "hypertension"
        elif any(w in msg_lower for w in ["睡不着", "失眠", "睡不好"]):
            condition = "insomnia"
        elif any(w in msg_lower for w in ["感冒", "着凉", "咳嗽"]):
            condition = "cold"
        elif any(w in msg_lower for w in ["胃", "消化", "肚子"]):
            condition = "digestion"
        food_therapy["dialect_tip"] = dialect_companion.get_food_therapy(
            condition, dialect=chat_req.dialect, name="您"
        )

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        risk_info=risk_result,
        food_therapy=food_therapy,
        timestamp=datetime.now().isoformat()
    )


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取会话历史"""
    history = await conversation_store.get_history(current_user.user_id, session_id)
    return {"session_id": session_id, "history": history}


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """清除会话历史"""
    await conversation_store.clear_history(current_user.user_id, session_id)
    return {"message": "会话已清除"}


@router.get("/health-summary/{user_id}")
async def get_health_summary(
    user_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户健康摘要（给子女看）
    """
    _check_user_access(user_id, current_user, db)
    summary = risk_evaluator.get_user_health_summary(user_id)
    return summary


@router.get("/greeting")
@limiter.limit("60/minute")
async def get_dialect_greeting(
    request: Request,
    dialect: Literal["mandarin", "wuhan", "ezhou"] = Query(default="mandarin"),
    name: str = Query(default="您", max_length=20),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取方言问候语（待机页面 / 首页展示）

    根据当前时段和方言返回一句温暖问候
    """
    greeting = dialect_companion.get_greeting(dialect=dialect, name=name)
    return {
        "greeting": greeting,
        "dialect": dialect,
        "timestamp": datetime.now().isoformat(),
    }
