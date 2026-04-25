"""
北极星指标埋点（r20 · T 选项 · Insight #10）

旧北极星："日报打开率 60%" — 是子女端指标，不反映产品健康度。
新北极星：4 个真正反映"数字生命陪伴"价值的指标。

指标定义（与 Prometheus 集成；无 prometheus_client 时降级为本地计数器）：

| 指标 | Type | 含义 | 业务价值 |
|---|---|---|---|
| elder_active_chat | Counter | 老人主动对话事件 | 反映老人是否真把它当朋友 |
| proactive_acked | Counter | 主动消息被 ack | 反映"主动开口"是关怀还是骚扰 |
| companion_points_earned | Counter | 陪伴值进账 | D30 留存代理指标 |
| companion_points_redeemed | Counter | 陪伴值兑换 | 沉没成本"已实现"信号 |
| family_invite_accepted | Counter | 家庭邀请被接受 | 多人入会率 |
| family_account_created | Counter | 新建家庭账户 | 获客健康度 |
| memory_consolidated | Counter | 记忆整合成功 | "它记得我"的硬证据 |

设计原则：
- **任何业务事件埋点必须 fail-safe** —— 埋点异常不应影响主流程
- **轻量** —— 不引入新依赖，复用既有 prometheus_client
- **聚合可读** —— /api/admin/north-star 端点把瞬时计数器换算成"有用的产品指标"
"""
from __future__ import annotations

import logging
from collections import defaultdict
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ===== Prometheus 指标定义（带优雅降级）=====

