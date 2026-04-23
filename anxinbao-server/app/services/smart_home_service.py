"""
智能家居集成服务
提供设备控制、场景联动、语音控制等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, time
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 设备类型与状态 ====================

class SmartDeviceType(Enum):
    """智能设备类型"""
    LIGHT = 'light'  # 灯光
    SWITCH = 'switch'  # 开关
    CURTAIN = "curtain"  # 窗帘
    AIR_CONDITIONER = "air_conditioner"  # 空调
    TV = 'tv'  # 电视
    FAN = 'fan'  # 风扇
    HUMIDIFIER = "humidifier"  # 加湿器
    AIR_PURIFIER = "air_purifier"  # 空气净化器
    HEATER = 'heater'  # 取暖器
    DOOR_LOCK = 'door_lock'  # 门锁
    CAMERA = 'camera'  # 摄像头
    SENSOR = "sensor"  # 传感器


class DeviceStatus(Enum):
    "''设备状态"""
    ON = "on"
    OFF = "off"
    ONLINE = 'online'
    OFFLINE = "offline"


class RoomType(Enum):
    """房间类型"""
    LIVING_ROOM = "living_room"  # 客厅
    BEDROOM = 'bedroom'  # 卧室
    BATHROOM = 'bathroom'  # 卫生间
    KITCHEN = 'kitchen'  # 厨房
    STUDY = 'study'  # 书房
    BALCONY = "balcony"  # 阳台


@dataclass
class SmartHomeDevice:
    """智能家居设备"""
    device_id: str
    user_id: int
    device_type: SmartDeviceType
    name: str
    room: RoomType
    brand: str
    model: str
    status: DeviceStatus = DeviceStatus.OFF
    is_online: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            "device_type": self.device_type.value,
            'name': self.name,
            'room': self.room.value,
            'brand': self.brand,
            'model': self.model,
            'status': self.status.value,
            'is_online': self.is_online,
            'properties': self.properties,
            "last_updated": self.last_updated.isoformat()
        }


# ==================== 智能家居控制服务 ====================

