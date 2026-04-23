"""
IoT设备集成服务
支持智能家居设备联动：智能灯、空调、窗帘、健康监测设备等
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json
import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DeviceType(Enum):
    """设备类型"""
    SMART_LIGHT = "smart_light"  # 智能灯
    SMART_AC = "smart_ac"  # 智能空调
    SMART_CURTAIN = "smart_curtain"  # 智能窗帘
    SMART_TV = "smart_tv"  # 智能电视
    BLOOD_PRESSURE = "blood_pressure"  # 血压计
    BLOOD_GLUCOSE = "blood_glucose"  # 血糖仪
    HEART_RATE = "heart_rate"  # 心率监测
    SLEEP_MONITOR = "sleep_monitor"  # 睡眠监测
    FALL_DETECTOR = "fall_detector"  # 跌倒检测
    SOS_BUTTON = "sos_button"  # 紧急求助按钮
    SMART_SPEAKER = "smart_speaker"  # 智能音箱（安心宝主设备）
    SMART_WATCH = "smart_watch"  # 智能手表


class DeviceStatus(Enum):
    """设备状态"""
    ONLINE = "online"
    OFFLINE = 'offline'
    ERROR = 'error'
    UNKNOWN = 'unknown'


class DevicePlatform(Enum):
    """IoT平台"""
    TUYA = 'tuya'  # 涂鸦智能
    XIAOMI = 'xiaomi'  # 米家
    ALIBABA = 'alibaba'  # 阿里智能
    HUAWEI = 'huawei'  # 华为HiLink
    CUSTOM = "custom"  # 自定义协议


# ==================== 设备基类 ====================

class BaseDevice(ABC):
    """设备基类"""

    def __init__(
        self,
        device_id: str,
        device_type: DeviceType,
        name: str,
        platform: DevicePlatform = DevicePlatform.CUSTOM
    ):
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.platform = platform
        self.status = DeviceStatus.UNKNOWN
        self.last_seen = None
        self.properties = {}

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        pass

    @abstractmethod
    async def execute_command(self, command: str, params: Dict = None) -> bool:
        """执行设备命令"""
        pass

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'device_id': self.device_id,
            "device_type": self.device_type.value,
            'name': self.name,
            'platform': self.platform.value,
            'status': self.status.value,
            'last_seen': str(self.last_seen) if self.last_seen else None,
            'properties': self.properties
        }


# ==================== 智能家居设备 ====================

class SmartLight(BaseDevice):
    """智能灯"""

    def __init__(self, device_id: str, name: str, platform: DevicePlatform = DevicePlatform.CUSTOM):
        super().__init__(device_id, DeviceType.SMART_LIGHT, name, platform)
        self.properties = {
            'power': False,
            'brightness': 100,
            'color_temp': 4000,  # 色温（K）
            'color': "#FFFFFF"
        }

    async def get_status(self) -> Dict[str, Any]:
        """获取灯光状态"""
        return {
            'power': self.properties.get('power', False),
            'brightness': self.properties.get('brightness', 100),
            'color_temp': self.properties.get('color_temp', 4000)
        }

    async def execute_command(self, command: str, params: Dict = None) -> bool:
        """执行灯光命令"""
        params = params or {}

        if command == 'turn_on':
            self.properties['power'] = True
            logger.info(f'智能灯 {self.name} 已开启')
            return True

        elif command == 'turn_off':
            self.properties['power'] = False
            logger.info(f'智能灯 {self.name} 已关闭')
            return True

        elif command == 'set_brightness':
            brightness = params.get('brightness', 100)
            self.properties['brightness'] = max(1, min(100, brightness))
            logger.info(f'智能灯 {self.name} 亮度设为 {brightness}%')
            return True

        elif command == 'night_mode':
            # 夜间模式：低亮度暖光
            self.properties['power'] = True
            self.properties['brightness'] = 20
            self.properties['color_temp'] = 2700
            logger.info(f"智能灯 {self.name} 切换到夜间模式")
            return True

        return False


class SmartAC(BaseDevice):
    """智能空调"""

    def __init__(self, device_id: str, name: str, platform: DevicePlatform = DevicePlatform.CUSTOM):
        super().__init__(device_id, DeviceType.SMART_AC, name, platform)
        self.properties = {
            'power': False,
            'mode': 'cool',  # cool/heat/auto/fan
            "temperature": 26,
            'fan_speed': 'auto',  # low/medium/high/auto
            'swing': False
        }

    async def get_status(self) -> Dict[str, Any]:
        return self.properties.copy()

    async def execute_command(self, command: str, params: Dict = None) -> bool:
        params = params or {}

        if command == 'turn_on':
            self.properties['power'] = True
            logger.info(f'空调 {self.name} 已开启')
            return True

        elif command == 'turn_off':
            self.properties['power'] = False
            logger.info(f'空调 {self.name} 已关闭')
            return True

        elif command == "set_temperature":
            temp = params.get("temperature", 26)
            self.properties["temperature"] = max(16, min(30, temp))
            logger.info(f'空调 {self.name} 温度设为 {temp}°C')
            return True

        elif command == 'comfort_mode':
            # 舒适模式：适合老人的温度
            self.properties["power"] = True
            self.properties["temperature"] = 24
            self.properties['mode'] = "auto"
            self.properties['fan_speed'] = 'low'
            logger.info(f"空调 {self.name} 切换到舒适模式")
            return True

        return False


class SmartCurtain(BaseDevice):
    """智能窗帘"""

    def __init__(self, device_id: str, name: str, platform: DevicePlatform = DevicePlatform.CUSTOM):
        super().__init__(device_id, DeviceType.SMART_CURTAIN, name, platform)
        self.properties = {
            'position': 0,  # 0-100, 0=全关, 100=全开
            'is_moving': False
        }

    async def get_status(self) -> Dict[str, Any]:
        return self.properties.copy()

    async def execute_command(self, command: str, params: Dict = None) -> bool:
        params = params or {}

        if command == 'open':
            self.properties['position'] = 100
            logger.info(f'窗帘 {self.name} 已打开')
            return True

        elif command == 'close':
            self.properties['position'] = 0
            logger.info(f'窗帘 {self.name} 已关闭')
            return True

        elif command == 'set_position':
            position = params.get('position', 50)
            self.properties['position'] = max(0, min(100, position))
            logger.info(f"窗帘 {self.name} 位置设为 {position}%")
            return True

        return False


# ==================== 健康监测设备 ====================

class BloodPressureMonitor(BaseDevice):
    """血压计"""

    def __init__(self, device_id: str, name: str, platform: DevicePlatform = DevicePlatform.CUSTOM):
        super().__init__(device_id, DeviceType.BLOOD_PRESSURE, name, platform)
        self.readings = []  # 历史读数

    async def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.status == DeviceStatus.ONLINE,
            "last_reading": self.readings[-1] if self.readings else None,
            "readings_count": len(self.readings)
        }

    async def execute_command(self, command: str, params: Dict = None) -> bool:
        if command == "start_measure":
            logger.info(f"血压计 {self.name} 开始测量")
            return True
        return False

    def add_reading(self, systolic: int, diastolic: int, pulse: int):
        """添加血压读数"""
        reading = {
            'systolic': systolic,  # 收缩压
            'diastolic': diastolic,  # 舒张压
            'pulse': pulse,  # 脉搏
            "timestamp": datetime.now().isoformat(),
            "is_abnormal": self._check_abnormal(systolic, diastolic, pulse)
        }
        self.readings.append(reading)

        # 只保留最近100条
        if len(self.readings) > 100:
            self.readings = self.readings[-100:]

        return reading

    def _check_abnormal(self, systolic: int, diastolic: int, pulse: int) -> bool:
        """检查是否异常"""
        # 正常范围：收缩压90-140，舒张压60-90，脉搏60-100
        if systolic < 90 or systolic > 140:
            return True
        if diastolic < 60 or diastolic > 90:
            return True
        if pulse < 60 or pulse > 100:
            return True
        return False


class FallDetector(BaseDevice):
    """跌倒检测器"""

    def __init__(self, device_id: str, name: str, platform: DevicePlatform = DevicePlatform.CUSTOM):
        super().__init__(device_id, DeviceType.FALL_DETECTOR, name, platform)
        self.alerts = []
        self.properties = {
            'sensitivity': 'medium',  # low/medium/high
            'auto_call': True,  # 自动拨打紧急电话
            "alert_delay": 30  # 确认延迟（秒）
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.status == DeviceStatus.ONLINE,
            "sensitivity": self.properties.get("sensitivity"),
            'auto_call': self.properties.get('auto_call'),
            "recent_alerts": self.alerts[-5:] if self.alerts else []
        }

    async def execute_command(self, command: str, params: Dict = None) -> bool:
        params = params or {}

        if command == "set_sensitivity":
            sensitivity = params.get('sensitivity', 'medium')
            if sensitivity in ['low', 'medium', 'high']:
                self.properties["sensitivity"] = sensitivity
                return True

        elif command == "cancel_alert":
            # 取消当前警报
            logger.info(f"跌倒检测器 {self.name} 警报已取消")
            return True

        return False

    def trigger_alert(self, confidence: float = 0.8):
        """触发跌倒警报"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'status': 'active',
            'handled': False
        }
        self.alerts.append(alert)
        logger.warning(f"跌倒检测警报！设备: {self.name}, 置信度: {confidence}")
        return alert