try:
    from prometheus_client import Counter, Gauge

    NS_ELDER_ACTIVE_CHAT = Counter(
        "anxinbao_elder_active_chat_total",
        "老人主动对话事件总数",
        ["dialect"],
    )
    NS_PROACTIVE_ACKED = Counter(
        "anxinbao_proactive_acked_total",
        "主动消息被 ack 总数",
        ["trigger_name"],
    )
    NS_PROACTIVE_GENERATED = Counter(
        "anxinbao_proactive_generated_total",
        "主动消息生成总数（含未 ack 的）",
        ["trigger_name"],
    )
    NS_POINTS_EARNED = Counter(
        "anxinbao_companion_points_earned_total",
        "陪伴值进账（按 type）",
        ["earn_type"],
    )
    NS_POINTS_REDEEMED = Counter(
        "anxinbao_companion_points_redeemed_total",
        "陪伴值消耗（按兑换码）",
        ["item_key"],
    )
    NS_FAMILY_INVITE_ACCEPTED = Counter(
        "anxinbao_family_invite_accepted_total",
        "家庭邀请被接受总数",
        ["invited_role"],
    )
    NS_FAMILY_ACCOUNT_CREATED = Counter(
        "anxinbao_family_account_created_total",
        "家庭账户新建总数",
    )
    NS_MEMORY_CONSOLIDATED = Counter(
        "anxinbao_memory_consolidated_total",
        "记忆整合写入总数",
        ["memory_type"],
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus_client 未装，北极星指标降级为本地计数器")
    NS_ELDER_ACTIVE_CHAT = None
    NS_PROACTIVE_ACKED = None
    NS_PROACTIVE_GENERATED = None
    NS_POINTS_EARNED = None
    NS_POINTS_REDEEMED = None
    NS_FAMILY_INVITE_ACCEPTED = None
    NS_FAMILY_ACCOUNT_CREATED = None
    NS_MEMORY_CONSOLIDATED = None
    PROMETHEUS_AVAILABLE = False


# ===== 本地计数器（降级 / /admin/north-star 端点用）=====

_LOCAL_COUNTERS: Dict[str, int] = defaultdict(int)
_LOCAL_LOCK = Lock()


def _bump_local(name: str, labels: Optional[Dict[str, str]] = None, by: int = 1) -> None:
    """本地计数器 + 1（线程安全）"""
    if labels:
        key = name + "{" + ",".join(f"{k}={v}" for k, v in sorted(labels.items())) + "}"
    else:
        key = name
    with _LOCAL_LOCK:
        _LOCAL_COUNTERS[key] += by


def get_local_snapshot() -> Dict[str, int]:
    """供 /admin/north-star 端点拿当前快照"""
    with _LOCAL_LOCK:
        return dict(_LOCAL_COUNTERS)


# ===== 公开 record_* API（业务代码 import 后调）=====


def record_elder_chat(dialect: str = "mandarin") -> None:
    try:
        if NS_ELDER_ACTIVE_CHAT is not None:
            NS_ELDER_ACTIVE_CHAT.labels(dialect=dialect or "mandarin").inc()
        _bump_local("elder_active_chat", {"dialect": dialect or "mandarin"})
    except Exception as exc:
        logger.debug(f"[north_star] record_elder_chat 异常: {exc}")


def record_proactive_generated(trigger_name: str) -> None:
    try:
        if NS_PROACTIVE_GENERATED is not None:
            NS_PROACTIVE_GENERATED.labels(trigger_name=trigger_name).inc()
        _bump_local("proactive_generated", {"trigger_name": trigger_name})
    except Exception as exc:
        logger.debug(f"[north_star] record_proactive_generated 异常: {exc}")


def record_proactive_acked(trigger_name: str) -> None:
    try:
        if NS_PROACTIVE_ACKED is not None:
            NS_PROACTIVE_ACKED.labels(trigger_name=trigger_name).inc()
        _bump_local("proactive_acked", {"trigger_name": trigger_name})
    except Exception as exc:
        logger.debug(f"[north_star] record_proactive_acked 异常: {exc}")


def record_points_earned(earn_type: str, amount: int = 1) -> None:
    try:
        if NS_POINTS_EARNED is not None:
            NS_POINTS_EARNED.labels(earn_type=earn_type).inc(amount)
        _bump_local("points_earned", {"earn_type": earn_type}, by=amount)
    except Exception as exc:
        logger.debug(f"[north_star] record_points_earned 异常: {exc}")


def record_points_redeemed(item_key: str, cost: int = 0) -> None:
    try:
        if NS_POINTS_REDEEMED is not None:
            NS_POINTS_REDEEMED.labels(item_key=item_key).inc(cost or 1)
        _bump_local("points_redeemed", {"item_key": item_key}, by=cost or 1)
    except Exception as exc:
        logger.debug(f"[north_star] record_points_redeemed 异常: {exc}")


def record_family_invite_accepted(invited_role: str = "caretaker") -> None:
    try:
        if NS_FAMILY_INVITE_ACCEPTED is not None:
            NS_FAMILY_INVITE_ACCEPTED.labels(invited_role=invited_role).inc()
        _bump_local("family_invite_accepted", {"invited_role": invited_role})
    except Exception as exc:
        logger.debug(f"[north_star] record_family_invite_accepted 异常: {exc}")


def record_family_account_created() -> None:
    try:
        if NS_FAMILY_ACCOUNT_CREATED is not None:
            NS_FAMILY_ACCOUNT_CREATED.inc()
        _bump_local("family_account_created")
    except Exception as exc:
        logger.debug(f"[north_star] record_family_account_created 异常: {exc}")


def record_memory_consolidated(memory_type: str) -> None:
    try:
        if NS_MEMORY_CONSOLIDATED is not None:
            NS_MEMORY_CONSOLIDATED.labels(memory_type=memory_type).inc()
        _bump_local("memory_consolidated", {"memory_type": memory_type})
    except Exception as exc:
        logger.debug(f"[north_star] record_memory_consolidated 异常: {exc}")


# ===== 业务级聚合 view（供 /admin/north-star 端点）=====


def compute_north_star_view() -> Dict[str, any]:
    """
    把瞬时累计 → 业务可读的"北极星仪表盘"。

    注意：当前是进程内累计，**不是真实日活/月活**（重启清零）。
    生产场景应配合 Prometheus 拉取 + Grafana 看板做时间序列。
    本端点仅供运维快速验证埋点是否生效。
    """
    snap = get_local_snapshot()

    # 按 prefix 聚合
    def _sum_prefix(prefix: str) -> int:
        return sum(v for k, v in snap.items() if k.startswith(prefix))

    elder_chat_total = _sum_prefix("elder_active_chat")
    proactive_gen = _sum_prefix("proactive_generated")
    proactive_ack = _sum_prefix("proactive_acked")
    ack_rate = round(proactive_ack / proactive_gen, 3) if proactive_gen > 0 else 0.0

    return {
        "_note": "进程内累计，重启清零；生产请用 Prometheus 时间序列",
        "_prometheus_available": PROMETHEUS_AVAILABLE,
        "north_star": {
            "elder_chat_events_total": elder_chat_total,
            "proactive_messages_generated": proactive_gen,
            "proactive_messages_acked": proactive_ack,
            "proactive_ack_rate": ack_rate,
            "companion_points_earned": _sum_prefix("points_earned"),
            "companion_points_redeemed": _sum_prefix("points_redeemed"),
            "family_accounts_created": _sum_prefix("family_account_created"),
            "family_invites_accepted": _sum_prefix("family_invite_accepted"),
            "memories_consolidated": _sum_prefix("memory_consolidated"),
        },
        "raw": snap,
    }


def reset_local_counters() -> None:
    """仅供测试使用"""
    with _LOCAL_LOCK:
        _LOCAL_COUNTERS.clear()
