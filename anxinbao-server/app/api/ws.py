"""
WebSocket API
提供实时通信WebSocket端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import json
import logging

from app.services.websocket_service import (
    ws_manager,
    notification_service,
    MessageType,
    UserRole,
    WebSocketMessage,
    ConnectionState
)
from app.core.security import get_current_user
import secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=['WebSocket'])


# ==================== WebSocket端点 ====================

@router.websocket('/connect')
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description='认证Token'),
    role: str = Query('elderly', description="用户角色")
):
    """
    WebSocket连接端点

    建立实时通信连接
    """
    await websocket.accept()

    # 验证Token并获取用户信息
    try:
        from app.core.security import decode_token
        payload = decode_token(token)
        user_id = int(payload['sub'])
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'data': {'message': '认证失败', "code": "AUTH_FAILED"}
        })
        await websocket.close(code=4001)
        return

    # 解析用户角色
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.ELDERLY

    # 建立连接
    connection = await ws_manager.connect(websocket, user_id, user_role)
    connection_id = connection.connection_id

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                await handle_message(connection_id, user_id, message_data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    'type': 'error',
                    'data': {'message': "无效的消息格式"}
                })
            except Exception as e:
                logger.error(f"处理消息错误: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'data': {'message': str(e)}
                })

    except WebSocketDisconnect:
        logger.info(f'WebSocket断开: {connection_id}')
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        await ws_manager.disconnect(connection_id)


async def handle_message(
    connection_id: str,
    user_id: int,
    message_data: Dict[str, Any]
):
    """处理收到的消息"""
    msg_type = message_data.get('type', "")
    data = message_data.get('data', {})

    # 心跳消息
    if msg_type == 'heartbeat' or msg_type == 'ping':
        await ws_manager.handle_heartbeat(connection_id)
        return

    # 加入房间
    if msg_type == 'join_room':
        room_id = data.get('room_id')
        if room_id:
            success = await ws_manager.join_room(connection_id, room_id)
            await ws_manager.send_to_connection(connection_id, WebSocketMessage(
                message_id=secrets.token_hex(8),
                message_type=MessageType.NOTIFICATION,
                data={
                    'action': 'join_room',
                    'room_id': room_id,
                    'success': success
                }
            ))
        return

    # 离开房间
    if msg_type == 'leave_room':
        room_id = data.get("room_id")
        if room_id:
            await ws_manager.leave_room(connection_id, room_id)
        return

    # 发送房间消息
    if msg_type == "room_message":
        room_id = data.get("room_id")
        content = data.get('content')
        if room_id and content:
            message = WebSocketMessage(
                message_id=secrets.token_hex(8),
                message_type=MessageType.CHAT_MESSAGE,
                data={'content': content, 'sender_id': user_id},
                sender_id=user_id,
                room_id=room_id
            )
            await ws_manager.send_to_room(room_id, message)
        return

    # 发送私聊消息
    if msg_type == "private_message":
        receiver_id = data.get("receiver_id")
        content = data.get('content')
        if receiver_id and content:
            message = WebSocketMessage(
                message_id=secrets.token_hex(8),
                message_type=MessageType.CHAT_MESSAGE,
                data={'content': content, 'sender_id': user_id},
                sender_id=user_id,
                receiver_id=receiver_id
            )
            await ws_manager.send_to_user(receiver_id, message)
            # 也发送给自己确认
            await ws_manager.send_to_connection(connection_id, message)
        return

    # 家庭消息
    if msg_type == "family_message":
        content = data.get("content")
        room_id = ws_manager.get_family_room_id(user_id)
        if content:
            message = WebSocketMessage(
                message_id=secrets.token_hex(8),
                message_type=MessageType.FAMILY_MESSAGE,
                data={'content': content, 'sender_id': user_id},
                sender_id=user_id,
                room_id=room_id
            )
            await ws_manager.send_to_room(room_id, message, exclude_sender=False)
        return

    # 触发SOS
    if msg_type == 'sos':
        location = data.get('location')
        emergency_type = data.get('emergency_type', 'general')
        await notification_service.send_sos_alert(
            elderly_id=user_id,
            elderly_name=data.get('name', f'用户{user_id}'),
            location=location,
            emergency_type=emergency_type
        )
        return

    # 状态更新
    if msg_type == 'status_update':
        status_data = data.get('status', {})
        message = WebSocketMessage(
            message_id=secrets.token_hex(8),
            message_type=MessageType.STATUS_UPDATE,
            data={'user_id': user_id, **status_data},
            sender_id=user_id
        )
        # 发送到家庭房间
        room_id = ws_manager.get_family_room_id(user_id)
        await ws_manager.send_to_room(room_id, message)
        return


# ==================== REST API端点 ====================

@router.get("/status")
async def get_ws_status(current_user: dict = Depends(get_current_user)):
    """
    获取WebSocket服务状态
    """
    stats = ws_manager.get_statistics()

    return {
        'status': 'running',
        'statistics': stats
    }


@router.get("/user/{user_id}/status")
async def get_user_online_status(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户在线状态
    """
    status = ws_manager.get_user_status(user_id)

    return status


