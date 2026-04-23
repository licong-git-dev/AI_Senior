"""
Prometheus指标导出模块
提供应用程序性能和业务指标的监控
"""
import time
from typing import Callable, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# 尝试导入prometheus_client，如果未安装则使用模拟实现
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary, Info,
        generate_latest, CONTENT_TYPE_LATEST,
        CollectorRegistry, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client未安装，指标收集将被禁用")


# ==================== 指标定义 ====================

if PROMETHEUS_AVAILABLE:
    # 请求指标
    REQUEST_COUNT = Counter(
        'anxinbao_http_requests_total',
        'HTTP请求总数',
        ['method', 'endpoint', 'status']
    )

    REQUEST_LATENCY = Histogram(
        'anxinbao_http_request_duration_seconds',
        'HTTP请求延迟',
        ['method', 'endpoint'],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    # AI服务指标
    AI_REQUEST_COUNT = Counter(
        'anxinbao_ai_requests_total',
        'AI服务请求总数',
        ['service', 'status']
    )

    AI_REQUEST_LATENCY = Histogram(
        'anxinbao_ai_request_duration_seconds',
        'AI服务请求延迟',
        ['service'],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
    )

    AI_TOKEN_USAGE = Counter(
        'anxinbao_ai_tokens_total',
        'AI服务Token使用量',
        ['service', 'type']  # type: input/output
    )

    # 对话指标
    CHAT_MESSAGE_COUNT = Counter(
        'anxinbao_chat_messages_total',
        '对话消息总数',
        ['role', 'category']  # role: user/assistant, category: health/daily/chat
    )

    CHAT_RISK_SCORE = Histogram(
        'anxinbao_chat_risk_score',
        '对话风险评分分布',
        ['category'],
        buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    )

    HIGH_RISK_ALERTS = Counter(
        'anxinbao_high_risk_alerts_total',
        '高风险告警总数',
        ['severity']  # severity: warning/critical
    )

    # 用户活跃指标
    ACTIVE_USERS = Gauge(
        'anxinbao_active_users',
        '当前活跃用户数',
        ['type']  # type: elder/family/device
    )

    DAILY_ACTIVE_USERS = Gauge(
        'anxinbao_daily_active_users',
        '日活跃用户数'
    )

    # 会话指标
    ACTIVE_SESSIONS = Gauge(
        'anxinbao_active_sessions',
        '当前活跃会话数'
    )

    SESSION_DURATION = Histogram(
        'anxinbao_session_duration_seconds',
        '会话持续时间',
        buckets=[60, 300, 600, 1800, 3600, 7200]
    )

    # 数据库指标
    DB_QUERY_COUNT = Counter(
        'anxinbao_db_queries_total',
        '数据库查询总数',
        ['operation', 'table']
    )

    DB_QUERY_LATENCY = Histogram(
        'anxinbao_db_query_duration_seconds',
        '数据库查询延迟',
        ['operation'],
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
    )

    DB_CONNECTION_POOL = Gauge(
        'anxinbao_db_connection_pool',
        '数据库连接池状态',
        ['state']  # state: active/idle/overflow
    )

    # 缓存指标
    CACHE_HIT_COUNT = Counter(
        'anxinbao_cache_hits_total',
        '缓存命中次数',
        ['cache_type']
    )

    CACHE_MISS_COUNT = Counter(
        'anxinbao_cache_misses_total',
        '缓存未命中次数',
        ['cache_type']
    )

    # 认证指标
    AUTH_ATTEMPTS = Counter(
        'anxinbao_auth_attempts_total',
        '认证尝试次数',
        ['method', 'status']  # method: password/token/device, status: success/failure
    )

    TOKEN_REFRESH_COUNT = Counter(
        'anxinbao_token_refreshes_total',
        '令牌刷新次数',
        ['status']
    )

    # 系统信息
    APP_INFO = Info(
        'anxinbao_app',
        '应用程序信息'
    )

    # 情绪统计
    EMOTION_DISTRIBUTION = Counter(
        'anxinbao_emotion_detected_total',
        '检测到的情绪分布',
        ['emotion_type', "intensity_level"]  # intensity_level: low/medium/high
    )


# ==================== 指标收集器 ====================

class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.enabled = PROMETHEUS_AVAILABLE

        if self.enabled:
            # 设置应用信息
            APP_INFO.info({
                'version': "1.0.0",
                'service': 'anxinbao-server',
                'environment': 'production'
            })

    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """记录HTTP请求"""
        if not self.enabled:
            return

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_ai_request(
        self,
        service: str,
        success: bool,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0
    ):
        """记录AI服务请求"""
        if not self.enabled:
            return

        status = 'success' if success else "failure"
        AI_REQUEST_COUNT.labels(service=service, status=status).inc()
        AI_REQUEST_LATENCY.labels(service=service).observe(duration)

        if input_tokens > 0:
            AI_TOKEN_USAGE.labels(service=service, type='input').inc(input_tokens)
        if output_tokens > 0:
            AI_TOKEN_USAGE.labels(service=service, type='output').inc(output_tokens)

    def record_chat_message(
        self,
        role: str,
        category: str,
        risk_score: float
    ):
        """记录对话消息"""
        if not self.enabled:
            return

        CHAT_MESSAGE_COUNT.labels(role=role, category=category).inc()
        CHAT_RISK_SCORE.labels(category=category).observe(risk_score)

        if risk_score >= 7:
            severity = 'critical' if risk_score >= 9 else "warning"
            HIGH_RISK_ALERTS.labels(severity=severity).inc()

    def record_emotion(self, emotion_type: str, intensity: int):
        """记录情绪检测"""
        if not self.enabled:
            return

        intensity_level = 'low' if intensity <= 2 else ('medium' if intensity <= 3 else "high")
        EMOTION_DISTRIBUTION.labels(
            emotion_type=emotion_type,
            intensity_level=intensity_level
        ).inc()

    def set_active_users(self, user_type: str, count: int):
        """设置活跃用户数"""
        if not self.enabled:
            return
        ACTIVE_USERS.labels(type=user_type).set(count)

    def set_active_sessions(self, count: int):
        """设置活跃会话数"""
        if not self.enabled:
            return
        ACTIVE_SESSIONS.set(count)

    def record_auth_attempt(self, method: str, success: bool):
        """记录认证尝试"""
        if not self.enabled:
            return

        status = 'success' if success else "failure"
        AUTH_ATTEMPTS.labels(method=method, status=status).inc()

    def record_cache_access(self, cache_type: str, hit: bool):
        """记录缓存访问"""
        if not self.enabled:
            return

        if hit:
            CACHE_HIT_COUNT.labels(cache_type=cache_type).inc()
        else:
            CACHE_MISS_COUNT.labels(cache_type=cache_type).inc()

    def record_db_query(self, operation: str, table: str, duration: float):
        """记录数据库查询"""
        if not self.enabled:
            return

        DB_QUERY_COUNT.labels(operation=operation, table=table).inc()
        DB_QUERY_LATENCY.labels(operation=operation).observe(duration)


# 全局指标收集器
metrics = MetricsCollector()


# ==================== 装饰器 ====================

def track_request_metrics(endpoint: str = None):
    """跟踪请求指标的装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                ep = endpoint or func.__name__
                metrics.record_request('POST', ep, status, duration)

        return wrapper
    return decorator


def track_ai_metrics(service: str):
    """跟踪AI服务指标的装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_ai_request(service, success, duration)

        return wrapper
    return decorator


# ==================== FastAPI集成 ====================

def create_metrics_endpoint():
    """创建指标导出端点"""
    from fastapi import APIRouter, Response

    router = APIRouter(tags=['监控'])

    @router.get("/metrics")
    async def metrics_endpoint():
        """Prometheus指标导出端点"""
        if not PROMETHEUS_AVAILABLE:
            return Response(
                content="# Prometheus client not installed",
                media_type='text/plain'
            )

        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )

    return router


