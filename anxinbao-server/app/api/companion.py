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
    db: Session = Depends(get_db),
):
    """
    与数字生命对话（Phase 1 骨架版 + r19 陪伴值钩子）

    当前行为：调用 Hermes，但 Hermes 内部降级到 qwen_service.chat_async。
    Phase 1 完成后会接 LLM + memory recall + tool calling 完整链路。

    r19: 对话成功 → 陪伴值 +1（每天上限 30）；首次对话当天 → +5 签到
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

    # r19 · 陪伴值钩子（safe_earn 内部已吞限频/异常，不影响对话主路径）
    try:
        from app.services.companion_points_service import companion_points_service
        companion_points_service.daily_signin(db, elder_id)
        companion_points_service.safe_earn(
            db, elder_id, "earn_chat_message",
            related_object_type="chat",
            note=body.message[:40],
        )
    except Exception as exc:
        # 钩子异常绝不影响对话；只记日志
        import logging as _logging
        _logging.getLogger(__name__).warning(f"[points hook] chat earn 异常: {exc}")

    # r20 · T 选项：北极星埋点（老人主动对话事件）
    try:
        from app.core.north_star_metrics import record_elder_chat
        record_elder_chat(dialect=body.dialect or "mandarin")
    except Exception:
        pass

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


# ===== Phase 2 · 主动开口 =====


class DNDConfigRequest(BaseModel):
    dnd_start: Optional[str] = Field(None, description="HH:MM，如 22:00")
    dnd_end: Optional[str] = Field(None, description="HH:MM，如 07:00")
    daily_quota: Optional[int] = Field(None, ge=0, le=20)
    enabled: Optional[bool] = None
    push_proactive: Optional[bool] = Field(
        None, description="主动消息是否触发通知推送（默认 true）"
    )


@router.get("/proactive/inbox")
async def proactive_inbox(
    only_undelivered: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    拉取主动消息收件箱。only_undelivered=true 仅返回老人未读的。
    """
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    store = get_store()
    items = store.list_inbox(elder_id, limit=limit, only_undelivered=only_undelivered)
    return {
        "total": len(items),
        "items": [
            {
                "id": m.id,
                "trigger_name": m.trigger_name,
                "text": m.text,
                "priority": m.priority,
                "reason": m.reason,
                "delivered": m.delivered,
                "acknowledged": m.acknowledged,
                "created_at": m.created_at,
            }
            for m in items
        ],
    }


@router.post("/proactive/{message_id}/delivered")
async def mark_proactive_delivered(
    message_id: int,
    current_user: UserInfo = Depends(get_current_user),
):
    """前端拉取后标记为已展示"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    ok = get_store().mark_delivered(message_id, elder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="消息不存在或无权操作")
    return {"ok": True}


@router.post("/proactive/{message_id}/ack")
async def acknowledge_proactive(
    message_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    老人回应了主动消息（点击/语音回复）后，标记已确认。用于 NPS 与触发器调优。

    r19: ack 时陪伴值 +2 (earn_proactive_ack，每天上限 6)
    """
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    ok = get_store().acknowledge(message_id, elder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="消息不存在或无权操作")

    # r19 · 陪伴值钩子
    try:
        from app.services.companion_points_service import companion_points_service
        companion_points_service.safe_earn(
            db, elder_id, "earn_proactive_ack",
            related_object_type="proactive_message",
            related_object_id=str(message_id),
        )
    except Exception:
        pass

    # r20 · T 选项：北极星埋点
    try:
        from app.core.north_star_metrics import record_proactive_acked
        from app.services.proactive_engagement import get_store as _get_store
        # 拿 trigger_name 作为标签
        msg = _get_store().get_message(message_id, elder_id) if hasattr(_get_store(), "get_message") else None
        trigger_name = getattr(msg, "trigger_name", "unknown") if msg else "unknown"
        record_proactive_acked(trigger_name)
    except Exception:
        pass

    return {"ok": True}


@router.get("/dnd")
async def get_dnd(current_user: UserInfo = Depends(get_current_user)):
    """查看老人的 DND 配置（请勿打扰时段 + 每日主动消息配额）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    return get_store().get_dnd(elder_id)


@router.put("/dnd")
async def update_dnd(
    body: DNDConfigRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    """更新 DND 配置；仅传需要改的字段即可"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    return get_store().upsert_dnd(
        user_id=elder_id,
        dnd_start=body.dnd_start,
        dnd_end=body.dnd_end,
        daily_quota=body.daily_quota,
        enabled=body.enabled,
        push_proactive=body.push_proactive,
    )


@router.post("/proactive/run-now")
async def trigger_proactive_now(
    current_user: UserInfo = Depends(get_current_user),
):
    """
    手动触发一次主动评估（用于调试 / 验证触发器是否工作）。
    与 scheduler 的定时任务行为完全相同，仅作用于当前老人。
    """
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import evaluate_and_send
    msgs = await evaluate_and_send(elder_id)
    return {
        "evaluated": True,
        "generated": len(msgs),
        "messages": [
            {"id": m.id, "trigger_name": m.trigger_name, "text": m.text, "priority": m.priority}
            for m in msgs
        ],
    }


