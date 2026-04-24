"""
安心宝云端服务 - 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter

from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.api.notify import router as notify_router
from app.api.users import router as users_router
from app.api.health import router as health_router
from app.api.video import router as video_router
from app.api.auth import router as auth_router
from app.api.accessibility import router as accessibility_router
from app.api.iot import router as iot_router
from app.api.dialect import router as dialect_router
from app.api.simple import router as simple_router
from app.api.entertainment import router as entertainment_router
from app.api.games import router as games_router
from app.api.emergency import router as emergency_router
from app.api.social import router as social_router
from app.api.family import router as family_router
from app.api.messages import router as messages_router
from app.api.voice_feedback import router as voice_feedback_router
from app.api.onboarding import router as onboarding_router
from app.api.preferences import router as preferences_router
from app.api.subscription import router as subscription_router
from app.api.payment import router as payment_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.marketing import router as marketing_router
from app.api.i18n import router as i18n_router
from app.api.ai import router as ai_router
from app.api.integration import router as integration_router
from app.api.support import router as support_router
from app.api.life import router as life_router
from app.api.smart_home import router as smart_home_router
from app.api.safety import router as safety_router
from app.api.medication import router as medication_router
from app.api.nutrition import router as nutrition_router
from app.api.exercise import router as exercise_router
from app.api.memory import router as memory_router
from app.api.mental_health import router as mental_health_router
from app.api.community import router as community_router
from app.api.file import router as file_router
from app.api.ws import router as ws_router
from app.api.report import router as report_router
from app.api.audit import router as audit_router
from app.api.proactive import router as proactive_router
from app.api.memory_api import router as memory_api_router
from app.api.drug_api import router as drug_api_router
from app.api.cognitive_api import router as cognitive_api_router
from app.api.daily_report import router as daily_report_router
from app.models.database import init_db, engine
from app.core.config import get_settings
from app.core.logging import setup_logging, RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.metrics import (
    create_metrics_endpoint,
    create_health_endpoints,
    PrometheusMiddleware,
    health_probe
)

# 配置日志
logger = setup_logging()

# 获取配置
settings = get_settings()

# 初始化限流器（从 app.core.limiter 导入）


# ==================== 应用生命周期 ====================

def _enforce_production_secrets() -> None:
    """
    生产环境（DEBUG=False）的不可妥协安全门：
    - JWT_SECRET_KEY 必须由环境变量显式设置（不能依赖默认 token_urlsafe 自动生成
      —— 否则每次重启密钥都不同，已签发的所有 JWT 立刻失效，全员被踢）
    - ENCRYPTION_KEY 必须设置（敏感字段加密依赖此密钥）
    - 不可使用占位符值（test_/your_/please-replace 等）

    检测 JWT 是否来自 env：直接查 os.environ，不信任 settings 字段
    （pydantic 默认值会让 settings.jwt_secret_key 永远非空，无法区分）
    """
    import os

    if settings.debug:
        return  # DEBUG=True 时只警告不阻断（保留开发便利）

    fatal_errors: list[str] = []

    if not os.environ.get("JWT_SECRET_KEY"):
        fatal_errors.append(
            "JWT_SECRET_KEY 必须通过环境变量显式设置（不可使用代码默认值），"
            "否则每次重启所有用户被踢。"
            " 生成方式：python -c 'import secrets; print(secrets.token_urlsafe(48))'"
        )
    else:
        jwt_status = _classify(os.environ.get("JWT_SECRET_KEY", ""))
        if jwt_status != "real" or len(os.environ.get("JWT_SECRET_KEY", "")) < 32:
            fatal_errors.append(
                f"JWT_SECRET_KEY 看起来是占位符或太短（status={jwt_status}），生产环境必须 ≥32 字符且非占位。"
            )

    if not getattr(settings, "encryption_key", ""):
        fatal_errors.append(
            "ENCRYPTION_KEY 必须设置（敏感字段加密依赖此密钥）。"
            " 生成方式：python -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'"
        )

    # ===== CORS 守卫：生产环境拒绝通配符 / localhost / 非 HTTPS =====
    raw_origins = (settings.allowed_origins or "").strip()
    if raw_origins == "*":
        fatal_errors.append(
            "ALLOWED_ORIGINS=* 在生产环境是严重风险（任意域可发起 credentialed CORS 请求）。"
            " 请改为具体域名，例如 ALLOWED_ORIGINS=https://anxinbao.com,https://app.anxinbao.com"
        )
    else:
        origins_list = [o.strip() for o in raw_origins.split(",") if o.strip()]
        if not origins_list:
            fatal_errors.append("ALLOWED_ORIGINS 不能为空（生产环境必须配置具体的前端域名）")
        else:
            bad_origins = []
            for o in origins_list:
                ol = o.lower()
                # 拒绝：localhost / 127. / 0.0.0.0 / 非 https
                if "localhost" in ol or ol.startswith("http://127.") or ol.startswith("http://0.0.0.0"):
                    bad_origins.append(f"{o}（本地地址不应出现在生产 CORS 白名单）")
                elif ol.startswith("http://"):
                    bad_origins.append(f"{o}（生产环境必须 HTTPS）")
                elif ol == "*":
                    bad_origins.append(f"{o}（不允许通配符）")
            if bad_origins:
                fatal_errors.append(
                    "ALLOWED_ORIGINS 含不安全条目：\n      "
                    + "\n      ".join(bad_origins)
                    + "\n    生产环境必须全部为 https://your-domain.com 形式"
                )

    if fatal_errors:
        msg = "\n".join(f"  - {e}" for e in fatal_errors)
        logger.error("\n[FATAL] 生产环境启动被拒绝，缺少以下不可妥协的密钥：\n" + msg)
        raise SystemExit(
            "拒绝以不安全的配置启动生产服务。设置必需的环境变量后重试，"
            "或临时设置 DEBUG=true 进入开发模式（但不要把开发模式部署到生产）。"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("安心宝云端服务启动中...")

    # 不可妥协的生产密钥校验（必须在 init_db 之前，启动失败也不留下半就绪状态）
    _enforce_production_secrets()

    # 初始化数据库
    init_db()
    logger.info("数据库初始化完成")

    # 初始化定时任务调度器
    try:
        from app.core.scheduler import init_scheduler
        init_scheduler()
        logger.info("定时任务调度器已启动")
    except Exception as e:
        logger.warning(f"定时任务调度器启动失败: {e}")

    # 恢复进行中的紧急事件（服务重启后从数据库还原内存状态）
    try:
        from app.services.emergency_service import emergency_service
        emergency_service.restore_from_db()
    except Exception as e:
        logger.warning(f"恢复紧急事件失败: {e}")

    # 关键第三方集成真实性自检（非致命，只打印告警）
    # 杜绝"凭据缺失时静默走入 mock 模式"在生产环境无人察觉
    try:
        critical_pairs = [
            ("aliyun_sms (SOS短信)", getattr(settings, "aliyun_access_key_id", "")),
            ("alipay (订阅付费)", getattr(settings, "alipay_app_id", "")),
            ("encryption_key (敏感数据)", getattr(settings, "encryption_key", "")),
        ]
        for name, value in critical_pairs:
            classified = _classify(value)
            if classified != "real":
                logger.warning(
                    f"⚠️  关键集成未配置真实凭据: {name} status={classified}。"
                    f"该链路将走入 mock 或失败。详见 GET /health/integrations。"
                )
    except Exception as e:
        logger.warning(f"集成自检失败（非致命）: {e}")

    logger.info("安心宝云端服务启动完成")

    yield  # 应用运行中

    # 关闭时执行
    logger.info("安心宝云端服务关闭中...")

    try:
        from app.core.scheduler import shutdown_scheduler
        shutdown_scheduler()
        logger.info("定时任务调度器已关闭")
    except Exception as e:
        logger.warning(f"定时任务调度器关闭失败: {e}")

    logger.info("安心宝云端服务已关闭")


# ==================== API文档配置 ====================

# API标签定义 - 按功能模块分组
tags_metadata = [
    {
        "name": "认证授权",
        "description": "用户登录、注册、Token管理等认证相关接口",
    },
    {
        "name": "用户管理",
        "description": "用户信息CRUD、个人设置等",
    },
    {
        "name": "健康管理",
        "description": "健康数据记录、趋势分析、告警管理、健康报告等",
    },
    {
        "name": "用药管理",
        "description": "用药计划、服药记录、依从性统计、库存管理等",
    },
    {
        "name": "紧急服务",
        "description": "SOS求助、跌倒检测、紧急联系人、事件处理等",
    },
    {
        "name": "智能对话",
        "description": "AI对话、语音交互、方言识别等",
    },
    {
        "name": "语音服务",
        "description": "语音识别(ASR)、语音合成(TTS)、语音反馈等",
    },
    {
        "name": "通知推送",
        "description": "消息推送、提醒通知、系统公告等",
    },
    {
        "name": "视频通话",
        "description": "音视频通话、屏幕共享等",
    },
    {
        "name": "无障碍服务",
        "description": "大字体、高对比度、语音引导等无障碍功能",
    },
    {
        "name": "IoT设备",
        "description": "智能设备绑定、数据同步、状态监控等",
    },
    {
        "name": "方言服务",
        "description": "方言识别、方言合成、地区配置等",
    },
    {
        "name": "简化模式",
        "description": "老年人简化操作模式配置",
    },
    {
        "name": "娱乐服务",
        "description": "音乐、戏曲、有声书、新闻等内容服务",
    },
    {
        "name": "认知训练",
        "description": "记忆游戏、数字游戏、棋牌等认知训练",
    },
    {
        "name": "社交功能",
        "description": "好友管理、群组聊天、动态分享等",
    },
    {
        "name": "家庭绑定",
        "description": "家庭成员绑定、监护权限、远程关怀等",
    },
    {
        "name": "消息中心",
        "description": "站内信、系统消息、消息设置等",
    },
    {
        "name": "新手引导",
        "description": "使用教程、功能引导、帮助中心等",
    },
    {
        "name": "个性化配置",
        "description": "用户偏好、界面设置、AI人设等",
    },
    {
        "name": "会员订阅",
        "description": "会员套餐、订阅管理、权益说明等",
    },
    {
        "name": "支付接口",
        "description": "支付下单、订单查询、退款处理等",
    },
    {
        "name": "运营管理",
        "description": "后台管理、用户审核、内容管理等",
    },
    {
        "name": "数据分析",
        "description": "用户分析、使用统计、数据报表等",
    },
    {
        "name": "营销推广",
        "description": "活动管理、优惠券、推广统计等",
    },
    {
        "name": "国际化",
        "description": "多语言支持、地区适配等",
    },
    {
        "name": "AI功能",
        "description": "高级AI能力、智能推荐、情感分析等",
    },
    {
        "name": "第三方集成",
        "description": "医院对接、保险对接、政府服务等",
    },
    {
        "name": "客户支持",
        "description": "工单系统、在线客服、意见反馈等",
    },
    {
        "name": "生活服务",
        "description": "天气、日历、提醒、新闻等便民服务",
    },
    {
        "name": "智能家居",
        "description": "家电控制、场景联动、环境监测等",
    },
    {
        "name": "安全守护",
        "description": "位置追踪、电子围栏、异常报警等",
    },
    {
        "name": "营养饮食",
        "description": "饮食记录、营养分析、食谱推荐等",
    },
    {
        "name": "运动康复",
        "description": "运动记录、康复训练、健身指导等",
    },
    {
        "name": "回忆录",
        "description": "照片管理、人生故事、语音日记等",
    },
    {
        "name": "心理健康",
        "description": "情绪评估、心理疏导、冥想放松等",
    },
    {
        "name": "社区服务",
        "description": "社区活动、志愿服务、邻里互助等",
    },
    {
        "name": "文件管理",
        "description": "文件上传、下载、存储管理等",
    },
    {
        "name": "实时通信",
        "description": "WebSocket连接、实时消息、状态同步等",
    },
    {
        "name": "报表导出",
        "description": "数据报表、PDF导出、Excel导出等",
    },
    {
        "name": "审计日志",
        "description": "操作日志、安全审计、合规记录等",
    },
    {
        "name": "主动交互",
        "description": "智能问候、主动提醒、行为学习、个性化关怀等",
    },
    {
        "name": "情感记忆",
        "description": "用户画像、记忆管理、重要日期、人生故事等",
    },
    {
        "name": "药品识别",
        "description": "OCR药品识别、药物相互作用检查、老年人用药提示等",
    },
    {
        "name": "认知训练",
        "description": "认知游戏、评估测试、训练计划、统计报告等",
    },
    {
        "name": "系统监控",
        "description": "健康检查、性能指标、系统状态等",
    },
    {
        "name": "今日爸妈",
        "description": "子女安心日报、安心指数趋势、每日状态摘要等",
    },
]

# 创建应用
app = FastAPI(
    title="安心宝云端服务",
    description="""
