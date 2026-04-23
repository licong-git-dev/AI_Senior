# 安心宝云端服务 API 文档

## 概述

安心宝云端服务提供RESTful API接口，支持老年人健康陪聊、语音交互、健康监测等功能。

**Base URL:** `https://api.anxinbao.com` (生产) / `http://localhost:8000` (开发)

**API版本:** v1.0

**认证方式:** JWT Bearer Token

## 认证

所有需要认证的接口都需要在请求头中携带 `Authorization` 字段：

```
Authorization: Bearer <access_token>
```

### 获取令牌

#### 用户登录

```http
POST /api/auth/login
```

**请求体：**
```json
{
    "username": "13800138000",
    "password": "your_password"
}
```

**响应 (200 OK)：**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": "1",
        "username": "13800138000",
        "role": "elder"
    }
}
```

**错误响应 (401 Unauthorized)：**
```json
{
    "detail": "用户名或密码错误"
}
```

---

#### 设备登录

```http
POST /api/auth/device/login
```

**请求体：**
```json
{
    "device_id": "speaker-001",
    "device_secret": "device_secret_key"
}
```

**响应 (200 OK)：**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "device": {
        "id": "1",
        "device_id": "speaker-001",
        "device_type": "speaker",
        "user_id": 1
    }
}
```

---

#### 刷新令牌

```http
POST /api/auth/refresh
```

**请求体：**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应 (200 OK)：**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

#### 用户注册

```http
POST /api/auth/register
```

**请求体：**
```json
{
    "username": "13800138000",
    "password": "SecurePassword123",
    "role": "family",
    "name": "张三"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（手机号） |
| password | string | 是 | 密码（至少8位） |
| role | string | 是 | 角色：elder/family/admin |
| name | string | 是 | 姓名 |

**响应 (200 OK)：**
```json
{
    "success": true,
    "user_id": "123",
    "message": "注册成功"
}
```

---

#### 登出

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "message": "已成功登出"
}
```

---

#### 修改密码

```http
POST /api/auth/change-password
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "old_password": "OldPassword123",
    "new_password": "NewPassword456"
}
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "message": "密码修改成功"
}
```

---

## 对话接口

### 发送消息

```http
POST /api/chat/message
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "message": "我今天头有点晕",
    "session_id": "sess-abc123",
    "dialect": "mandarin"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 是 | 用户消息内容 |
| session_id | string | 否 | 会话ID，不传则创建新会话 |
| dialect | string | 否 | 方言：mandarin/wuhan/ezhou，默认mandarin |

**响应 (200 OK)：**
```json
{
    "reply": "别担心，头晕很常见，可能是休息不好。您最近睡眠怎么样？",
    "session_id": "sess-abc123",
    "message_id": "msg-xyz789",
    "risk_info": {
        "risk_score": 3,
        "risk_reason": "轻微头晕，建议休息",
        "need_notify": false,
        "category": "health",
        "emotion": {
            "type": "neutral",
            "intensity": 2,
            "keywords": ["头晕"]
        },
        "topics": ["健康", "症状"]
    },
    "food_therapy": {
        "name": "枸杞菊花茶",
        "ingredients": ["枸杞10颗", "菊花5朵"],
        "steps": "开水冲泡，焖5分钟",
        "effect": "清肝明目，缓解头晕"
    },
    "timestamp": "2025-12-24T10:30:00Z"
}
```

**风险评分说明：**

| 分数 | 级别 | 说明 | 是否通知家属 |
|------|------|------|-------------|
| 1-3 | 低 | 日常闲聊或轻微不适 | 否 |
| 4-6 | 中 | 需要关注 | 否 |
| 7-8 | 高 | 建议就医 | 是 |
| 9-10 | 紧急 | 疑似紧急情况 | 是（紧急） |

**情绪类型说明：**

| 类型 | 说明 |
|------|------|
| neutral | 中性/平静 |
| lonely | 孤独 |
| anxious | 焦虑 |
| sad | 悲伤 |
| happy | 开心 |

---

### 获取对话历史

```http
GET /api/chat/history
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 是 | 会话ID |
| limit | int | 否 | 返回条数，默认20 |
| offset | int | 否 | 偏移量，默认0 |

**响应 (200 OK)：**
```json
{
    "session_id": "sess-abc123",
    "messages": [
        {
            "id": "msg-001",
            "role": "user",
            "content": "你好",
            "timestamp": "2025-12-24T10:00:00Z"
        },
        {
            "id": "msg-002",
            "role": "assistant",
            "content": "您好！有什么可以帮您的？",
            "timestamp": "2025-12-24T10:00:05Z"
        }
    ],
    "total": 10,
    "has_more": false
}
```

