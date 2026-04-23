"""
紧急求助服务
提供SOS紧急求助、跌倒检测、位置追踪、紧急联系人管理等功能
"""
import logging
import asyncio
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class EmergencyType(Enum):
    """紧急事件类型"""
    SOS = 'sos'  # 手动求助
    FALL = 'fall'  # 跌倒检测
    HEALTH = 'health'  # 健康异常
    INACTIVITY = 'inactivity'  # 长时间无活动
    LOCATION = 'location'  # 位置异常
    DEVICE = 'device'  # 设备异常


class EmergencyLevel(Enum):
    """紧急级别"""
    LOW = 1  # 低级（提醒）
    MEDIUM = 2  # 中级（警告）
    HIGH = 3  # 高级（紧急）
    CRITICAL = 4  # 危急（立即处理）


class AlertStatus(Enum):
    """警报状态"""
    ACTIVE = 'active'  # 进行中
    ACKNOWLEDGED = 'acknowledged'  # 已确认
    HANDLING = 'handling'  # 处理中
    RESOLVED = 'resolved'  # 已解决
    CANCELLED = 'cancelled'  # 已取消
    FALSE_ALARM = "false_alarm"  # 误报


@dataclass
class EmergencyContact:
    """紧急联系人"""
    contact_id: str
    user_id: int
    name: str
    phone: str
    relationship: str  # 关系：儿子、女儿、配偶等
    is_primary: bool = False  # 主要联系人
    notify_order: int = 1  # 通知顺序
    openid: Optional[str] = None  # 微信OpenID
    email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'contact_id': self.contact_id,
            'name': self.name,
            'phone': self.phone,
            "relationship": self.relationship,
            'is_primary': self.is_primary,
            "notify_order": self.notify_order
        }


@dataclass
class Location:
    """位置信息"""
    latitude: float
    longitude: float
    accuracy: float = 0  # 精度（米）
    address: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy': self.accuracy,
            'address': self.address,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class EmergencyAlert:
    """紧急警报"""
    alert_id: str
    user_id: int
    user_name: str
    emergency_type: EmergencyType
    level: EmergencyLevel
    status: AlertStatus
    description: str
    location: Optional[Location] = None
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    handled_by: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            "emergency_type": self.emergency_type.value,
            'level': self.level.value,
            'level_name': self._get_level_name(),
            'status': self.status.value,
            "description": self.description,
            'location': self.location.to_dict() if self.location else None,
            'created_at': self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            'handled_by': self.handled_by,
            'notes': self.notes,
            "duration_minutes": self._get_duration_minutes()
        }

    def _get_level_name(self) -> str:
        names = {
            EmergencyLevel.LOW: '低级',
            EmergencyLevel.MEDIUM: '中级',
            EmergencyLevel.HIGH: '紧急',
            EmergencyLevel.CRITICAL: '危急'
        }
        return names.get(self.level, '未知')

    def _get_duration_minutes(self) -> int:
        end_time = self.resolved_at or datetime.now()
        return int((end_time - self.created_at).total_seconds() / 60)


# ==================== 紧急求助服务 ====================

