"""
限流器模块
提供全局共享的slowapi Limiter实例，供各API路由使用
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

# 测试/调试环境中禁用限流
_enabled = not get_settings().debug

# 全局限流器实例，使用客户端IP作为限流键
limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