# 安心宝 - 智能健康陪聊音箱后端API

## 项目简介
安心宝是一款专为老年人设计的智能健康管理平台，通过AI语音交互技术，提供健康监测、用药提醒、紧急求助、情感陪伴等全方位服务。

## 核心功能模块

### 🏥 健康管理
- 血压、心率、血糖、血氧等健康数据记录与分析
- 智能健康告警与趋势分析
- 周/月健康报告自动生成

### 💊 用药管理
- 用药计划制定与提醒
- 服药依从性统计
- 药品库存管理与补货提醒

### 🆘 紧急服务
- 一键SOS求助
- 跌倒自动检测与报警
- 紧急联系人管理
- 事件全流程追踪

### 🗣️ 智能对话
- 自然语言理解与对话
- 多方言识别支持
- 情感化语音交互

### 👨‍👩‍👧‍👦 家庭关怀
- 家庭成员绑定
- 远程健康监护
- 活动轨迹查看

## API认证
本API使用JWT Token进行身份认证。请在请求头中携带：
```
Authorization: Bearer <your_token>
```

## 错误码说明
| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权或Token过期 |
| 403 | 无访问权限 |
| 404 | 资源不存在 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

## 联系我们
- 技术支持：support@anxinbao.com
- 官方网站：https://www.anxinbao.com
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    contact={
        "name": "安心宝技术支持",
        "url": "https://www.anxinbao.com",
        "email": "support@anxinbao.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    lifespan=lifespan
)