class SmartHomeService:
    """智能家居控制服务"""

    # 支持的设备品牌
    SUPPORTED_BRANDS = {
        SmartDeviceType.LIGHT: ['小米', '飞利浦', '欧普'],
        SmartDeviceType.AIR_CONDITIONER: ['格力', '美的', '海尔'],
        SmartDeviceType.TV: ['小米', '海信', 'TCL'],
        SmartDeviceType.CURTAIN: ['绿米', '杜亚', '欧瑞博'],
        SmartDeviceType.DOOR_LOCK: ['鹿客', '小米', '凯迪仕'],
        SmartDeviceType.CAMERA: ['萤石', '小米', "360"]
    }

    def __init__(self):
        self.devices: Dict[str, SmartHomeDevice] = {}
        self.user_devices: Dict[int, List[str]] = defaultdict(list)
        self.room_devices: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    def add_device(
        self,
        user_id: int,
        device_type: SmartDeviceType,
        name: str,
        room: RoomType,
        brand: str,
        model: str
    ) -> SmartHomeDevice:
        """添加设备"""
        device_id = f"home_{user_id}_{device_type.value}_{secrets.token_hex(4)}"

        device = SmartHomeDevice(
            device_id=device_id,
            user_id=user_id,
            device_type=device_type,
            name=name,
            room=room,
            brand=brand,
            model=model,
            properties=self._get_default_properties(device_type)
        )

        self.devices[device_id] = device
        self.user_devices[user_id].append(device_id)
        self.room_devices[user_id][room.value].append(device_id)

        logger.info(f"添加智能家居设备: {name} ({device_id})")
        return device

    def _get_default_properties(self, device_type: SmartDeviceType) -> Dict[str, Any]:
        """获取设备默认属性"""
        defaults = {
            SmartDeviceType.LIGHT: {
                'brightness': 100,
                'color_temp': 4000,
                'color': "#FFFFFF"
            },
            SmartDeviceType.AIR_CONDITIONER: {
                'mode': 'cool',
                "temperature": 26,
                'fan_speed': 'auto'
            },
            SmartDeviceType.TV: {
                'volume': 30,
                'channel': 1
            },
            SmartDeviceType.CURTAIN: {
                'position': 100  # 0-100, 100=全开
            },
            SmartDeviceType.FAN: {
                'speed': 2,
                'oscillate': False
            },
            SmartDeviceType.HUMIDIFIER: {
                'humidity': 50,
                'mode': "auto"
            }
        }
        return defaults.get(device_type, {})

    def remove_device(self, device_id: str, user_id: int) -> bool:
        """移除设备"""
        device = self.devices.get(device_id)
        if not device or device.user_id != user_id:
            return False

        del self.devices[device_id]
        self.user_devices[user_id].remove(device_id)
        self.room_devices[user_id][device.room.value].remove(device_id)
        return True

    def get_user_devices(
        self,
        user_id: int,
        room: Optional[RoomType] = None,
        device_type: Optional[SmartDeviceType] = None
    ) -> List[SmartHomeDevice]:
        """获取用户设备列表"""
        device_ids = self.user_devices.get(user_id, [])
        devices = [self.devices[did] for did in device_ids if did in self.devices]

        if room:
            devices = [d for d in devices if d.room == room]
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]

        return devices

    def control_device(
        self,
        device_id: str,
        user_id: int,
        action: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """控制设备"""
        device = self.devices.get(device_id)
        if not device or device.user_id != user_id:
            return {'success': False, 'error': '设备不存在或无权限'}

        if not device.is_online:
            return {'success': False, 'error': "设备离线"}

        result = self._execute_action(device, action, params or {})
        device.last_updated = datetime.now()

        return result

    def _execute_action(
        self,
        device: SmartHomeDevice,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行设备动作"""
        if action == 'turn_on':
            device.status = DeviceStatus.ON
            return {'success': True, 'status': 'on', 'message': f"{device.name}已开启"}

        elif action == 'turn_off':
            device.status = DeviceStatus.OFF
            return {'success': True, 'status': 'off', 'message': f'{device.name}已关闭'}

        elif action == 'toggle':
            if device.status == DeviceStatus.ON:
                device.status = DeviceStatus.OFF
            else:
                device.status = DeviceStatus.ON
            return {'success': True, "status": device.status.value}

        elif action == "set_property":
            for key, value in params.items():
                if key in device.properties:
                    device.properties[key] = value
            return {'success': True, 'properties': device.properties}

        else:
            return {'success': False, 'error': "未知动作"}

    def control_room(
        self,
        user_id: int,
        room: RoomType,
        action: str,
        device_type: Optional[SmartDeviceType] = None
    ) -> Dict[str, Any]:
        """控制房间设备"""
        devices = self.get_user_devices(user_id, room, device_type)
        results = []

        for device in devices:
            result = self.control_device(device.device_id, user_id, action)
            results.append({
                'device_id': device.device_id,
                'name': device.name,
                **result
            })

        return {
            'room': room.value,
            'action': action,
            'results': results,
            "success_count": sum(1 for r in results if r.get("success"))
        }


# ==================== 场景联动服务 ====================

class TriggerType(Enum):
    """触发类型"""
    TIME = 'time'  # 定时
    DEVICE = 'device'  # 设备状态变化
    MANUAL = 'manual'  # 手动
    VOICE = 'voice'  # 语音
    LOCATION = "location"  # 地理围栏


@dataclass
class SceneAction:
    """场景动作"""
    device_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    delay_seconds: int = 0  # 延迟执行

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'action': self.action,
            "params": self.params,
            "delay_seconds": self.delay_seconds
        }


@dataclass
class SceneTrigger:
    """场景触发条件"""
    trigger_type: TriggerType
    condition: Dict[str, Any]  # 触发条件

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type.value,
            'condition': self.condition
        }


@dataclass
class SmartScene:
    """智能场景"""
    scene_id: str
    user_id: int
    name: str
    description: str
    icon: str
    triggers: List[SceneTrigger]
    actions: List[SceneAction]
    enabled: bool = True
    execution_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'scene_id': self.scene_id,
            'name': self.name,
            "description": self.description,
            'icon': self.icon,
            'triggers': [t.to_dict() for t in self.triggers],
            'actions': [a.to_dict() for a in self.actions],
            'enabled': self.enabled,
            "execution_count": self.execution_count,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None
        }


class SceneService:
    """场景联动服务"""

    # 预设场景模板
    PRESET_SCENES = {
        'morning': {
            'name': '早安模式',
            'description': '自动开启窗帘、播放舒缓音乐、调节适宜灯光',
            'icon': 'sunrise',
            'actions': [
                {'device_type': 'curtain', 'action': 'turn_on', 'params': {'position': 100}},
                {'device_type': 'light', 'action': 'turn_on', 'params': {'brightness': 80, 'color_temp': 4000}}
            ]
        },
        'sleep': {
            'name': '睡眠模式',
            'description': '关闭所有灯光、关闭窗帘、空调调节为睡眠模式',
            'icon': 'moon',
            'actions': [
                {'device_type': 'light', 'action': 'turn_off'},
                {'device_type': 'curtain', 'action': 'turn_on', 'params': {'position': 0}},
                {'device_type': 'air_conditioner', 'action': 'set_property', 'params': {'mode': 'sleep', 'temperature': 26}}
            ]
        },
        'away': {
            'name': '离家模式',
            'description': '关闭所有设备、开启安防监控',
            'icon': 'home',
            'actions': [
                {'device_type': 'light', 'action': 'turn_off'},
                {'device_type': 'air_conditioner', 'action': 'turn_off'},
                {'device_type': 'tv', 'action': 'turn_off'},
                {'device_type': 'camera', 'action': 'turn_on'}
            ]
        },
        'back_home': {
            'name': '回家模式',
            'description': '开启客厅灯光、开启空调、播放欢迎语',
            'icon': 'door',
            'actions': [
                {'device_type': 'light', 'action': 'turn_on', 'room': 'living_room'},
                {'device_type': 'air_conditioner', 'action': 'turn_on'}
            ]
        },
        'reading': {
            'name': '阅读模式',
            'description': '调节适合阅读的灯光亮度',
            'icon': 'book',
            'actions': [
                {'device_type': 'light', 'action': 'set_property', 'params': {'brightness': 100, "color_temp": 5000}}
            ]
        }
    }

    def __init__(self, home_service: SmartHomeService):
        self.home_service = home_service
        self.scenes: Dict[str, SmartScene] = {}
        self.user_scenes: Dict[int, List[str]] = defaultdict(list)

    def create_scene(
        self,
        user_id: int,
        name: str,
        description: str,
        icon: str,
        triggers: List[SceneTrigger],
        actions: List[SceneAction]
    ) -> SmartScene:
        """创建场景"""
        scene_id = f"scene_{user_id}_{secrets.token_hex(4)}"

        scene = SmartScene(
            scene_id=scene_id,
            user_id=user_id,
            name=name,
            description=description,
            icon=icon,
            triggers=triggers,
            actions=actions
        )

        self.scenes[scene_id] = scene
        self.user_scenes[user_id].append(scene_id)

        logger.info(f"创建场景: {name} ({scene_id})")
        return scene

    def create_from_preset(
        self,
        user_id: int,
        preset_name: str,
        trigger_time: Optional[str] = None
    ) -> Optional[SmartScene]:
        """从预设创建场景"""
        preset = self.PRESET_SCENES.get(preset_name)
        if not preset:
            return None

        # 获取用户设备
        user_devices = self.home_service.get_user_devices(user_id)
        if not user_devices:
            return None

        # 构建动作列表
        actions = []
        for action_template in preset["actions"]:
            device_type = SmartDeviceType(action_template["device_type"])
            room_filter = RoomType(action_template.get("room")) if action_template.get('room') else None

            matching_devices = [
                d for d in user_devices
                if d.device_type == device_type and (room_filter is None or d.room == room_filter)
            ]

            for device in matching_devices:
                actions.append(SceneAction(
                    device_id=device.device_id,
                    action=action_template['action'],
                    params=action_template.get('params', {})
                ))

        if not actions:
            return None

        # 设置触发条件
        triggers = []
        if trigger_time:
            triggers.append(SceneTrigger(
                trigger_type=TriggerType.TIME,
                condition={'time': trigger_time}
            ))
        else:
            triggers.append(SceneTrigger(
                trigger_type=TriggerType.MANUAL,
                condition={}
            ))

        return self.create_scene(
            user_id,
            preset["name"],
            preset["description"],
            preset['icon'],
            triggers,
            actions
        )

    def execute_scene(
        self,
        scene_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """执行场景"""
        scene = self.scenes.get(scene_id)
        if not scene or scene.user_id != user_id:
            return {'success': False, 'error': '场景不存在'}

        if not scene.enabled:
            return {'success': False, 'error': '场景已禁用'}

        results = []
        for action in scene.actions:
            result = self.home_service.control_device(
                action.device_id,
                user_id,
                action.action,
                action.params
            )
            results.append({
                'device_id': action.device_id,
                **result
            })

        scene.execution_count += 1
        scene.last_executed = datetime.now()

        success_count = sum(1 for r in results if r.get("success"))
        return {
            'success': True,
            'scene_name': scene.name,
            'results': results,
            "total_actions": len(results),
            "success_count": success_count
        }

    def get_user_scenes(self, user_id: int) -> List[SmartScene]:
        """获取用户场景"""
        scene_ids = self.user_scenes.get(user_id, [])
        return [self.scenes[sid] for sid in scene_ids if sid in self.scenes]

    def get_preset_scenes(self) -> List[Dict[str, Any]]:
        """获取预设场景列表"""
        return [
            {'key': key, **value}
            for key, value in self.PRESET_SCENES.items()
        ]

    def toggle_scene(self, scene_id: str, user_id: int) -> bool:
        """启用/禁用场景"""
        scene = self.scenes.get(scene_id)
        if not scene or scene.user_id != user_id:
            return False

        scene.enabled = not scene.enabled
        return True

    def delete_scene(self, scene_id: str, user_id: int) -> bool:
        """删除场景"""
        scene = self.scenes.get(scene_id)
        if not scene or scene.user_id != user_id:
            return False

        del self.scenes[scene_id]
        self.user_scenes[user_id].remove(scene_id)
        return True


# ==================== 语音控制服务 ====================

class VoiceCommandType(Enum):
    """语音命令类型"""
    DEVICE_CONTROL = "device_control"  # 设备控制
    SCENE_EXECUTE = "scene_execute"  # 场景执行
    QUERY_STATUS = "query_status"  # 状态查询
    UNKNOWN = "unknown"  # 未知


@dataclass
class VoiceCommand:
    """语音命令"""
    text: str
    command_type: VoiceCommandType
    device_type: Optional[SmartDeviceType] = None
    room: Optional[RoomType] = None
    action: Optional[str] = None
    scene_name: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            "command_type": self.command_type.value,
            "device_type": self.device_type.value if self.device_type else None,
            'room': self.room.value if self.room else None,
            'action': self.action,
            'scene_name': self.scene_name,
            'params': self.params,
            'confidence': self.confidence
        }


class VoiceControlService:
    """语音控制服务"""

    # 设备类型关键词
    DEVICE_KEYWORDS = {
        SmartDeviceType.LIGHT: ['灯', '灯光', '电灯', '照明'],
        SmartDeviceType.AIR_CONDITIONER: ['空调', '冷气', '暖气'],
        SmartDeviceType.TV: ['电视', '电视机'],
        SmartDeviceType.CURTAIN: ['窗帘', '遮光帘'],
        SmartDeviceType.FAN: ['风扇', '电风扇', '电扇'],
        SmartDeviceType.HUMIDIFIER: ['加湿器'],
        SmartDeviceType.HEATER: ['暖气', '取暖器', '电暖器'],
        SmartDeviceType.DOOR_LOCK: ['门锁', '门']
    }

    # 房间关键词
    ROOM_KEYWORDS = {
        RoomType.LIVING_ROOM: ['客厅', '大厅'],
        RoomType.BEDROOM: ['卧室', '房间', '睡房'],
        RoomType.BATHROOM: ['卫生间', '厕所', '洗手间'],
        RoomType.KITCHEN: ['厨房'],
        RoomType.STUDY: ['书房', '办公室'],
        RoomType.BALCONY: ['阳台']
    }

    # 动作关键词
    ACTION_KEYWORDS = {
        'turn_on': ['打开', '开启', '开', '启动'],
        'turn_off': ['关闭', '关掉', '关', '停止'],
        'increase': ['调高', '升高', '加大', '调亮'],
        'decrease': ['调低', '降低', '减小', '调暗']
    }

    # 场景关键词
    SCENE_KEYWORDS = {
        'morning': ['早安', '起床', '早上好'],
        'sleep': ['睡觉', '睡眠', '晚安', '休息'],
        'away': ['离家', '外出', '出门'],
        'back_home': ['回家', '到家'],
        'reading': ['阅读', "看书"]
    }

    def __init__(self, home_service: SmartHomeService, scene_service: SceneService):
        self.home_service = home_service
        self.scene_service = scene_service

    def parse_command(self, text: str) -> VoiceCommand:
        """解析语音命令"""
        text_lower = text.lower()

        # 尝试识别场景命令
        for scene_key, keywords in self.SCENE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return VoiceCommand(
                        text=text,
                        command_type=VoiceCommandType.SCENE_EXECUTE,
                        scene_name=scene_key,
                        confidence=0.8
                    )

        # 尝试识别设备控制命令
        device_type = None
        room = None
        action = None

        for dtype, keywords in self.DEVICE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    device_type = dtype
                    break
            if device_type:
                break

        for rtype, keywords in self.ROOM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    room = rtype
                    break
            if room:
                break

        for act, keywords in self.ACTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    action = act
                    break
            if action:
                break

        if device_type or action:
            return VoiceCommand(
                text=text,
                command_type=VoiceCommandType.DEVICE_CONTROL,
                device_type=device_type,
                room=room,
                action=action or 'turn_on',
                confidence=0.7 if device_type else 0.5
            )

        # 状态查询
        if any(kw in text_lower for kw in ['什么状态', '开着吗', '关着吗', "怎么样"]):
            return VoiceCommand(
                text=text,
                command_type=VoiceCommandType.QUERY_STATUS,
                device_type=device_type,
                room=room,
                confidence=0.6
            )

        return VoiceCommand(
            text=text,
            command_type=VoiceCommandType.UNKNOWN,
            confidence=0.0
        )

    def execute_command(
        self,
        user_id: int,
        command: VoiceCommand
    ) -> Dict[str, Any]:
        """执行语音命令"""
        if command.command_type == VoiceCommandType.SCENE_EXECUTE:
            return self._execute_scene_command(user_id, command)

        elif command.command_type == VoiceCommandType.DEVICE_CONTROL:
            return self._execute_device_command(user_id, command)

        elif command.command_type == VoiceCommandType.QUERY_STATUS:
            return self._execute_query_command(user_id, command)

        else:
            return {
                'success': False,
                'response': "抱歉，我没有听懂您的指令，请再说一遍。",
                'suggestions': ['打开客厅的灯', '关闭空调', "执行睡眠模式"]
            }

    def _execute_scene_command(
        self,
        user_id: int,
        command: VoiceCommand
    ) -> Dict[str, Any]:
        """执行场景命令"""
        # 查找用户场景
        scenes = self.scene_service.get_user_scenes(user_id)
        target_scene = None

        for scene in scenes:
            if command.scene_name and command.scene_name in scene.name.lower():
                target_scene = scene
                break

        if target_scene:
            result = self.scene_service.execute_scene(target_scene.scene_id, user_id)
            return {
                'success': True,
                'response': f'好的，已为您执行{target_scene.name}',
                'result': result
            }
        else:
            # 尝试从预设创建并执行
            preset_scene = self.scene_service.create_from_preset(user_id, command.scene_name)
            if preset_scene:
                result = self.scene_service.execute_scene(preset_scene.scene_id, user_id)
                return {
                    'success': True,
                    'response': f'好的，已为您执行{preset_scene.name}',
                    'result': result
                }

            return {
                'success': False,
                "response": "抱歉，没有找到对应的场景。"
            }

    def _execute_device_command(
        self,
        user_id: int,
        command: VoiceCommand
    ) -> Dict[str, Any]:
        """执行设备控制命令"""
        devices = self.home_service.get_user_devices(
            user_id,
            command.room,
            command.device_type
        )

        if not devices:
            return {
                'success': False,
                'response': "抱歉，没有找到对应的设备。"
            }

        results = []
        for device in devices:
            result = self.home_service.control_device(
                device.device_id,
                user_id,
                command.action,
                command.params
            )
            results.append(result)

        if len(devices) == 1:
            device_name = devices[0].name
            action_text = '打开' if command.action == 'turn_on' else '关闭'
            response = f'好的，已为您{action_text}{device_name}'
        else:
            action_text = '打开' if command.action == 'turn_on' else "关闭"
            response = f"好的，已为您{action_text}{len(devices)}个设备"

        return {
            'success': True,
            "response": response,
            "devices_affected": len(devices),
            'results': results
        }

    def _execute_query_command(
        self,
        user_id: int,
        command: VoiceCommand
    ) -> Dict[str, Any]:
        """执行状态查询命令"""
        devices = self.home_service.get_user_devices(
            user_id,
            command.room,
            command.device_type
        )

        if not devices:
            return {
                'success': False,
                'response': "抱歉，没有找到对应的设备。"
            }

        status_list = []
        for device in devices:
            status_text = '开启' if device.status == DeviceStatus.ON else "关闭"
            status_list.append(f"{device.name}当前{status_text}")

        return {
            'success': True,
            'response': '，'.join(status_list),
            "devices": [d.to_dict() for d in devices]
        }


# ==================== 统一智能家居服务 ====================

class SmartHomeIntegration:
    """统一智能家居集成服务"""

    def __init__(self):
        self.home = SmartHomeService()
        self.scene = SceneService(self.home)
        self.voice = VoiceControlService(self.home, self.scene)


# 全局服务实例
smart_home_service = SmartHomeIntegration()
