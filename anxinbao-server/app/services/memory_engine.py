"""
长期记忆引擎（Phase 1 v1：SQLite + 关键词召回，无新依赖）

设计目标：
- 让安心宝跨会话"记得"老人的事实/偏好/关系/事件/心境
- 不引入向量库依赖（lancedb、qdrant 等留给 v2 升级路径）
- 可被 5 个 agent 共享读写

记忆分类（仿 Claude Memory Tool）：
- fact      事实（姓名、年龄、籍贯、子女数）
- preference 偏好（口味、爱好、忌讳）
- relation  关系（家庭成员 + 关系强度 + 上次互动）
- event     事件（生日、忌日、入院、出游）
- mood      心境（连续 N 天情绪曲线）

召回策略：
1. 关键词匹配
2. 时间衰减（最近 7d 权重 1.0，30d 0.7，90d 0.3）
3. 类型过滤（fact 永远召回，event 仅日期临近）
4. Top-K = 8

升级路径 v2：把 _recall() 内部换成向量召回，对外接口不变。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============ 类型 ============

class MemoryType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    RELATION = "relation"
    EVENT = "event"
    MOOD = "mood"
    LIFE_STORY = "life_story"  # r17 · 人生故事 / 录音 / 给后辈的话；不参与对话召回


class MemoryVisibility(str, Enum):
    """老人对 AI 倾诉的内容分级"""
    SELF_ONLY = "self_only"   # 仅老人 AI 间，绝不暴露给家属
    FAMILY = "family"         # 可在日报里暴露给家属（如"今天聊到旅游"）
    NEVER_SHARE = "never_share"  # 高敏感（医疗细节、负面评价）—— 完全不出系统


@dataclass
class MemoryRecord:
    user_id: int                    # 老人 User.id
    type: MemoryType
    content: str                    # 文本主体（建议 ≤ 200 字）
    keywords: List[str] = field(default_factory=list)
    visibility: MemoryVisibility = MemoryVisibility.SELF_ONLY
    importance: float = 0.5         # 0-1，影响召回权重
    occurred_at: Optional[str] = None  # ISO 时间戳，可选（事件类必填）
    expires_at: Optional[str] = None   # 自动过期（如临时心境）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None        # 由 DB 自增

    def to_dict(self) -> dict:
        return asdict(self)


# ============ 引擎接口（抽象 + 默认 SQLite 实现）============


class MemoryEngine:
    """
    SQLite 持久化记忆引擎（线程安全）。

    DB 路径：默认 ./companion_memory.db；通过环境变量 COMPANION_MEMORY_DB 覆盖。
    与现有 anxinbao.db 隔离，避免破坏既有 schema。
    """

    def __init__(self, db_path: Optional[str] = None):
        import os
        self.db_path = db_path or os.environ.get("COMPANION_MEMORY_DB", "./companion_memory.db")
        # 同一进程多线程共享一个 connection 不安全；用 thread-local
        self._local = threading.local()
        self._init_schema()

    @contextmanager
    def _conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                self.db_path,
                isolation_level=None,  # autocommit
                check_same_thread=True,
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        yield self._local.conn

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    keywords TEXT NOT NULL DEFAULT '[]',
                    visibility TEXT NOT NULL DEFAULT 'self_only',
                    importance REAL NOT NULL DEFAULT 0.5,
                    occurred_at TEXT,
                    expires_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS ix_mem_user_type ON memories(user_id, type)")
            c.execute("CREATE INDEX IF NOT EXISTS ix_mem_user_created ON memories(user_id, created_at)")

    # ===== 写 =====

    def save(self, record: MemoryRecord) -> int:
        with self._conn() as c:
            cur = c.execute(
                """INSERT INTO memories
                (user_id, type, content, keywords, visibility, importance, occurred_at, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.user_id, record.type.value, record.content,
                    json.dumps(record.keywords, ensure_ascii=False),
                    record.visibility.value, record.importance,
                    record.occurred_at, record.expires_at, record.created_at,
                ),
            )
            return cur.lastrowid or 0

    def forget(self, memory_id: int, user_id: int) -> bool:
        """老人主动"忘记我吧" —— 必须校验 user_id 防越权"""
        with self._conn() as c:
            cur = c.execute(
                "DELETE FROM memories WHERE id = ? AND user_id = ?",
                (memory_id, user_id),
            )
            return cur.rowcount > 0

    def forget_all(self, user_id: int) -> int:
        """彻底删除某个老人的所有记忆（GDPR 'Right to be forgotten'）"""
        with self._conn() as c:
            cur = c.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            return cur.rowcount

    # ===== 读 / 召回 =====

    def list_all(self, user_id: int, limit: int = 100) -> List[MemoryRecord]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT * FROM memories
                WHERE user_id = ?
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC LIMIT ?""",
                (user_id, datetime.now().isoformat(), limit),
            ).fetchall()
            return [self._row_to_record(r) for r in rows]

    def recall(
        self,
        user_id: int,
        query: str = "",
        types: Optional[List[MemoryType]] = None,
        top_k: int = 8,
    ) -> List[MemoryRecord]:
        """
        基于关键词 + 时间衰减 + 类型 + 重要性的简单打分召回。

        关键设计：
        - LIFE_STORY 类型默认**不参与召回**（避免老人讲过的话被反复喂回去）
        - 仅当 types 显式包含 LIFE_STORY 时才召回（典型场景：LifeMomentTrigger / 数字遗产导出）

        v2 可换成向量召回，接口不变。
        """
        with self._conn() as c:
            sql = "SELECT * FROM memories WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)"
            params: list = [user_id, datetime.now().isoformat()]
            if types:
                placeholders = ",".join(["?"] * len(types))
                sql += f" AND type IN ({placeholders})"
                params.extend([t.value for t in types])
            else:
                # 默认排除 LIFE_STORY（避免反复喂回老人讲过的话）
                sql += " AND type != ?"
                params.append(MemoryType.LIFE_STORY.value)
            rows = c.execute(sql, params).fetchall()

        scored: List[Tuple[float, MemoryRecord]] = []
        query_lc = (query or "").lower()
        now = datetime.now()
        for r in rows:
            rec = self._row_to_record(r)
            score = self._score(rec, query_lc, now)
            scored.append((score, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored[:top_k]]

    @staticmethod
    def _score(rec: MemoryRecord, query_lc: str, now: datetime) -> float:
        """打分：基础重要性 + 关键词命中 + 时间衰减 + 事件临近加分"""
        score = rec.importance

        # 关键词命中
        if query_lc:
            content_lc = rec.content.lower()
            kw_hit = sum(1 for kw in rec.keywords if kw.lower() in query_lc)
            if kw_hit:
                score += 0.5 * kw_hit
            elif any(token in content_lc for token in query_lc.split() if len(token) >= 2):
                score += 0.2

        # 时间衰减（仅对 mood / event 类敏感；fact 永久有效）
        if rec.type in (MemoryType.MOOD.value, MemoryType.EVENT.value):
            try:
                created = datetime.fromisoformat(rec.created_at)
                days = (now - created).days
                if days <= 7:
                    score *= 1.0
                elif days <= 30:
                    score *= 0.7
                elif days <= 90:
                    score *= 0.3
                else:
                    score *= 0.1
            except (ValueError, TypeError):
                pass

        # 事件临近加分（生日、忌日等 7 天内）
        if rec.type == MemoryType.EVENT.value and rec.occurred_at:
            try:
                evt = datetime.fromisoformat(rec.occurred_at)
                # 把年份替换为今年比对（生日是循环的）
                evt_this_year = evt.replace(year=now.year)
                delta = abs((evt_this_year - now).days)
                if delta <= 7:
                    score += 0.8
            except (ValueError, TypeError):
                pass

        # FACT 类永远召回（base 加成）
        if rec.type == MemoryType.FACT.value:
            score += 0.3

        return score

    # ===== 工具 =====

    def stats(self, user_id: int) -> dict:
        """供 /api/companion/memory/stats 端点"""
        with self._conn() as c:
            counts = {}
            for t in MemoryType:
                row = c.execute(
                    "SELECT COUNT(*) as n FROM memories WHERE user_id = ? AND type = ?",
                    (user_id, t.value),
                ).fetchone()
                counts[t.value] = row["n"]
            row = c.execute(
                "SELECT COUNT(*) as total FROM memories WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return {"user_id": user_id, "total": row["total"], "by_type": counts}

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            user_id=row["user_id"],
            type=MemoryType(row["type"]),
            content=row["content"],
            keywords=json.loads(row["keywords"] or "[]"),
            visibility=MemoryVisibility(row["visibility"]),
            importance=row["importance"],
            occurred_at=row["occurred_at"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )


# 全局单例（lazy init）
_engine: Optional[MemoryEngine] = None
_engine_lock = threading.Lock()


def get_memory_engine() -> MemoryEngine:
    """全局共享的记忆引擎（lazy init，避免 import 时建 DB）"""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = MemoryEngine()
    return _engine
