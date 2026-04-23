"""
结构化日志模块
提供JSON格式的日志输出，便于日志聚合和分析
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data['data'] = record.extra_data

        # 添加请求信息
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger(logging.Logger):
    """结构化日志记录器"""

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        extra_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs
    ):
        """带额外数据的日志记录"""
        extra = kwargs.get('extra', {})
        if extra_data:
            extra['extra_data'] = extra_data
        if request_id:
            extra['request_id'] = request_id
        if user_id:
            extra['user_id'] = user_id
        if ip_address:
            extra['ip_address'] = ip_address

        kwargs['extra'] = extra
        super()._log(level, msg, (), **kwargs)

    def info_with_data(self, msg: str, **kwargs):
        self._log_with_extra(logging.INFO, msg, **kwargs)

    def warning_with_data(self, msg: str, **kwargs):
        self._log_with_extra(logging.WARNING, msg, **kwargs)

    def error_with_data(self, msg: str, **kwargs):
        self._log_with_extra(logging.ERROR, msg, **kwargs)

    def debug_with_data(self, msg: str, **kwargs):
        self._log_with_extra(logging.DEBUG, msg, **kwargs)


def setup_logging(
    log_level: str = 'INFO',
    json_format: bool = True,
    log_file: Optional[str] = None
):
    """
    配置日志系统

    Args:
        log_level: 日志级别
        json_format: 是否使用JSON格式
        log_file: 日志文件路径（可选）
    """
    # 设置自定义Logger类
    logging.setLoggerClass(StructuredLogger)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 选择格式化器
    if json_format and not settings.debug:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> StructuredLogger:
    """获取日志记录器"""
    return logging.getLogger(name)


# API请求日志中间件
class RequestLoggingMiddleware:
    """请求日志中间件"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("api.request")

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        import time
        import uuid

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 提取请求信息
        method = scope.get("method", "")
        path = scope.get('path', "")
        query_string = scope.get('query_string', b'').decode()
        client = scope.get('client', ("", 0))
        ip_address = client[0] if client else ""

        # 记录请求开始
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                'request_id': request_id,
                'ip_address': ip_address,
                'extra_data': {
                    'method': method,
                    'path': path,
                    "query_string": query_string
                }
            }
        )

        # 捕获响应状态
        response_status = [0]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_status[0] = message.get('status', 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            response_status[0] = 500
            self.logger.error(
                f"Request error: {method} {path}",
                extra={
                    'request_id': request_id,
                    'ip_address': ip_address,
                    'extra_data': {'error': str(e)}
                },
                exc_info=True
            )
            raise
        finally:
            # 记录请求结束
            duration = (time.time() - start_time) * 1000
            self.logger.info(
                f"Request completed: {method} {path} - {response_status[0]}",
                extra={
                    'request_id': request_id,
                    'ip_address': ip_address,
                    'extra_data': {
                        'status': response_status[0],
                        "duration_ms": round(duration, 2)
                    }
                }
            )


# 业务日志记录器
class BusinessLogger:
    """业务日志记录器"""

    def __init__(self, name: str = "business"):
        self.logger = get_logger(name)

    def log_chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
        response: str,
        risk_score: float,
        duration_ms: float
    ):
        """记录对话日志"""
        self.logger.info(
            "Chat interaction",
            extra={
                'user_id': user_id,
                'extra_data': {
                    'event': 'chat',
                    'session_id': session_id,
                    "message_length": len(message),
                    "response_length": len(response),
                    'risk_score': risk_score,
                    "duration_ms": duration_ms
                }
            }
        )

    def log_health_alert(
        self,
        user_id: str,
        risk_score: float,
        reason: str,
        notified_family: bool
    ):
        """记录健康告警"""
        self.logger.warning(
            "Health alert triggered",
            extra={
                'user_id': user_id,
                'extra_data': {
                    'event': "health_alert",
                    'risk_score': risk_score,
                    'reason': reason,
                    "notified_family": notified_family
                }
            }
        )

    def log_auth(
        self,
        action: str,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """记录认证日志"""
        level = logging.INFO if success else logging.WARNING
        self.logger._log(
            level,
            f"Auth {action}: {'success' if success else 'failed'}",
            (),
            extra={
                'user_id': user_id,
                'ip_address': ip_address,
                'extra_data': {
                    'event': f'auth_{action}',
                    'success': success,
                    **(details or {})
                }
            }
        )

    def log_api_call(
        self,
        service: str,
        endpoint: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """记录第三方API调用"""
        level = logging.INFO if success else logging.ERROR
        self.logger._log(
            level,
            f"External API call: {service}",
            (),
            extra={
                'extra_data': {
                    'event': "external_api",
                    'service': service,
                    'endpoint': endpoint,
                    "duration_ms": duration_ms,
                    'success': success,
                    'error': error
                }
            }
        )


# 全局业务日志实例
business_logger = BusinessLogger()
