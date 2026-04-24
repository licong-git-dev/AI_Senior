"""
ProactiveEngagement · 主动开口编排器（Phase 2 核心）

职责：
1. 由 scheduler 周期触发（早 8 / 午 13 / 晚 19，每天 3 次）
2. 评估所有 trigger
3. 检查老人 DND 配置（"请勿打扰"时段）
4. 检查日配额（默认每天最多 4 次主动消息）
5. 检查 cooldown（同 trigger 类型 N 小时不重复）
6. 调用 Hermes 生成消息（不强制走 LLM，可降级模板）
7. 写入 ProactiveInbox 由前端拉取

不直接走推送通道 —— 推送由 NotificationService 接管（已有 retry + DLQ）。
本模块只负责"决定说什么、什么时候说"。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, time as dtime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ===== 配置 =====

DAILY_QUOTA = 4         # 每老人每天最多 4 条主动消息
DEFAULT_DND_START = "22:00"   # 默认请勿打扰
DEFAULT_DND_END = "07:00"
PRIORITY_BREAK_DND = 9        # 优先级 ≥ 9 才能突破 DND（如重要纪念日）


@dataclass
class ProactiveMessage:
    user_id: int
    trigger_name: str
    text: str
    priority: int
    reason: str = ""
    suggested_topic: str = ""
    delivered: bool = False           # 是否被前端拉取过
    acknowledged: bool = False        # 老人是否回应了
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None


# ===== 持久化（独立 SQLite，与主库隔离）=====


class ProactiveStore:
    """主动消息 + DND 配置存储；线程安全"""

    def __init__(self, db_path: Optional[str] = None):
        import os
        self.db_path = db_path or os.environ.get(
            "COMPANION_PROACTIVE_DB", "./companion_proactive.db"
        )
        self._local = threading.local()
        self._init_schema()

    @contextmanager
    def _conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                self.db_path, isolation_level=None, check_same_thread=True,
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        yield self._local.conn

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS proactive_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    trigger_name TEXT NOT NULL,
                    text TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    reason TEXT,
                    suggested_topic TEXT,
                    delivered INTEGER DEFAULT 0,
                    acknowledged INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS dnd_configs (
                    user_id INTEGER PRIMARY KEY,
                    dnd_start TEXT NOT NULL DEFAULT '22:00',
                    dnd_end TEXT NOT NULL DEFAULT '07:00',
                    daily_quota INTEGER NOT NULL DEFAULT 4,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS trigger_cooldowns (
                    user_id INTEGER NOT NULL,
                    trigger_name TEXT NOT NULL,
                    fired_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, trigger_name)
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS ix_pm_user_created ON proactive_messages(user_id, created_at)")

    # ----- 主动消息 -----

    def save_message(self, msg: ProactiveMessage) -> int:
        with self._conn() as c:
            cur = c.execute(
                """INSERT INTO proactive_messages
                (user_id, trigger_name, text, priority, reason, suggested_topic, delivered, acknowledged, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)""",
                (msg.user_id, msg.trigger_name, msg.text, msg.priority,
                 msg.reason, msg.suggested_topic, msg.created_at),
            )
            return cur.lastrowid or 0

    def list_inbox(self, user_id: int, limit: int = 20,
                   only_undelivered: bool = False) -> List[ProactiveMessage]:
        with self._conn() as c:
            sql = "SELECT * FROM proactive_messages WHERE user_id = ?"
            params: list = [user_id]
            if only_undelivered:
                sql += " AND delivered = 0"
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = c.execute(sql, params).fetchall()
            return [self._row_to_msg(r) for r in rows]

    def mark_delivered(self, message_id: int, user_id: int) -> bool:
        with self._conn() as c:
            cur = c.execute(
                "UPDATE proactive_messages SET delivered = 1 WHERE id = ? AND user_id = ?",
                (message_id, user_id),
            )
            return cur.rowcount > 0

    def acknowledge(self, message_id: int, user_id: int) -> bool:
        with self._conn() as c:
            cur = c.execute(
                "UPDATE proactive_messages SET acknowledged = 1 WHERE id = ? AND user_id = ?",
                (message_id, user_id),
            )
            return cur.rowcount > 0

    def count_today(self, user_id: int) -> int:
        today = datetime.now().date().isoformat()
        with self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) AS n FROM proactive_messages WHERE user_id = ? AND date(created_at) = ?",
                (user_id, today),
            ).fetchone()
            return row["n"]

    # ----- DND 配置 -----

    def get_dnd(self, user_id: int) -> Dict[str, any]:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM dnd_configs WHERE user_id = ?", (user_id,),
            ).fetchone()
            if not row:
                return {
                    "user_id": user_id,
                    "dnd_start": DEFAULT_DND_START,
                    "dnd_end": DEFAULT_DND_END,
                    "daily_quota": DAILY_QUOTA,
                    "enabled": True,
                }
            return dict(row)

    def upsert_dnd(self, user_id: int, dnd_start: Optional[str] = None,
                   dnd_end: Optional[str] = None, daily_quota: Optional[int] = None,
                   enabled: Optional[bool] = None) -> Dict[str, any]:
        existing = self.get_dnd(user_id)
        merged = {
            "dnd_start": dnd_start or existing["dnd_start"],
            "dnd_end": dnd_end or existing["dnd_end"],
            "daily_quota": daily_quota if daily_quota is not None else existing["daily_quota"],
            "enabled": int(enabled) if enabled is not None else int(existing["enabled"]),
        }
        with self._conn() as c:
            c.execute(
                """INSERT INTO dnd_configs
                (user_id, dnd_start, dnd_end, daily_quota, enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    dnd_start = excluded.dnd_start,
                    dnd_end = excluded.dnd_end,
                    daily_quota = excluded.daily_quota,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at""",
                (user_id, merged["dnd_start"], merged["dnd_end"],
                 merged["daily_quota"], merged["enabled"],
                 datetime.now().isoformat()),
            )
        return self.get_dnd(user_id)

    # ----- Cooldown -----

    def in_cooldown(self, user_id: int, trigger_name: str, hours: int) -> bool:
        with self._conn() as c:
            row = c.execute(
                "SELECT fired_at FROM trigger_cooldowns WHERE user_id = ? AND trigger_name = ?",
                (user_id, trigger_name),
            ).fetchone()
            if not row:
                return False
            try:
                fired = datetime.fromisoformat(row["fired_at"])
                return (datetime.now() - fired) < timedelta(hours=hours)
            except ValueError:
                return False

    def record_cooldown(self, user_id: int, trigger_name: str) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO trigger_cooldowns (user_id, trigger_name, fired_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, trigger_name) DO UPDATE SET fired_at = excluded.fired_at""",
                (user_id, trigger_name, datetime.now().isoformat()),
            )

    @staticmethod
    def _row_to_msg(row: sqlite3.Row) -> ProactiveMessage:
        return ProactiveMessage(
            id=row["id"],
            user_id=row["user_id"],
            trigger_name=row["trigger_name"],
            text=row["text"],
            priority=row["priority"],
            reason=row["reason"] or "",
            suggested_topic=row["suggested_topic"] or "",
            delivered=bool(row["delivered"]),
            acknowledged=bool(row["acknowledged"]),
            created_at=row["created_at"],
        )


