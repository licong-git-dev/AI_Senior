"""
API路由 - 认证模块
提供用户注册、登录、令牌刷新、设备认证等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query, status
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timedelta
import hashlib
import json
import threading

from app.core.security import (
    get_password_hash,
    verify_password,
    create_tokens,
    decode_token,
    get_current_user,
    UserInfo,
    TokenResponse
)
from app.models.database import SessionLocal, UserAuth, DeviceAuth, RefreshToken, AuditLog, User, FamilyMember, get_db
from app.core.limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ============= 登录失败锁定 =============

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# { username: { "attempts": int, "first_attempt": datetime, "locked_until": datetime | None } }
_login_attempts: dict = {}
_login_attempts_lock = threading.Lock()


def _cleanup_expired_entries():
    """清理过期的登录尝试记录"""
    now = datetime.utcnow()
    expired = [
        k for k, v in _login_attempts.items()
        if (v.get("locked_until") and v["locked_until"] < now)
        or (now - v["first_attempt"] > timedelta(minutes=LOCKOUT_MINUTES))
    ]
    for k in expired:
        del _login_attempts[k]


def _check_login_allowed(username: str):
    """检查是否允许登录，若被锁定则抛出429"""
    now = datetime.utcnow()
    with _login_attempts_lock:
        _cleanup_expired_entries()
        record = _login_attempts.get(username)
        if record and record.get("locked_until"):
            if now < record["locked_until"]:
                remaining = int((record["locked_until"] - now).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"登录尝试次数过多，请在{remaining}秒后重试"
                )
            else:
                # 锁定已过期，清除记录
                del _login_attempts[username]


def _record_failed_attempt(username: str):
    """记录一次失败的登录尝试，达到阈值则锁定"""
    now = datetime.utcnow()
    with _login_attempts_lock:
        record = _login_attempts.get(username)
        if record is None or (now - record["first_attempt"] > timedelta(minutes=LOCKOUT_MINUTES)):
            _login_attempts[username] = {
                "attempts": 1,
                "first_attempt": now,
                "locked_until": None,
            }
        else:
            record["attempts"] += 1
            if record["attempts"] >= MAX_LOGIN_ATTEMPTS:
                record["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)


def _clear_failed_attempts(username: str):
    """登录成功后清除失败记录"""
    with _login_attempts_lock:
        _login_attempts.pop(username, None)


# ============= 请求/响应模型 =============

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description='用户名/手机号')
    password: str = Field(..., min_length=6, max_length=100, description='密码')
    role: Literal["elder", "family"] = Field(default="family", description="角色：elder/family")
    name: Optional[str] = Field(None, description="姓名")


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description='用户名/手机号')
    password: str = Field(..., description="密码")


class DeviceLoginRequest(BaseModel):
    """设备登录请求"""
    device_id: str = Field(..., description='设备ID')
    device_secret: str = Field(..., description="设备密钥")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description='旧密码')
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class DeviceRegisterRequest(BaseModel):
    """设备注册请求"""
    device_id: str = Field(..., description='设备ID')
    device_type: str = Field(default='speaker', description="设备类型")


class DeviceBindRequest(BaseModel):
    """设备绑定请求"""
    device_id: str = Field(..., description='设备ID')
    elder_id: int = Field(..., description="老人ID")


# ============= 辅助函数 =============

def log_audit(
    db,
    action: str,
    user_id: str = None,
    resource: str = None,
    resource_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    details: dict = None,
    status: str = "success"
):
    """记录审计日志"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=json.dumps(details) if details else None,
        status=status
    )
    db.add(audit)
    db.commit()


def hash_token(token: str) -> str:
    """哈希令牌（用于存储）"""
    return hashlib.sha256(token.encode()).hexdigest()


# ============= API端点 =============

