"""
API路由 - 视频通话
基于WebRTC的视频通话信令服务
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import json

router = APIRouter(prefix="/api/video", tags=["视频通话"])


class CallRequest(BaseModel):
    """发起通话请求"""
    caller_id: str
    callee_id: str
    caller_name: str


class CallResponse(BaseModel):
    """通话响应"""
    call_id: str
    action: str  # accept/reject


# 活跃通话存储
active_calls: Dict[str, dict] = {}
# WebSocket连接存储
connections: Dict[str, WebSocket] = {}
# 待接听通话
pending_calls: Dict[str, dict] = {}


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f'用户 {user_id} 已连接视频通话服务')

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"用户 {user_id} 已断开视频通话服务")

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
            return True
        return False

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections


manager = ConnectionManager()


@router.post("/call/initiate")
async def initiate_call(request: CallRequest):
    """发起视频通话"""
    call_id = str(uuid.uuid4())

    # 检查被叫方是否在线
    if not manager.is_online(request.callee_id):
        return {
            'success': False,
            'error': '对方不在线',
            'call_id': None
        }

    # 创建通话记录
    call_info = {
        'call_id': call_id,
        'caller_id': request.caller_id,
        "callee_id": request.callee_id,
        "caller_name": request.caller_name,
        'status': 'ringing',
        'started_at': datetime.now().isoformat()
    }

    pending_calls[call_id] = call_info

    # 通知被叫方
    await manager.send_message(request.callee_id, {
        'type': 'incoming_call',
        'call_id': call_id,
        "caller_id": request.caller_id,
        "caller_name": request.caller_name
    })

    return {
        'success': True,
        'call_id': call_id,
        'message': "正在呼叫对方"
    }


@router.post("/call/respond")
async def respond_to_call(response: CallResponse):
    """响应通话请求"""
    call_id = response.call_id

    if call_id not in pending_calls:
        raise HTTPException(status_code=404, detail='通话不存在')

    call_info = pending_calls[call_id]

    if response.action == 'accept':
        # 接听通话
        call_info['status'] = 'connected'
        active_calls[call_id] = call_info
        del pending_calls[call_id]

        # 通知主叫方
        await manager.send_message(call_info['caller_id'], {
            "type": "call_accepted",
            'call_id': call_id
        })

        return {'success': True, 'message': '通话已接通'}

    elif response.action == 'reject':
        # 拒绝通话
        del pending_calls[call_id]

        # 通知主叫方
        await manager.send_message(call_info['caller_id'], {
            "type": "call_rejected",
            'call_id': call_id
        })

        return {'success': True, 'message': '已拒绝通话'}

    else:
        raise HTTPException(status_code=400, detail="无效的操作")


@router.post("/call/end/{call_id}")
async def end_call(call_id: str, user_id: str):
    """结束通话"""
    call_info = active_calls.get(call_id) or pending_calls.get(call_id)

    if not call_info:
        raise HTTPException(status_code=404, detail='通话不存在')

    # 通知双方
    other_user = call_info['callee_id'] if call_info['caller_id'] == user_id else call_info['caller_id']
    await manager.send_message(other_user, {
        'type': 'call_ended',
        'call_id': call_id,
        'ended_by': user_id
    })

    # 清理通话记录
    if call_id in active_calls:
        del active_calls[call_id]
    if call_id in pending_calls:
        del pending_calls[call_id]

    return {'success': True, 'message': "通话已结束"}


@router.get("/status/{user_id}")
async def get_user_status(user_id: str):
    """获取用户在线状态"""
    return {
        'user_id': user_id,
        'is_online': manager.is_online(user_id)
    }


@router.websocket("/ws/{user_id}")
async def video_websocket(websocket: WebSocket, user_id: str):
    """视频通话WebSocket连接"""
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == 'offer':
                # 转发SDP offer
                target_id = data.get('target_id')
                await manager.send_message(target_id, {
                    'type': 'offer',
                    'call_id': data.get('call_id'),
                    'sdp': data.get('sdp'),
                    'from_id': user_id
                })

            elif message_type == 'answer':
                # 转发SDP answer
                target_id = data.get('target_id')
                await manager.send_message(target_id, {
                    'type': 'answer',
                    'call_id': data.get('call_id'),
                    'sdp': data.get('sdp'),
                    "from_id": user_id
                })

            elif message_type == "ice_candidate":
                # 转发ICE候选
                target_id = data.get("target_id")
                await manager.send_message(target_id, {
                    'type': "ice_candidate",
                    'call_id': data.get('call_id'),
                    'candidate': data.get('candidate'),
                    'from_id': user_id
                })

            elif message_type == 'ping':
                # 心跳响应
                await websocket.send_json({'type': 'pong'})

    except WebSocketDisconnect:
        manager.disconnect(user_id)

        # 结束该用户参与的所有通话
        for call_id, call_info in list(active_calls.items()):
            if user_id in [call_info['caller_id'], call_info['callee_id']]:
                other_user = call_info['callee_id'] if call_info['caller_id'] == user_id else call_info['caller_id']
                await manager.send_message(other_user, {
                    'type': 'call_ended',
                    'call_id': call_id,
                    'reason': "对方已断开连接"
                })
                del active_calls[call_id]