_store: Optional[ProactiveStore] = None
_store_lock = threading.Lock()


def get_store() -> ProactiveStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = ProactiveStore()
    return _store


# ===== 主入口（被 scheduler 调用）=====


def _is_in_dnd(now: datetime, dnd_start: str, dnd_end: str) -> bool:
    """处理跨午夜的 DND 区间（如 22:00 - 07:00）"""
    try:
        start = dtime.fromisoformat(dnd_start)
        end = dtime.fromisoformat(dnd_end)
    except ValueError:
        return False
    cur = now.time()
    if start <= end:
        return start <= cur < end
    return cur >= start or cur < end


async def evaluate_and_send(user_id: int) -> List[ProactiveMessage]:
    """
    对单个老人评估所有 trigger；通过过滤后调用 Hermes 生成文本并入库。
    返回本次新生成的 ProactiveMessage 列表（可空）。
    """
    from app.services.companion_triggers import evaluate_all

    store = get_store()
    dnd = store.get_dnd(user_id)
    now = datetime.now()
    in_dnd = bool(dnd.get("enabled")) and _is_in_dnd(
        now, dnd["dnd_start"], dnd["dnd_end"]
    )

    today_count = store.count_today(user_id)
    quota = dnd.get("daily_quota") or DAILY_QUOTA
    over_quota = today_count >= quota

    results: List[ProactiveMessage] = []
    for ev in evaluate_all(user_id):
        # 1) DND：仅高优先级（≥9）可突破
        if in_dnd and ev.priority < PRIORITY_BREAK_DND:
            logger.debug(f"[proactive] {ev.trigger_name} 命中 DND，跳过")
            continue
        # 2) 配额
        if over_quota and ev.priority < PRIORITY_BREAK_DND:
            logger.debug(f"[proactive] 已达每日配额 {quota}，跳过 {ev.trigger_name}")
            continue
        # 3) Cooldown
        cooldown = next(
            (t.cooldown_hours for t in __import__(
                "app.services.companion_triggers", fromlist=["ALL_TRIGGERS"]
            ).ALL_TRIGGERS if t.name == ev.trigger_name), 24,
        )
        if store.in_cooldown(user_id, ev.trigger_name, cooldown):
            continue

        # 4) 生成文本：调用 Hermes（如果可用）；失败用模板兜底
        text = await _generate_text(user_id, ev)
        msg = ProactiveMessage(
            user_id=user_id,
            trigger_name=ev.trigger_name,
            text=text,
            priority=ev.priority,
            reason=ev.reason,
            suggested_topic=ev.suggested_topic,
        )
        msg.id = store.save_message(msg)
        store.record_cooldown(user_id, ev.trigger_name)
        results.append(msg)
        today_count += 1
        if today_count >= quota:
            over_quota = True

    return results


