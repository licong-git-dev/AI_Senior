"""
智能家居API
提供设备控制、场景联动、语音控制等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.smart_home_service import (
    smart_home_service,
    SmartDeviceType,
    RoomType,
    DeviceStatus,
    TriggerType
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/smart-home", tags=["智能家居"])


# ==================== 请求模型 ====================

class AddDeviceRequest(BaseModel):
    """添加设备请求"""
    device_type: str = Field(..., description='设备类型')
    name: str = Field(..., max_length=50, description='设备名称')
    room: str = Field(..., description='房间')
    brand: str = Field(..., description='品牌')
    model: str = Field(..., description="型号")


class ControlDeviceRequest(BaseModel):
    """控制设备请求"""
    action: str = Field(..., description="动作: turn_on/turn_off/toggle/set_property")
    params: Optional[Dict[str, Any]] = Field(None, description="参数")


class ControlRoomRequest(BaseModel):
    """控制房间请求"""
    action: str = Field(..., description="动作: turn_on/turn_off")
    device_type: Optional[str] = Field(None, description='设备类型筛选')


class CreateSceneRequest(BaseModel):
    """创建场景请求"""
    name: str = Field(..., max_length=50, description='场景名称')
    description: str = Field(..., max_length=200, description='场景描述')
    icon: str = Field('star', description='图标')
    actions: List[Dict[str, Any]] = Field(..., description='动作列表')
    trigger_time: Optional[str] = Field(None, description="触发时间 HH:MM")


class VoiceCommandRequest(BaseModel):
    """语音命令请求"""
    text: str = Field(..., max_length=200, description='语音文本')


# ==================== 设备管理API ====================

@router.post("/devices")
async def add_device(
    request: AddDeviceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    添加智能家居设备
    """
    user_id = int(current_user['sub'])

    try:
        device_type = SmartDeviceType(request.device_type)
    except ValueError:
        valid_types = [t.value for t in SmartDeviceType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的设备类型，可选: {valid_types}"
        )

    try:
        room = RoomType(request.room)
    except ValueError:
        valid_rooms = [r.value for r in RoomType]
        raise HTTPException(
            status_code=400,
            detail=f"无效的房间类型，可选: {valid_rooms}"
        )

    device = smart_home_service.home.add_device(
        user_id,
        device_type,
        request.name,
        room,
        request.brand,
        request.model
    )

    return {
        'success': True,
        'device': device.to_dict(),
        "message": f"设备 {request.name} 添加成功"
    }


