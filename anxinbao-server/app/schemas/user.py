"""
用户相关模式定义
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

from .base import BaseSchema, TimestampMixin, GenderEnum, RoleEnum, StatusEnum


class UserBase(BaseSchema):
    """用户基础信息"""
    username: str = Field(..., min_length=2, max_length=50, description='用户名')
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$', description='手机号')
    email: Optional[EmailStr] = Field(None, description='邮箱')
    nickname: Optional[str] = Field(None, max_length=50, description='昵称')
    avatar: Optional[str] = Field(None, description='头像URL')
    gender: Optional[GenderEnum] = Field(None, description='性别')
    birthday: Optional[date] = Field(None, description="生日")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=128, description='密码')
    role: RoleEnum = Field(default=RoleEnum.ELDERLY, description='角色')

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("密码长度至少6位")
        return v


class UserUpdate(BaseSchema):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birthday: Optional[date] = None


class UserResponse(UserBase, TimestampMixin):
    """用户响应"""
    id: str
    role: RoleEnum
    status: StatusEnum = StatusEnum.ACTIVE
    last_login: Optional[datetime] = None
    login_count: int = 0


class UserProfile(BaseSchema):
    """用户详细资料"""
    id: str
    username: str
    phone: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birthday: Optional[date] = None
    age: Optional[int] = None
    address: Optional[str] = None
    emergency_contacts: List['EmergencyContact'] = []
    health_profile: Optional['HealthProfile'] = None


class EmergencyContact(BaseSchema):
    """紧急联系人"""
    id: Optional[str] = None
    name: str = Field(..., max_length=50, description='姓名')
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$', description='手机号')
    relationship: str = Field(..., max_length=20, description='关系')
    is_primary: bool = Field(default=False, description="是否主要联系人")


class HealthProfile(BaseSchema):
    """健康档案"""
    blood_type: Optional[str] = Field(None, description='血型')
    height: Optional[float] = Field(None, ge=0, le=300, description='身高(cm)')
    weight: Optional[float] = Field(None, ge=0, le=500, description='体重(kg)')
    chronic_diseases: List[str] = Field(default=[], description='慢性病')
    allergies: List[str] = Field(default=[], description='过敏史')
    medical_history: Optional[str] = Field(None, description='病史')
    disability_level: Optional[str] = Field(None, description='残疾等级')
    mobility_status: Optional[str] = Field(None, description="行动能力")


# ========== 认证相关 ==========

class LoginRequest(BaseSchema):
    """登录请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description='手机号')
    password: str = Field(..., min_length=6, description='密码')
    device_id: Optional[str] = Field(None, description="设备ID")


class LoginResponse(BaseSchema):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseSchema):
    """刷新令牌请求"""
    refresh_token: str


class ChangePasswordRequest(BaseSchema):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v, info):
        if 'old_password' in info.data and v == info.data['old_password']:
            raise ValueError("新密码不能与旧密码相同")
        return v


class ResetPasswordRequest(BaseSchema):
    """重置密码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    verification_code: str = Field(..., min_length=4, max_length=6)
    new_password: str = Field(..., min_length=6)


class SendVerificationCodeRequest(BaseSchema):
    """发送验证码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    purpose: str = Field(default='register', description="用途: register/login/reset_password")


class VerifyCodeRequest(BaseSchema):
    """验证码验证请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6)


# ========== 老人端特定 ==========

class ElderlyProfile(UserProfile):
    """老人资料"""
    care_level: Optional[str] = Field(None, description="护理等级")
    living_status: Optional[str] = Field(None, description="居住状态: 独居/与家人同住/养老院")
    interests: List[str] = Field(default=[], description='兴趣爱好')
    dialect: Optional[str] = Field(None, description='方言偏好')
    font_size: str = Field(default='large', description='字体大小偏好')
    voice_enabled: bool = Field(default=True, description="是否启用语音")


class ElderlySettingsUpdate(BaseSchema):
    """老人设置更新"""
    font_size: Optional[str] = None
    voice_enabled: Optional[bool] = None
    dialect: Optional[str] = None
    theme: Optional[str] = None
    notification_sound: Optional[bool] = None


# ========== 管理端特定 ==========

class AdminUserCreate(UserCreate):
    """管理员创建用户"""
    role: RoleEnum = Field(..., description='角色')
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)
    permissions: List[str] = Field(default=[], description="权限列表")


class AdminUserUpdate(UserUpdate):
    """管理员更新用户"""
    role: Optional[RoleEnum] = None
    status: Optional[StatusEnum] = None
    permissions: Optional[List[str]] = None


class UserListFilter(BaseSchema):
    """用户列表过滤器"""
    role: Optional[RoleEnum] = None
    status: Optional[StatusEnum] = None
    keyword: Optional[str] = Field(None, description="搜索关键词")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