class PrometheusMiddleware:
    """Prometheus指标中间件"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope.get('method', "")
        path = scope.get('path', "")
        status = [200]

        async def send_wrapper(message):
            if message['type'] == "http.response.start":
                status[0] = message.get('status', 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            # 对路径进行规范化，避免基数爆炸
            normalized_path = self._normalize_path(path)
            metrics.record_request(method, normalized_path, status[0], duration)

    def _normalize_path(self, path: str) -> str:
        """规范化路径，用占位符替换动态部分"""
        parts = path.split("/")
        normalized = []

        for part in parts:
            if part.isdigit():
                normalized.append('{id}')
            elif len(part) == 36 and '-' in part:  # UUID
                normalized.append('{uuid}')
            else:
                normalized.append(part)

        return '/'.join(normalized)


# ==================== 健康检查探针 ====================

class HealthProbe:
    """健康检查探针"""

    def __init__(self):
        self.checks = {}

    def register_check(self, name: str, check_func: Callable):
        """注册健康检查函数"""
        self.checks[name] = check_func

    async def check_all(self) -> dict:
        """执行所有健康检查"""
        results = {}
        overall_healthy = True

        for name, check_func in self.checks.items():
            try:
                if callable(check_func):
                    result = await check_func() if hasattr(check_func, "__await__") else check_func()
                    results[name] = {'status': 'healthy' if result else 'unhealthy'}
                    if not result:
                        overall_healthy = False
            except Exception as e:
                results[name] = {'status': 'unhealthy', 'error': str(e)}
                overall_healthy = False

        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'checks': results
        }


# 全局健康探针
health_probe = HealthProbe()


def create_health_endpoints():
    """创建健康检查端点"""
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter(tags=["健康检查"])

    @router.get("/health/live")
    async def liveness():
        """存活探针 - Kubernetes liveness probe"""
        return {'status': 'ok'}

    @router.get("/health/ready")
    async def readiness():
        """就绪探针 - Kubernetes readiness probe"""
        result = await health_probe.check_all()
        status_code = 200 if result['status'] == 'healthy' else 503
        return JSONResponse(content=result, status_code=status_code)

    @router.get("/health/detailed")
    async def detailed_health():
        """详细健康检查"""
        result = await health_probe.check_all()
        return result

    return router