@router.post("/register", response_model=dict)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db=Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名或手机号（唯一）
    - **password**: 密码（至少6位）
    - **role**: 用户角色，可选 elder（老人）或 family（家属），默认family
    - **name**: 姓名（可选）
    """
    # 检查用户名是否已存在
    existing = db.query(UserAuth).filter(UserAuth.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='用户名已存在'
        )

    # 创建用户认证记录
    user_auth = UserAuth(
        username=body.username,
        password_hash=get_password_hash(body.password),
        role=body.role
    )

    # 如果是老人角色，同时创建User记录
    if body.role == 'elder':
        user = User(name=body.name or body.username)
        db.add(user)
        db.flush()  # 获取user.id
        user_auth.user_id = user.id

    db.add(user_auth)
    db.commit()
    db.refresh(user_auth)

    # 记录审计日志
    log_audit(
        db,
        action='register',
        user_id=str(user_auth.id),
        resource='user_auth',
        resource_id=str(user_auth.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
        details={'username': body.username, 'role': body.role}
    )

    return {
        'success': True,
        'message': '注册成功',
        'user_id': user_auth.id
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db=Depends(get_db)
):
    """
    用户登录

    返回访问令牌和刷新令牌
    """
    # 检查是否被锁定
    _check_login_allowed(body.username)

    # 查找用户
    user_auth = db.query(UserAuth).filter(
        UserAuth.username == body.username
    ).first()

    if not user_auth or not verify_password(body.password, user_auth.password_hash):
        _record_failed_attempt(body.username)
        log_audit(
            db,
            action="login_failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            details={'username': body.username},
            status='failure'
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='用户名或密码错误'
        )

    if not user_auth.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='账号已被禁用'
        )

    # 登录成功，清除失败记录
    _clear_failed_attempts(body.username)

    # 创建令牌
    tokens = create_tokens(
        user_id=str(user_auth.id),
        role=user_auth.role
    )

    # 更新最后登录时间
    user_auth.last_login = datetime.now()
    db.commit()

    # 存储刷新令牌哈希（用于撤销）
    from app.core.config import get_settings
    settings = get_settings()
    from datetime import timedelta
    refresh_token_record = RefreshToken(
        token_hash=hash_token(tokens.refresh_token),
        user_auth_id=user_auth.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    )
    db.add(refresh_token_record)
    db.commit()

    # 记录审计日志
    log_audit(
        db,
        action='login',
        user_id=str(user_auth.id),
        resource='user_auth',
        resource_id=str(user_auth.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return tokens


@router.post("/device/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # 防止设备 secret 暴力破解（与 user login 同强度）
async def device_login(
    body: DeviceLoginRequest,
    request: Request,
    db=Depends(get_db)
):
    """
    设备登录

    设备使用device_id和device_secret进行认证
    """
    # 查找设备
    device = db.query(DeviceAuth).filter(
        DeviceAuth.device_id == body.device_id
    ).first()

    if not device or not verify_password(body.device_secret, device.device_secret):
        log_audit(
            db,
            action="device_login_failed",
            ip_address=request.client.host if request.client else None,
            details={'device_id': body.device_id},
            status="failure"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='设备认证失败'
        )

    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='设备已被禁用'
        )

    # 创建令牌
    tokens = create_tokens(
        user_id=str(device.user_id) if device.user_id else f'device_{device.id}',
        role="device",
        device_id=device.device_id
    )

    # 更新最后活跃时间
    device.last_active = datetime.now()
    db.commit()

    # 存储刷新令牌
    from app.core.config import get_settings
    settings = get_settings()
    from datetime import timedelta
    refresh_token_record = RefreshToken(
        token_hash=hash_token(tokens.refresh_token),
        device_auth_id=device.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    )
    db.add(refresh_token_record)
    db.commit()

    # 记录审计日志
    log_audit(
        db,
        action="device_login",
        user_id=f'device_{device.id}',
        resource='device_auth',
        resource_id=str(device.id),
        ip_address=request.client.host if request.client else None,
        details={'device_id': body.device_id}
    )

    return tokens


@router.post('/refresh', response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    db=Depends(get_db)
):
    """
    刷新访问令牌

    使用刷新令牌获取新的访问令牌
    """
    # 验证刷新令牌
    payload = decode_token(body.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='无效的刷新令牌'
        )

    if payload.type != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='请使用刷新令牌'
        )

    # 检查令牌是否被撤销
    token_hash = hash_token(body.refresh_token)
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if token_record and token_record.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='令牌已被撤销'
        )

    # 创建新令牌
    tokens = create_tokens(
        user_id=payload.sub,
        role=payload.role,
        device_id=payload.device_id
    )

    # 撤销旧的刷新令牌
    if token_record:
        token_record.is_revoked = True

    # 存储新的刷新令牌
    from app.core.config import get_settings
    settings = get_settings()
    from datetime import timedelta
    new_token_record = RefreshToken(
        token_hash=hash_token(tokens.refresh_token),
        user_auth_id=token_record.user_auth_id if token_record else None,
        device_auth_id=token_record.device_auth_id if token_record else None,
        expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    )
    db.add(new_token_record)
    db.commit()

    return tokens


@router.post("/logout")
async def logout(
    body: RefreshTokenRequest,
    request: Request,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    登出

    撤销刷新令牌，使其无法再刷新访问令牌
    """
    token_hash = hash_token(body.refresh_token)
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if token_record:
        token_record.is_revoked = True
        db.commit()

    # 记录审计日志
    log_audit(
        db,
        action='logout',
        user_id=current_user.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )

    return {'success': True, 'message': "登出成功"}


