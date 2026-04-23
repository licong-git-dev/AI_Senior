"""
安全认证模块
提供JWT认证、密码哈希、数据加密等安全功能
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import base64
import hashlib
import hmac
import time

from app.core.config import get_settings

settings = get_settings()

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer Token认证
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: str  # 主题（用户ID）
    type: str  # 令牌类型：access/refresh
    role: str  # 用户角色：elder/family/admin/device
    exp: datetime  # 过期时间
    iat: datetime  # 签发时间
    device_id: Optional[str] = None  # 设备ID（设备认证时使用）


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class UserInfo(BaseModel):
    """当前用户信息"""
    user_id: str
    role: str
    device_id: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    role: str,
    device_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        user_id: 用户ID
        role: 用户角色（elder/family/admin/device）
        device_id: 设备ID（可选）
        expires_delta: 自定义过期时间

    Returns:
        JWT访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode = {
        "sub": user_id,
        "type": "access",
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    if device_id:
        to_encode["device_id"] = device_id

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    role: str,
    device_id: Optional[str] = None
) -> str:
    """
    创建刷新令牌

    Args:
        user_id: 用户ID
        role: 用户角色
        device_id: 设备ID（可选）

    Returns:
        JWT刷新令牌
    """
    expire = datetime.utcnow() + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )

    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    if device_id:
        to_encode["device_id"] = device_id

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_tokens(
    user_id: str,
    role: str,
    device_id: Optional[str] = None
) -> TokenResponse:
    """
    创建访问令牌和刷新令牌

    Args:
        user_id: 用户ID
        role: 用户角色
        device_id: 设备ID（可选）

    Returns:
        TokenResponse包含两个令牌
    """
    access_token = create_access_token(user_id, role, device_id)
    refresh_token = create_refresh_token(user_id, role, device_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    解码并验证JWT令牌

    Args:
        token: JWT令牌

    Returns:
        TokenPayload或None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return TokenPayload(
            sub=payload.get("sub"),
            type=payload.get("type"),
            role=payload.get("role"),
            exp=datetime.fromtimestamp(payload.get("exp")),
            iat=datetime.fromtimestamp(payload.get("iat")),
            device_id=payload.get("device_id")
        )
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInfo:
    """
    获取当前认证用户（依赖注入）

    用法:
        @router.get("/protected")
        async def protected_route(current_user: UserInfo = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserInfo(
        user_id=payload.sub,
        role=payload.role,
        device_id=payload.device_id
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInfo]:
    """
    获取当前用户（可选，不强制认证）

    用法:
        @router.get("/public")
        async def public_route(current_user: Optional[UserInfo] = Depends(get_current_user_optional)):
            if current_user:
                return {"authenticated": True}
            return {"authenticated": False}
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None or payload.type != "access":
        return None

    return UserInfo(
        user_id=payload.sub,
        role=payload.role,
        device_id=payload.device_id
    )


def require_role(*roles: str):
    """
    角色权限装饰器（依赖注入工厂）

    用法:
        @router.get("/admin-only")
        async def admin_route(current_user: UserInfo = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}

        @router.get("/family-or-admin")
        async def family_route(current_user: UserInfo = Depends(require_role("family", "admin"))):
            return {"message": "Access granted"}
    """
    async def role_checker(
        current_user: UserInfo = Depends(get_current_user)
    ) -> UserInfo:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色权限: {', '.join(roles)}"
            )
        return current_user

    return role_checker


def generate_api_signature(
    method: str,
    path: str,
    timestamp: int,
    body: str = "",
    secret_key: str = ""
) -> str:
    """
    生成API请求签名（用于防重放攻击）

    Args:
        method: HTTP方法
        path: 请求路径
        timestamp: 时间戳（秒）
        body: 请求体
        secret_key: 签名密钥

    Returns:
        签名字符串
    """
    if not secret_key:
        secret_key = settings.jwt_secret_key

    message = f"{method.upper()}|{path}|{timestamp}|{body}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_api_signature(
    method: str,
    path: str,
    timestamp: int,
    signature: str,
    body: str = "",
    secret_key: str = "",
    max_age: int = 300  # 签名有效期5分钟
) -> bool:
    """
    验证API请求签名

    Args:
        method: HTTP方法
        path: 请求路径
        timestamp: 时间戳
        signature: 待验证的签名
        body: 请求体
        secret_key: 签名密钥
        max_age: 签名最大有效期（秒）

    Returns:
        验证是否通过
    """
    # 检查时间戳是否过期
    current_time = int(time.time())
    if abs(current_time - timestamp) > max_age:
        return False

    # 验证签名
    expected_signature = generate_api_signature(
        method, path, timestamp, body, secret_key
    )

    return hmac.compare_digest(signature, expected_signature)


class DataEncryptor:
    """
    敏感数据加密器
    使用AES-256-GCM加密
    """

    def __init__(self, key: Optional[str] = None):
        """
        初始化加密器

        Args:
            key: 32字节的Base64编码密钥，如果不提供则使用配置中的密钥
        """
        if key:
            self.key = base64.b64decode(key)
        elif settings.encryption_key:
            self.key = base64.b64decode(settings.encryption_key)
        else:
            # 开发环境生成临时密钥（生产环境必须配置）
            self.key = hashlib.sha256(
                settings.jwt_secret_key.encode()
            ).digest()

    def encrypt(self, plaintext: str) -> str:
        """
        加密数据

        Args:
            plaintext: 明文

        Returns:
            Base64编码的密文
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            import os

            aesgcm = AESGCM(self.key)
            nonce = os.urandom(12)  # 96-bit nonce
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

            # 将nonce和密文组合后Base64编码
            result = base64.b64encode(nonce + ciphertext).decode()
            return result
        except ImportError:
            # 如果cryptography未安装，返回原文（开发环境）
            return plaintext

    def decrypt(self, ciphertext: str) -> str:
        """
        解密数据

        Args:
            ciphertext: Base64编码的密文

        Returns:
            明文
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            data = base64.b64decode(ciphertext)
            nonce = data[:12]
            encrypted = data[12:]

            aesgcm = AESGCM(self.key)
            plaintext = aesgcm.decrypt(nonce, encrypted, None)

            return plaintext.decode()
        except ImportError:
            # 如果cryptography未安装，返回原文
            return ciphertext
        except Exception:
            # 解密失败（可能是未加密的旧数据）
            return ciphertext


# 全局加密器实例
data_encryptor = DataEncryptor()


def mask_phone(phone: str) -> str:
    """
    手机号脱敏

    Args:
        phone: 手机号

    Returns:
        脱敏后的手机号，如 138****1234
    """
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_id_card(id_card: str) -> str:
    """
    身份证号脱敏

    Args:
        id_card: 身份证号

    Returns:
        脱敏后的身份证号，如 110***********1234
    """
    if not id_card or len(id_card) < 8:
        return id_card
    return id_card[:3] + "*" * (len(id_card) - 7) + id_card[-4:]


def mask_name(name: str) -> str:
    """
    姓名脱敏

    Args:
        name: 姓名

    Returns:
        脱敏后的姓名，如 张*明
    """
    if not name:
        return name
    if len(name) == 2:
        return name[0] + "*"
    if len(name) >= 3:
        return name[0] + "*" * (len(name) - 2) + name[-1]
    return name


def mask_address(address: str) -> str:
    """
    地址脱敏

    Args:
        address: 地址

    Returns:
        脱敏后的地址，保留省市区，隐藏详细地址
    """
    if not address or len(address) < 10:
        return address
    # 简单处理：保留前10个字符
    return address[:10] + "****"