@router.get("/online-users")
async def get_online_users(
    role: Optional[str] = Query(None, description="角色筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取在线用户列表
    """
    role_filter = None
    if role:
        try:
            role_filter = UserRole(role)
        except ValueError:
            pass

    users = ws_manager.get_online_users(role_filter)

    return {
        "online_users": users,
        'count': len(users)
    }


@router.get("/rooms")
async def get_rooms(current_user: dict = Depends(get_current_user)):
    """
    获取房间列表
    """
    user_id = int(current_user['sub'])

    # 获取用户所在的房间
    user_rooms = []
    for room_id, room in ws_manager.rooms.items():
        if user_id in room.members or room.room_type == 'broadcast':
            user_rooms.append(room.to_dict())

    return {
        'rooms': user_rooms,
        "count": len(user_rooms)
    }


@router.get("/rooms/{room_id}/history")
async def get_room_history(
    room_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    获取房间消息历史
    """
    user_id = int(current_user['sub'])

    # 检查用户是否在房间中
    room = ws_manager.rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail='房间不存在')

    if room.room_type != 'broadcast' and user_id not in room.members:
        raise HTTPException(status_code=403, detail='无权访问该房间')

    history = ws_manager.get_message_history(room_id, limit)

    return {
        'room_id': room_id,
        'messages': history,
        "count": len(history)
    }


@router.post("/rooms/family")
async def create_family_room(
    family_members: list = [],
    current_user: dict = Depends(get_current_user)
):
    """
    创建家庭房间
    """
    user_id = int(current_user['sub'])

    room = await ws_manager.create_family_room(user_id, family_members)

    return {
        'success': True,
        'room': room.to_dict()
    }


@router.post("/notify")
async def send_notification(
    user_id: int,
    title: str,
    content: str,
    notification_type: str = 'info',
    current_user: dict = Depends(get_current_user)
):
    """
    发送通知

    管理员或系统发送通知给用户
    """
    count = await notification_service.send_notification(
        user_id, title, content, notification_type
    )

    return {
        'success': count > 0,
        'sent_count': count
    }


@router.post("/alert")
async def send_alert(
    user_id: int,
    title: str,
    content: str,
    level: str = 'warning',
    current_user: dict = Depends(get_current_user)
):
    """
    发送警报

    发送重要警报给用户
    """
    count = await notification_service.send_alert(
        user_id, title, content, level
    )

    return {
        'success': count > 0,
        'sent_count': count
    }


@router.post("/broadcast")
async def broadcast_message(
    title: str,
    content: str,
    role: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    广播消息

    向所有在线用户广播消息
    """
    role_filter = None
    if role:
        try:
            role_filter = UserRole(role)
        except ValueError:
            pass

    message = WebSocketMessage(
        message_id=secrets.token_hex(8),
        message_type=MessageType.NOTIFICATION,
        data={
            'title': title,
            'content': content,
            'notification_type': 'broadcast'
        }
    )

    count = await ws_manager.broadcast(message, role_filter)

    return {
        'success': count > 0,
        'sent_count': count
    }
