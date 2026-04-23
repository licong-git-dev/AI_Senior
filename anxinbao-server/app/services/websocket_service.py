"""
WebSocket实时通信服务
提供消息推送、状态同步、实时通知等功能
"""
import logging
import json
import asyncio
from typing import Optional, Dict, List, Any, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import secrets

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class MessageType(Enum):
    """消息类型"""
    # 系统消息
    CONNECTED = "connected"  # 连接成功
    DISCONNECTED = "disconnected"  # 断开连接
    HEARTBEAT = 'heartbeat'  # 心跳
    ERROR = "error"  # 错误

    # 通知消息
    NOTIFICATION = "notification"  # 通知
    ALERT = 'alert'  # 警报
    REMINDER = "reminder"  # 提醒

    # 状态更新
    STATUS_UPDATE = "status_update"  # 状态更新
    HEALTH_UPDATE = "health_update"  # 健康数据更新
    LOCATION_UPDATE = "location_update"  # 位置更新
    DEVICE_STATUS = "device_status"  # 设备状态

    # 聊天消息
    CHAT_MESSAGE = "chat_message"  # 聊天消息
    VOICE_MESSAGE = "voice_message"  # 语音消息

    # 家庭互动
    FAMILY_MESSAGE = "family_message"  # 家庭消息
    SOS_ALERT = "sos_alert"  # 紧急求助
    CARE_REMINDER = "care_reminder"  # 关怀提醒

    # 活动事件
    ACTIVITY_START = "activity_start"  # 活动开始
    ACTIVITY_END = "activity_end"  # 活动结束
    MEDICATION_REMINDER = "medication_reminder"  # 服药提醒


