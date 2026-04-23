"""
IoT设备管理API
支持智能家居设备控制和健康监测设备数据获取
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.iot_service import (
    iot_device_manager,
    scene_automation,
    health_aggregator,
    DeviceType,
    DeviceStatus,
    DevicePlatform
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/iot", tags=["IoT设备管理"])


# ==================== 请求/响应模型 ====================

class DeviceRegisterRequest(BaseModel):
    """设备注册请求"""
    device_id: str = Field(..., description='设备唯一标识')
    device_type: str = Field(..., description='设备类型')
    name: str = Field(..., description='设备名称')
    platform: str = Field(default='custom', description="IoT平台")


class DeviceCommandRequest(BaseModel):
    """设备命令请求"""
    command: str = Field(..., description='命令名称')
    params: Optional[Dict[str, Any]] = Field(default=None, description="命令参数")


class SceneRegisterRequest(BaseModel):
    """场景注册请求"""
    scene_id: str = Field(..., description='场景ID')
    name: str = Field(..., description='场景名称')
    actions: List[Dict[str, Any]] = Field(..., description="场景动作列表")


class BloodPressureReading(BaseModel):
    """血压读数"""
    systolic: int = Field(..., ge=60, le=200, description='收缩压')
    diastolic: int = Field(..., ge=40, le=130, description='舒张压')
    pulse: int = Field(..., ge=40, le=180, description="脉搏")


class DeviceResponse(BaseModel):
    """设备响应"""
    device_id: str
    device_type: str
    name: str
    platform: str
    status: str
    last_seen: Optional[str]
    properties: Dict[str, Any]


class CommandResponse(BaseModel):
    """命令执行响应"""
    success: bool
    device_id: str
    command: str
    timestamp: str
    error: Optional[str] = None


# ==================== 设备管理端点 ====================

@router.post("/devices", response_model=DeviceResponse)
async def register_device(
    request: DeviceRegisterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    注册新设备

    支持的设备类型:
    - smart_light: 智能灯
    - smart_ac: 智能空调
    - smart_curtain: 智能窗帘
    - blood_pressure: 血压计
    - fall_detector: 跌倒检测器
    - sos_button: SOS按钮
    """
    user_id = int(current_user['sub'])

    # 验证设备类型
    try:
        device_type = DeviceType(request.device_type)
    except ValueError:
        valid_types = [t.value for t in DeviceType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的设备类型，可选: {valid_types}"
        )

    # 验证平台
    try:
        platform = DevicePlatform(request.platform)
    except ValueError:
        valid_platforms = [p.value for p in DevicePlatform]
        raise HTTPException(
            status_code=400,
            detail=f"无效的平台，可选: {valid_platforms}"
        )

    device = iot_device_manager.register_device(
        device_id=request.device_id,
        device_type=device_type,
        name=request.name,
        user_id=user_id,
        platform=platform
    )

    return DeviceResponse(**device.to_dict())


@router.get("/devices", response_model=List[DeviceResponse])
async def get_user_devices(current_user: dict = Depends(get_current_user)):
    """获取用户的所有设备"""
    user_id = int(current_user['sub'])
    devices = iot_device_manager.get_user_devices(user_id)
    return [DeviceResponse(**d.to_dict()) for d in devices]


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取设备详情"""
    device = iot_device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return DeviceResponse(**device.to_dict())


@router.get("/devices/{device_id}/status")
async def get_device_status(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取设备状态"""
    device = iot_device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail='设备不存在')

    status = await device.get_status()
    return {
        'device_id': device_id,
        'name': device.name,
        "status": status
    }


@router.post("/devices/{device_id}/command", response_model=CommandResponse)
async def execute_device_command(
    device_id: str,
    request: DeviceCommandRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    执行设备命令

    智能灯命令:
    - turn_on: 开灯
    - turn_off: 关灯
    - set_brightness: 设置亮度 (params: {brightness: 0-100})
    - night_mode: 夜间模式

    智能空调命令:
    - turn_on: 开机
    - turn_off: 关机
    - set_temperature: 设置温度 (params: {temperature: 16-30})
    - comfort_mode: 舒适模式

    智能窗帘命令:
    - open: 打开
    - close: 关闭
    - set_position: 设置位置 (params: {position: 0-100})
    """
    result = await iot_device_manager.execute_device_command(
        device_id=device_id,
        command=request.command,
        params=request.params
    )

    return CommandResponse(
        success=result.get('success', False),
        device_id=device_id,
        command=request.command,
        timestamp=result.get('timestamp', datetime.now().isoformat()),
        error=result.get('error')
    )


@router.delete("/devices/{device_id}")
async def unregister_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """注销设备"""
    success = iot_device_manager.unregister_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail='设备不存在')
    return {'success': True, 'message': '设备已注销'}


# ==================== 场景控制端点 ====================

@router.post("/scenes")
async def register_scene(
    request: SceneRegisterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    注册自定义场景

    动作格式:
    ```json
    {
        'device_id': '设备ID',
        'command': '命令名称',
        'params': {'参数': "值"}
    }
    ```
    """
    user_id = int(current_user['sub'])

    scene_automation.register_scene(
        scene_id=request.scene_id,
        name=request.name,
        user_id=user_id,
        actions=request.actions
    )

    return {
        'success': True,
        'scene_id': request.scene_id,
        'name': request.name
    }


@router.post("/scenes/{scene_id}/execute")
async def execute_scene(
    scene_id: str,
    current_user: dict = Depends(get_current_user)
):
    """执行自定义场景"""
    result = await scene_automation.execute_scene(scene_id)

    if not result.get("success") and 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])

    return result