# 添加限流器到应用状态
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS配置（从配置文件读取）
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# 添加安全响应头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 添加GZip响应压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=500)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 添加Prometheus指标中间件
app.add_middleware(PrometheusMiddleware)

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板
templates = Jinja2Templates(directory="templates")

# ===== 生产环境 OpenAPI 守卫 =====
# 红色就绪度模块（参见 FEATURE_STATUS.md）在生产环境从 Swagger schema 隐藏，
# 避免攻击者通过 /docs 探测到内部数据结构、避免投资人/合伙人误以为这些功能可用。
# 路由本身保留（向后兼容已存在的客户端），仅从文档中隐藏 + 由路由层各自做 410/0 处理。
_RED_ROUTERS_HIDE_IN_PROD = {"users", "admin", "analytics", "ai"}


def _include_router_safely(router_obj, *, name: str = "") -> None:
    """生产环境：对红色就绪度模块统一加 include_in_schema=False"""
    if not settings.debug and name in _RED_ROUTERS_HIDE_IN_PROD:
        app.include_router(router_obj, include_in_schema=False)
    else:
        app.include_router(router_obj)


# 注册路由
app.include_router(auth_router)  # 认证路由放在最前面
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(notify_router)
_include_router_safely(users_router, name="users")  # 已废弃，生产环境从 Swagger 隐藏
app.include_router(health_router)
app.include_router(video_router)
app.include_router(accessibility_router)  # 无障碍设置
app.include_router(iot_router)  # IoT设备管理
app.include_router(dialect_router)  # 方言服务
app.include_router(simple_router)  # 简化操作模式
app.include_router(entertainment_router)  # 娱乐服务
app.include_router(games_router)  # 认知训练游戏
app.include_router(emergency_router)  # 紧急求助
app.include_router(social_router)  # 社交功能
app.include_router(family_router)  # 家庭绑定
app.include_router(messages_router)  # 消息中心
app.include_router(voice_feedback_router)  # 语音反馈
app.include_router(onboarding_router)  # 新手引导
app.include_router(preferences_router)  # 个性化配置
app.include_router(subscription_router)  # 会员订阅
app.include_router(payment_router)  # 支付
_include_router_safely(admin_router, name="admin")  # 红色就绪度，生产隐藏
_include_router_safely(analytics_router, name="analytics")  # 红色就绪度，生产隐藏
app.include_router(marketing_router)  # 营销推广
app.include_router(i18n_router)  # 国际化
_include_router_safely(ai_router, name="ai")  # 红色就绪度，生产隐藏（与 chat 域职责重叠）
app.include_router(integration_router)  # 第三方集成
app.include_router(support_router)  # 客户支持
app.include_router(life_router)  # 生活服务
app.include_router(smart_home_router)  # 智能家居
app.include_router(safety_router)  # 安全守护
app.include_router(medication_router)  # 用药管理
app.include_router(nutrition_router)  # 营养饮食
app.include_router(exercise_router)  # 运动康复
app.include_router(memory_router)  # 回忆录
app.include_router(mental_health_router)  # 心理健康
app.include_router(community_router)  # 社区服务
app.include_router(file_router)  # 文件管理
app.include_router(ws_router)  # WebSocket实时通信
app.include_router(report_router)  # 报表导出
app.include_router(audit_router)  # 审计日志
app.include_router(proactive_router)  # 主动交互系统
app.include_router(memory_api_router)  # 情感记忆系统
app.include_router(drug_api_router)  # 药品识别模块
app.include_router(cognitive_api_router)  # 认知训练模块
app.include_router(daily_report_router)  # 今日爸妈-子女安心日报

