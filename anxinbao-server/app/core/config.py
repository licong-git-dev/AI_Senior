"""
配置管理模块
"""
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    # 科大讯飞配置
    xfyun_appid: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""

    # 通义千问配置
    dashscope_api_key: str = ""

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # 数据库配置
    database_url: str = "sqlite:///./anxinbao.db"

    # 健康风险阈值
    health_risk_threshold: int = 7

    # JWT认证配置
    jwt_secret_key: str = secrets.token_urlsafe(32)  # 生产环境必须通过环境变量设置
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30  # 访问令牌30分钟过期
    jwt_refresh_token_expire_days: int = 7  # 刷新令牌7天过期

    # 安全配置
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"  # 生产环境设置为具体域名，如 "https://example.com,https://app.example.com'
    api_rate_limit: str = '100/minute'  # API限流配置

    # 数据加密密钥（用于敏感数据加密）
    encryption_key: str = ""  # 生产环境必须设置，32字节base64编码

    # Redis配置（可选）
    redis_url: str = ''  # 如 "redis://localhost:6379/0"

    # ===== 第三方集成（services/ 实际读取的字段，必须显式声明否则 .env 不加载）=====
    # 阿里云短信（健康告警 / SOS 紧急通知）
    # 历史 .env 用 SMS_ACCESS_KEY_ID 命名，这里通过 AliasChoices 兼容两种环境变量名。
    aliyun_access_key_id: str = Field(
        default="",
        validation_alias=AliasChoices("aliyun_access_key_id", "sms_access_key_id"),
    )
    aliyun_access_key_secret: str = Field(
        default="",
        validation_alias=AliasChoices("aliyun_access_key_secret", "sms_access_key_secret"),
    )
    sms_sign_name: str = "安心宝"
    sms_template_code: str = ""
    sms_template_emergency: str = ""
    sms_template_health_alert: str = ""

    # 极光推送
    jpush_app_key: str = ""
    jpush_master_secret: str = ""

    # 支付宝
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""
    payment_notify_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        # 允许 .env 中存在未声明的额外字段，避免对历史扩展环境变量的破坏性变更。
        extra = "ignore"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
