"""
安全守护系统服务
提供跌倒检测、行为异常监测、GPS定位与安全区域等功能
"""
import logging
import secrets
import math
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 跌倒检测系统 ====================

class FallSeverity(Enum):
    """跌倒严重程度"""
    MILD = 'mild'  # 轻微
    MODERATE = 'moderate'  # 中等
    SEVERE = 'severe'  # 严重
    CRITICAL = "critical"  # 危急


class FallStatus(Enum):
    """跌倒事件状态"""
    DETECTED = 'detected'  # 检测到
    CONFIRMED = "confirmed"  # 已确认
    FALSE_ALARM = "false_alarm"  # 误报
    HANDLED = "handled"  # 已处理
    EMERGENCY_SENT = "emergency_sent"  # 已发送紧急求助


@dataclass
class FallEvent:
    """跌倒事件"""
    event_id: str
    user_id: int
    severity: FallSeverity
    status: FallStatus
    detected_at: datetime
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sensor_data: Dict[str, Any] = field(default_factory=dict)
    response_time_seconds: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    handled_at: Optional[datetime] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'user_id': self.user_id,
            'severity': self.severity.value,
            'status': self.status.value,
            "detected_at": self.detected_at.isoformat(),
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            "response_time_seconds": self.response_time_seconds,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            'handled_at': self.handled_at.isoformat() if self.handled_at else None,
            'notes': self.notes
        }