# 注册监控路由
app.include_router(create_metrics_endpoint())
app.include_router(create_health_endpoints())


# ==================== 健康检查注册 ====================

async def check_database():
    """检查数据库连接"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


async def check_redis():
    """检查Redis连接"""
    try:
        from app.core.cache import get_redis_client
        client = get_redis_client()
        if client:
            return client.ping()
        return True  # Redis未配置时视为健康
    except Exception:
        return False


# 注册健康检查
health_probe.register_check("database", check_database)
health_probe.register_check("redis", check_redis)


@app.get("/")
async def index(request: Request):
    """首页 - Web演示界面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查（简单版）"""
    return {"status": "ok", "service": "anxinbao-server", "version": "1.0.0"}


# 关键第三方集成的占位特征：用于识别"看似配置实则是测试样板"
_PLACEHOLDER_HINTS = ("test_", "your_", "xxx", "changeme", "placeholder", "example")


def _classify(value: str | None) -> str:
    """将凭据值分类为 real / placeholder / missing。"""
    if not value:
        return "missing"
    v = str(value).strip().lower()
    if not v:
        return "missing"
    if any(h in v for h in _PLACEHOLDER_HINTS):
        return "placeholder"
    return "real"


@app.get("/health/integrations")
async def integrations_health():
    """
    第三方集成真实性自检：暴露每个外部服务是 real/mock/missing。
    目的是杜绝"凭据缺失时静默走入 mock"导致 SOS 短信、支付等关键链路在生产环境
    悄无声息地失败。运维和投资人能用这个端点一眼看清"哪些链路是真实的"。
    """
    # 注意：属性名必须与 services/ 中实际读取的字段一致
    # （历史上 .env.example 写 SMS_ACCESS_KEY_ID 但代码读 aliyun_access_key_id，
    #  导致用户填了 .env 也无效，是另一个隐藏的"凭据失联"bug）
    checks = [
        ("dashscope_qwen",
         _classify(getattr(settings, "dashscope_api_key", "")),
         "通义千问 AI 对话"),
        ("xfyun_asr_tts",
         _classify(getattr(settings, "xfyun_appid", "")
                   and getattr(settings, "xfyun_api_key", "")
                   and getattr(settings, "xfyun_api_secret", "")),
         "讯飞语音识别/合成（含方言）"),
        ("aliyun_sms",
         _classify(getattr(settings, "aliyun_access_key_id", "")),
         "阿里云短信（健康告警/SOS）"),
        ("jpush",
         _classify(getattr(settings, "jpush_app_key", "")),
         "极光推送"),
        ("alipay",
         _classify(getattr(settings, "alipay_app_id", "")),
         "支付宝（订阅付费）"),
        ("encryption_key",
         _classify(getattr(settings, "encryption_key", "")),
         "敏感数据加密密钥"),
        ("jwt_secret",
         "real" if (
             getattr(settings, "jwt_secret_key", "")
             and len(str(settings.jwt_secret_key)) >= 32
         ) else "weak",
         "JWT 签名密钥"),
    ]

    results = []
    critical_missing = []
    for name, status, desc in checks:
        results.append({
            "name": name,
            "description": desc,
            "status": status,  # real / placeholder / missing / weak
            "production_ready": status == "real",
        })
        # SOS、支付、加密、JWT 是不可降级的关键链路
        if name in {"aliyun_sms", "alipay", "encryption_key", "jwt_secret"} \
                and status != "real":
            critical_missing.append(name)

    # ===== CORS 自检（与 _enforce_production_secrets 同一套规则但只报告不阻断）=====
    cors_status = "real"
    cors_issues: list[str] = []
    raw_origins = (settings.allowed_origins or "").strip()
    if raw_origins == "*":
        cors_status = "missing"  # 与"无配置"等价的危险
        cors_issues.append("ALLOWED_ORIGINS=* 在生产是任意域可发 credentialed 请求")
    elif not raw_origins:
        cors_status = "missing"
        cors_issues.append("ALLOWED_ORIGINS 未配置")
    else:
        for o in (x.strip() for x in raw_origins.split(",") if x.strip()):
            ol = o.lower()
            if "localhost" in ol or ol.startswith("http://127.") or ol.startswith("http://0.0.0.0"):
                cors_status = "placeholder"
                cors_issues.append(f"{o} 是本地地址，不该出现在生产 CORS")
            elif ol.startswith("http://"):
                cors_status = "placeholder"
                cors_issues.append(f"{o} 非 HTTPS")

    # ===== DLQ 状态 =====
    dlq_size = 0
    dlq_critical = 0
    dlq_counts: dict[str, int] = {}
    try:
        from app.core.dead_letter import dead_letter_queue
        dlq_size = dead_letter_queue.size()
        dlq_counts = dict(dead_letter_queue.counts)
        dlq_critical = sum(
            1 for r in dead_letter_queue.list(limit=10000) if r.severity == "critical"
        )
    except Exception:
        pass

    # ===== Scheduler 状态 =====
    scheduler_metrics: dict[str, int] = {}
    try:
        from app.core.scheduler import scheduler as _scheduler
        scheduler_metrics = dict(_scheduler.metrics)
    except Exception:
        pass

    # 把 CORS 加入 results 列表（保持原数组结构，前端不破坏）
    results.append({
        "name": "cors",
        "description": "生产 CORS 白名单（不可含 *、localhost、http://）",
        "status": cors_status,
        "production_ready": cors_status == "real",
        "issues": cors_issues,
    })
    if cors_status != "real":
        critical_missing.append("cors")

    # 把 DLQ critical 也作为生产门：累计 ≥10 条 critical 视为生产不就绪
    dlq_block = dlq_critical >= 10
    if dlq_block:
        critical_missing.append("dead_letter_queue")

    return {
        "service": "anxinbao-server",
        "production_ready": len(critical_missing) == 0,
        "critical_missing": critical_missing,
        "integrations": results,
        "dead_letter_queue": {
            "size": dlq_size,
            "critical_count": dlq_critical,
            "counts_by_channel": dlq_counts,
            "blocking_production": dlq_block,
            "note": "critical 累计 ≥10 条视为生产不就绪；运维补偿后调用 POST /api/admin/dlq/clear",
        },
        "scheduler": {
            "metrics": scheduler_metrics,
            "note": "包含 jobs_errored / jobs_missed / jobs_max_instances（启动以来累计）",
        },
        "note": (
            "production_ready=false 表示存在未真实配置的关键链路或 DLQ 堆积；"
            "上线前必须把 critical_missing 全部解决。"
        ),
    }


@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "name": "安心宝云端服务",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth - 认证接口",
            "chat": "/api/chat - 对话接口",
            "voice": "/api/voice - 语音接口",
            "notify": "/api/notify - 通知接口",
            "users": "/api/users - 用户管理",
            "health": "/api/health - 健康数据管理",
            "video": "/api/video - 视频通话",
            "accessibility": "/api/accessibility - 无障碍设置",
            "iot": "/api/iot - IoT设备管理",
            "dialect": "/api/dialect - 方言服务",
            "simple": "/api/simple - 简化操作模式",
            "entertainment": "/api/entertainment - 娱乐服务",
            "games": "/api/games - 认知训练游戏",
            "emergency": "/api/emergency - 紧急求助",
            "social": "/api/social - 社交功能",
            "family": "/api/family - 家庭绑定监护",
            "messages": "/api/messages - 消息中心",
            "voice_feedback": "/api/voice-feedback - 语音反馈",
            "onboarding": "/api/onboarding - 新手引导",
            "preferences": "/api/preferences - 个性化配置",
            "subscription": "/api/subscription - 会员订阅",
            "payment": "/api/payment - 支付接口",
            "admin": "/api/admin - 运营管理后台",
            "analytics": "/api/analytics - 数据分析报表",
            "marketing": "/api/marketing - 营销推广",
            "i18n": "/api/i18n - 国际化本地化",
            "ai": "/api/ai - 高级AI功能",
            "integration": "/api/integration - 第三方集成",
            "support": "/api/support - 客户支持",
            "life": "/api/life - 生活服务",
            "smart_home": "/api/smart-home - 智能家居",
            "safety": "/api/safety - 安全守护",
            "medication": "/api/medication - 用药管理",
            "nutrition": "/api/nutrition - 营养饮食",
            "exercise": "/api/exercise - 运动康复",
            "memory": "/api/memory - 回忆录",
            "mental_health": "/api/mental-health - 心理健康",
            "community": "/api/community - 社区服务",
            "files": "/api/files - 文件管理",
            "websocket": "/api/ws - WebSocket实时通信",
            "reports": "/api/reports - 报表导出",
            "audit": "/api/audit - 审计日志",
            "proactive": "/api/proactive - 主动交互系统",
            "memory_profile": "/api/memory-profile - 情感记忆系统",
            "drug": "/api/drug - 药品识别模块",
            "cognitive": "/api/cognitive - 认知训练模块",
            "daily_report": "/api/daily-report - 今日爸妈安心日报",
            "metrics": "/metrics - Prometheus指标"
        },
        "monitoring": {
            "metrics": "/metrics",
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "health_detailed": "/health/detailed"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
