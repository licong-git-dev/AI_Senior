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
                    pushed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            # 兼容老版本：若 pushed 列不存在则 ALTER 加（sqlite 允许）
            try:
                c.execute("ALTER TABLE proactive_messages ADD COLUMN pushed INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # 列已存在
            c.execute("""
                CREATE TABLE IF NOT EXISTS dnd_configs (
                    user_id INTEGER PRIMARY KEY,
                    dnd_start TEXT NOT NULL DEFAULT '22:00',
                    dnd_end TEXT NOT NULL DEFAULT '07:00',
                    daily_quota INTEGER NOT NULL DEFAULT 4,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    push_proactive INTEGER NOT NULL DEFAULT 1,
                    special_mode TEXT,
                    special_mode_started_at TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            try:
                c.execute("ALTER TABLE dnd_configs ADD COLUMN push_proactive INTEGER NOT NULL DEFAULT 1")
            except sqlite3.OperationalError:
                pass
            # r17 · 危机时刻 / 温度时刻 special_mode 支持
            # 取值: normal / bereavement / crisis / hospital / relocation
            try:
                c.execute("ALTER TABLE dnd_configs ADD COLUMN special_mode TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                c.execute("ALTER TABLE dnd_configs ADD COLUMN special_mode_started_at TEXT")
            except sqlite3.OperationalError:
                pass
            c.execute("""
                CREATE TABLE IF NOT EXISTS trigger_cooldowns (
                    user_id INTEGER NOT NULL,
                    trigger_name TEXT NOT NULL,
                    fired_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, trigger_name)
                )
            """)
            # Phase 3: MEDIUM/CRITICAL 工具调用待确认
            c.execute("""
                CREATE TABLE IF NOT EXISTS pending_confirmations (
                    confirm_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    safety_level TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed INTEGER DEFAULT 0
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS ix_pm_user_created ON proactive_messages(user_id, created_at)")
            c.execute("CREATE INDEX IF NOT EXISTS ix_pc_user ON pending_confirmations(user_id, consumed)")

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
                    "push_proactive": True,
                    "special_mode": None,
                    "special_mode_started_at": None,
                }
            # 兼容老 schema 无 push_proactive 列
            result = dict(row)
            if "push_proactive" not in result:
                result["push_proactive"] = 1
            return result

    def upsert_dnd(self, user_id: int, dnd_start: Optional[str] = None,
                   dnd_end: Optional[str] = None, daily_quota: Optional[int] = None,
                   enabled: Optional[bool] = None,
                   push_proactive: Optional[bool] = None,
                   special_mode: Optional[str] = None) -> Dict[str, any]:
        existing = self.get_dnd(user_id)
        merged = {
            "dnd_start": dnd_start or existing["dnd_start"],
            "dnd_end": dnd_end or existing["dnd_end"],
            "daily_quota": daily_quota if daily_quota is not None else existing["daily_quota"],
            "enabled": int(enabled) if enabled is not None else int(existing["enabled"]),
            "push_proactive": int(push_proactive) if push_proactive is not None else int(existing.get("push_proactive", 1)),
        }
        # 处理 special_mode 切换
        new_special_mode = special_mode if special_mode is not None else existing.get("special_mode")
        new_special_mode_started_at = (
            datetime.now().isoformat()
            if special_mode is not None and special_mode != existing.get("special_mode")
            else existing.get("special_mode_started_at")
        )

        with self._conn() as c:
            c.execute(
                """INSERT INTO dnd_configs
                (user_id, dnd_start, dnd_end, daily_quota, enabled, push_proactive,
                 special_mode, special_mode_started_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    dnd_start = excluded.dnd_start,
                    dnd_end = excluded.dnd_end,
                    daily_quota = excluded.daily_quota,
                    enabled = excluded.enabled,
                    push_proactive = excluded.push_proactive,
                    special_mode = excluded.special_mode,
                    special_mode_started_at = excluded.special_mode_started_at,
                    updated_at = excluded.updated_at""",
                (user_id, merged["dnd_start"], merged["dnd_end"],
                 merged["daily_quota"], merged["enabled"], merged["push_proactive"],
                 new_special_mode, new_special_mode_started_at,
                 datetime.now().isoformat()),
            )
        return self.get_dnd(user_id)

    def mark_pushed(self, message_id: int) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE proactive_messages SET pushed = 1 WHERE id = ?",
                (message_id,),
            )

    # ----- Pending Confirmations (Phase 3 工具安全网关) -----

    def create_confirmation(
        self, user_id: int, tool_name: str, params: dict, safety_level: str,
        ttl_seconds: int = 600,
    ) -> str:
        import secrets
        confirm_id = f"conf_{secrets.token_urlsafe(16)}"
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        with self._conn() as c:
            c.execute(
                """INSERT INTO pending_confirmations
                (confirm_id, user_id, tool_name, params_json, safety_level, created_at, expires_at, consumed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                (confirm_id, user_id, tool_name, json.dumps(params, ensure_ascii=False),
                 safety_level, now.isoformat(), expires_at.isoformat()),
            )
        return confirm_id

    def get_confirmation(self, confirm_id: str, user_id: int) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute(
                """SELECT * FROM pending_confirmations
                WHERE confirm_id = ? AND user_id = ? AND consumed = 0""",
                (confirm_id, user_id),
            ).fetchone()
            if not row:
                return None
            try:
                exp = datetime.fromisoformat(row["expires_at"])
                if datetime.now() > exp:
                    return None
            except ValueError:
                return None
            return {
                "confirm_id": row["confirm_id"],
                "user_id": row["user_id"],
                "tool_name": row["tool_name"],
                "params": json.loads(row["params_json"] or "{}"),
                "safety_level": row["safety_level"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
            }

    def consume_confirmation(self, confirm_id: str, user_id: int) -> bool:
        with self._conn() as c:
            cur = c.execute(
                "UPDATE pending_confirmations SET consumed = 1 WHERE confirm_id = ? AND user_id = ? AND consumed = 0",
                (confirm_id, user_id),
            )
            return cur.rowcount > 0

    def list_pending_confirmations(self, user_id: int, limit: int = 10) -> List[dict]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT * FROM pending_confirmations
                WHERE user_id = ? AND consumed = 0 AND expires_at > ?
                ORDER BY created_at DESC LIMIT ?""",
                (user_id, datetime.now().isoformat(), limit),
            ).fetchall()
            return [
                {
                    "confirm_id": r["confirm_id"],
                    "tool_name": r["tool_name"],
                    "params": json.loads(r["params_json"] or "{}"),
                    "safety_level": r["safety_level"],
                    "created_at": r["created_at"],
                    "expires_at": r["expires_at"],
                }
                for r in rows
            ]

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

    r17 · 加入 special_mode 调度（详见 CRISIS_PLAYBOOK.md）：
    - bereavement → quota 减半 + 跳过 family_absence/festival/life_moment
    - crisis → 跳过所有非 critical 触发
    - hospital → quota=1，仅 SOS 类
    - relocation → 暂时不限制（可后续添加专属逻辑）
    """
    from app.services.companion_triggers import evaluate_all

    store = get_store()
    dnd = store.get_dnd(user_id)
    now = datetime.now()
    in_dnd = bool(dnd.get("enabled")) and _is_in_dnd(
        now, dnd["dnd_start"], dnd["dnd_end"]
    )

    # ===== Special Mode 守卫（r17） =====
    special = (dnd.get("special_mode") or "normal").lower()
    if special == "crisis":
        # 危机模式：跳过所有非 critical（priority < 9）触发
        logger.info(f"[proactive] 用户 {user_id} 处于 crisis mode，仅响应 priority>=9")

    # 模式 → 配额调整
    base_quota = dnd.get("daily_quota") or DAILY_QUOTA
    if special == "bereavement":
        base_quota = max(1, base_quota // 2)
    elif special == "hospital":
        base_quota = 1
    elif special == "crisis":
        base_quota = 1

    today_count = store.count_today(user_id)
    quota = base_quota
    over_quota = today_count >= quota

    # 模式 → 屏蔽特定 trigger 名
    muted_triggers = set()
    if special == "bereavement":
        muted_triggers = {"family_absence", "festival", "life_moment", "memorial"}
    elif special == "crisis":
        muted_triggers = {"family_absence", "festival", "life_moment", "memorial", "weather", "silence"}
    elif special == "hospital":
        muted_triggers = {"family_absence", "festival", "life_moment", "weather"}

    results: List[ProactiveMessage] = []
    for ev in evaluate_all(user_id):
        # 0) Special mode 守卫（r17）：mute 特定 trigger
        if ev.trigger_name in muted_triggers:
            logger.debug(f"[proactive] special_mode={special} 屏蔽 {ev.trigger_name}")
            continue
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

        # r20 · T 选项：北极星埋点（生成事件）
        try:
            from app.core.north_star_metrics import record_proactive_generated
            record_proactive_generated(ev.trigger_name)
        except Exception:
            pass

        # 5) Phase 2 H：真实推送链路（仅当老人开启 push_proactive）
        if dnd.get("push_proactive"):
            await _push_proactive(user_id, msg)

    return results


async def _push_proactive(user_id: int, msg: ProactiveMessage) -> None:
    """
    把主动消息推给家属 / 老人设备（走 NotificationService）。
    失败已由 notification_service 内部 retry + DLQ 兜底（r9），这里只需调。

    推送内容策略（隐私优先）：
    - 标题：固定"安心宝来消息了"（不泄露触发器名 / 私密话题）
    - 正文：仅前 40 字（避免在通知栏暴露完整 LLM 输出）
    - 点击 deep link 回 /api/companion/proactive/inbox
    """
    try:
        from app.services.notification_service import (
            NotificationTemplate,
            notification_service,
        )
    except Exception as exc:
        logger.warning(f"[proactive push] notification_service 不可用: {exc}")
        return

    preview = (msg.text or "")[:40]
    if len(msg.text or "") > 40:
        preview += "…"

    try:
        await notification_service.send_notification(
            user_id=user_id,
            template=NotificationTemplate.HEALTH_ALERT
            if msg.priority >= 7
            else NotificationTemplate.APP_NOTIFICATION
            if hasattr(NotificationTemplate, "APP_NOTIFICATION")
            else NotificationTemplate.HEALTH_ALERT,
            content=preview,
            extra_data={
                "source": "companion_proactive",
                "message_id": msg.id,
                "trigger_name": msg.trigger_name,
                "priority": msg.priority,
                "deep_link": "/api/companion/proactive/inbox",
            },
        )
        # 标记已推（不管成功/失败，避免重复推送）
        get_store().mark_pushed(msg.id or 0)
    except Exception as exc:
        logger.warning(f"[proactive push] 推送异常（DLQ 已兜底）: {exc}")


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
