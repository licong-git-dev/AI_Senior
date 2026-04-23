"""
第三方集成API
提供医疗机构对接、智能硬件、社区服务、保险理赔等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.integration_service import (
    integration_service,
    MedicalRecordType,
    DeviceType,
    DeviceStatus,
    CommunityServiceType,
    InsuranceType,
    ClaimStatus
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/integration", tags=["第三方集成"])


# ==================== 请求模型 ====================

class SyncRecordsRequest(BaseModel):
    """同步医疗记录请求"""
    institution_id: str = Field(..., description='医疗机构ID')
    auth_token: str = Field(..., description="授权令牌")


class BookAppointmentRequest(BaseModel):
    """预约挂号请求"""
    institution_id: str = Field(..., description='医疗机构ID')
    department: str = Field(..., description='科室')
    preferred_date: datetime = Field(..., description='期望就诊时间')
    doctor: Optional[str] = Field(None, description="指定医生")


class PairDeviceRequest(BaseModel):
    """配对设备请求"""
    device_type: str = Field(..., description='设备类型')
    brand: str = Field(..., description='品牌')
    model: str = Field(..., description='型号')
    mac_address: Optional[str] = Field(None, description="MAC地址")


class CreateServiceOrderRequest(BaseModel):
    """创建服务订单请求"""
    service_id: str = Field(..., description='服务ID')
    scheduled_time: datetime = Field(..., description='预约时间')
    address: str = Field(..., description='服务地址')
    contact_phone: str = Field(..., description='联系电话')
    notes: Optional[str] = Field(None, description="备注")


class AddPolicyRequest(BaseModel):
    """添加保单请求"""
    insurance_type: str = Field(..., description='保险类型')
    insurer: str = Field(..., description='保险公司')
    policy_number: str = Field(..., description='保单号')
    coverage_amount: float = Field(..., description='保额')
    premium: float = Field(..., description='保费')
    start_date: datetime = Field(..., description='起保日期')
    end_date: datetime = Field(..., description="终保日期")


class CreateClaimRequest(BaseModel):
    """创建理赔请求"""
    policy_id: str = Field(..., description='保单ID')
    claim_type: str = Field(..., description='理赔类型')
    claim_amount: float = Field(..., description='理赔金额')
    description: str = Field(..., description='理赔说明')
    documents: Optional[List[str]] = Field(None, description='证明文件')
    medical_records: Optional[List[str]] = Field(None, description="医疗记录")


# ==================== 医疗机构API ====================

@router.get("/medical/institutions")
async def get_nearby_institutions(
    latitude: float = Query(39.9, description='纬度'),
    longitude: float = Query(116.4, description='经度'),
    radius_km: float = Query(5, description="搜索半径(公里)")
):
    """
    获取附近医疗机构
    """
    institutions = integration_service.medical.get_nearby_institutions(
        latitude, longitude, radius_km
    )

    return {
        "institutions": [i.to_dict() for i in institutions],
        'count': len(institutions),
        "search_params": {
            'latitude': latitude,
            'longitude': longitude,
            'radius_km': radius_km
        }
    }


@router.get("/medical/institutions/{institution_id}")
async def get_institution_detail(institution_id: str):
    """
    获取医疗机构详情
    """
    institution = integration_service.medical.get_institution(institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="医疗机构不存在")

    return {"institution": institution.to_dict()}


@router.post("/medical/records/sync")
async def sync_medical_records(
    request: SyncRecordsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    同步医疗记录

    从医疗机构同步用户的医疗记录
    """
    user_id = int(current_user['sub'])

    records = integration_service.medical.sync_medical_records(
        user_id, request.institution_id, request.auth_token
    )

    return {
        'synced': True,
        'records': [r.to_dict() for r in records],
        'count': len(records),
        "institution_id": request.institution_id
    }