@router.post("/scenes/morning")
async def execute_morning_scene(current_user: dict = Depends(get_current_user)):
    """
    执行早晨场景

    自动执行:
    - 开灯（80%亮度）
    - 打开窗帘
    """
    user_id = int(current_user['sub'])
    result = await scene_automation.morning_scene(user_id)
    return result


@router.post("/scenes/night")
async def execute_night_scene(current_user: dict = Depends(get_current_user)):
    """
    执行夜间场景

    自动执行:
    - 开启夜灯模式（低亮度暖光）
    - 关闭其他灯
    - 关闭窗帘
    - 空调切换到舒适模式
    """
    user_id = int(current_user['sub'])
    result = await scene_automation.night_scene(user_id)
    return result


@router.post("/scenes/emergency")
async def execute_emergency_scene(current_user: dict = Depends(get_current_user)):
    """
    执行紧急场景

    自动执行:
    - 打开所有灯（最大亮度）
    """
    user_id = int(current_user['sub'])
    result = await scene_automation.emergency_scene(user_id)
    return result


# ==================== 健康监测端点 ====================

@router.get("/health/summary")
async def get_health_summary(current_user: dict = Depends(get_current_user)):
    """
    获取健康数据摘要

    汇总所有健康监测设备的最新数据
    """
    user_id = int(current_user['sub'])
    summary = await health_aggregator.get_health_summary(user_id)
    return summary


@router.post("/devices/{device_id}/blood-pressure")
async def add_blood_pressure_reading(
    device_id: str,
    reading: BloodPressureReading,
    current_user: dict = Depends(get_current_user)
):
    """
    添加血压读数

    用于手动录入血压数据
    """
    from app.services.iot_service import BloodPressureMonitor

    device = iot_device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail='设备不存在')

    if not isinstance(device, BloodPressureMonitor):
        raise HTTPException(status_code=400, detail='该设备不是血压计')

    result = device.add_reading(
        systolic=reading.systolic,
        diastolic=reading.diastolic,
        pulse=reading.pulse
    )

    return {
        'success': True,
        'reading': result,
        'is_abnormal': result["is_abnormal"]
    }


@router.post("/devices/{device_id}/fall-alert")
async def trigger_fall_alert(
    device_id: str,
    confidence: float = 0.8,
    current_user: dict = Depends(get_current_user)
):
    """
    触发跌倒警报（测试用）
    """
    from app.services.iot_service import FallDetector

    device = iot_device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail='设备不存在')

    if not isinstance(device, FallDetector):
        raise HTTPException(status_code=400, detail='该设备不是跌倒检测器')

    alert = device.trigger_alert(confidence)
    return {
        'success': True,
        "alert": alert
    }


@router.post("/devices/{device_id}/sos")
async def trigger_sos(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    触发SOS紧急求助
    """
    from app.services.iot_service import SOSButton

    device = iot_device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail='设备不存在')

    if not isinstance(device, SOSButton):
        raise HTTPException(status_code=400, detail='该设备不是SOS按钮')

    alert = device.trigger_sos()

    # 这里可以触发紧急通知
    # await notification_service.send_emergency_alert(...)

    return {
        'success': True,
        'alert': alert,
        "message": "紧急求助已发送，正在通知紧急联系人"
    }


# ==================== 设备类型查询 ====================

@router.get("/device-types")
async def get_device_types():
    """获取支持的设备类型列表"""
    types = []
    for dt in DeviceType:
        types.append({
            'value': dt.value,
            'name': _get_device_type_name(dt)
        })
    return {'types': types}


@router.get("/platforms")
async def get_platforms():
    """获取支持的IoT平台列表"""
    platforms = []
    for p in DevicePlatform:
        platforms.append({
            'value': p.value,
            'name': _get_platform_name(p)
        })
    return {'platforms': platforms}


def _get_device_type_name(dt: DeviceType) -> str:
    """获取设备类型中文名"""
    names = {
        DeviceType.SMART_LIGHT: '智能灯',
        DeviceType.SMART_AC: '智能空调',
        DeviceType.SMART_CURTAIN: '智能窗帘',
        DeviceType.SMART_TV: '智能电视',
        DeviceType.BLOOD_PRESSURE: '血压计',
        DeviceType.BLOOD_GLUCOSE: '血糖仪',
        DeviceType.HEART_RATE: '心率监测',
        DeviceType.SLEEP_MONITOR: '睡眠监测',
        DeviceType.FALL_DETECTOR: '跌倒检测器',
        DeviceType.SOS_BUTTON: '紧急求助按钮',
        DeviceType.SMART_SPEAKER: '智能音箱',
        DeviceType.SMART_WATCH: "智能手表"
    }
    return names.get(dt, dt.value)


def _get_platform_name(p: DevicePlatform) -> str:
    """获取平台中文名"""
    names = {
        DevicePlatform.TUYA: '涂鸦智能',
        DevicePlatform.XIAOMI: '米家',
        DevicePlatform.ALIBABA: '阿里智能',
        DevicePlatform.HUAWEI: '华为HiLink',
        DevicePlatform.CUSTOM: "自定义协议"
    }
    return names.get(p, p.value)