class EmergencyService:
    """紧急求助服务"""

    def __init__(self):
        self.alerts: Dict[str, EmergencyAlert] = {}
        self.user_alerts: Dict[int, List[str]] = {}  # user_id -> alert_ids
        self.contacts: Dict[int, List[EmergencyContact]] = {}  # user_id -> contacts
        self.user_locations: Dict[int, Location] = {}  # 最新位置
        self.alert_callbacks: List[callable] = []  # 警报回调

    def restore_from_db(self) -> int:
        """从数据库恢复进行中的紧急事件到内存（服务重启后调用）"""
        try:
            from app.models.database import SessionLocal, EmergencyEvent as EmergencyEventModel
            db = SessionLocal()
            try:
                active_events = db.query(EmergencyEventModel).filter(
                    EmergencyEventModel.status.in_(["triggered", "notifying", "responding"])
                ).all()

                restored = 0
                for event in active_events:
                    # 构建 alert_id（与数据库 id 对应）
                    alert_id = f"db_event_{event.id}"

                    # 映射 emergency_type
                    try:
                        emergency_type = EmergencyType(event.emergency_type)
                    except ValueError:
                        emergency_type = EmergencyType.SOS

                    # 映射 status
                    status_map = {
                        "triggered": AlertStatus.ACTIVE,
                        "notifying": AlertStatus.ACTIVE,
                        "responding": AlertStatus.HANDLING,
                    }
                    status = status_map.get(event.status, AlertStatus.ACTIVE)

                    # 重建位置信息
                    location = None
                    if event.latitude and event.longitude:
                        location = Location(
                            latitude=event.latitude,
                            longitude=event.longitude,
                            address=event.address,
                        )

                    # 获取用户名
                    user_name = "未知用户"
                    try:
                        from app.models.database import User
                        user = db.query(User).filter(User.id == event.user_id).first()
                        if user:
                            user_name = user.name
                    except Exception:
                        pass

                    alert = EmergencyAlert(
                        alert_id=alert_id,
                        user_id=event.user_id,
                        user_name=user_name,
                        emergency_type=emergency_type,
                        level=EmergencyLevel.HIGH,
                        status=status,
                        description=event.description or "",
                        location=location,
                        created_at=event.created_at or datetime.now(),
                    )

                    self.alerts[alert_id] = alert

                    if event.user_id not in self.user_alerts:
                        self.user_alerts[event.user_id] = []
                    self.user_alerts[event.user_id].append(alert_id)

                    restored += 1

                logger.info(f"从数据库恢复了 {restored} 个进行中的紧急事件")
                return restored
            finally:
                db.close()
        except Exception as e:
            logger.error(f"恢复紧急事件失败: {e}")
            return 0

    def register_callback(self, callback: callable):
        """注册警报回调函数"""
        self.alert_callbacks.append(callback)

    async def _notify_callbacks(self, alert: EmergencyAlert):
        """通知所有回调"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"警报回调执行失败: {e}")

    # ==================== 紧急联系人管理 ====================

    def add_contact(
        self,
        user_id: int,
        name: str,
        phone: str,
        relationship: str,
        is_primary: bool = False
    ) -> EmergencyContact:
        """添加紧急联系人"""
        contact_id = f"contact_{user_id}_{len(self.contacts.get(user_id, []))}"

        contact = EmergencyContact(
            contact_id=contact_id,
            user_id=user_id,
            name=name,
            phone=phone,
            relationship=relationship,
            is_primary=is_primary,
            notify_order=len(self.contacts.get(user_id, [])) + 1
        )

        if user_id not in self.contacts:
            self.contacts[user_id] = []

        # 如果设为主要联系人，取消其他主要联系人
        if is_primary:
            for c in self.contacts[user_id]:
                c.is_primary = False

        self.contacts[user_id].append(contact)
        logger.info(f"用户 {user_id} 添加紧急联系人: {name}")
        return contact

    def remove_contact(self, user_id: int, contact_id: str) -> bool:
        """移除紧急联系人"""
        if user_id not in self.contacts:
            return False

        self.contacts[user_id] = [
            c for c in self.contacts[user_id]
            if c.contact_id != contact_id
        ]
        return True

    def get_contacts(self, user_id: int) -> List[EmergencyContact]:
        """获取用户的紧急联系人列表"""
        contacts = self.contacts.get(user_id, [])
        # 按通知顺序排序
        return sorted(contacts, key=lambda c: (not c.is_primary, c.notify_order))

    def set_primary_contact(self, user_id: int, contact_id: str) -> bool:
        """设置主要联系人"""
        if user_id not in self.contacts:
            return False

        for contact in self.contacts[user_id]:
            contact.is_primary = (contact.contact_id == contact_id)
        return True

    # ==================== 位置管理 ====================

    def update_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        accuracy: float = 0,
        address: Optional[str] = None
    ) -> Location:
        """更新用户位置"""
        location = Location(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            address=address,
            timestamp=datetime.now()
        )
        self.user_locations[user_id] = location
        logger.debug(f"用户 {user_id} 位置更新: {latitude}, {longitude}")
        return location

    def get_location(self, user_id: int) -> Optional[Location]:
        """获取用户最新位置"""
        return self.user_locations.get(user_id)

    # ==================== 警报管理 ====================

    async def create_alert(
        self,
        user_id: int,
        user_name: str,
        emergency_type: EmergencyType,
        level: EmergencyLevel,
        description: str,
        location: Optional[Location] = None,
        metadata: Optional[Dict] = None
    ) -> EmergencyAlert:
        """创建紧急警报"""
        alert_id = f"alert_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 如果没有提供位置，使用最新位置
        if location is None:
            location = self.user_locations.get(user_id)

        alert = EmergencyAlert(
            alert_id=alert_id,
            user_id=user_id,
            user_name=user_name,
            emergency_type=emergency_type,
            level=level,
            status=AlertStatus.ACTIVE,
            description=description,
            location=location,
            metadata=metadata or {}
        )

        self.alerts[alert_id] = alert

        if user_id not in self.user_alerts:
            self.user_alerts[user_id] = []
        self.user_alerts[user_id].append(alert_id)

        logger.warning(f"紧急警报创建: {alert_id} - {emergency_type.value} - {description}")

        # 触发通知
        await self._send_emergency_notifications(alert)

        # 通知回调
        await self._notify_callbacks(alert)

        return alert

    async def _send_emergency_notifications(self, alert: EmergencyAlert):
        """发送紧急通知"""
        contacts = self.get_contacts(alert.user_id)

        if not contacts:
            logger.warning(f"用户 {alert.user_id} 没有紧急联系人")
            return

        # 构建通知内容
        level_text = alert._get_level_name()
        type_text = self._get_type_text(alert.emergency_type)

        message = f"""