async def _generate_text(user_id: int, ev) -> str:
    """
    用 Hermes 生成主动消息文案；失败用静态模板兜底。
    构造一条"伪用户消息"：把 trigger.suggested_topic 当 user_message 喂给 Hermes，
    让它按 persona 输出对老人的开场白。
    """
    instruction = (
        f"现在请你主动跟长辈说话（不是回复老人，是你主动开口）。"
        f"情境：{ev.reason}。请按这个方向开口：{ev.suggested_topic}。"
        f"输出 ≤60 字，温暖、克制、不要催促。"
    )
    try:
        from app.services.agents.hermes import hermes
        resp = await hermes.chat(
            user_id=user_id,
            user_message=instruction,
        )
        if resp.text and not resp.fallback:
            return resp.text
    except Exception as exc:
        logger.warning(f"[proactive] Hermes 生成失败: {exc}（使用模板兜底）")

    # ===== 兜底模板 =====
    fallbacks = {
        "silence": "嘿，您家这阵子在忙么事？我有点想你嘞。",
        "health_anomaly": "您家最近血压有点不稳，是不是有心事？跟我讲讲呗。",
        "family_absence": "妈，要不我帮您给孩子发个语音？想他了吧。",
        "festival": "节日快到嘞，咱们说点开心的好不？",
        "memorial": "今天有特别的日子，想跟我聊聊吗？",
        "weather": "明天天气有点变化，记得加件衣裳哈。",
    }
    return fallbacks.get(ev.trigger_name, "您家好啊，安心宝来陪您唠几句。")


def evaluate_all_users_sync() -> int:
    """
    供 scheduler 调用的同步入口：扫描所有老人 → 异步评估 → 返回总生成数。
    """
    import asyncio
    try:
        from app.models.database import SessionLocal, User
    except Exception as exc:
        logger.warning(f"[proactive] User 表不可用，跳过本次评估: {exc}")
        return 0

    db = SessionLocal()
    try:
        elder_ids = [u.id for u in db.query(User).all()]
    finally:
        db.close()

    if not elder_ids:
        return 0

    async def _run():
        total = 0
        for uid in elder_ids:
            try:
                msgs = await evaluate_and_send(uid)
                total += len(msgs)
            except Exception as exc:
                logger.exception(f"[proactive] 用户 {uid} 评估异常: {exc}")
        return total

    try:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except Exception as exc:
        logger.exception(f"[proactive] 主调度异常: {exc}")
        return 0
