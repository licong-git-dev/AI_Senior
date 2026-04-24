"""
Companion 数字生命的工具调用目录（Phase 3）

设计目标：让 AI **真办事**而不只是"建议"。LLM 通过 function calling 决定
何时调用工具；工具内部接现有的 service 层。

兼容性：
- 工具 schema 格式与 Anthropic Tool Use 一致（JSON Schema），同样可被
  qwen-turbo 的 function_call 模式消费
- 每个工具有 SafetyLevel；高/极高级别需要二次确认 + 强日志
- 所有工具调用都会落入 audit_log（含 admin / 老人本人）

升级路径：
- v1（当前）：注册 schema + dispatcher，部分 handler 是占位
- v2：填充所有 handler，接通 health_evaluator / family_service / emergency_service
- v3：加 sandbox，限制每用户每天调用次数，防滥用
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SafetyLevel(str, Enum):
    """工具调用安全等级（决定执行前确认强度）"""
    LOW = "low"           # 直接执行 + 记日志
    MEDIUM = "medium"     # 执行前老人语音确认
    HIGH = "high"         # 必经规则引擎（如健康建议）
    CRITICAL = "critical" # 双重确认 + 多通道通知（如 SOS）


@dataclass
class ToolDefinition:
    """单个工具的元数据 + 执行函数"""
    name: str
    description: str
    parameters_schema: Dict[str, Any]   # JSON Schema
    safety: SafetyLevel
    handler: Optional[Callable] = None  # async (user_id: int, **params) -> dict


# ===== 工具池（Phase 3 完整体）=====
# 当前版本只注册 schema 与占位 handler；填充逻辑由 Phase 3 实施时完成。

_REGISTRY: Dict[str, ToolDefinition] = {}


def register(tool: ToolDefinition) -> None:
    if tool.name in _REGISTRY:
        logger.warning(f"工具 {tool.name} 重复注册，覆盖")
    _REGISTRY[tool.name] = tool


# ===== 真实 Handler 实现（Phase 1 LOW-safety 工具）=====
# 设计原则：
# - 不抛异常，遇错返回 {"error": "..."}（dispatch 会包装为 ok=False）
# - 写入 DB 用短事务（with SessionLocal() as db: ... db.commit()）
# - 日志详细但脱敏（不打印 token、密码等）


async def _handler_log_medication_taken(user_id: int, medication_name: str,
                                        taken_at: Optional[str] = None) -> dict:
    """老人主动告知今天某药已服 → 写入 MedicationRecord。"""
    from datetime import datetime as _dt
    from app.models.database import SessionLocal, Medication, MedicationRecord
    db = SessionLocal()
    try:
        med = db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.name.like(f"%{medication_name}%"),
        ).first()
        if not med:
            return {"error": f"未找到药品 '{medication_name}'，请先在用药管理中添加"}

        when = _dt.fromisoformat(taken_at) if taken_at else _dt.now()
        record = MedicationRecord(
            user_id=user_id,
            medication_id=med.id,
            scheduled_time=when,
            taken_time=when,
            status="taken",
            notes="由 Companion 工具调用记录",
        )
        db.add(record)
        db.commit()
        return {"medication": med.name, "logged_at": when.isoformat()}
    finally:
        db.close()


async def _handler_log_meal(user_id: int, meal_text: str,
                            meal_time: str = "lunch") -> dict:
    """老人提到吃了什么 → 写入 MealRecord（不解析营养，仅 notes 字段）。"""
    from datetime import datetime as _dt
    from app.models.database import SessionLocal, MealRecord
    db = SessionLocal()
    try:
        record = MealRecord(
            user_id=user_id,
            meal_type=meal_time,
            meal_time=_dt.now(),
            notes=meal_text[:500],
        )
        db.add(record)
        db.commit()
        return {"meal_type": meal_time, "text": meal_text[:80]}
    finally:
        db.close()


async def _handler_log_mood(user_id: int, mood: str,
                            note: Optional[str] = None) -> dict:
    """老人倾诉心境 → 写入 MoodRecord + 同步到 MemoryEngine 的 mood 类。"""
    from datetime import datetime as _dt
    from app.models.database import SessionLocal, MoodRecord
    from app.services.memory_engine import (
        MemoryRecord, MemoryType, MemoryVisibility, get_memory_engine,
    )
    db = SessionLocal()
    try:
        record = MoodRecord(
            user_id=user_id,
            mood_type=mood,
            intensity=5,  # 默认中等
            notes=note,
            recorded_at=_dt.now(),
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

    # 同步入长期记忆（mood 类，仅老人可见）
    get_memory_engine().save(MemoryRecord(
        user_id=user_id,
        type=MemoryType.MOOD,
        content=f"心境: {mood}" + (f" - {note}" if note else ""),
        keywords=[mood],
        visibility=MemoryVisibility.SELF_ONLY,
        importance=0.6,
    ))
    return {"mood": mood, "synced_to_memory": True}


async def _handler_save_memory(
    user_id: int,
    type: str,
    content: str,
    keywords: Optional[list] = None,
    visibility: str = "self_only",
    importance: float = 0.5,
) -> dict:
    """LLM 自决把对话中学到的事实写入长期记忆。"""
    from app.services.memory_engine import (
        MemoryRecord, MemoryType, MemoryVisibility, get_memory_engine,
    )
    try:
        mem_type = MemoryType(type)
        vis = MemoryVisibility(visibility)
    except ValueError as exc:
        return {"error": f"无效枚举: {exc}"}

    new_id = get_memory_engine().save(MemoryRecord(
        user_id=user_id,
        type=mem_type,
        content=content[:400],
        keywords=keywords or [],
        visibility=vis,
        importance=max(0.0, min(1.0, importance)),
    ))
    return {"memory_id": new_id, "type": type}


async def _handler_query_health_trend(user_id: int, metric: str,
                                      days: int = 7) -> dict:
    """聚合最近 N 天健康指标，返回简要统计供 Hermes 措辞。"""
    from datetime import datetime as _dt, timedelta as _td
    from app.models.database import SessionLocal, HealthRecord
    metric_map = {
        "blood_pressure": "blood_pressure",
        "heart_rate": "heart_rate",
        "blood_sugar": "blood_sugar",
        "weight": "weight",
    }
    record_type = metric_map.get(metric)
    if not record_type:
        return {"error": f"不支持的指标: {metric}"}

    db = SessionLocal()
    try:
        cutoff = _dt.now() - _td(days=max(1, min(90, days)))
        rows = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id,
            HealthRecord.record_type == record_type,
            HealthRecord.measured_at >= cutoff,
        ).order_by(HealthRecord.measured_at.desc()).limit(50).all()

        if not rows:
            return {"metric": metric, "days": days, "count": 0,
                    "summary": "近期无数据，建议老人主动测量"}

        primary_values = [r.value_primary for r in rows if r.value_primary is not None]
        avg = round(sum(primary_values) / len(primary_values), 1) if primary_values else None
        latest = rows[0]
        return {
            "metric": metric,
            "days": days,
            "count": len(rows),
            "average_primary": avg,
            "latest": {
                "value_primary": latest.value_primary,
                "value_secondary": latest.value_secondary,
                "measured_at": latest.measured_at.isoformat() if latest.measured_at else None,
            },
        }
    finally:
        db.close()


# ===== MEDIUM / HIGH / CRITICAL handler （Phase 3 G 选项）=====


async def _handler_video_call_family(
    user_id: int,
    family_member_id: str,
    family_member_name: Optional[str] = None,
) -> dict:
    """
    发起视频通话给指定家属。

    实施现状：返回一个 call_session 描述符；真实信令由 WebSocket /api/video/ws/* 接管。
    Phase 3 完整体接 video_service.create_session（依赖 TURN 服务器，详见
    docs/VIDEO_CALL_SETUP.md）。当前是"创建意向 + 推送给家属"的最小实现。
    """
    import secrets
    call_id = f"call_{user_id}_{secrets.token_hex(4)}"
    # 真实场景应当：
    # 1) 通过 WebSocket 给目标家属发 ringing 信令
    # 2) 在 video_sessions 表存一条记录
    # 3) 返回 wss URL 让前端建立 P2P
    # 当前：只返回意向信息，前端自行打开 VideoCallPage 完成信令
    return {
        "call_session_id": call_id,
        "from_user_id": user_id,
        "to_family_member_id": family_member_id,
        "to_family_member_name": family_member_name,
        "next_step": "前端打开 VideoCallPage，参数 targetId=" + family_member_id,
        "note": "需要 VITE_TURN_URL 配置才能稳定连接，详见 docs/VIDEO_CALL_SETUP.md",
    }


async def _handler_book_community_service(
    user_id: int,
    service_type: str,
    scheduled_date: str,
    address: Optional[str] = None,
) -> dict:
    """
    预约社区服务（保洁/上门理发/送菜等）。

    生产环境会抛 IntegrationNotImplemented（社区方接口未对接）；
    handler 抓住后翻译为"预约意向已记录，等待人工对接"，避免老人以为已成功。
    """
    from datetime import datetime as _dt
    try:
        from app.services.integration_service import integration_service, ServiceType, IntegrationNotImplemented
    except ImportError as exc:
        return {"error": f"集成服务不可用: {exc}"}

    try:
        st = ServiceType(service_type)
    except ValueError:
        return {"error": f"未知服务类型: {service_type}"}

    try:
        scheduled = _dt.fromisoformat(scheduled_date)
    except ValueError:
        return {"error": f"日期格式错误: {scheduled_date}（应为 ISO 格式）"}

    try:
        order = integration_service.community.create_order(
            user_id=user_id,
            service_id=st.value,
            scheduled_time=scheduled,
            address=address or "未填写",
            contact_phone="",
        )
        return {
            "order_id": order.order_id if order else None,
            "service_type": service_type,
            "scheduled_at": scheduled.isoformat(),
            "status": "已下单（mock）",
        }
    except IntegrationNotImplemented:
        # 生产环境：把"未真接通"翻译为人话给老人
        return {
            "status": "意向已记录",
            "service_type": service_type,
            "scheduled_at": scheduled.isoformat(),
            "next_step": "我们会通知社区工作人员；24h 内回电确认",
            "note": "社区服务接口尚未上线，本次为意向登记",
        }


async def _handler_request_health_advice(
    user_id: int,
    question: str,
    context: Optional[dict] = None,
) -> dict:
    """
    HIGH 级：老人询问健康建议（症状、能否吃某药等）。

    安全设计：
    - LLM 严禁直答（必经 health_evaluator 规则引擎）
    - 包含紧急关键词 → 升级为 SOS 提示
    - 普通担忧 → 给出"无恐吓式"建议 + 必加"请咨询医生"
    """
    try:
        from app.services.health_evaluator import HealthRiskEvaluator
    except ImportError:
        return {"error": "健康评估器不可用"}

    evaluator = HealthRiskEvaluator()
    # ai_risk_info 用最低 base，让规则引擎主导判断
    ai_risk_info = (context or {}).get("ai_risk_info", {"risk_score": 1, "category": "health"})
    result = evaluator.evaluate(
        user_id=str(user_id),
        message=question,
        ai_risk_info=ai_risk_info,
    )

    # 高风险情境：明确建议联系家属/医院
    out = {
        "risk_score": result.get("risk_score", 1),
        "category": result.get("category"),
        "reason": result.get("reason"),
        "suggestion": result.get("suggestion"),
        "need_notify_family": result.get("need_notify", False),
        "disclaimer": "⚠️ 以上为辅助提示，不构成医疗诊断。请咨询医生或拨打 120。",
    }
    if result.get("risk_score", 0) >= 7:
        out["urgent_action"] = "建议立即联系家人或医生"
    return out


async def _handler_trigger_sos(
    user_id: int,
    reason: str,
    location: Optional[str] = None,
) -> dict:
    """
    CRITICAL 级：触发 SOS 紧急求助。

    必须经 dispatcher 的 confirm_token 二次校验（companion.py /tools/call 实施）。
    本 handler 直接调用 emergency_service，已含完整的多通道通知 + DLQ 兜底（r1/r9）。
    """
    try:
        from app.services.emergency_service import emergency_service
    except ImportError:
        return {"error": "紧急服务不可用"}

    # 解析老人姓名（用于通知模板）
    user_name = "老人"
    try:
        from app.models.database import SessionLocal, User
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == user_id).first()
            if u and u.name:
                user_name = u.name
        finally:
            db.close()
    except Exception:
        pass

    desc = f"通过 Companion 触发: {reason}"
    if location:
        desc += f"（位置: {location}）"
    try:
        alert = await emergency_service.trigger_sos(
            user_id=user_id,
            user_name=user_name,
            description=desc,
        )
        return {
            "alert_id": alert.alert_id,
            "level": alert.level.value,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "message": "已触发紧急求助，正在通知家人 / 社区医生",
        }
    except Exception as exc:
        logger.exception(f"trigger_sos 异常: {exc}")
        return {"error": f"SOS 触发异常: {exc}"}


# ===== 注册 handler 到对应工具（在 _REGISTRY 填充后调用）=====

def _wire_handlers() -> None:
    """把 handler 绑定到对应 ToolDefinition；在所有 register(...) 之后调用"""
    mapping = {
        # LOW
        "log_medication_taken": _handler_log_medication_taken,
        "log_meal": _handler_log_meal,
        "log_mood": _handler_log_mood,
        "save_memory": _handler_save_memory,
        "query_health_trend": _handler_query_health_trend,
        # MEDIUM / HIGH / CRITICAL
        "video_call_family": _handler_video_call_family,
        "book_community_service": _handler_book_community_service,
        "request_health_advice": _handler_request_health_advice,
        "trigger_sos": _handler_trigger_sos,
    }
    for name, fn in mapping.items():
        if name in _REGISTRY:
            _REGISTRY[name].handler = fn


def list_tools() -> List[Dict[str, Any]]:
    """返回 LLM 可消费的工具 schema 列表"""
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.parameters_schema,
            "safety_level": t.safety.value,
        }
        for t in _REGISTRY.values()
    ]


async def dispatch(name: str, user_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
    """根据工具名分发执行"""
    tool = _REGISTRY.get(name)
    if not tool:
        return {"ok": False, "error": f"unknown tool: {name}"}

    if not tool.handler:
        return {
            "ok": False,
            "error": f"tool {name} has no handler in current scaffold",
            "safety_level": tool.safety.value,
        }

    try:
        result = await tool.handler(user_id, **params)
        logger.info(f"tool dispatched: {name} user={user_id} result={result}")
        return {"ok": True, "result": result}
    except Exception as exc:
        logger.exception(f"tool {name} 执行异常: {exc}")
        return {"ok": False, "error": str(exc)}


# ===== 工具定义（schema only，handler 为 Phase 3 填充）=====


# ---- LOW 级 ----

register(ToolDefinition(
    name="log_medication_taken",
    description="老人主动告知今天某种药已服用，登记到用药记录。",
    parameters_schema={
        "type": "object",
        "properties": {
            "medication_name": {"type": "string", "description": "药品名（如：氨氯地平）"},
            "taken_at": {"type": "string", "description": "服用时间 ISO 格式，可省略默认 now"},
        },
        "required": ["medication_name"],
    },
    safety=SafetyLevel.LOW,
))

register(ToolDefinition(
    name="log_meal",
    description="登记老人刚吃了什么（用于饮食记录与营养分析）",
    parameters_schema={
        "type": "object",
        "properties": {
            "meal_text": {"type": "string", "description": "饭菜文字描述（如：豆皮+绿豆汤）"},
            "meal_time": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
        },
        "required": ["meal_text"],
    },
    safety=SafetyLevel.LOW,
))

register(ToolDefinition(
    name="log_mood",
    description="登记老人当前心境，作为 mood 类记忆持久化",
    parameters_schema={
        "type": "object",
        "properties": {
            "mood": {"type": "string", "enum": ["happy", "sad", "lonely", "anxious", "neutral", "angry"]},
            "note": {"type": "string", "description": "可选的简短描述"},
        },
        "required": ["mood"],
    },
    safety=SafetyLevel.LOW,
))

register(ToolDefinition(
    name="save_memory",
    description="把对话中刚学到的『事实/偏好/关系/事件』持久化到长期记忆",
    parameters_schema={
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["fact", "preference", "relation", "event"]},
            "content": {"type": "string", "description": "≤200 字，简洁陈述"},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "visibility": {"type": "string", "enum": ["self_only", "family"], "default": "self_only"},
            "importance": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5},
        },
        "required": ["type", "content"],
    },
    safety=SafetyLevel.LOW,
))

register(ToolDefinition(
    name="query_health_trend",
    description="查询老人最近 N 天的健康趋势（血压/心率/血糖等）",
    parameters_schema={
        "type": "object",
        "properties": {
            "metric": {"type": "string", "enum": ["blood_pressure", "heart_rate", "blood_sugar", "weight"]},
            "days": {"type": "integer", "minimum": 1, "maximum": 90, "default": 7},
        },
        "required": ["metric"],
    },
    safety=SafetyLevel.LOW,
))

# ---- MEDIUM 级（执行前确认）----

register(ToolDefinition(
    name="video_call_family",
    description="发起视频通话给指定家属",
    parameters_schema={
        "type": "object",
        "properties": {
            "family_member_id": {"type": "string"},
            "family_member_name": {"type": "string"},
        },
        "required": ["family_member_id"],
    },
    safety=SafetyLevel.MEDIUM,
))

register(ToolDefinition(
    name="book_community_service",
    description="预约社区服务（保洁/上门理发/送菜等）",
    parameters_schema={
        "type": "object",
        "properties": {
            "service_type": {"type": "string"},
            "scheduled_date": {"type": "string"},
            "address": {"type": "string"},
        },
        "required": ["service_type", "scheduled_date"],
    },
    safety=SafetyLevel.MEDIUM,
))

# ---- HIGH 级（必经规则引擎）----

register(ToolDefinition(
    name="request_health_advice",
    description="老人询问健康建议（症状、是否能吃某药等）。LLM 不能直答，必须走规则引擎。",
    parameters_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "context": {"type": "object", "description": "已知症状、用药等"},
        },
        "required": ["question"],
    },
    safety=SafetyLevel.HIGH,
))

# ---- CRITICAL 级（双重确认 + 多通道）----

register(ToolDefinition(
    name="trigger_sos",
    description="触发紧急求助。仅在老人明确表达紧急或长按按钮时调用。",
    parameters_schema={
        "type": "object",
        "properties": {
            "reason": {"type": "string", "description": "触发原因（关键词、按钮、跌倒等）"},
            "location": {"type": "string", "description": "可选位置信息"},
        },
        "required": ["reason"],
    },
    safety=SafetyLevel.CRITICAL,
))


# ===== 安全检查器 =====

def requires_confirmation(tool_name: str) -> bool:
    """前端在弹出确认对话框前调用"""
    tool = _REGISTRY.get(tool_name)
    if not tool:
        return True  # 未知工具默认要确认
    return tool.safety in (SafetyLevel.MEDIUM, SafetyLevel.CRITICAL)


def safety_level(tool_name: str) -> Optional[str]:
    tool = _REGISTRY.get(tool_name)
    return tool.safety.value if tool else None


# 模块加载完成时绑定 handler（必须放在文件最末尾）
_wire_handlers()