@router.get("/devices")
async def get_my_devices(
    room: Optional[str] = Query(None, description='房间筛选'),
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的设备列表
    """
    user_id = int(current_user['sub'])

    room_filter = None
    if room:
        try:
            room_filter = RoomType(room)
        except ValueError:
            pass

    type_filter = None
    if device_type:
        try:
            type_filter = SmartDeviceType(device_type)
        except ValueError:
            pass

    devices = smart_home_service.home.get_user_devices(user_id, room_filter, type_filter)

    return {
        'devices': [d.to_dict() for d in devices],
        'count': len(devices)
    }


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    移除设备
    """
    user_id = int(current_user['sub'])

    success = smart_home_service.home.remove_device(device_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail='设备不存在或无权限')

    return {
        'success': True,
        'message': "设备已移除"
    }


@router.post("/devices/{device_id}/control")
async def control_device(
    device_id: str,
    request: ControlDeviceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    控制设备

    支持的动作:
    - turn_on: 打开
    - turn_off: 关闭
    - toggle: 切换
    - set_property: 设置属性
    """
    user_id = int(current_user['sub'])

    result = smart_home_service.home.control_device(
        device_id,
        user_id,
        request.action,
        request.params
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/rooms/{room}/control")
async def control_room(
    room: str,
    request: ControlRoomRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    控制整个房间的设备
    """
    user_id = int(current_user['sub'])

    try:
        room_type = RoomType(room)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的房间")

    type_filter = None
    if request.device_type:
        try:
            type_filter = SmartDeviceType(request.device_type)
        except ValueError:
            pass

    result = smart_home_service.home.control_room(
        user_id,
        room_type,
        request.action,
        type_filter
    )

    return result


# ==================== 场景管理API ====================

@router.get("/scenes/presets")
async def get_preset_scenes():
    """
    获取预设场景列表
    """
    presets = smart_home_service.scene.get_preset_scenes()
    return {
        'presets': presets,
        'count': len(presets)
    }


@router.post("/scenes")
async def create_scene(
    request: CreateSceneRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建自定义场景
    """
    user_id = int(current_user['sub'])

    from app.services.smart_home_service import SceneAction, SceneTrigger, TriggerType

    # 构建动作列表
    actions = []
    for action_data in request.actions:
        actions.append(SceneAction(
            device_id=action_data['device_id'],
            action=action_data['action'],
            params=action_data.get("params", {}),
            delay_seconds=action_data.get("delay_seconds", 0)
        ))

    # 构建触发条件
    triggers = []
    if request.trigger_time:
        triggers.append(SceneTrigger(
            trigger_type=TriggerType.TIME,
            condition={'time': request.trigger_time}
        ))
    else:
        triggers.append(SceneTrigger(
            trigger_type=TriggerType.MANUAL,
            condition={}
        ))

    scene = smart_home_service.scene.create_scene(
        user_id,
        request.name,
        request.description,
        request.icon,
        triggers,
        actions
    )

    return {
        'success': True,
        'scene': scene.to_dict(),
        "message": f"场景 {request.name} 创建成功"
    }


@router.post("/scenes/preset/{preset_name}")
async def create_from_preset(
    preset_name: str,
    trigger_time: Optional[str] = Query(None, description="触发时间 HH:MM"),
    current_user: dict = Depends(get_current_user)
):
    """
    从预设创建场景
    """
    user_id = int(current_user['sub'])

    scene = smart_home_service.scene.create_from_preset(user_id, preset_name, trigger_time)
    if not scene:
        raise HTTPException(status_code=400, detail="预设不存在或没有匹配的设备")

    return {
        'success': True,
        'scene': scene.to_dict(),
        "message": f"场景 {scene.name} 创建成功"
    }


@router.get("/scenes")
async def get_my_scenes(current_user: dict = Depends(get_current_user)):
    """
    获取我的场景列表
    """
    user_id = int(current_user['sub'])

    scenes = smart_home_service.scene.get_user_scenes(user_id)

    return {
        'scenes': [s.to_dict() for s in scenes],
        'count': len(scenes)
    }


@router.post("/scenes/{scene_id}/execute")
async def execute_scene(
    scene_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    执行场景
    """
    user_id = int(current_user['sub'])

    result = smart_home_service.scene.execute_scene(scene_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/scenes/{scene_id}/toggle")
async def toggle_scene(
    scene_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    启用/禁用场景
    """
    user_id = int(current_user['sub'])

    success = smart_home_service.scene.toggle_scene(scene_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail='场景不存在')

    scene = smart_home_service.scene.scenes.get(scene_id)
    status = '启用' if scene and scene.enabled else '禁用'

    return {
        'success': True,
        'enabled': scene.enabled if scene else False,
        "message": f"场景已{status}"
    }


@router.delete("/scenes/{scene_id}")
async def delete_scene(
    scene_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除场景
    """
    user_id = int(current_user['sub'])

    success = smart_home_service.scene.delete_scene(scene_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail='场景不存在')

    return {
        'success': True,
        'message': "场景已删除"
    }


# ==================== 语音控制API ====================

@router.post("/voice/command")
async def voice_command(
    request: VoiceCommandRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    语音命令控制

    支持的命令示例:
    - '打开客厅的灯'
    - '关闭空调'
    - '执行睡眠模式'
    - "客厅灯什么状态"
    """
    user_id = int(current_user['sub'])

    # 解析命令
    command = smart_home_service.voice.parse_command(request.text)

    # 执行命令
    result = smart_home_service.voice.execute_command(user_id, command)

    return {
        "input": request.text,
        "parsed_command": command.to_dict(),
        **result
    }


@router.get("/voice/examples")
async def get_voice_examples():
    """
    获取语音命令示例
    """
    return {
        'examples': [
            {
                'category': '设备控制',
                'commands': [
                    '打开客厅的灯',
                    '关闭卧室空调',
                    '把灯光调亮一点',
                    '打开窗帘'
                ]
            },
            {
                'category': '场景执行',
                'commands': [
                    '早安模式',
                    '睡眠模式',
                    '离家模式',
                    '回家模式'
                ]
            },
            {
                'category': '状态查询',
                'commands': [
                    '客厅灯开着吗',
                    '空调什么状态',
                    "现在温度多少"
                ]
            }
        ]
    }


# ==================== 设备类型与房间API ====================

@router.get("/device-types")
async def get_device_types():
    """
    获取支持的设备类型
    """
    return {
        "device_types": [
            {'value': t.value, 'name': t.name}
            for t in SmartDeviceType
        ]
    }


@router.get("/room-types")
async def get_room_types():
    """
    获取支持的房间类型
    """
    room_names = {
        RoomType.LIVING_ROOM: '客厅',
        RoomType.BEDROOM: '卧室',
        RoomType.BATHROOM: '卫生间',
        RoomType.KITCHEN: '厨房',
        RoomType.STUDY: '书房',
        RoomType.BALCONY: '阳台'
    }

    return {
        'room_types': [
            {'value': r.value, "name": room_names.get(r, r.name)}
            for r in RoomType
        ]
    }


@router.get("/supported-brands")
async def get_supported_brands():
    """
    获取支持的品牌列表
    """
    return {
        'brands': smart_home_service.home.SUPPORTED_BRANDS
    }


# ==================== 首页仪表板API ====================

@router.get("/dashboard")
async def get_smart_home_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取智能家居仪表板

    包含设备状态概览、常用场景等
    """
    user_id = int(current_user['sub'])

    devices = smart_home_service.home.get_user_devices(user_id)
    scenes = smart_home_service.scene.get_user_scenes(user_id)

    # 统计设备状态
    online_count = sum(1 for d in devices if d.is_online)
    on_count = sum(1 for d in devices if d.status == DeviceStatus.ON)

    # 按房间分组
    rooms = {}
    for device in devices:
        room_name = device.room.value
        if room_name not in rooms:
            rooms[room_name] = []
        rooms[room_name].append(device.to_dict())

    return {
        "summary": {
            "total_devices": len(devices),
            "online_devices": online_count,
            "active_devices": on_count
        },
        'rooms': rooms,
        'scenes': [s.to_dict() for s in scenes[:5]],
        "quick_actions": [
            {'name': '全部关灯', "action": "turn_off_all_lights"},
            {'name': '离家模式', "action": "execute_away_scene"},
            {'name': '睡眠模式', "action": "execute_sleep_scene"}
        ]
    }
