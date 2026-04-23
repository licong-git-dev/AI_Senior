"""
基础模式定义
"""
from datetime import datetime
from typing import Optional, Any, List, Dict, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class StatusEnum(str, Enum):
    """通用状态枚举"""
    ACTIVE = "active"
    INACTIVE = 'inactive'
    PENDING = 'pending'
    DELETED = 'deleted'


class GenderEnum(str, Enum):
    """性别枚举"""
    MALE = "male"
    FEMALE = 'female'
    OTHER = 'other'


class RoleEnum(str, Enum):
    """角色枚举"""
    ELDERLY = "elderly"
    FAMILY = 'family'
    ADMIN = 'admin'
    SUPER_ADMIN = "super_admin"


# 泛型类型变量
T = TypeVar("T")


class BaseSchema(BaseModel):
    """基础模式"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )


class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description='页码')
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )


class APIResponse(BaseSchema, Generic[T]):
    """通用API响应"""
    success: bool = True
    message: str = '操作成功'
    data: Optional[T] = None
    code: int = 200

    @classmethod
    def ok(cls, data: T = None, message: str = '操作成功'):
        return cls(success=True, data=data, message=message, code=200)

    @classmethod
    def error(cls, message: str = "操作失败", code: int = 400):
        return cls(success=False, message=message, code=code)


class ErrorResponse(BaseSchema):
    """错误响应"""
    success: bool = False
    message: str
    code: int
    details: Optional[Dict[str, Any]] = None


class IDResponse(BaseSchema):
    """ID响应"""
    id: str
    success: bool = True
    message: str = "创建成功"


class DeleteResponse(BaseSchema):
    """删除响应"""
    success: bool = True
    message: str = "删除成功"
    deleted_count: int = 1


class BatchDeleteRequest(BaseSchema):
    """批量删除请求"""
    ids: List[str] = Field(..., min_length=1, description="要删除的ID列表")


class DateRangeFilter(BaseSchema):
    """日期范围过滤器"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SortOrder(str, Enum):
    """排序顺序"""
    ASC = "asc"
    DESC = 'desc'


class SortParams(BaseSchema):
    """排序参数"""
    sort_by: str = "created_at"
    order: SortOrder = SortOrder.DESC
