"""
MemoryConsolidator · 对话事实抽取（Phase 1 关键组件）

职责：每轮对话结束后，**异步**从老人发言中抽取：
- 新事实（fact）：如"我有 3 个孙子"
- 新偏好（preference）：如"我不喜欢吃辣"
- 新关系（relation）：如"小军是我大儿子"
- 新事件（event）：如"昨天我去了东湖"

关键设计：
1. **异步执行**（不阻塞 Hermes 主对话回路）
2. **失败静默**（抽取失败不影响老人体验，仅记日志）
3. **去重**：抽到的事实先与已有 fact 类记忆做相似度比较，避免重复
4. **小模型**：用 qwen-turbo（最便宜），单次成本 < ¥0.001
5. **限频**：单老人 30 秒内最多触发 1 次（防止快速对话刷爆 LLM）

未实施 LLM 调用时的 fallback：用关键词规则做轻量抽取，保证基线功能。
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict, List, Optional

from app.services.memory_engine import (
    MemoryRecord,
    MemoryType,
    MemoryVisibility,
    get_memory_engine,
)

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationCandidate:
    """LLM 抽取出的候选事实（待入库前）"""
    type: str  # fact / preference / relation / event
    content: str
    keywords: List[str]
    importance: float = 0.5


# ===== 限频（单老人 30 秒 1 次）=====
_LAST_RUN: Dict[int, float] = {}
_LAST_RUN_LOCK = Lock()
_MIN_INTERVAL_SEC = 30.0


def _can_run_now(user_id: int) -> bool:
    with _LAST_RUN_LOCK:
        last = _LAST_RUN.get(user_id, 0.0)
        now = time.time()
        if now - last < _MIN_INTERVAL_SEC:
            return False
        _LAST_RUN[user_id] = now
        return True


# ===== 关键词 fallback（无 LLM 时也能用）=====

_RELATION_KW = {
    "儿子": "relation", "女儿": "relation", "孙子": "relation",
    "孙女": "relation", "老伴": "relation", "媳妇": "relation",
    "女婿": "relation", "小军": "relation", "小红": "relation",
}

_PREFERENCE_KW = {
    "喜欢": "preference", "爱吃": "preference", "讨厌": "preference",
    "不喜欢": "preference", "不爱": "preference",
}

_EVENT_KW = {
    "昨天": "event", "今天": "event", "上周": "event", "上次": "event",
    "前几天": "event", "刚才": "event", "明天": "event", "周末": "event",
}


def _keyword_extract(user_message: str) -> List[ConsolidationCandidate]:
    """
    无 LLM 时的 fallback：按关键词触发，把短句直接作为候选。
    精度低于 LLM，但不会幻觉，且零成本。
    """
    msg = user_message.strip()
    if len(msg) < 4 or len(msg) > 100:
        return []

    candidates = []
    for kw, type_ in (
        list(_RELATION_KW.items())
        + list(_PREFERENCE_KW.items())
        + list(_EVENT_KW.items())
    ):
        if kw in msg:
            candidates.append(ConsolidationCandidate(
                type=type_,
                content=msg[:120],
                keywords=[kw],
                importance=0.4,
            ))
            break  # 一句话只产一条候选，避免重复
    return candidates


# ===== LLM 抽取（Phase 1 核心，调用 qwen-turbo）=====


_LLM_PROMPT = """你是一个事实抽取助手。从下面这位长辈刚才说的话里，抽取所有"
"值得长期记忆"的事实/偏好/关系/事件。

抽取规则：
- 只抽取含具体信息的句子（如"我有 3 个孙子"是事实；"今天天气真好"不是）
- 严禁编造未提到的内容
- 每条 ≤80 字，简洁陈述
- 类型必须是: fact / preference / relation / event 之一
- 如果没有可抽取的内容，返回空数组

输出 JSON 数组（不要 markdown 代码块），示例：
[
  {"type": "fact", "content": "有 3 个孙子", "keywords": ["孙子"]},
  {"type": "preference", "content": "喜欢吃豆皮", "keywords": ["豆皮", "饮食"]}
]

