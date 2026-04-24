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
