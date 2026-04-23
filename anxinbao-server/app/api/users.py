"""
API路由 - 用户管理
管理老人和家属信息
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/users", tags=["用户管理"])


class ElderProfile(BaseModel):
    """老人档案"""
    id: str
    name: str
    age: int
    gender: str  # male/female
    phone: Optional[str] = None
    address: Optional[str] = None
    health_conditions: List[str] = []  # 既往病史
    medications: List[str] = []  # 正在服用的药物
    dialect: str = "mandarin"  # 方言偏好
    device_id: Optional[str] = None
    created_at: str


class FamilyMember(BaseModel):
    """家属信息"""
    id: str
    elder_id: str  # 关联的老人ID
    name: str
    relationship: str  # 与老人的关系
    phone: str
    wechat_openid: Optional[str] = None
    is_primary: bool = False  # 是否主要联系人
    notify_enabled: bool = True  # 是否接收通知
    created_at: str


class CreateElderRequest(BaseModel):
    """创建老人档案请求"""
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    address: Optional[str] = None
    health_conditions: List[str] = []
    medications: List[str] = []
    dialect: str = "mandarin"


class CreateFamilyRequest(BaseModel):
    """创建家属请求"""
    elder_id: str
    name: str
    relationship: str
    phone: str
    is_primary: bool = False


# 数据存储（生产环境用数据库）
elders_store: Dict[str, ElderProfile] = {}
family_store: Dict[str, List[FamilyMember]] = {}


@router.post("/elder/create")
async def create_elder(request: CreateElderRequest):
    """创建老人档案"""
    elder_id = str(uuid.uuid4())

    elder = ElderProfile(
        id=elder_id,
        name=request.name,
        age=request.age,
        gender=request.gender,
        phone=request.phone,
        address=request.address,
        health_conditions=request.health_conditions,
        medications=request.medications,
        dialect=request.dialect,
        created_at=datetime.now().isoformat()
    )

    elders_store[elder_id] = elder

    return {
        'success': True,
        'elder_id': elder_id,
        'message': "老人档案创建成功"
    }


@router.get("/elder/{elder_id}")
async def get_elder(elder_id: str):
    """获取老人档案"""
    elder = elders_store.get(elder_id)
    if not elder:
        raise HTTPException(status_code=404, detail="老人档案不存在")
    return elder.model_dump()


@router.put("/elder/{elder_id}")
async def update_elder(elder_id: str, request: CreateElderRequest):
    """更新老人档案"""
    elder = elders_store.get(elder_id)
    if not elder:
        raise HTTPException(status_code=404, detail='老人档案不存在')

    elder.name = request.name
    elder.age = request.age
    elder.gender = request.gender
    elder.phone = request.phone
    elder.address = request.address
    elder.health_conditions = request.health_conditions
    elder.medications = request.medications
    elder.dialect = request.dialect

    return {'success': True, 'message': "档案更新成功"}


@router.post("/family/create")
async def create_family_member(request: CreateFamilyRequest):
    """添加家属"""
    if request.elder_id not in elders_store:
        raise HTTPException(status_code=404, detail='老人档案不存在')

    family_id = str(uuid.uuid4())

    family = FamilyMember(
        id=family_id,
        elder_id=request.elder_id,
        name=request.name,
        relationship=request.relationship,
        phone=request.phone,
        is_primary=request.is_primary,
        created_at=datetime.now().isoformat()
    )

    if request.elder_id not in family_store:
        family_store[request.elder_id] = []

    family_store[request.elder_id].append(family)

    return {
        'success': True,
        'family_id': family_id,
        'message': "家属添加成功"
    }


@router.get("/family/{elder_id}")
async def get_family_members(elder_id: str):
    """获取老人的家属列表"""
    return {
        'elder_id': elder_id,
        "family_members": [f.model_dump() for f in family_store.get(elder_id, [])]
    }


@router.delete("/family/{family_id}")
async def remove_family_member(family_id: str, elder_id: str):
    """移除家属"""
    if elder_id not in family_store:
        raise HTTPException(status_code=404, detail='记录不存在')

    family_store[elder_id] = [
        f for f in family_store[elder_id]
        if f.id != family_id
    ]

    return {'success': True, 'message': "家属已移除"}


@router.get("/elder/{elder_id}/bind-device")
async def bind_device(elder_id: str, device_id: str):
    """绑定设备"""
    elder = elders_store.get(elder_id)
    if not elder:
        raise HTTPException(status_code=404, detail='老人档案不存在')

    elder.device_id = device_id

    return {'success': True, 'message': "设备绑定成功"}


@router.get("/device/{device_id}")
async def get_elder_by_device(device_id: str):
    """通过设备ID获取老人信息"""
    for elder in elders_store.values():
        if elder.device_id == device_id:
            return elder.model_dump()

    raise HTTPException(status_code=404, detail="设备未绑定")
