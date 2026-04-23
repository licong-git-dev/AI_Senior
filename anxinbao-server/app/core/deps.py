"""
依赖注入模块
提供数据库会话、Redis客户端、当前用户等FastAPI依赖项
"""
from typing import Generator, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.models.database import SessionLocal
from app.core.config import get_settings, Settings
from app.core.cache import (
    get_redis_client,
    SessionStore,
    ConversationStore,
    CacheStore,
    session_store,
    conversation_store,
    cache_store,
)
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    require_role,
    UserInfo,
)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_settings_dep() -> Settings:
    """获取应用配置（依赖注入）"""
    return get_settings()


def get_redis():
    """获取Redis客户端（依赖注入），无Redis时返回None"""
    return get_redis_client()


def get_session_store() -> SessionStore:
    """获取会话存储实例"""
    return session_store


def get_conversation_store() -> ConversationStore:
    """获取对话历史存储实例"""
    return conversation_store


def get_cache() -> CacheStore:
    """获取缓存存储实例"""
    return cache_store


def get_current_active_user(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserInfo:
    """
    获取当前激活用户（检查用户状态是否有效）

    在需要确认用户账户仍处于激活状态时使用此依赖。
    """
    from app.models.database import UserAuth

    user_auth = db.query(UserAuth).filter(
        UserAuth.id == int(current_user.user_id)
    ).first()

    if not user_auth or not user_auth.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用",
        )

    return current_user


def get_current_elder(
    current_user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """获取当前老人用户（仅老人角色可访问）"""
    if current_user.role != "elder":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅老人用户可访问此接口",
        )
    return current_user


def get_current_family(
    current_user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """获取当前家属用户（仅家属角色可访问）"""
    if current_user.role != "family":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅家属用户可访问此接口",
        )
    return current_user


def get_current_admin(
    current_user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """获取当前管理员用户（仅管理员角色可访问）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问此接口",
        )
    return current_user
