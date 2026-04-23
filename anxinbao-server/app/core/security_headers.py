"""
安全响应头中间件

为所有HTTP响应添加安全头，防止常见的Web安全攻击。
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件

    添加以下安全头：
    - X-Frame-Options: 防止点击劫持
    - X-Content-Type-Options: 防止MIME类型嗅探
    - X-XSS-Protection: 启用浏览器XSS过滤
    - Strict-Transport-Security: 强制HTTPS（仅生产环境）
    - Referrer-Policy: 控制Referer头发送策略
    - Permissions-Policy: 限制浏览器功能权限
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"

        # 仅在生产环境中添加HSTS头
        settings = get_settings()
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