【安心宝紧急通知】

{alert.user_name} 发出{type_text}！

紧急级别：{level_text}
详情：{alert.description}
时间：{alert.created_at.strftime("%Y-%m-%d %H:%M:%S")}
"""

        if alert.location:
            location_str = alert.location.address or f"{alert.location.latitude}, {alert.location.longitude}"
            message += f"\n位置：{location_str}"

        message += '\n\n请立即查看或联系老人确认安全！'

        location_address = ""
        if alert.location:
            location_address = alert.location.address or f"{alert.location.latitude}, {alert.location.longitude}"

        # Collect phone numbers from contacts for SMS service
        phone_numbers = [contact.phone for contact in contacts]

        # Send SMS emergency alerts
        try:
            from app.services.sms_service import sms_service
            await sms_service.send_emergency_alert(
                phone_numbers=phone_numbers,
                user_name=alert.user_name,
                phone="",
                location_address=location_address
            )
        except Exception as e:
            logger.error(f"发送紧急SMS通知失败: {e}")

        # Send via notification service with EMERGENCY template
        try:
            from app.services.notification_service import notification_service, NotificationTemplate

            for contact in contacts:
                logger.info(f"向 {contact.name}({contact.phone}) 发送紧急通知")
                await notification_service.send_notification(
                    user_id=alert.user_id,
                    template=NotificationTemplate.EMERGENCY,
                    alert=alert,
                    contact=contact,
                    message=message
                )
        except Exception as e:
            logger.error(f"发送紧急通知失败: {e}")

    def _get_type_text(self, emergency_type: EmergencyType) -> str:
        """获取紧急类型文本"""
        texts = {
            EmergencyType.SOS: '紧急求助',
            EmergencyType.FALL: '跌倒警报',
            EmergencyType.HEALTH: '健康异常警报',
            EmergencyType.INACTIVITY: '长时间无活动警报',
            EmergencyType.LOCATION: '位置异常警报',
            EmergencyType.DEVICE: '设备异常警报'
        }
        return texts.get(emergency_type, '紧急警报')

    async def trigger_sos(
        self,
        user_id: int,
        user_name: str,
        description: str = '用户按下紧急求助按钮'
    ) -> EmergencyAlert:
        """触发SOS求助"""
        return await self.create_alert(
            user_id=user_id,
            user_name=user_name,
            emergency_type=EmergencyType.SOS,
            level=EmergencyLevel.CRITICAL,
            description=description
        )

    async def trigger_fall_alert(
        self,
        user_id: int,
        user_name: str,
        confidence: float = 0.8
    ) -> EmergencyAlert:
        """触发跌倒警报"""
        level = EmergencyLevel.CRITICAL if confidence > 0.9 else EmergencyLevel.HIGH

        return await self.create_alert(
            user_id=user_id,
            user_name=user_name,
            emergency_type=EmergencyType.FALL,
            level=level,
            description=f"检测到可能跌倒（置信度: {confidence:.0%}）",
            metadata={'confidence': confidence}
        )

    async def trigger_health_alert(
        self,
        user_id: int,
        user_name: str,
        health_data: Dict[str, Any]
    ) -> EmergencyAlert:
        """触发健康异常警报"""
        # 根据健康数据判断级别
        level = EmergencyLevel.HIGH

        if health_data.get('systolic', 0) > 180 or health_data.get('diastolic', 0) > 110:
            level = EmergencyLevel.CRITICAL

        description = self._build_health_description(health_data)

        return await self.create_alert(
            user_id=user_id,
            user_name=user_name,
            emergency_type=EmergencyType.HEALTH,
            level=level,
            description=description,
            metadata={"health_data": health_data}
        )

    def _build_health_description(self, health_data: Dict) -> str:
        """构建健康异常描述"""
        parts = []

        if 'systolic' in health_data and 'diastolic' in health_data:
            parts.append(f"血压 {health_data['systolic']}/{health_data['diastolic']} mmHg")

        if 'heart_rate' in health_data:
            parts.append(f"心率 {health_data['heart_rate']} bpm")

        if 'blood_glucose' in health_data:
            parts.append(f"血糖 {health_data['blood_glucose']} mmol/L")

        return '健康指标异常：' + '，'.join(parts) if parts else '健康指标异常'

    async def trigger_inactivity_alert(
        self,
        user_id: int,
        user_name: str,
        inactive_hours: int
    ) -> EmergencyAlert:
        """触发不活跃警报"""
        level = EmergencyLevel.HIGH if inactive_hours >= 24 else EmergencyLevel.MEDIUM

        return await self.create_alert(
            user_id=user_id,
            user_name=user_name,
            emergency_type=EmergencyType.INACTIVITY,
            level=level,
            description=f"超过 {inactive_hours} 小时无任何活动记录",
            metadata={"inactive_hours": inactive_hours}
        )

    def acknowledge_alert(
        self,
        alert_id: str,
        handler: str
    ) -> Optional[EmergencyAlert]:
        """确认警报"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        alert.handled_by = handler
        alert.notes.append(f"{datetime.now().strftime('%H:%M')} - {handler} 已确认警报")

        logger.info(f"警报 {alert_id} 已被 {handler} 确认")
        return alert

    def resolve_alert(
        self,
        alert_id: str,
        handler: str,
        resolution: str
    ) -> Optional[EmergencyAlert]:
        """解决警报"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        alert.handled_by = handler
        alert.notes.append(f"{datetime.now().strftime('%H:%M')} - {handler}: {resolution}")

        logger.info(f'警报 {alert_id} 已解决: {resolution}')
        return alert

    def cancel_alert(
        self,
        alert_id: str,
        reason: str = '用户取消'
    ) -> Optional[EmergencyAlert]:
        """取消警报"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.CANCELLED
        alert.resolved_at = datetime.now()
        alert.notes.append(f"{datetime.now().strftime('%H:%M')} - 已取消: {reason}")

        logger.info(f'警报 {alert_id} 已取消: {reason}')
        return alert

    def mark_false_alarm(
        self,
        alert_id: str,
        reason: str = '误报'
    ) -> Optional[EmergencyAlert]:
        """标记为误报"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.FALSE_ALARM
        alert.resolved_at = datetime.now()
        alert.notes.append(f"{datetime.now().strftime('%H:%M')} - 标记为误报: {reason}")

        logger.info(f"警报 {alert_id} 标记为误报: {reason}")
        return alert

    def get_alert(self, alert_id: str) -> Optional[EmergencyAlert]:
        """获取警报详情"""
        return self.alerts.get(alert_id)

    def get_user_alerts(
        self,
        user_id: int,
        status: Optional[AlertStatus] = None,
        limit: int = 20
    ) -> List[EmergencyAlert]:
        """获取用户的警报列表"""
        alert_ids = self.user_alerts.get(user_id, [])
        alerts = [self.alerts[aid] for aid in alert_ids if aid in self.alerts]

        if status:
            alerts = [a for a in alerts if a.status == status]

        # 按时间倒序
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        return alerts[:limit]

    def get_active_alerts(self, user_id: Optional[int] = None) -> List[EmergencyAlert]:
        """获取活跃警报"""
        active_statuses = {AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, AlertStatus.HANDLING}

        if user_id:
            alerts = self.get_user_alerts(user_id)
        else:
            alerts = list(self.alerts.values())

        return [a for a in alerts if a.status in active_statuses]

    def get_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取警报统计"""
        cutoff = datetime.now() - timedelta(days=days)
        alerts = [
            a for a in self.get_user_alerts(user_id, limit=1000)
            if a.created_at >= cutoff
        ]

        type_counts = {}
        level_counts = {}
        status_counts = {}

        for alert in alerts:
            type_counts[alert.emergency_type.value] = type_counts.get(alert.emergency_type.value, 0) + 1
            level_counts[alert.level.value] = level_counts.get(alert.level.value, 0) + 1
            status_counts[alert.status.value] = status_counts.get(alert.status.value, 0) + 1

        false_alarm_rate = (
            status_counts.get("false_alarm", 0) / len(alerts) * 100
            if alerts else 0
        )

        return {
            "total_alerts": len(alerts),
            'days': days,
            'by_type': type_counts,
            'by_level': level_counts,
            'by_status': status_counts,
            "false_alarm_rate": round(false_alarm_rate, 2),
            "active_count": len([a for a in alerts if a.status == AlertStatus.ACTIVE])
        }