---

### 清除对话历史

```http
DELETE /api/chat/history
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 是 | 会话ID |

**响应 (200 OK)：**
```json
{
    "success": true,
    "message": "对话历史已清除"
}
```

---

### 获取会话列表

```http
GET /api/chat/sessions
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
    "sessions": [
        {
            "session_id": "sess-abc123",
            "created_at": "2025-12-24T10:00:00Z",
            "last_message_at": "2025-12-24T10:30:00Z",
            "message_count": 15,
            "summary": "健康咨询 - 头晕"
        }
    ],
    "total": 5
}
```

---

## 语音接口

### 语音合成 (TTS)

```http
POST /api/voice/tts
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "text": "您好，今天感觉怎么样？",
    "voice": "xiaoyan",
    "speed": 50,
    "volume": 50
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要合成的文本 |
| voice | string | 否 | 发音人，默认xiaoyan |
| speed | int | 否 | 语速0-100，默认50 |
| volume | int | 否 | 音量0-100，默认50 |

**响应 (200 OK)：**
```
Content-Type: audio/wav
[二进制音频数据]
```

---

### 语音识别 (ASR)

```http
POST /api/voice/asr
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audio | file | 是 | 音频文件（WAV/PCM） |
| dialect | string | 否 | 方言：mandarin/wuhan/ezhou |

**响应 (200 OK)：**
```json
{
    "text": "我今天感觉不错",
    "confidence": 0.95,
    "dialect_detected": "mandarin"
}
```

---

## 通知接口

### 获取通知列表

```http
GET /api/notify/list
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | int | 否 | 老人ID（家属查看） |
| is_read | bool | 否 | 是否已读 |
| limit | int | 否 | 返回条数 |

**响应 (200 OK)：**
```json
{
    "notifications": [
        {
            "id": 1,
            "user_id": 1,
            "user_name": "王奶奶",
            "conversation_summary": "老人表示胸闷不适",
            "risk_score": 8,
            "risk_reason": "胸闷症状，建议及时就医",
            "is_read": false,
            "is_handled": false,
            "created_at": "2025-12-24T10:30:00Z"
        }
    ],
    "unread_count": 3,
    "total": 10
}
```

---

### 标记通知已读

```http
POST /api/notify/{notification_id}/read
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "message": "已标记为已读"
}
```

---

### 标记通知已处理

```http
POST /api/notify/{notification_id}/handle
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "action": "called_doctor",
    "notes": "已联系社区医生上门检查"
}
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "message": "已标记为已处理"
}
```

---

## 用户管理接口

### 获取当前用户信息

```http
GET /api/users/me
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
    "id": 1,
    "name": "王奶奶",
    "username": "13800138000",
    "role": "elder",
    "dialect": "mandarin",
    "created_at": "2025-01-01T00:00:00Z",
    "profile": {
        "age": 75,
        "health_conditions": ["高血压", "糖尿病"],
        "interests": ["太极拳", "养花"],
        "preferences": "喜欢聊家常"
    }
}
```

---

### 更新用户信息

```http
PUT /api/users/me
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "name": "王奶奶",
    "dialect": "wuhan",
    "profile": {
        "interests": ["太极拳", "养花", "下棋"]
    }
}
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "message": "信息更新成功"
}
```

---

### 获取家属列表

```http
GET /api/users/family
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
    "family_members": [
        {
            "id": 1,
            "name": "张小明",
            "phone": "13900139000",
            "is_primary": true,
            "relationship": "儿子"
        }
    ]
}
```

---

### 添加家属

```http
POST /api/users/family
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "name": "张小红",
    "phone": "13900139001",
    "is_primary": false,
    "relationship": "女儿"
}
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "family_id": 2,
    "message": "家属添加成功"
}
```

---

## 健康数据接口

### 获取健康摘要

```http
GET /api/health/summary
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | int | 否 | 老人ID |
| days | int | 否 | 最近N天，默认7 |

**响应 (200 OK)：**
```json
{
    "user_id": 1,
    "user_name": "王奶奶",
    "period": {
        "start": "2025-12-17",
        "end": "2025-12-24"
    },
    "summary": {
        "total_conversations": 45,
        "avg_risk_score": 2.3,
        "high_risk_count": 2,
        "emotion_distribution": {
            "neutral": 30,
            "happy": 10,
            "lonely": 3,
            "anxious": 2
        },
        "top_topics": ["健康", "天气", "家人", "饮食"],
        "activity_level": "正常"
    },
    "alerts": [
        {
            "date": "2025-12-20",
            "risk_score": 7,
            "reason": "头晕症状",
            "handled": true
        }
    ],
    "recommendations": [
        "建议保持规律作息",
        "注意补充水分",
        "可以多和家人视频通话"
    ]
}
```

---

### 获取风险历史

```http
GET /api/health/risks
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | int | 否 | 老人ID |
| min_score | int | 否 | 最低风险分 |
| days | int | 否 | 最近N天 |

