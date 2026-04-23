"""
配置管理模块
"""
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

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> Settings:
    return Settings()
