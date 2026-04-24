"""
Companion API · 数字生命陪伴（Phase 1 alpha）

⚠️ 本端点 alpha 状态，由环境变量 COMPANION_ENABLED=true 显式开启。
- 默认在生产环境从 OpenAPI schema 隐藏
- 不替换现有 /api/chat —— 仅并行存在
- Hermes / persona / memory_engine 当前是骨架，对话能力等同 qwen_service

详见 docs/DIGITAL_COMPANION_RFC.md
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import UserInfo, get_current_user

logger = logging.getLogger(__name__)


def _companion_enabled() -> bool:
    return os.environ.get("COMPANION_ENABLED", "false").lower() in ("1", "true", "yes")


router = APIRouter(prefix="/api/companion", tags=["数字生命陪伴 (Alpha)"])


# ===== 请求/响应模型 =====

class CompanionChatRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    elder_name: Optional[str] = Field(None, max_length=50)
    dialect: str = Field("wuhan", description="wuhan / mandarin")


class CompanionChatResponse(BaseModel):
    text: str
    used_memories: List[int] = []
    agent_reports: List[dict] = []
    fallback: bool = True
    note: Optional[str] = None


class SaveMemoryRequest(BaseModel):
    type: str = Field(..., description="fact / preference / relation / event / mood")
    content: str = Field(..., max_length=400)
    keywords: List[str] = []
    visibility: str = Field("self_only", description="self_only / family / never_share")
    importance: float = Field(0.5, ge=0.0, le=1.0)
    occurred_at: Optional[str] = None


# ===== 守卫 =====

def _require_enabled():
    if not _companion_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "companion_disabled",
                "message": "Companion (数字生命陪伴) 模式默认关闭。设置环境变量 COMPANION_ENABLED=true 启用",
                "doc": "anxinbao-server/docs/DIGITAL_COMPANION_RFC.md",
            },
        )


def _resolve_elder_id(current_user: UserInfo) -> int:
    """从 JWT 解析老人 User.id（与 CLAUDE.md 中身份模型一致）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="无效的用户身份")


# ===== 路由 =====

@router.get("/persona")
async def get_persona():
    """查看 Anxinbao Persona 配置（用于 debug / 设置页展示）"""
    _require_enabled()
    from app.services.persona import get_persona_summary
    return get_persona_summary()


@router.post("/chat", response_model=CompanionChatResponse)
async def companion_chat(
    body: CompanionChatRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    与数字生命对话（Phase 1 骨架版）

    当前行为：调用 Hermes，但 Hermes 内部降级到 qwen_service.chat_async。
    Phase 1 完成后会接 LLM + memory recall + tool calling 完整链路。
    """
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)

    from app.services.agents.hermes import hermes
    resp = await hermes.chat(
        user_id=elder_id,
        user_message=body.message,
        elder_name=body.elder_name or "您",
        dialect=body.dialect,
    )

    return CompanionChatResponse(
        text=resp.text,
        used_memories=resp.used_memories,
        agent_reports=[
            {
                "agent": r.agent_name,
                "severity": r.severity,
                "summary": r.summary,
                "details": r.details,
            }
            for r in resp.agent_reports
        ],
        fallback=resp.fallback,
        note="Alpha 版本 · 详见 docs/DIGITAL_COMPANION_RFC.md",
    )


@router.get("/memory/stats")
async def get_memory_stats(current_user: UserInfo = Depends(get_current_user)):
    """查看当前老人的长期记忆数量统计"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.memory_engine import get_memory_engine
    return get_memory_engine().stats(elder_id)


@router.get("/memory/list")
async def list_memories(
    limit: int = Query(50, ge=1, le=500),
    current_user: UserInfo = Depends(get_current_user),
):
    """列出当前老人的所有记忆（仅本人可见）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.memory_engine import get_memory_engine
    items = get_memory_engine().list_all(elder_id, limit=limit)
    return {"total": len(items), "items": [m.to_dict() for m in items]}


@router.post("/memory/save")
async def save_memory(
    body: SaveMemoryRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    """老人主动 / Hermes 自决 写入一条记忆"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.memory_engine import (
        MemoryRecord,
        MemoryType,
        MemoryVisibility,
        get_memory_engine,
    )

    try:
        mem_type = MemoryType(body.type)
        visibility = MemoryVisibility(body.visibility)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"无效的枚举值: {exc}")

    record = MemoryRecord(
        user_id=elder_id,
        type=mem_type,
        content=body.content,
        keywords=body.keywords,
        visibility=visibility,
        importance=body.importance,
        occurred_at=body.occurred_at,
    )
    new_id = get_memory_engine().save(record)
    return {"ok": True, "memory_id": new_id}


@router.delete("/memory/{memory_id}")
async def forget_memory(
    memory_id: int,
    current_user: UserInfo = Depends(get_current_user),
):
    """老人主动'忘记我吧' —— 仅可删自己的记忆"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.memory_engine import get_memory_engine
    ok = get_memory_engine().forget(memory_id, elder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记忆不存在或无权删除")
    return {"ok": True}


@router.delete("/memory/all/clear")
async def forget_all(
    confirm: bool = Query(False, description="必须 confirm=true 才执行"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    彻底清空老人的所有长期记忆（GDPR 'Right to be forgotten'）。
    必须 confirm=true 才执行。
    """
    _require_enabled()
    if not confirm:
        raise HTTPException(status_code=400, detail="请传 confirm=true 确认")
    elder_id = _resolve_elder_id(current_user)
    from app.services.memory_engine import get_memory_engine
    n = get_memory_engine().forget_all(elder_id)
    logger.warning(f"用户 {elder_id} 清空了所有记忆 ({n} 条)")
    return {"ok": True, "deleted_count": n}


@router.get("/tools")
async def list_companion_tools():
    """列出 Companion 可用的 function calling 工具池（schema only）"""
    _require_enabled()
    from app.services.companion_tools import list_tools
    return {"tools": list_tools()}