class SOSButton(BaseDevice):
    """紧急求助按钮"""

    def __init__(self, device_id: str, name: str, platform: DevicePlatform = DevicePlatform.CUSTOM):
        super().__init__(device_id, DeviceType.SOS_BUTTON, name, platform)
        self.alerts = []

    async def get_status(self) -> Dict[str, Any]:
        return {
            'connected': self.status == DeviceStatus.ONLINE,
            "battery_level": self.properties.get("battery_level", 100),
            "recent_alerts": self.alerts[-5:] if self.alerts else []
        }

    async def execute_command(self, command: str, params: Dict = None) -> bool:
        if command == 'test':
            logger.info(f"SOS按钮 {self.name} 测试成功")
            return True
        return False

    def trigger_sos(self, location: Optional[Dict] = None):
        """触发SOS警报"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'location': location,
            'status': 'active',
            'handled': False
        }
        self.alerts.append(alert)
        logger.critical(f"SOS紧急求助！设备: {self.name}")
        return alert


# ==================== IoT设备管理器 ====================

class IoTDeviceManager:
    """IoT设备管理器"""

    def __init__(self):
        self.devices: Dict[str, BaseDevice] = {}
        self.user_devices: Dict[int, List[str]] = {}  # user_id -> device_ids

    def register_device(
        self,
        device_id: str,
        device_type: DeviceType,
        name: str,
        user_id: int,
        platform: DevicePlatform = DevicePlatform.CUSTOM
    ) -> BaseDevice:
        """注册设备"""
        # 根据类型创建设备实例
        device_class_map = {
            DeviceType.SMART_LIGHT: SmartLight,
            DeviceType.SMART_AC: SmartAC,
            DeviceType.SMART_CURTAIN: SmartCurtain,
            DeviceType.BLOOD_PRESSURE: BloodPressureMonitor,
            DeviceType.FALL_DETECTOR: FallDetector,
            DeviceType.SOS_BUTTON: SOSButton,
        }

        device_class = device_class_map.get(device_type, BaseDevice)
        device = device_class(device_id, name, platform)
        device.status = DeviceStatus.ONLINE

        self.devices[device_id] = device

        # 关联到用户
        if user_id not in self.user_devices:
            self.user_devices[user_id] = []
        if device_id not in self.user_devices[user_id]:
            self.user_devices[user_id].append(device_id)

        logger.info(f"设备已注册: {name} ({device_id}) -> 用户 {user_id}")
        return device

    def unregister_device(self, device_id: str) -> bool:
        """注销设备"""
        if device_id in self.devices:
            del self.devices[device_id]

            # 从用户关联中移除
            for user_id, devices in self.user_devices.items():
                if device_id in devices:
                    devices.remove(device_id)

            logger.info(f"设备已注销: {device_id}")
            return True
        return False

    def get_device(self, device_id: str) -> Optional[BaseDevice]:
        """获取设备"""
        return self.devices.get(device_id)

    def get_user_devices(self, user_id: int) -> List[BaseDevice]:
        """获取用户的所有设备"""
        device_ids = self.user_devices.get(user_id, [])
        return [self.devices[did] for did in device_ids if did in self.devices]

    def get_devices_by_type(self, user_id: int, device_type: DeviceType) -> List[BaseDevice]:
        """获取用户指定类型的设备"""
        return [
            d for d in self.get_user_devices(user_id)
            if d.device_type == device_type
        ]

    async def execute_device_command(
        self,
        device_id: str,
        command: str,
        params: Dict = None
    ) -> Dict[str, Any]:
        """执行设备命令"""
        device = self.get_device(device_id)
        if not device:
            return {'success': False, 'error': '设备不存在'}

        try:
            success = await device.execute_command(command, params)
            return {
                'success': success,
                'device_id': device_id,
                'command': command,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"执行设备命令失败: {e}")
            return {'success': False, "error": str(e)}


# ==================== 场景联动服务 ====================

class SceneAutomation:
    """场景联动服务"""

    def __init__(self, device_manager: IoTDeviceManager):
        self.device_manager = device_manager
        self.scenes: Dict[str, Dict] = {}

    def register_scene(
        self,
        scene_id: str,
        name: str,
        user_id: int,
        actions: List[Dict]
    ):
        """注册场景"""
        self.scenes[scene_id] = {
            'name': name,
            'user_id': user_id,
            'actions': actions,
            'created_at': datetime.now().isoformat()
        }
        logger.info(f"场景已注册: {name} ({scene_id})")

    async def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景"""
        scene = self.scenes.get(scene_id)
        if not scene:
            return {'success': False, 'error': '场景不存在'}

        results = []
        for action in scene['actions']:
            device_id = action.get("device_id")
            command = action.get('command')
            params = action.get('params', {})

            result = await self.device_manager.execute_device_command(
                device_id, command, params
            )
            results.append(result)

        success_count = sum(1 for r in results if r.get('success'))
        return {
            'success': success_count == len(results),
            'scene_id': scene_id,
            'scene_name': scene['name'],
            "total_actions": len(results),
            "success_count": success_count,
            'results': results
        }

    async def morning_scene(self, user_id: int) -> Dict[str, Any]:
        """早晨场景：开灯、开窗帘"""
        actions = []

        # 获取用户的智能灯
        lights = self.device_manager.get_devices_by_type(user_id, DeviceType.SMART_LIGHT)
        for light in lights:
            actions.append({
                'device_id': light.device_id,
                'command': 'turn_on',
                'params': {'brightness': 80}
            })

        # 获取用户的窗帘
        curtains = self.device_manager.get_devices_by_type(user_id, DeviceType.SMART_CURTAIN)
        for curtain in curtains:
            actions.append({
                'device_id': curtain.device_id,
                'command': 'open',
                'params': {}
            })

        # 执行所有动作
        results = []
        for action in actions:
            result = await self.device_manager.execute_device_command(
                action['device_id'], action['command'], action['params']
            )
            results.append(result)

        return {
            'scene': 'morning',
            'success': all(r.get('success') for r in results),
            "results": results
        }

    async def night_scene(self, user_id: int) -> Dict[str, Any]:
        """夜间场景：关灯、关窗帘、调节空调"""
        actions = []

        # 关闭主灯，开启夜灯模式
        lights = self.device_manager.get_devices_by_type(user_id, DeviceType.SMART_LIGHT)
        for i, light in enumerate(lights):
            if i == 0:  # 保留一盏夜灯
                actions.append({
                    'device_id': light.device_id,
                    'command': 'night_mode',
                    'params': {}
                })
            else:
                actions.append({
                    'device_id': light.device_id,
                    'command': 'turn_off',
                    'params': {}
                })

        # 关闭窗帘
        curtains = self.device_manager.get_devices_by_type(user_id, DeviceType.SMART_CURTAIN)
        for curtain in curtains:
            actions.append({
                'device_id': curtain.device_id,
                'command': 'close',
                'params': {}
            })

        # 空调舒适模式
        acs = self.device_manager.get_devices_by_type(user_id, DeviceType.SMART_AC)
        for ac in acs:
            actions.append({
                'device_id': ac.device_id,
                "command": "comfort_mode",
                'params': {}
            })

        # 执行所有动作
        results = []
        for action in actions:
            result = await self.device_manager.execute_device_command(
                action['device_id'], action['command'], action['params']
            )
            results.append(result)

        return {
            'scene': 'night',
            'success': all(r.get('success') for r in results),
            "results": results
        }

    async def emergency_scene(self, user_id: int) -> Dict[str, Any]:
        """紧急场景：全部开灯"""
        actions = []

        # 打开所有灯
        lights = self.device_manager.get_devices_by_type(user_id, DeviceType.SMART_LIGHT)
        for light in lights:
            actions.append({
                'device_id': light.device_id,
                'command': 'turn_on',
                'params': {'brightness': 100}
            })

        # 执行所有动作
        results = []
        for action in actions:
            result = await self.device_manager.execute_device_command(
                action['device_id'], action['command'], action['params']
            )
            results.append(result)

        return {
            'scene': 'emergency',
            'success': all(r.get('success') for r in results),
            "results": results
        }


