"""
通用异步重试装饰器（含指数退避 + 抖动）

设计目标：
- 网络抖动 / 第三方 API 瞬时不可用时自动重试，提升成功率
- 永久错误（4xx 等）不重试，避免浪费配额
- 重试间隔有上限（max_delay），避免雪崩
- 加少量抖动（jitter），避免多个并发请求"齐步重试"再次打挂下游

使用示例：

    from app.core.retry import async_retry

    class WeChatPusher:
        @async_retry(max_attempts=3, backoff_base=0.5, retryable=(httpx.TransportError,))
        async def push(self, recipient, title, content, data):
            ...

不要把所有异常都吞掉重试 —— 必须 explicit 列出 retryable 异常类，避免：
- 配置错误 (ValueError) 被无谓重试
- HTTPException(401) 被重试导致更多失败日志
"""
from __future__ import annotations

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Awaitable, Callable, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def async_retry(
    *,
    max_attempts: int = 3,
    backoff_base: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    jitter: float = 0.1,
    retryable: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    异步重试装饰器。

    Args:
        max_attempts: 最多尝试次数（含首次）
        backoff_base: 第一次重试前等待秒数
        backoff_factor: 每次重试等待时间乘数
        max_delay: 单次重试最大等待秒数
        jitter: ±jitter 随机扰动比例（0~1），减少齐步雪崩
        retryable: 命中这些异常类才重试；其他直接抛出
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: BaseException | None = None
            delay = backoff_base
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable as exc:
                    last_exc = exc
                    if attempt >= max_attempts:
                        logger.warning(
                            f"[retry] {func.__name__} 第 {attempt}/{max_attempts} 次仍失败，放弃: {exc}"
                        )
                        raise
                    sleep_for = min(max_delay, delay)
                    sleep_for *= 1 + random.uniform(-jitter, jitter)
                    sleep_for = max(0.0, sleep_for)
                    logger.info(
                        f"[retry] {func.__name__} 第 {attempt} 次失败 ({exc!r})，"
                        f"{sleep_for:.2f}s 后重试"
                    )
                    await asyncio.sleep(sleep_for)
                    delay *= backoff_factor
            # 不应该到达这里，但 type checker 需要
            assert last_exc is not None  # noqa: S101
            raise last_exc

        return wrapper

    return decorator