长辈说："""


async def _llm_extract(user_message: str) -> List[ConsolidationCandidate]:
    """
    用 qwen-turbo 抽取事实。失败时返回空列表，由 fallback 兜底。
    """
    try:
        from app.services.qwen_service import qwen_service
    except ImportError:
        return []

    full_prompt = _LLM_PROMPT + user_message

    try:
        # qwen_service.chat_async 是项目主要 LLM 调用入口
        # 这里用一个临时 user_id（事实抽取不需要老人身份上下文）
        raw = await qwen_service.chat_async(
            user_id="memory_consolidator",
            message=full_prompt,
            system_prompt="你是事实抽取助手，只输出 JSON 数组，不输出其他文本。",
        )
    except Exception as exc:
        logger.warning(f"MemoryConsolidator LLM 抽取失败: {exc}")
        return []

    # LLM 输出可能含 markdown 代码块，用正则提取 JSON
    json_match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not json_match:
        return []

    try:
        items = json.loads(json_match.group(0))
    except json.JSONDecodeError:
        logger.warning(f"MemoryConsolidator JSON 解析失败: {raw[:200]}")
        return []

    candidates = []
    for it in items[:5]:  # 单轮最多 5 条，防爆
        if not isinstance(it, dict):
            continue
        type_ = it.get("type")
        content = (it.get("content") or "").strip()
        if type_ not in ("fact", "preference", "relation", "event"):
            continue
        if not content or len(content) > 200:
            continue
        candidates.append(ConsolidationCandidate(
            type=type_,
            content=content[:120],
            keywords=it.get("keywords", []) or [],
            importance=0.5,
        ))
    return candidates


# ===== 去重（避免把"有 3 个孙子"重复入库）=====


def _is_duplicate(user_id: int, cand: ConsolidationCandidate) -> bool:
    """
    简单去重：召回同 type 的已存在记忆，content 完全相同或包含关系视为重复。
    """
    engine = get_memory_engine()
    existing = engine.recall(
        user_id=user_id,
        query=cand.content,
        types=[MemoryType(cand.type)],
        top_k=5,
    )
    cand_lower = cand.content.lower().strip()
    for ex in existing:
        ex_lower = ex.content.lower().strip()
        if cand_lower == ex_lower:
            return True
        # 短句包含关系也算重复（如新："孙子叫小军"已有："小军是孙子"）
        if len(cand_lower) <= 30 and (cand_lower in ex_lower or ex_lower in cand_lower):
            return True
    return False


# ===== 主入口 =====


async def consolidate(
    user_id: int,
    user_message: str,
    use_llm: bool = True,
) -> List[int]:
    """
    主入口：从一条用户消息抽取记忆并持久化。
    返回新写入的 memory_id 列表（可空）。

    use_llm=False 时仅用关键词 fallback，便于 CI 测试或 LLM 不可用时降级。
    """
    if not _can_run_now(user_id):
        logger.debug(f"MemoryConsolidator 限频跳过: user={user_id}")
        return []

    # LLM 优先，失败用关键词兜底
    candidates: List[ConsolidationCandidate] = []
    if use_llm:
        candidates = await _llm_extract(user_message)
    if not candidates:
        candidates = _keyword_extract(user_message)

    if not candidates:
        return []

    engine = get_memory_engine()
    new_ids: List[int] = []
    for cand in candidates:
        if _is_duplicate(user_id, cand):
            continue
        try:
            new_id = engine.save(MemoryRecord(
                user_id=user_id,
                type=MemoryType(cand.type),
                content=cand.content,
                keywords=cand.keywords,
                visibility=MemoryVisibility.SELF_ONLY,
                importance=cand.importance,
            ))
            new_ids.append(new_id)
        except Exception as exc:
            logger.warning(f"MemoryConsolidator 保存失败: {exc}")

    if new_ids:
        logger.info(
            f"MemoryConsolidator user={user_id} 抽取 {len(candidates)} 条 → "
            f"入库 {len(new_ids)} 条 (id={new_ids})"
        )
    return new_ids


def schedule_consolidation(user_id: int, user_message: str) -> None:
    """
    fire-and-forget：不阻塞主对话。

    Hermes 每轮对话后调用这个函数即可，错误自动吞掉。
    用 asyncio.create_task 避免协程未 await 的告警。
    """
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(_safe_consolidate(user_id, user_message))
    except RuntimeError:
        # 非 async 上下文调用（如同步代码）→ 用 asyncio.run
        try:
            asyncio.run(_safe_consolidate(user_id, user_message))
        except Exception as exc:
            logger.warning(f"schedule_consolidation 同步执行失败: {exc}")


async def _safe_consolidate(user_id: int, user_message: str) -> None:
    try:
        await consolidate(user_id, user_message)
    except Exception as exc:
        logger.exception(f"MemoryConsolidator 异常: {exc}")
