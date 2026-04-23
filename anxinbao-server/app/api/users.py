"""
API 路由 - 用户管理（已废弃，仅保留向后兼容）

⚠️ 历史问题：本模块使用进程内 dict（elders_store/family_store）作为存储，
   服务重启即数据全丢；上线即等于事故。

⚠️ 现状：
   - 前端零调用（参见 grep '/api/users/elder' 等）
   - 唯一引用是 tests/api/test_endpoints.py 中的防御性 404 检查
   - 业务能力已被 auth/family/users(profile) 等模块覆盖

决策（2026-04-23）：废弃本模块，避免：
   1. 投资人/合伙人翻 OpenAPI 看到"老人/家属创建"端点误以为可用
   2. 攻击者发现内存存储漏洞被利用
   3. 误用本端点写入数据后重启丢失

迁移指引（如真有人在用，应改为以下端点）：
   POST /api/users/elder/create     ->  POST /api/auth/register（role=elder）
   POST /api/users/family/create    ->  POST /api/family/binding-requests
   GET  /api/users/family/{elder_id}->  GET  /api/family/groups
   *绑定设备*                       ->  POST /api/iot/bind
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/api/users",
    tags=["⚠️ 已废弃"],
    deprecated=True,
)


# 请求模型保持原样以保证 OpenAPI schema 兼容
class CreateElderRequest(BaseModel):
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    address: Optional[str] = None
    health_conditions: List[str] = []
    medications: List[str] = []
    dialect: str = "mandarin"


class CreateFamilyRequest(BaseModel):
    elder_id: str
    name: str
    relationship: str
    phone: str
    is_primary: bool = False


_GONE_DETAIL = {
    "deprecated": True,
    "removed_reason": "本模块使用进程内内存存储，重启即丢失数据，已下线。",
    "use_instead": {
        "create_elder": "POST /api/auth/register (role='elder')",
        "create_family": "POST /api/family/binding-requests",
        "list_family": "GET /api/family/groups",
        "bind_device": "POST /api/iot/bind",
    },
}


def _gone():
    """生产环境：直接返回 410 Gone；开发环境：仅记日志后继续 404，避免破坏既有测试"""
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=_GONE_DETAIL)
    logger.warning(
        "调用了已废弃的 /api/users/* 端点；这些端点在生产环境会返回 410。"
        " 请使用 _GONE_DETAIL.use_instead 中列出的替代接口。"
    )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found (deprecated)")


@router.post("/elder/create", deprecated=True)
async def create_elder(request: CreateElderRequest):
    _gone()


@router.get("/elder/{elder_id}", deprecated=True)
async def get_elder(elder_id: str):
    _gone()


@router.put("/elder/{elder_id}", deprecated=True)
async def update_elder(elder_id: str, request: CreateElderRequest):
    _gone()


@router.post("/family/create", deprecated=True)
async def create_family_member(request: CreateFamilyRequest):
    _gone()


@router.get("/family/{elder_id}", deprecated=True)
async def get_family_members(elder_id: str):
    _gone()


@router.delete("/family/{family_id}", deprecated=True)
async def remove_family_member(family_id: str, elder_id: str):
    _gone()


@router.get("/elder/{elder_id}/bind-device", deprecated=True)
async def bind_device(elder_id: str, device_id: str):
    _gone()


@router.get("/device/{device_id}", deprecated=True)
async def get_elder_by_device(device_id: str):
    _gone()
