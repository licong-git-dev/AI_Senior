"""
死信队列（Dead Letter Queue · DLQ）

用途：所有重试后仍失败的"关键消息"（SOS 通知、健康告警、支付回调等）必须
落入死信队列，运维 / 客服可以在此追溯并人工补偿，避免"消息悄无声息地丢了"。

当前实现：内存 + 滚动文件日志（轻量、无依赖）。
生产环境建议升级：
  - 落入数据库（DeadLetter 表）方便查询
  - 接入 Sentry / 钉钉 webhook 做告警
  - 落入 Redis Stream / RabbitMQ 让独立 worker 重跑

使用：

    from app.core.dead_letter import dead_letter_queue, DeadLetterRecord

    try:
        await pusher.push(...)
    except Exception as exc:
        dead_letter_queue.record(DeadLetterRecord(
            channel="wechat",
            recipient=user_id,
            template="emergency",
            payload={"alert_id": alert.id},
            error=str(exc),
            severity="critical",
        ))
        raise  # 让上层决定是否继续走 fallback 通道
"""
from __future__ import annotations

import json
import logging
import threading
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DeadLetterRecord:
    channel: str                  # wechat / sms / app_push / payment_callback / ...
    recipient: str                # 用户 ID / 手机号 / openid 等
    template: str                 # 模板名（如 emergency / health_alert）
    payload: Dict[str, Any]       # 原始业务数据（注意不要塞密码 / token）
    error: str                    # 末次失败原因
    severity: str = "warning"     # info / warning / critical
    occurred_at: str = field(default_factory=lambda: datetime.now().isoformat())
    attempts: int = 1


class DeadLetterQueue:
    """线程安全的死信队列（内存 + 日志）"""

    def __init__(self, max_in_memory: int = 1000):
        self._lock = threading.Lock()
        self._records: Deque[DeadLetterRecord] = deque(maxlen=max_in_memory)
        # 简单计数，便于 /metrics 暴露
        self.counts: Dict[str, int] = {}

    def record(self, item: DeadLetterRecord) -> None:
        with self._lock:
            self._records.append(item)
            self.counts[item.channel] = self.counts.get(item.channel, 0) + 1

        # 关键级别：记 ERROR 日志，方便 ELK / 告警系统识别
        log_payload = json.dumps(asdict(item), ensure_ascii=False, default=str)
        if item.severity == "critical":
            logger.error(f"[DLQ-CRITICAL] {log_payload}")
        elif item.severity == "warning":
            logger.warning(f"[DLQ] {log_payload}")
        else:
            logger.info(f"[DLQ] {log_payload}")

    def list(
        self,
        channel: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[DeadLetterRecord]:
        with self._lock:
            items: Iterable[DeadLetterRecord] = list(self._records)
        if channel:
            items = [r for r in items if r.channel == channel]
        if severity:
            items = [r for r in items if r.severity == severity]
        return list(items)[-limit:]

    def clear(self) -> int:
        """清空队列（运维确认补偿后调用）；返回清空的条数"""
        with self._lock:
            n = len(self._records)
            self._records.clear()
            return n

    def size(self) -> int:
        with self._lock:
            return len(self._records)


# 全局单例
dead_letter_queue = DeadLetterQueue()