class FallDetectionService:
    """跌倒检测服务"""

    # 跌倒检测阈值
    DETECTION_THRESHOLDS = {
        "acceleration_threshold": 2.5,  # 加速度阈值 (g)
        "impact_threshold": 3.0,  # 冲击阈值 (g)
        "orientation_change": 60,  # 姿态变化角度
        "immobility_seconds": 10  # 静止时间阈值
    }

    # 确认等待时间
    CONFIRMATION_TIMEOUT = 60  # 秒

    def __init__(self):
        self.events: Dict[str, FallEvent] = {}
        self.user_events: Dict[int, List[str]] = defaultdict(list)
        self.user_settings: Dict[int, Dict] = {}

    def analyze_sensor_data(
        self,
        user_id: int,
        acceleration: Dict[str, float],
        gyroscope: Dict[str, float],
        orientation: Dict[str, float]
    ) -> Optional[FallEvent]:
        """分析传感器数据检测跌倒"""
        # 计算加速度向量
        acc_magnitude = math.sqrt(
            acceleration.get('x', 0) ** 2 +
            acceleration.get('y', 0) ** 2 +
            acceleration.get('z', 0) ** 2
        )

        # 计算角速度
        gyro_magnitude = math.sqrt(
            gyroscope.get('x', 0) ** 2 +
            gyroscope.get('y', 0) ** 2 +
            gyroscope.get("z", 0) ** 2
        )

        # 判断是否跌倒
        is_fall = False
        severity = FallSeverity.MILD

        if acc_magnitude > self.DETECTION_THRESHOLDS["impact_threshold"]:
            is_fall = True
            if acc_magnitude > 4.0:
                severity = FallSeverity.SEVERE
            elif acc_magnitude > 3.5:
                severity = FallSeverity.MODERATE

        if gyro_magnitude > 200:  # 快速旋转
            is_fall = True
            if severity == FallSeverity.MILD:
                severity = FallSeverity.MODERATE

        if not is_fall:
            return None

        # 创建跌倒事件
        event = self._create_fall_event(
            user_id,
            severity,
            {
                "acceleration": acceleration,
                'gyroscope': gyroscope,
                "orientation": orientation,
                "acc_magnitude": acc_magnitude,
                "gyro_magnitude": gyro_magnitude
            }
        )

        logger.warning(f"检测到跌倒事件: 用户 {user_id}, 严重程度 {severity.value}")
        return event

    def _create_fall_event(
        self,
        user_id: int,
        severity: FallSeverity,
        sensor_data: Dict[str, Any],
        location: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> FallEvent:
        """创建跌倒事件"""
        event_id = f"fall_{user_id}_{int(datetime.now().timestamp())}"

        event = FallEvent(
            event_id=event_id,
            user_id=user_id,
            severity=severity,
            status=FallStatus.DETECTED,
            detected_at=datetime.now(),
            location=location,
            latitude=latitude,
            longitude=longitude,
            sensor_data=sensor_data
        )

        self.events[event_id] = event
        self.user_events[user_id].append(event_id)

        return event

    def confirm_fall(self, event_id: str, is_real: bool, notes: str = None) -> bool:
        """确认跌倒事件"""
        event = self.events.get(event_id)
        if not event:
            return False

        if is_real:
            event.status = FallStatus.CONFIRMED
        else:
            event.status = FallStatus.FALSE_ALARM

        event.confirmed_at = datetime.now()
        event.response_time_seconds = int(
            (event.confirmed_at - event.detected_at).total_seconds()
        )
        event.notes = notes

        return True

    def trigger_emergency(self, event_id: str) -> Dict[str, Any]:
        """触发紧急求助"""
        event = self.events.get(event_id)
        if not event:
            return {'success': False, 'error': '事件不存在'}

        event.status = FallStatus.EMERGENCY_SENT

        # 模拟发送紧急求助
        return {
            'success': True,
            "event_id": event_id,
            "emergency_contacts_notified": True,
            "location_shared": True,
            'message': "紧急求助已发送，家人和紧急联系人将收到通知"
        }

    def mark_handled(self, event_id: str, notes: str = None) -> bool:
        """标记事件已处理"""
        event = self.events.get(event_id)
        if not event:
            return False

        event.status = FallStatus.HANDLED
        event.handled_at = datetime.now()
        if notes:
            event.notes = notes

        return True

    def get_user_events(
        self,
        user_id: int,
        status: Optional[FallStatus] = None,
        limit: int = 50
    ) -> List[FallEvent]:
        """获取用户跌倒事件"""
        event_ids = self.user_events.get(user_id, [])
        events = [self.events[eid] for eid in event_ids if eid in self.events]

        if status:
            events = [e for e in events if e.status == status]

        events.sort(key=lambda x: x.detected_at, reverse=True)
        return events[:limit]

    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取跌倒统计"""
        events = self.get_user_events(user_id)

        total = len(events)
        confirmed = sum(1 for e in events if e.status == FallStatus.CONFIRMED)
        false_alarms = sum(1 for e in events if e.status == FallStatus.FALSE_ALARM)

        avg_response = 0
        response_times = [e.response_time_seconds for e in events if e.response_time_seconds]
        if response_times:
            avg_response = sum(response_times) / len(response_times)

        return {
            "total_events": total,
            "confirmed_falls": confirmed,
            "false_alarms": false_alarms,
            "accuracy_rate": (confirmed / total * 100) if total > 0 else 0,
            "average_response_seconds": round(avg_response, 1),
            "last_30_days": sum(1 for e in events if e.detected_at > datetime.now() - timedelta(days=30))
        }


# ==================== 行为异常检测 ====================

class BehaviorType(Enum):
    """行为类型"""
    SLEEP = 'sleep'  # 睡眠
    ACTIVITY = 'activity'  # 活动
    MEAL = 'meal'  # 用餐
    MEDICATION = 'medication'  # 用药
    SOCIAL = 'social'  # 社交
    OUTDOOR = "outdoor"  # 外出


class AnomalyLevel(Enum):
    """异常级别"""
    LOW = 'low'  # 低
    MEDIUM = 'medium'  # 中
    HIGH = "high"  # 高


@dataclass
class BehaviorPattern:
    """行为模式"""
    user_id: int
    behavior_type: BehaviorType
    usual_time: str  # HH:MM
    usual_duration: int  # 分钟
    frequency: str  # daily/weekly
    tolerance_minutes: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior_type": self.behavior_type.value,
            'usual_time': self.usual_time,
            "usual_duration": self.usual_duration,
            'frequency': self.frequency,
            "tolerance_minutes": self.tolerance_minutes
        }


@dataclass
class BehaviorAnomaly:
    """行为异常"""
    anomaly_id: str
    user_id: int
    behavior_type: BehaviorType
    level: AnomalyLevel
    description: str
    expected: str
    actual: str
    detected_at: datetime
    notified: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            "behavior_type": self.behavior_type.value,
            'level': self.level.value,
            "description": self.description,
            'expected': self.expected,
            'actual': self.actual,
            "detected_at": self.detected_at.isoformat(),
            'notified': self.notified,
            'resolved': self.resolved
        }


class BehaviorMonitorService:
    """行为监测服务"""

    def __init__(self):
        self.patterns: Dict[int, List[BehaviorPattern]] = defaultdict(list)
        self.anomalies: Dict[str, BehaviorAnomaly] = {}
        self.user_anomalies: Dict[int, List[str]] = defaultdict(list)
        self.activity_logs: Dict[int, List[Dict]] = defaultdict(list)

    def set_behavior_pattern(
        self,
        user_id: int,
        behavior_type: BehaviorType,
        usual_time: str,
        usual_duration: int,
        frequency: str = 'daily',
        tolerance_minutes: int = 60
    ) -> BehaviorPattern:
        """设置行为模式"""
        pattern = BehaviorPattern(
            user_id=user_id,
            behavior_type=behavior_type,
            usual_time=usual_time,
            usual_duration=usual_duration,
            frequency=frequency,
            tolerance_minutes=tolerance_minutes
        )

        # 更新或添加模式
        existing = [p for p in self.patterns[user_id] if p.behavior_type == behavior_type]
        if existing:
            self.patterns[user_id].remove(existing[0])

        self.patterns[user_id].append(pattern)
        return pattern

    def log_activity(
        self,
        user_id: int,
        behavior_type: BehaviorType,
        started_at: datetime,
        duration_minutes: int = None
    ) -> Optional[BehaviorAnomaly]:
        """记录活动并检测异常"""
        # 记录活动
        self.activity_logs[user_id].append({
            "behavior_type": behavior_type.value,
            'started_at': started_at.isoformat(),
            "duration_minutes": duration_minutes
        })

        # 检查是否异常
        patterns = [p for p in self.patterns.get(user_id, []) if p.behavior_type == behavior_type]
        if not patterns:
            return None

        pattern = patterns[0]
        anomaly = self._check_anomaly(user_id, behavior_type, started_at, duration_minutes, pattern)

        return anomaly

    def _check_anomaly(
        self,
        user_id: int,
        behavior_type: BehaviorType,
        actual_time: datetime,
        actual_duration: int,
        pattern: BehaviorPattern
    ) -> Optional[BehaviorAnomaly]:
        """检查行为异常"""
        # 解析预期时间
        expected_hour, expected_minute = map(int, pattern.usual_time.split(":"))
        expected_time = actual_time.replace(hour=expected_hour, minute=expected_minute)

        # 计算时间差
        time_diff = abs((actual_time - expected_time).total_seconds() / 60)

        # 判断异常
        if time_diff <= pattern.tolerance_minutes:
            return None

        # 确定异常级别
        if time_diff > pattern.tolerance_minutes * 3:
            level = AnomalyLevel.HIGH
        elif time_diff > pattern.tolerance_minutes * 2:
            level = AnomalyLevel.MEDIUM
        else:
            level = AnomalyLevel.LOW

        # 创建异常记录
        anomaly_id = f"anomaly_{user_id}_{int(datetime.now().timestamp())}"

        behavior_names = {
            BehaviorType.SLEEP: '睡眠',
            BehaviorType.ACTIVITY: '活动',
            BehaviorType.MEAL: '用餐',
            BehaviorType.MEDICATION: '用药',
            BehaviorType.SOCIAL: '社交',
            BehaviorType.OUTDOOR: '外出'
        }

        anomaly = BehaviorAnomaly(
            anomaly_id=anomaly_id,
            user_id=user_id,
            behavior_type=behavior_type,
            level=level,
            description=f'{behavior_names.get(behavior_type, behavior_type.value)}时间异常',
            expected=pattern.usual_time,
            actual=actual_time.strftime('%H:%M'),
            detected_at=datetime.now()
        )

        self.anomalies[anomaly_id] = anomaly
        self.user_anomalies[user_id].append(anomaly_id)

        logger.warning(f"检测到行为异常: 用户 {user_id}, {behavior_type.value}, 级别 {level.value}")
        return anomaly

    def check_inactivity(self, user_id: int, hours: int = 12) -> Optional[BehaviorAnomaly]:
        """检查长时间无活动"""
        logs = self.activity_logs.get(user_id, [])
        if not logs:
            return None

        # 获取最后活动时间
        last_activity = max(logs, key=lambda x: x['started_at'])
        last_time = datetime.fromisoformat(last_activity['started_at'])

        inactive_hours = (datetime.now() - last_time).total_seconds() / 3600

        if inactive_hours < hours:
            return None

        anomaly_id = f"inactivity_{user_id}_{int(datetime.now().timestamp())}"
        level = AnomalyLevel.HIGH if inactive_hours > 24 else AnomalyLevel.MEDIUM

        anomaly = BehaviorAnomaly(
            anomaly_id=anomaly_id,
            user_id=user_id,
            behavior_type=BehaviorType.ACTIVITY,
            level=level,
            description=f'超过{int(inactive_hours)}小时无活动记录',
            expected='正常活动',
            actual=f"{int(inactive_hours)}小时无活动",
            detected_at=datetime.now()
        )

        self.anomalies[anomaly_id] = anomaly
        self.user_anomalies[user_id].append(anomaly_id)

        return anomaly

    def get_user_anomalies(
        self,
        user_id: int,
        resolved: Optional[bool] = None,
        limit: int = 50
    ) -> List[BehaviorAnomaly]:
        """获取用户行为异常"""
        anomaly_ids = self.user_anomalies.get(user_id, [])
        anomalies = [self.anomalies[aid] for aid in anomaly_ids if aid in self.anomalies]

        if resolved is not None:
            anomalies = [a for a in anomalies if a.resolved == resolved]

        anomalies.sort(key=lambda x: x.detected_at, reverse=True)
        return anomalies[:limit]

    def resolve_anomaly(self, anomaly_id: str, notes: str = None) -> bool:
        """解决异常"""
        anomaly = self.anomalies.get(anomaly_id)
        if not anomaly:
            return False

        anomaly.resolved = True
        return True

    def get_user_patterns(self, user_id: int) -> List[BehaviorPattern]:
        """获取用户行为模式"""
        return self.patterns.get(user_id, [])


# ==================== GPS定位与安全区域 ====================

@dataclass
class SafeZone:
    """安全区域"""
    zone_id: str
    user_id: int
    name: str
    latitude: float
    longitude: float
    radius_meters: int
    is_home: bool = False
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'zone_id': self.zone_id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            "radius_meters": self.radius_meters,
            'is_home': self.is_home,
            'enabled': self.enabled
        }


@dataclass
class LocationRecord:
    """位置记录"""
    record_id: str
    user_id: int
    latitude: float
    longitude: float
    accuracy: float
    address: Optional[str] = None
    in_safe_zone: bool = True
    safe_zone_id: Optional[str] = None
    recorded_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy': self.accuracy,
            'address': self.address,
            "in_safe_zone": self.in_safe_zone,
            "recorded_at": self.recorded_at.isoformat()
        }


@dataclass
class ZoneAlert:
    """区域警报"""
    alert_id: str
    user_id: int
    zone_id: str
    alert_type: str  # exit/enter
    latitude: float
    longitude: float
    distance_meters: float
    created_at: datetime = field(default_factory=datetime.now)
    notified: bool = False
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'zone_id': self.zone_id,
            'alert_type': self.alert_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            "distance_meters": self.distance_meters,
            'created_at': self.created_at.isoformat(),
            "acknowledged": self.acknowledged
        }


class LocationService:
    """位置服务"""

    def __init__(self):
        self.safe_zones: Dict[str, SafeZone] = {}
        self.user_zones: Dict[int, List[str]] = defaultdict(list)
        self.location_history: Dict[int, List[LocationRecord]] = defaultdict(list)
        self.zone_alerts: Dict[str, ZoneAlert] = {}
        self.user_alerts: Dict[int, List[str]] = defaultdict(list)
        self.last_location: Dict[int, LocationRecord] = {}

    def add_safe_zone(
        self,
        user_id: int,
        name: str,
        latitude: float,
        longitude: float,
        radius_meters: int,
        is_home: bool = False
    ) -> SafeZone:
        """添加安全区域"""
        zone_id = f"zone_{user_id}_{secrets.token_hex(4)}"

        zone = SafeZone(
            zone_id=zone_id,
            user_id=user_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            is_home=is_home
        )

        self.safe_zones[zone_id] = zone
        self.user_zones[user_id].append(zone_id)

        logger.info(f"添加安全区域: {name} ({zone_id})")
        return zone

    def remove_safe_zone(self, zone_id: str, user_id: int) -> bool:
        """移除安全区域"""
        zone = self.safe_zones.get(zone_id)
        if not zone or zone.user_id != user_id:
            return False

        del self.safe_zones[zone_id]
        self.user_zones[user_id].remove(zone_id)
        return True

    def get_user_zones(self, user_id: int) -> List[SafeZone]:
        """获取用户安全区域"""
        zone_ids = self.user_zones.get(user_id, [])
        return [self.safe_zones[zid] for zid in zone_ids if zid in self.safe_zones]

    def update_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        accuracy: float,
        address: str = None
    ) -> Tuple[LocationRecord, Optional[ZoneAlert]]:
        """更新位置"""
        record_id = f"loc_{user_id}_{int(datetime.now().timestamp())}"

        # 检查是否在安全区域内
        in_safe_zone = False
        current_zone_id = None

        for zone in self.get_user_zones(user_id):
            if not zone.enabled:
                continue

            distance = self._calculate_distance(
                latitude, longitude,
                zone.latitude, zone.longitude
            )

            if distance <= zone.radius_meters:
                in_safe_zone = True
                current_zone_id = zone.zone_id
                break

        record = LocationRecord(
            record_id=record_id,
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            address=address,
            in_safe_zone=in_safe_zone,
            safe_zone_id=current_zone_id
        )

        self.location_history[user_id].append(record)
        if len(self.location_history[user_id]) > 1000:
            self.location_history[user_id] = self.location_history[user_id][-500:]

        # 检查是否产生警报
        alert = None
        last = self.last_location.get(user_id)

        if last and last.in_safe_zone and not in_safe_zone:
            # 离开安全区域
            alert = self._create_zone_alert(user_id, last.safe_zone_id, 'exit', latitude, longitude)
        elif last and not last.in_safe_zone and in_safe_zone:
            # 进入安全区域
            alert = self._create_zone_alert(user_id, current_zone_id, "enter", latitude, longitude)

        self.last_location[user_id] = record
        return record, alert

    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """计算两点间距离(米)"""
        R = 6371000  # 地球半径(米)

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _create_zone_alert(
        self,
        user_id: int,
        zone_id: str,
        alert_type: str,
        latitude: float,
        longitude: float
    ) -> ZoneAlert:
        """创建区域警报"""
        alert_id = f"zalert_{user_id}_{int(datetime.now().timestamp())}"

        zone = self.safe_zones.get(zone_id)
        distance = 0
        if zone:
            distance = self._calculate_distance(
                latitude, longitude,
                zone.latitude, zone.longitude
            )

        alert = ZoneAlert(
            alert_id=alert_id,
            user_id=user_id,
            zone_id=zone_id,
            alert_type=alert_type,
            latitude=latitude,
            longitude=longitude,
            distance_meters=distance
        )

        self.zone_alerts[alert_id] = alert
        self.user_alerts[user_id].append(alert_id)

        logger.warning(f"区域警报: 用户 {user_id} {alert_type} 安全区域")
        return alert

    def get_last_location(self, user_id: int) -> Optional[LocationRecord]:
        """获取最后位置"""
        return self.last_location.get(user_id)

    def get_location_history(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 100
    ) -> List[LocationRecord]:
        """获取位置历史"""
        cutoff = datetime.now() - timedelta(hours=hours)
        history = self.location_history.get(user_id, [])

        filtered = [r for r in history if r.recorded_at > cutoff]
        return filtered[-limit:]

    def get_user_alerts(
        self,
        user_id: int,
        acknowledged: Optional[bool] = None,
        limit: int = 50
    ) -> List[ZoneAlert]:
        """获取用户区域警报"""
        alert_ids = self.user_alerts.get(user_id, [])
        alerts = [self.zone_alerts[aid] for aid in alert_ids if aid in self.zone_alerts]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        alerts.sort(key=lambda x: x.created_at, reverse=True)
        return alerts[:limit]

    def acknowledge_alert(self, alert_id: str, user_id: int) -> bool:
        """确认警报"""
        alert = self.zone_alerts.get(alert_id)
        if not alert or alert.user_id != user_id:
            return False

        alert.acknowledged = True
        return True


# ==================== 统一安全守护服务 ====================

class SafetyGuardianService:
    """统一安全守护服务"""

    def __init__(self):
        self.fall_detection = FallDetectionService()
        self.behavior_monitor = BehaviorMonitorService()
        self.location = LocationService()


# 全局服务实例
safety_service = SafetyGuardianService()