# ==================== 安全围栏服务 ====================

class GeofenceService:
    """地理围栏服务"""

    def __init__(self):
        self.user_fences: Dict[int, List[Dict]] = {}  # 用户的围栏配置

    def add_fence(
        self,
        user_id: int,
        name: str,
        center_lat: float,
        center_lng: float,
        radius: int,  # 米
        fence_type: str = 'home'  # home/hospital/other
    ) -> Dict:
        """添加地理围栏"""
        fence = {
            'fence_id': f"fence_{user_id}_{len(self.user_fences.get(user_id, []))}",
            'name': name,
            'center': {'lat': center_lat, 'lng': center_lng},
            'radius': radius,
            'type': fence_type,
            'enabled': True
        }

        if user_id not in self.user_fences:
            self.user_fences[user_id] = []
        self.user_fences[user_id].append(fence)

        logger.info(f"用户 {user_id} 添加围栏: {name}")
        return fence

    def check_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """检查位置是否在围栏内"""
        fences = self.user_fences.get(user_id, [])
        results = []

        for fence in fences:
            if not fence.get('enabled'):
                continue

            distance = self._calculate_distance(
                latitude, longitude,
                fence['center']['lat'], fence['center']['lng']
            )

            inside = distance <= fence['radius']
            results.append({
                'fence_id': fence['fence_id'],
                'name': fence['name'],
                'inside': inside,
                'distance': round(distance)
            })

        all_outside = all(not r['inside'] for r in results) if results else False

        return {
            'fences': results,
            "all_outside": all_outside,
            "alert_needed": all_outside and len(results) > 0
        }

    def _calculate_distance(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """计算两点间距离（米）- 简化计算"""
        import math

        R = 6371000  # 地球半径（米）

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c


# 全局服务实例
emergency_service = EmergencyService()
geofence_service = GeofenceService()