@router.post("/change-password")
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    修改密码
    """
    # 查找用户
    user_auth = db.query(UserAuth).filter(
        UserAuth.id == int(current_user.user_id)
    ).first()

    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 验证旧密码
    if not verify_password(body.old_password, user_auth.password_hash):
        log_audit(
            db,
            action="change_password_failed",
            user_id=current_user.user_id,
            ip_address=request.client.host if request.client else None,
            status='failure'
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='旧密码错误'
        )

    # 更新密码
    user_auth.password_hash = get_password_hash(body.new_password)
    user_auth.updated_at = datetime.now()
    db.commit()

    # 撤销所有刷新令牌
    db.query(RefreshToken).filter(
        RefreshToken.user_auth_id == user_auth.id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()

    # 记录审计日志
    log_audit(
        db,
        action="change_password",
        user_id=current_user.user_id,
        resource='user_auth',
        resource_id=current_user.user_id,
        ip_address=request.client.host if request.client else None
    )

    return {'success': True, 'message': "密码修改成功，请重新登录"}


@router.post("/device/register")
@limiter.limit("3/minute")
async def register_device(
    request: Request,
    body: DeviceRegisterRequest,
    db=Depends(get_db)
):
    """
    注册新设备

    返回设备密钥（仅显示一次，请妥善保存）
    """
    # 检查设备ID是否已存在
    existing = db.query(DeviceAuth).filter(
        DeviceAuth.device_id == body.device_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="设备ID已存在"
        )

    # 生成设备密钥
    import secrets
    device_secret = secrets.token_urlsafe(32)

    # 创建设备记录
    device = DeviceAuth(
        device_id=body.device_id,
        device_secret=get_password_hash(device_secret),
        device_type=body.device_type
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    # 记录审计日志
    log_audit(
        db,
        action="device_register",
        resource="device_auth",
        resource_id=str(device.id),
        ip_address=request.client.host if request.client else None,
        details={'device_id': body.device_id, "device_type": body.device_type}
    )

    return {
        'success': True,
        'message': '设备注册成功',
        "device_id": body.device_id,
        "device_secret": device_secret,  # 仅显示一次
        "warning": "请妥善保存设备密钥，此密钥仅显示一次"
    }


@router.post("/device/bind")
@limiter.limit("10/minute")  # 防止恶意批量绑定枚举有效设备 ID
async def bind_device(
    body: DeviceBindRequest,
    request: Request,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    绑定设备到老人

    将设备与老人账号关联
    """
    # 检查权限（只有家属或管理员可以绑定设备）
    if current_user.role not in ['family', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='无权限执行此操作'
        )

    # 查找设备
    device = db.query(DeviceAuth).filter(
        DeviceAuth.device_id == body.device_id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='设备不存在'
        )

    # 检查老人是否存在
    elder = db.query(User).filter(User.id == body.elder_id).first()
    if not elder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="老人账号不存在"
        )

    # 绑定设备
    device.user_id = body.elder_id
    device.updated_at = datetime.now()
    db.commit()

    # 记录审计日志
    log_audit(
        db,
        action="device_bind",
        user_id=current_user.user_id,
        resource="device_auth",
        resource_id=str(device.id),
        ip_address=request.client.host if request.client else None,
        details={'device_id': body.device_id, 'elder_id': body.elder_id}
    )

    return {
        'success': True,
        'message': '设备绑定成功'
    }