# ==================== 健康数据聚合 ====================

class HealthDataAggregator:
    """健康数据聚合器"""

    def __init__(self, device_manager: IoTDeviceManager):
        self.device_manager = device_manager

    async def get_health_summary(self, user_id: int) -> Dict[str, Any]:
        """获取用户健康数据摘要"""
        summary = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            "blood_pressure": None,
            'heart_rate': None,
            'sleep': None,
            'activity': None,
            'alerts': []
        }

        # 获取血压数据
        bp_monitors = self.device_manager.get_devices_by_type(
            user_id, DeviceType.BLOOD_PRESSURE
        )
        for monitor in bp_monitors:
            if isinstance(monitor, BloodPressureMonitor) and monitor.readings:
                latest = monitor.readings[-1]
                summary["blood_pressure"] = {
                    'systolic': latest['systolic'],
                    'diastolic': latest['diastolic'],
                    'pulse': latest['pulse'],
                    'timestamp': latest['timestamp'],
                    'is_abnormal': latest['is_abnormal']
                }
                if latest["is_abnormal"]:
                    summary['alerts'].append({
                        'type': "blood_pressure",
                        'message': '血压异常',
                        'data': latest
                    })

        # 获取跌倒检测警报
        fall_detectors = self.device_manager.get_devices_by_type(
            user_id, DeviceType.FALL_DETECTOR
        )
        for detector in fall_detectors:
            if isinstance(detector, FallDetector):
                active_alerts = [a for a in detector.alerts if a['status'] == 'active']
                for alert in active_alerts:
                    summary['alerts'].append({
                        'type': 'fall',
                        'message': '检测到跌倒',
                        'data': alert
                    })

        # 获取SOS警报
        sos_buttons = self.device_manager.get_devices_by_type(
            user_id, DeviceType.SOS_BUTTON
        )
        for button in sos_buttons:
            if isinstance(button, SOSButton):
                active_alerts = [a for a in button.alerts if a['status'] == 'active']
                for alert in active_alerts:
                    summary['alerts'].append({
                        'type': 'sos',
                        'message': '紧急求助',
                        "data": alert
                    })

        return summary


# 全局实例
iot_device_manager = IoTDeviceManager()
scene_automation = SceneAutomation(iot_device_manager)
health_aggregator = HealthDataAggregator(iot_device_manager)