@router.get("/medical/records")
async def get_medical_records(
    record_type: Optional[str] = Query(None, description="记录类型"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的医疗记录
    """
    user_id = int(current_user['sub'])

    type_filter = None
    if record_type:
        try:
            type_filter = MedicalRecordType(record_type)
        except ValueError:
            pass

    records = integration_service.medical.get_user_records(user_id, type_filter)

    return {
        'records': [r.to_dict() for r in records],
        'count': len(records)
    }


@router.post("/medical/appointments")
async def book_appointment(
    request: BookAppointmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    预约挂号
    """
    user_id = int(current_user['sub'])

    institution = integration_service.medical.get_institution(request.institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail='医疗机构不存在')

    if request.department not in institution.departments:
        raise HTTPException(status_code=400, detail='该机构不支持此科室')

    appointment = integration_service.medical.book_appointment(
        user_id,
        request.institution_id,
        request.department,
        request.preferred_date,
        request.doctor
    )

    return {
        "success": True,
        "appointment": appointment,
        'message': "预约成功"
    }


# ==================== 智能硬件API ====================

@router.get("/hardware/supported")
async def get_supported_devices():
    """
    获取支持的设备列表
    """
    devices = integration_service.hardware.get_supported_devices()
    return {
        "supported_devices": devices,
        "device_types": [dt.value for dt in DeviceType]
    }


@router.post("/hardware/devices/pair")
async def pair_device(
    request: PairDeviceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    配对智能设备
    """
    user_id = int(current_user['sub'])

    try:
        device_type = DeviceType(request.device_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="不支持的设备类型")

    # 检查品牌是否支持
    supported_brands = integration_service.hardware.SUPPORTED_BRANDS.get(device_type, [])
    if request.brand not in supported_brands:
        raise HTTPException(
            status_code=400,
            detail=f"该设备类型不支持此品牌，支持的品牌: {supported_brands}"
        )

    device = integration_service.hardware.pair_device(
        user_id, device_type, request.brand, request.model, request.mac_address
    )

    return {
        'success': True,
        'device': device.to_dict(),
        'message': "设备配对成功"
    }


@router.delete("/hardware/devices/{device_id}")
async def unpair_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    解除设备配对
    """
    user_id = int(current_user['sub'])

    success = integration_service.hardware.unpair_device(device_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail='设备不存在或无权操作')

    return {
        'success': True,
        'device_id': device_id,
        'message': "设备已解除配对"
    }


@router.get("/hardware/devices")
async def get_my_devices(current_user: dict = Depends(get_current_user)):
    """
    获取我的设备列表
    """
    user_id = int(current_user['sub'])

    devices = integration_service.hardware.get_user_devices(user_id)

    return {
        'devices': [d.to_dict() for d in devices],
        'count': len(devices)
    }


@router.post("/hardware/devices/{device_id}/sync")
async def sync_device_data(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    同步设备数据
    """
    user_id = int(current_user['sub'])

    readings = integration_service.hardware.sync_device_data(device_id, user_id)
    if not readings:
        raise HTTPException(status_code=404, detail='设备不存在或无数据')

    return {
        'synced': True,
        'readings': [r.to_dict() for r in readings],
        "count": len(readings)
    }


@router.get("/hardware/devices/{device_id}/readings")
async def get_device_readings(
    device_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取设备历史读数
    """
    readings = integration_service.hardware.get_device_readings(device_id, limit)

    return {
        'device_id': device_id,
        'readings': [r.to_dict() for r in readings],
        'count': len(readings)
    }


# ==================== 社区服务API ====================

@router.get("/community/services")
async def get_community_services(
    service_type: Optional[str] = Query(None, description="服务类型")
):
    """
    获取可用社区服务
    """
    type_filter = None
    if service_type:
        try:
            type_filter = CommunityServiceType(service_type)
        except ValueError:
            pass

    services = integration_service.community.get_available_services(type_filter)

    return {
        'services': [s.to_dict() for s in services],
        'count': len(services),
        "service_types": [st.value for st in CommunityServiceType]
    }


@router.post("/community/orders")
async def create_service_order(
    request: CreateServiceOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建服务订单
    """
    user_id = int(current_user['sub'])

    order = integration_service.community.create_order(
        user_id,
        request.service_id,
        request.scheduled_time,
        request.address,
        request.contact_phone,
        request.notes
    )

    if not order:
        raise HTTPException(status_code=400, detail='服务不可用或创建失败')

    return {
        'success': True,
        'order': order.to_dict(),
        'message': "订单创建成功"
    }


@router.get("/community/orders")
async def get_my_service_orders(current_user: dict = Depends(get_current_user)):
    """
    获取我的服务订单
    """
    user_id = int(current_user['sub'])

    orders = integration_service.community.get_user_orders(user_id)

    return {
        'orders': [o.to_dict() for o in orders],
        'count': len(orders)
    }


@router.post("/community/orders/{order_id}/cancel")
async def cancel_service_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    取消服务订单
    """
    user_id = int(current_user['sub'])

    success = integration_service.community.cancel_order(order_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail='订单不存在或无法取消')

    return {
        'success': True,
        'order_id': order_id,
        'message': "订单已取消"
    }


# ==================== 保险理赔API ====================

@router.post("/insurance/policies")
async def add_insurance_policy(
    request: AddPolicyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加保险保单
    """
    user_id = int(current_user['sub'])

    try:
        insurance_type = InsuranceType(request.insurance_type)
    except ValueError:
        valid_types = [t.value for t in InsuranceType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的保险类型，可选: {valid_types}"
        )

    policy = integration_service.insurance.add_policy(
        user_id,
        insurance_type,
        request.insurer,
        request.policy_number,
        request.coverage_amount,
        request.premium,
        request.start_date,
        request.end_date
    )

    return {
        'success': True,
        'policy': policy.to_dict(),
        'message': "保单添加成功"
    }


@router.get("/insurance/policies")
async def get_my_policies(current_user: dict = Depends(get_current_user)):
    """
    获取我的保单列表
    """
    user_id = int(current_user['sub'])

    policies = integration_service.insurance.get_user_policies(user_id)

    return {
        'policies': [p.to_dict() for p in policies],
        'count': len(policies)
    }


@router.post("/insurance/claims")
async def create_insurance_claim(
    request: CreateClaimRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建理赔申请
    """
    user_id = int(current_user['sub'])

    claim = integration_service.insurance.create_claim(
        user_id,
        request.policy_id,
        request.claim_type,
        request.claim_amount,
        request.description,
        request.documents,
        request.medical_records
    )

    if not claim:
        raise HTTPException(status_code=400, detail="保单不存在或无法创建理赔")

    return {
        'success': True,
        'claim': claim.to_dict(),
        'message': "理赔申请已创建"
    }


@router.post("/insurance/claims/{claim_id}/submit")
async def submit_insurance_claim(
    claim_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    提交理赔申请
    """
    user_id = int(current_user['sub'])

    success = integration_service.insurance.submit_claim(claim_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail='理赔不存在或无法提交')

    return {
        'success': True,
        'claim_id': claim_id,
        'message': "理赔已提交审核"
    }


@router.get("/insurance/claims")
async def get_my_claims(current_user: dict = Depends(get_current_user)):
    """
    获取我的理赔记录
    """
    user_id = int(current_user['sub'])

    claims = integration_service.insurance.get_user_claims(user_id)

    return {
        'claims': [c.to_dict() for c in claims],
        'count': len(claims)
    }


@router.get("/insurance/claims/{claim_id}")
async def get_claim_status(
    claim_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    查询理赔状态
    """
    status = integration_service.insurance.get_claim_status(claim_id)
    if not status:
        raise HTTPException(status_code=404, detail="理赔记录不存在")

    return status