@router.get("/me")
async def get_current_user_info(
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    获取当前用户信息
    """
    result = {
        'user_id': current_user.user_id,
        'role': current_user.role,
        'device_id': current_user.device_id
    }

    # 如果是普通用户，获取更多信息
    if current_user.role in ['elder', 'family']:
        user_auth = db.query(UserAuth).filter(
            UserAuth.id == int(current_user.user_id)
        ).first()

        if user_auth:
            result['username'] = user_auth.username
            result['last_login'] = user_auth.last_login.isoformat() if user_auth.last_login else None

            if user_auth.role == 'elder' and user_auth.user_id:
                # 老人端：UserAuth.user_id 直接指向 User.id
                user = db.query(User).filter(User.id == user_auth.user_id).first()
                if user:
                    result['name'] = user.name
                    result["elder_id"] = user.id

            elif user_auth.role == 'family' and user_auth.family_id:
                # 家属端：UserAuth.family_id → FamilyMember.user_id (老人 User.id)
                family_member = db.query(FamilyMember).filter(
                    FamilyMember.id == user_auth.family_id
                ).first()
                if family_member:
                    result['name'] = family_member.name
                    result['elder_id'] = family_member.user_id

    return result


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[str] = Query(None, description="按用户 ID 过滤；普通用户只能传自己的"),
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    获取审计日志（按角色作用域）。

    权限模型（修复 r10：原版本任意 admin 可查全量是合规风险）：
    - super_admin / admin（含 admin_service 注册）：可查全量；可按 user_id 过滤
    - elder / family / device：仅可查自己（current_user.user_id）的审计日志
    - 未授权角色：403

    审计日志含 PII / 业务敏感数据，全员可见会造成隐私泄漏。
    """
    role = current_user.role or ""
    is_privileged = role in {"admin", "super_admin"}

    # 二次校验：admin 角色还需在 admin_service 注册（防 token 伪造）
    if is_privileged and role == "admin":
        try:
            from app.services.admin_service import admin_service
            if not admin_service.get_admin(int(current_user.user_id)):
                is_privileged = False
        except (ValueError, TypeError):
            is_privileged = False

    query = db.query(AuditLog)

    if is_privileged:
        # 全量查看；按可选 user_id 过滤
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
    else:
        # 普通用户只能查自己；显式 user_id 必须等于自己
        if user_id and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="普通用户只能查询自己的审计日志",
            )
        query = query.filter(AuditLog.user_id == current_user.user_id)

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'scope': "all" if is_privileged else "self",
        'logs': [
            {
                'id': log.id,
                'user_id': log.user_id,
                'action': log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                'ip_address': log.ip_address,
                'status': log.status,
                'created_at': log.created_at.isoformat()
            }
            for log in logs
        ]
    }