@router.get("/proactive/triggers")
async def list_triggers():
    """列出当前注册的所有触发器（schema 与 cooldown）—— 仅 debug 用"""
    _require_enabled()
    from app.services.companion_triggers import ALL_TRIGGERS
    return {
        "triggers": [
            {"name": t.name, "cooldown_hours": t.cooldown_hours}
            for t in ALL_TRIGGERS
        ]
    }


# ===== Phase 3 · 工具调用安全网关 =====


class ToolCallRequest(BaseModel):
    name: str = Field(..., description="工具名，见 /api/companion/tools")
    params: dict = Field(default_factory=dict)
    confirm_token: Optional[str] = Field(
        None, description="MEDIUM/CRITICAL 级工具必须在二次调用时带 confirm_token"
    )


@router.post("/tools/call")
async def call_tool(
    body: ToolCallRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    调用 Companion 工具。按安全等级分流：

    - **LOW**：直接执行
    - **MEDIUM / CRITICAL**：首次调用返回 pending_confirmation（需前端弹确认框），
      二次调用带 confirm_token 才真正执行
    - **HIGH**：直接执行，但 handler 内部必经规则引擎（如 request_health_advice）

    生产环境已隐藏于 OpenAPI。
    """
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)

    from app.services.companion_tools import (
        dispatch,
        safety_level as tool_safety,
        _REGISTRY,
    )
    from app.services.proactive_engagement import get_store

    level = tool_safety(body.name)
    if level is None:
        raise HTTPException(status_code=404, detail=f"未知工具: {body.name}")

    store = get_store()

    # MEDIUM / CRITICAL：两步执行
    if level in ("medium", "critical"):
        if not body.confirm_token:
            # 第一步：产生 pending confirmation
            confirm_id = store.create_confirmation(
                user_id=elder_id,
                tool_name=body.name,
                params=body.params,
                safety_level=level,
                ttl_seconds=300 if level == "medium" else 120,  # CRITICAL 更短 TTL
            )
            return {
                "requires_confirmation": True,
                "safety_level": level,
                "confirm_token": confirm_id,
                "ttl_seconds": 300 if level == "medium" else 120,
                "tool": body.name,
                "params": body.params,
                "hint": "请向老人二次确认后，带 confirm_token 再次调用 /tools/call",
            }

        # 第二步：校验 token
        pending = store.get_confirmation(body.confirm_token, elder_id)
        if not pending:
            raise HTTPException(
                status_code=400,
                detail="confirm_token 无效、已使用或已过期，请重新发起确认流程",
            )
        if pending["tool_name"] != body.name:
            raise HTTPException(
                status_code=400,
                detail="confirm_token 对应的工具与本次调用不匹配",
            )
        # 消费 token（单次有效）
        consumed = store.consume_confirmation(body.confirm_token, elder_id)
        if not consumed:
            raise HTTPException(status_code=409, detail="confirm_token 已被消费")

    # 真正执行
    result = await dispatch(body.name, elder_id, body.params)
    return {
        "tool": body.name,
        "safety_level": level,
        "result": result,
    }


@router.get("/confirmations")
async def list_pending_confirmations(
    current_user: UserInfo = Depends(get_current_user),
):
    """前端拉取当前老人的待确认操作列表"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    return {"items": get_store().list_pending_confirmations(elder_id)}


# ===== r26 · Companion Onboarding (Insight #11) =====


class OnboardingProfileRequest(BaseModel):
    family_name: Optional[str] = Field(None, max_length=20, description="老人姓 (张/李)")
    addressed_as: Optional[str] = Field(None, max_length=20, description="老人称呼 (妈/婆婆)")
    closest_child_name: Optional[str] = Field(None, max_length=50, description="最亲子女名 (小军)")
    favorite_tv_show: Optional[str] = Field(None, max_length=100, description="喜欢看的节目")
    health_focus: Optional[str] = Field(None, max_length=50, description="健康关注点")


@router.put("/onboarding/profile")
async def update_onboarding_profile(
    body: OnboardingProfileRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家属注册时填写老人个性化字段（影响 3 句话激活质量）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)

    from app.models.database import User
    user = db.query(User).filter(User.id == elder_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="老人不存在")

    for field_name in ("family_name", "addressed_as", "closest_child_name",
                       "favorite_tv_show", "health_focus"):
        v = getattr(body, field_name, None)
        if v is not None:
            setattr(user, field_name, v)
    db.commit()
    return {
        "ok": True,
        "user_id": elder_id,
        "fields_set": {
            f: getattr(user, f) for f in
            ("family_name", "addressed_as", "closest_child_name",
             "favorite_tv_show", "health_focus")
        },
    }


@router.get("/onboarding/activation")
async def get_activation_script(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    拉取 3 句话激活脚本。
    StandbyScreen 在首次访问时调用。
    返回 idempotent: is_first_visit 字段告诉前端是否首次。
    """
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)

    from app.services.companion_onboarding_service import companion_onboarding_service
    is_first = not companion_onboarding_service.is_onboarded(db, elder_id)

    # 可选：拿 wttr.in 实时天气作为第 2 句注入
    weather_desc = None
    try:
        from app.services.weather_service import get_forecast_sync, DEFAULT_CITY
        wf = get_forecast_sync(DEFAULT_CITY)
        if wf:
            weather_desc = wf.tomorrow_weather_desc or None
    except Exception:
        pass

    script = companion_onboarding_service.generate_activation_script(
        db, elder_id, weather_desc=weather_desc,
    )
    return {
        "is_first_visit": is_first,
        "dialect": script.dialect,
        "estimated_total_seconds": script.estimated_total_seconds,
        "lines": [script.line_1, script.line_2, script.line_3],
        "full_text": script.as_full_text(),
    }


@router.post("/onboarding/mark-done")
async def mark_onboarding_done(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """老人首次激活完成后调用（StandbyScreen 播完 3 句话即触发）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.companion_onboarding_service import companion_onboarding_service
    companion_onboarding_service.mark_onboarded(db, elder_id)
    return {"ok": True}


@router.get("/onboarding/followup/{day_offset}")
async def get_followup(
    day_offset: int,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    拉取 D1/D3/D7 唤回脚本。
    day_offset 必须 in [1, 3, 7]，否则 400。
    已触发过则返 null。
    """
    _require_enabled()
    if day_offset not in (1, 3, 7):
        raise HTTPException(status_code=400, detail="day_offset 必须是 1, 3, 或 7")
    elder_id = _resolve_elder_id(current_user)
    from app.services.companion_onboarding_service import companion_onboarding_service
    script = companion_onboarding_service.generate_followup(db, elder_id, day_offset)
    if not script:
        return {"available": False, "reason": "尚未 onboarded 或本次 day 已触发"}
    return {
        "available": True,
        "day_offset": script.day_offset,
        "trigger_type": script.trigger_type,
        "text": script.text,
    }


@router.delete("/confirmations/{confirm_id}")
async def cancel_confirmation(
    confirm_id: str,
    current_user: UserInfo = Depends(get_current_user),
):
    """老人取消某个待确认操作（如 SOS 误触）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.proactive_engagement import get_store
    ok = get_store().consume_confirmation(confirm_id, elder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="confirmation 不存在或已失效")
    return {"ok": True, "cancelled": confirm_id}


# ===== r19 · S 选项 · 陪伴值养成系统 =====


class RedeemRequest(BaseModel):
    item_key: str = Field(..., description="兑换码，见 GET /points/catalog")
    context: Optional[dict] = Field(None, description="约束上下文，如 {is_birthday_today: true}")


@router.get("/points/balance")
async def get_points_balance(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """陪伴值余额 + 累计统计"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.companion_points_service import companion_points_service
    row = companion_points_service.get_or_create(db, elder_id)
    return {
        "balance": row.balance,
        "lifetime_earned": row.lifetime_earned,
        "lifetime_spent": row.lifetime_spent,
        "streak_days": row.streak_days,
        "last_earned_at": row.last_earned_at.isoformat() if row.last_earned_at else None,
    }


@router.get("/points/ledger")
async def get_points_ledger(
    limit: int = 50,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """陪伴值流水（最近 N 条；不可篡改记录）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.companion_points_service import companion_points_service
    rows = companion_points_service.list_ledger(db, elder_id, limit=limit)
    return {
        "items": [
            {
                "id": r.id,
                "delta": r.delta,
                "type": r.type,
                "note": r.note,
                "balance_after": r.balance_after,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/points/catalog")
async def get_redemption_catalog():
    """兑换池 —— 不需鉴权（前端展示）"""
    _require_enabled()
    from app.services.companion_points_service import REDEMPTION_CATALOG
    return {
        "items": [
            {
                "key": k,
                "title": v["title"],
                "description": v["description"],
                "cost": v["cost"],
                "constraint": v.get("constraint"),
                "permanent": v.get("permanent", False),
            }
            for k, v in REDEMPTION_CATALOG.items()
        ]
    }


@router.post("/points/redeem")
async def redeem_points(
    body: RedeemRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """老人兑换"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.companion_points_service import (
        InsufficientBalanceError,
        RedemptionConstraintViolatedError,
        UnknownRedemptionError,
        companion_points_service,
    )
    try:
        ledger = companion_points_service.redeem(
            db, elder_id, body.item_key, context=body.context
        )
    except UnknownRedemptionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=402, detail=str(e))  # 402 Payment Required（陪伴值不足）
    except RedemptionConstraintViolatedError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "ledger_id": ledger.id,
        "delta": ledger.delta,
        "balance_after": ledger.balance_after,
        "item_key": body.item_key,
    }


@router.post("/points/signin")
async def daily_signin(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """每日首次签到（前端打开时自动触发；重复调用安全）"""
    _require_enabled()
    elder_id = _resolve_elder_id(current_user)
    from app.services.companion_points_service import companion_points_service
    is_new, streak = companion_points_service.daily_signin(db, elder_id)
    return {"is_new_signin": is_new, "streak_days": streak}