class ConnectionState(Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = 'connected'
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class UserRole(Enum):
    """用户角色"""
    ELDERLY = 'elderly'  # 老人
    FAMILY = 'family'  # 家属
    CAREGIVER = 'caregiver'  # 护理员
    ADMIN = "admin"  # 管理员


# ==================== 数据模型 ====================

@dataclass
class WebSocketMessage:
    """WebSocket消息"""
    message_id: str
    message_type: MessageType
    data: Dict[str, Any]
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    room_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        return json.dumps({
            'message_id': self.message_id,
            'type': self.message_type.value,
            'data': self.data,
            'sender_id': self.sender_id,
            "receiver_id": self.receiver_id,
            'room_id': self.room_id,
            'timestamp': self.timestamp.isoformat()
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        data = json.loads(json_str)
        return cls(
            message_id=data.get('message_id', secrets.token_hex(8)),
            message_type=MessageType(data['type']),
            data=data.get('data', {}),
            sender_id=data.get('sender_id'),
            receiver_id=data.get("receiver_id"),
            room_id=data.get('room_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now()
        )


@dataclass
class Connection:
    """WebSocket连接"""
    connection_id: str
    user_id: int
    user_role: UserRole
    websocket: Any  # WebSocket对象
    state: ConnectionState = ConnectionState.CONNECTED
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            'user_id': self.user_id,
            'user_role': self.user_role.value,
            'state': self.state.value,
            'rooms': list(self.rooms),
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat()
        }


@dataclass
class Room:
    """聊天房间"""
    room_id: str
    name: str
    room_type: str  # family/group/broadcast
    members: Set[int] = field(default_factory=set)
    created_by: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'room_id': self.room_id,
            'name': self.name,
            'room_type': self.room_type,
            'members': list(self.members),
            'created_at': self.created_at.isoformat()
        }


# ==================== 连接管理器 ====================

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 连接存储
        self.connections: Dict[str, Connection] = {}
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)

        # 房间管理
        self.rooms: Dict[str, Room] = {}
        self.room_connections: Dict[str, Set[str]] = defaultdict(set)

        # 消息历史
        self.message_history: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.max_history = 100

        # 事件处理器
        self.event_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)

        # 初始化默认房间
        self._init_default_rooms()

    def _init_default_rooms(self):
        """初始化默认房间"""
        # 系统广播房间
        self.rooms['broadcast'] = Room(
            room_id='broadcast',
            name='系统广播',
            room_type='broadcast'
        )

        # 紧急通知房间
        self.rooms['emergency'] = Room(
            room_id='emergency',
            name='紧急通知',
            room_type="broadcast"
        )

    async def connect(
        self,
        websocket: Any,
        user_id: int,
        user_role: UserRole = UserRole.ELDERLY,
        metadata: Dict[str, Any] = None
    ) -> Connection:
        """建立连接"""
        connection_id = f"conn_{user_id}_{secrets.token_hex(4)}"

        connection = Connection(
            connection_id=connection_id,
            user_id=user_id,
            user_role=user_role,
            websocket=websocket,
            metadata=metadata or {}
        )

        self.connections[connection_id] = connection
        self.user_connections[user_id].add(connection_id)

        # 加入默认房间
        await self.join_room(connection_id, "broadcast")

        # 发送连接成功消息
        await self.send_to_connection(connection_id, WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.CONNECTED,
            data={
                "connection_id": connection_id,
                'user_id': user_id,
                'message': '连接成功'
            }
        ))

        logger.info(f"WebSocket连接建立: {connection_id}, 用户: {user_id}")
        return connection

    async def disconnect(self, connection_id: str):
        """断开连接"""
        connection = self.connections.get(connection_id)
        if not connection:
            return

        # 离开所有房间
        for room_id in list(connection.rooms):
            await self.leave_room(connection_id, room_id)

        # 清理连接
        self.user_connections[connection.user_id].discard(connection_id)
        del self.connections[connection_id]

        logger.info(f"WebSocket连接断开: {connection_id}")

    async def send_to_connection(
        self,
        connection_id: str,
        message: WebSocketMessage
    ) -> bool:
        """发送消息到指定连接"""
        connection = self.connections.get(connection_id)
        if not connection or connection.state != ConnectionState.CONNECTED:
            return False

        try:
            await connection.websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    async def send_to_user(
        self,
        user_id: int,
        message: WebSocketMessage
    ) -> int:
        """发送消息到用户的所有连接"""
        connection_ids = self.user_connections.get(user_id, set())
        success_count = 0

        for conn_id in connection_ids:
            if await self.send_to_connection(conn_id, message):
                success_count += 1

        return success_count

    async def send_to_room(
        self,
        room_id: str,
        message: WebSocketMessage,
        exclude_sender: bool = True
    ) -> int:
        """发送消息到房间"""
        room = self.rooms.get(room_id)
        if not room:
            return 0

        connection_ids = self.room_connections.get(room_id, set())
        success_count = 0

        for conn_id in connection_ids:
            connection = self.connections.get(conn_id)
            if not connection:
                continue

            # 排除发送者
            if exclude_sender and connection.user_id == message.sender_id:
                continue

            if await self.send_to_connection(conn_id, message):
                success_count += 1

        # 保存消息历史
        self._save_message_history(room_id, message)

        return success_count

    async def broadcast(
        self,
        message: WebSocketMessage,
        role_filter: UserRole = None
    ) -> int:
        """广播消息到所有连接"""
        success_count = 0

        for conn_id, connection in self.connections.items():
            if role_filter and connection.user_role != role_filter:
                continue

            if await self.send_to_connection(conn_id, message):
                success_count += 1

        return success_count

    # ==================== 房间管理 ====================

    def create_room(
        self,
        room_id: str,
        name: str,
        room_type: str,
        created_by: int = None,
        members: Set[int] = None
    ) -> Room:
        """创建房间"""
        room = Room(
            room_id=room_id,
            name=name,
            room_type=room_type,
            created_by=created_by,
            members=members or set()
        )
        self.rooms[room_id] = room
        return room

    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """加入房间"""
        connection = self.connections.get(connection_id)
        room = self.rooms.get(room_id)

        if not connection or not room:
            return False

        connection.rooms.add(room_id)
        room.members.add(connection.user_id)
        self.room_connections[room_id].add(connection_id)

        return True

    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """离开房间"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        connection.rooms.discard(room_id)
        self.room_connections[room_id].discard(connection_id)

        # 检查房间是否还有此用户的其他连接
        has_other_connections = any(
            self.connections.get(cid) and self.connections[cid].user_id == connection.user_id
            for cid in self.room_connections[room_id]
        )

        if not has_other_connections:
            room = self.rooms.get(room_id)
            if room:
                room.members.discard(connection.user_id)

        return True

    def get_family_room_id(self, user_id: int) -> str:
        """获取家庭房间ID"""
        return f"family_{user_id}"

    async def create_family_room(self, elderly_id: int, family_members: List[int]) -> Room:
        """创建家庭房间"""
        room_id = self.get_family_room_id(elderly_id)
        members = set(family_members + [elderly_id])

        room = self.create_room(
            room_id=room_id,
            name='家庭群',
            room_type="family",
            created_by=elderly_id,
            members=members
        )

        # 自动将在线成员加入房间
        for user_id in members:
            for conn_id in self.user_connections.get(user_id, set()):
                await self.join_room(conn_id, room_id)

        return room

    # ==================== 心跳管理 ====================

    async def handle_heartbeat(self, connection_id: str) -> bool:
        """处理心跳"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        connection.last_heartbeat = datetime.now()

        # 发送心跳响应
        await self.send_to_connection(connection_id, WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.HEARTBEAT,
            data={'status': 'ok', "timestamp": datetime.now().isoformat()}
        ))

        return True

    async def check_connections(self, timeout_seconds: int = 60):
        """检查连接超时"""
        now = datetime.now()
        timeout_connections = []

        for conn_id, connection in self.connections.items():
            if (now - connection.last_heartbeat).total_seconds() > timeout_seconds:
                timeout_connections.append(conn_id)

        for conn_id in timeout_connections:
            logger.warning(f"连接超时断开: {conn_id}")
            await self.disconnect(conn_id)

    # ==================== 消息历史 ====================

    def _save_message_history(self, room_id: str, message: WebSocketMessage):
        """保存消息历史"""
        history = self.message_history[room_id]
        history.append(message)

        # 限制历史消息数量
        if len(history) > self.max_history:
            self.message_history[room_id] = history[-self.max_history:]

    def get_message_history(
        self,
        room_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取消息历史"""
        history = self.message_history.get(room_id, [])
        messages = history[-limit:] if len(history) > limit else history
        return [json.loads(m.to_json()) for m in messages]

    # ==================== 事件处理 ====================

    def on(self, message_type: MessageType, handler: Callable):
        """注册事件处理器"""
        self.event_handlers[message_type].append(handler)

    async def emit(self, message: WebSocketMessage):
        """触发事件"""
        handlers = self.event_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"事件处理器错误: {e}")

    # ==================== 状态查询 ====================

    def get_user_status(self, user_id: int) -> Dict[str, Any]:
        """获取用户在线状态"""
        connections = self.user_connections.get(user_id, set())
        is_online = len(connections) > 0

        return {
            'user_id': user_id,
            'is_online': is_online,
            "connection_count": len(connections),
            "connections": [
                self.connections[cid].to_dict()
                for cid in connections
                if cid in self.connections
            ]
        }

    def get_online_users(self, role: UserRole = None) -> List[int]:
        """获取在线用户列表"""
        online_users = []

        for user_id, conn_ids in self.user_connections.items():
            if not conn_ids:
                continue

            if role:
                # 检查是否有指定角色的连接
                has_role = any(
                    self.connections.get(cid) and self.connections[cid].user_role == role
                    for cid in conn_ids
                )
                if has_role:
                    online_users.append(user_id)
            else:
                online_users.append(user_id)

        return online_users

    def get_statistics(self) -> Dict[str, Any]:
        """获取连接统计"""
        role_counts = defaultdict(int)
        for connection in self.connections.values():
            role_counts[connection.user_role.value] += 1

        return {
            "total_connections": len(self.connections),
            "total_users": len(self.user_connections),
            "total_rooms": len(self.rooms),
            'by_role': dict(role_counts)
        }


# ==================== 通知服务 ====================

class NotificationService:
    """实时通知服务"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def send_notification(
        self,
        user_id: int,
        title: str,
        content: str,
        notification_type: str = 'info',
        data: Dict[str, Any] = None
    ) -> int:
        """发送通知"""
        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.NOTIFICATION,
            data={
                'title': title,
                'content': content,
                "notification_type": notification_type,
                'extra': data or {}
            },
            receiver_id=user_id
        )

        return await self.manager.send_to_user(user_id, message)

    async def send_alert(
        self,
        user_id: int,
        title: str,
        content: str,
        level: str = 'warning',
        action_url: str = None
    ) -> int:
        """发送警报"""
        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.ALERT,
            data={
                'title': title,
                'content': content,
                'level': level,
                'action_url': action_url
            },
            receiver_id=user_id
        )

        return await self.manager.send_to_user(user_id, message)

    async def send_reminder(
        self,
        user_id: int,
        reminder_type: str,
        title: str,
        content: str,
        scheduled_time: datetime = None
    ) -> int:
        """发送提醒"""
        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.REMINDER,
            data={
                "reminder_type": reminder_type,
                'title': title,
                'content': content,
                "scheduled_time": scheduled_time.isoformat() if scheduled_time else None
            },
            receiver_id=user_id
        )

        return await self.manager.send_to_user(user_id, message)

    async def send_sos_alert(
        self,
        elderly_id: int,
        elderly_name: str,
        location: str = None,
        emergency_type: str = "general"
    ) -> int:
        """发送紧急求助警报到家庭成员"""
        room_id = self.manager.get_family_room_id(elderly_id)

        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.SOS_ALERT,
            data={
                'elderly_id': elderly_id,
                "elderly_name": elderly_name,
                'location': location,
                "emergency_type": emergency_type,
                'alert_message': f'{elderly_name}发起了紧急求助！'
            },
            sender_id=elderly_id,
            room_id=room_id
        )

        return await self.manager.send_to_room(room_id, message, exclude_sender=False)

    async def send_health_update(
        self,
        user_id: int,
        health_type: str,
        value: Any,
        unit: str = None,
        status: str = "normal"
    ) -> int:
        """发送健康数据更新"""
        room_id = self.manager.get_family_room_id(user_id)

        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.HEALTH_UPDATE,
            data={
                'user_id': user_id,
                "health_type": health_type,
                'value': value,
                'unit': unit,
                'status': status,
                "measured_at": datetime.now().isoformat()
            },
            sender_id=user_id,
            room_id=room_id
        )

        return await self.manager.send_to_room(room_id, message)

    async def send_medication_reminder(
        self,
        user_id: int,
        medication_name: str,
        dosage: str,
        scheduled_time: datetime
    ) -> int:
        """发送服药提醒"""
        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.MEDICATION_REMINDER,
            data={
                "medication_name": medication_name,
                'dosage': dosage,
                "scheduled_time": scheduled_time.isoformat(),
                'message': f"该吃药了：{medication_name} {dosage}"
            },
            receiver_id=user_id
        )

        return await self.manager.send_to_user(user_id, message)


# ==================== 全局实例 ====================

# 连接管理器
ws_manager = ConnectionManager()

# 通知服务
notification_service = NotificationService(ws_manager)