**响应 (200 OK)：**
```json
{
    "risks": [
        {
            "id": 1,
            "date": "2025-12-24",
            "risk_score": 7,
            "category": "health",
            "reason": "胸闷症状",
            "conversation_summary": "老人表示胸口有点闷",
            "action_taken": "已通知家属",
            "resolved": true
        }
    ],
    "statistics": {
        "total": 5,
        "avg_score": 5.2,
        "resolved_rate": 0.8
    }
}
```

---

## 视频通话接口

### 发起视频通话

```http
POST /api/video/call
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "target_user_id": 1,
    "call_type": "video"
}
```

**响应 (200 OK)：**
```json
{
    "call_id": "call-abc123",
    "room_id": "room-xyz789",
    "signaling_url": "wss://signal.anxinbao.com/room/xyz789",
    "ice_servers": [
        {
            "urls": "stun:stun.anxinbao.com:3478"
        }
    ],
    "expires_in": 300
}
```

---

### 接听通话

```http
POST /api/video/answer
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "call_id": "call-abc123",
    "accept": true
}
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "room_id": "room-xyz789",
    "signaling_url": "wss://signal.anxinbao.com/room/xyz789"
}
```

---

### 结束通话

```http
POST /api/video/hangup
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
    "call_id": "call-abc123"
}
```

**响应 (200 OK)：**
```json
{
    "success": true,
    "duration": 180,
    "message": "通话已结束"
}
```

---

## 监控接口

### Prometheus指标

```http
GET /metrics
```

返回Prometheus格式的指标数据，无需认证。

---

### 健康检查

#### 存活探针

```http
GET /health/live
```

**响应 (200 OK)：**
```json
{
    "status": "ok"
}
```

#### 就绪探针

```http
GET /health/ready
```

**响应 (200 OK)：**
```json
{
    "status": "healthy",
    "checks": {
        "database": {"status": "healthy"},
        "redis": {"status": "healthy"}
    }
}
```

**响应 (503 Service Unavailable)：**
```json
{
    "status": "unhealthy",
    "checks": {
        "database": {"status": "unhealthy", "error": "Connection refused"},
        "redis": {"status": "healthy"}
    }
}
```

---

## 错误码

| HTTP状态码 | 错误码 | 说明 |
|-----------|--------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未认证或令牌过期 |
| 403 | FORBIDDEN | 无权限访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 422 | VALIDATION_ERROR | 数据验证失败 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

**错误响应格式：**
```json
{
    "detail": "错误描述",
    "code": "ERROR_CODE",
    "timestamp": "2025-12-24T10:30:00Z"
}
```

---

## 速率限制

| 端点类型 | 限制 |
|---------|------|
| 认证接口 | 10次/分钟 |
| 对话接口 | 60次/分钟 |
| 其他接口 | 100次/分钟 |

超出限制时返回 `429 Too Many Requests`，响应头包含：
- `X-RateLimit-Limit`: 限制次数
- `X-RateLimit-Remaining`: 剩余次数
- `X-RateLimit-Reset`: 重置时间（Unix时间戳）

---

## SDK示例

### Python

```python
import httpx

class AnxinbaoClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        response = httpx.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        self.token = data["access_token"]
        return data

    def chat(self, message, session_id=None):
        response = httpx.post(
            f"{self.base_url}/api/chat/message",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"message": message, "session_id": session_id}
        )
        return response.json()

# 使用示例
client = AnxinbaoClient()
client.login("13800138000", "password")
reply = client.chat("今天天气怎么样")
print(reply["reply"])
```

### JavaScript

```javascript
class AnxinbaoClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        this.token = data.access_token;
        return data;
    }

    async chat(message, sessionId = null) {
        const response = await fetch(`${this.baseUrl}/api/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({message, session_id: sessionId})
        });
        return response.json();
    }
}

// 使用示例
const client = new AnxinbaoClient();
await client.login('13800138000', 'password');
const reply = await client.chat('今天天气怎么样');
console.log(reply.reply);
```
