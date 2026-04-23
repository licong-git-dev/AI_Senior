# API接口规范文档

## 目录
1. [API概述](#api概述)
2. [认证与授权](#认证与授权)
3. [基础规范](#基础规范)
4. [用户管理API](#用户管理api)
5. [健康数据API](#健康数据api)
6. [设备管理API](#设备管理api)
7. [服务记录API](#服务记录api)
8. [紧急呼叫API](#紧急呼叫api)
9. [AI分析API](#ai分析api)
10. [实时通信API](#实时通信api)
11. [错误处理](#错误处理)
12. [限流策略](#限流策略)

---

## API概述

### 服务架构
养老智能体系统采用微服务架构，提供RESTful API、GraphQL API和WebSocket实时通信接口，支持多端应用接入。

### 基础信息
- **API版本**: v1
- **基础URL**: `https://api.eldercare.ai/v1`
- **协议**: HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **日期格式**: ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ)

### 支持的API类型
1. **RESTful API**: 标准的REST接口
2. **GraphQL API**: 查询灵活，支持数据聚合
3. **WebSocket**: 实时双向通信

---

## 认证与授权

### 认证方式

#### 1. JWT Token认证
```http
Authorization: Bearer <jwt_token>
```

#### 2. API Key认证
```http
X-API-Key: <api_key>
```

### 权限级别
```yaml
权限级别:
  read_only: 只读权限
  read_write: 读写权限  
  admin: 管理权限
```

### 角色权限矩阵
```yaml
elderly:
  权限:
    - read:own_health_data
    - read:own_device_status
    - create:service_request
    - update:own_profile
  数据范围: 个人信息
    
family_member:
  权限:
    - read:family_health_data
    - read:family_device_status
    - create:service_request
    - update:family_profile
    - emergency:access
  数据范围: 家庭成员数据
    
caregiver:
  权限:
    - read:assigned_health_data
    - update:care_records
    - create:health_alerts
    - emergency:response
  数据范围: 护理对象数据
    
medical_staff:
  权限:
    - read:patient_health_data
    - update:medical_records
    - create:prescriptions
    - read:medical_devices
  数据范围: 患者医疗数据
```

---

## 基础规范

### 响应格式

#### 成功响应
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    // 业务数据
  },
  "timestamp": "2025-11-18T15:19:03.000Z"
}
```

#### 错误响应
```json
{
  "code": 400,
  "message": "Bad Request",
  "error": {
    "type": "ValidationError",
    "details": "参数验证失败",
    "field": "user_id"
  },
  "timestamp": "2025-11-18T15:19:03.000Z"
}
```

### HTTP状态码
```yaml
200: 请求成功
201: 创建成功
204: 删除成功
400: 请求参数错误
401: 未授权
403: 权限不足
404: 资源不存在
422: 数据验证失败
429: 请求频率超限
500: 服务器内部错误
502: 网关错误
503: 服务不可用
```

---

## 用户管理API

### 获取用户信息
```http
GET /users/{userId}
```

**路径参数:**
- `userId` (string): 用户ID

**查询参数:**
- `include` (string): 可选，包含关联数据
  - `health_records`: 健康记录
  - `devices`: 设备信息
  - `care_plans`: 护理计划

**示例:**
```http
GET /users/12345?include=health_records,devices
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "user_id": 12345,
    "uuid": "user-uuid-12345",
    "real_name": "张三",
    "phone": "13800138000",
    "gender": 1,
    "birth_date": "1950-01-01",
    "region_code": "420102",
    "health_records": [...],
    "devices": [...]
  }
}
```

### 创建用户
```http
POST /users
```

**请求体:**
```json
{
  "real_name": "张三",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "gender": 1,
  "birth_date": "1950-01-01",
  "region_code": "420102",
  "address": "武汉市江岸区",
  "emergency_contact_name": "李四",
  "emergency_contact_phone": "13900139000"
}
```

### 更新用户信息
```http
PUT /users/{userId}
```

### 获取用户列表
```http
GET /users
```

**查询参数:**
- `page` (integer): 页码，默认1
- `limit` (integer): 每页数量，默认20，最大100
- `region_code` (string): 地区编码
- `user_type` (integer): 用户类型
- `status` (integer): 用户状态

---

## 健康数据API

### 上传健康数据
```http
POST /health-records
```

**请求体:**
```json
{
  "user_id": 12345,
  "device_id": "device-uuid",
  "data_type": "blood_pressure",
  "systolic_pressure": 120.5,
  "diastolic_pressure": 80.0,
  "heart_rate": 75,
  "blood_sugar": 5.2,
  "temperature": 36.5,
  "unit": "mmHg",
  "measurement_time": "2025-11-18T15:19:03.000Z"
}
```

**数据类型说明:**
```yaml
data_type:
  blood_pressure: 血压
  heart_rate: 心率
  blood_sugar: 血糖
  weight: 体重
  temperature: 体温
  blood_oxygen: 血氧
  ecg: 心电图
```

### 批量上传健康数据
```http
POST /health-records/batch
```

**请求体:**
```json
{
  "records": [
    {
      "user_id": 12345,
      "data_type": "heart_rate",
      "data_value": 75,
      "unit": "bpm",
      "measurement_time": "2025-11-18T15:19:03.000Z"
    },
    {
      "user_id": 12345,
      "data_type": "temperature",
      "data_value": 36.5,
      "unit": "°C",
      "measurement_time": "2025-11-18T15:20:03.000Z"
    }
  ]
}
```

### 获取健康数据
```http
GET /users/{userId}/health-records
```

**查询参数:**
- `start_date` (string): 开始日期 (YYYY-MM-DD)
- `end_date` (string): 结束日期 (YYYY-MM-DD)
- `data_type` (string): 数据类型
- `limit` (integer): 限制数量，默认100，最大1000
- `offset` (integer): 偏移量，默认0

### 获取健康数据分析
```http
GET /health-records/{recordId}/analysis
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "record_id": 98765,
    "abnormal_flag": 0,
    "ai_analysis": {
      "health_score": 85,
      "trend_analysis": "stable",
      "recommendations": [
        "继续保持良好的生活习惯",
        "定期监测血压变化"
      ]
    }
  }
}
```

---

## 设备管理API

### 获取用户设备列表
```http
GET /users/{userId}/devices
```

### 注册设备
```http
POST /devices
```

**请求体:**
```json
{
  "user_id": 12345,
  "device_type": "smartwatch",
  "device_name": "Apple Watch Series 8",
  "device_model": "A2726",
  "manufacturer": "Apple",
  "serial_number": "ABC123456",
  "mac_address": "00:1B:44:11:3A:B7",
  "geo_region": "420102"
}
```

### 更新设备状态
```http
PUT /devices/{deviceId}/status
```

**请求体:**
```json
{
  "connection_status": 1,
  "battery_level": 85.5,
  "last_heartbeat": "2025-11-18T15:19:03.000Z",
  "firmware_version": "1.2.3"
}
```

### 设备数据同步
```http
POST /devices/{deviceId}/sync
```

**设备状态说明:**
```yaml
connection_status:
  0: 离线
  1: 在线
  2: 错误

status:
  1: 正常
  2: 维护
  3: 故障
  4: 报废
```

---

## 服务记录API

### 创建服务记录
```http
POST /service-records
```

**请求体:**
```json
{
  "user_id": 12345,
  "service_provider_id": 67890,
  "service_type": "medical_consultation",
  "service_category": 1,
  "service_name": "在线问诊",
  "service_description": "高血压咨询",
  "scheduled_start": "2025-11-18T14:00:00.000Z",
  "scheduled_end": "2025-11-18T14:30:00.000Z",
  "service_fee": 99.00,
  "address": "武汉市江岸区医院",
  "geo_location": {
    "latitude": 30.584354,
    "longitude": 114.304363
  }
}
```

### 获取服务记录
```http
GET /users/{userId}/service-records
```

**查询参数:**
- `start_date` (string): 开始日期
- `end_date` (string): 结束日期
- `service_type` (string): 服务类型
- `service_status` (integer): 服务状态
- `page` (integer): 页码
- `limit` (integer): 每页数量

### 更新服务状态
```http
PUT /service-records/{recordId}/status
```

**请求体:**
```json
{
  "service_status": 3,
  "actual_start": "2025-11-18T14:05:00.000Z",
  "actual_end": "2025-11-18T14:25:00.000Z",
  "service_quality_score": 4.5,
  "satisfaction_rating": 5,
  "notes": "服务完成，用户满意"
}
```

**服务状态说明:**
```yaml
service_status:
  1: 待开始
  2: 进行中
  3: 已完成
  4: 已取消
  5: 异常
```

---

## 紧急呼叫API

### 创建紧急呼叫
```http
POST /emergency-calls
```

**请求体:**
```json
{
  "user_id": 12345,
  "call_type": "health_emergency",
  "severity_level": 2,
  "location_latitude": 30.584354,
  "location_longitude": 114.304363,
  "description": "老人摔倒，意识不清",
  "health_data_snapshot": {
    "blood_pressure": "200/120",
    "heart_rate": "120",
    "blood_sugar": "8.5"
  }
}
```

### 响应紧急呼叫
```http
PUT /emergency-calls/{callId}/respond
```

**请求体:**
```json
{
  "responder_id": 98765,
  "response_time": "2025-11-18T15:25:00.000Z",
  "estimated_arrival": "2025-11-18T15:35:00.000Z"
}
```

### 完成紧急呼叫
```http
PUT /emergency-calls/{callId}/complete
```

**请求体:**
```json
{
  "completion_time": "2025-11-18T15:40:00.000Z",
  "outcome": "老人已安全，无大碍",
  "follow_up_required": false
}
```

### 获取紧急呼叫列表
```http
GET /emergency-calls
```

**查询参数:**
- `user_id` (string): 用户ID
- `status` (integer): 状态
- `severity_level` (integer): 严重程度
- `start_time` (string): 开始时间
- `end_time` (string): 结束时间

---

## AI分析API

### 健康数据分析
```http
POST /ai/health-analysis
```

**请求体:**
```json
{
  "user_id": 12345,
  "analysis_type": "comprehensive",
  "data_period": {
    "start_date": "2025-10-01",
    "end_date": "2025-11-18"
  },
  "include_predictions": true
}
```

### 异常检测
```http
POST /ai/anomaly-detection
```

### 行为模式分析
```http
POST /ai/behavior-analysis
```

### 健康趋势预测
```http
POST /ai/health-prediction
```

---

## 实时通信API

### WebSocket连接
```javascript
const ws = new WebSocket('wss://api.eldercare.ai/v1/ws');

ws.onopen = function(event) {
  // 发送认证信息
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'Bearer <jwt_token>',
    api_key: 'your_api_key'
  }));
};

// 订阅健康数据更新
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'health_data',
  user_id: 12345,
  data_types: ['blood_pressure', 'heart_rate']
}));
```

### 消息格式
```json
{
  "id": "msg-uuid-123",
  "type": "health_data|device_status|alert|system",
  "channel": "health_data|device_status|service_records",
  "user_id": 12345,
  "timestamp": "2025-11-18T15:19:03.000Z",
  "data": {
    // 具体业务数据
  },
  "metadata": {
    "version": "1.0",
    "source": "device|api|system",
    "priority": "low|normal|high|urgent"
  }
}
```

### 订阅频道
```yaml
health_data: 健康数据更新
device_status: 设备状态变化
emergency_calls: 紧急呼叫
service_updates: 服务状态更新
health_alerts: 健康预警
system_notifications: 系统通知
```

---

## 错误处理

### 错误码定义
```yaml
错误码:
  AUTH_FAILED: "认证失败"
  PERMISSION_DENIED: "权限不足"
  INVALID_PARAMETERS: "参数错误"
  RESOURCE_NOT_FOUND: "资源不存在"
  RATE_LIMIT_EXCEEDED: "请求频率超限"
  SERVICE_UNAVAILABLE: "服务不可用"
  DATA_VALIDATION_FAILED: "数据验证失败"
  HEALTH_DATA_UPLOAD_FAILED: "健康数据上传失败"
  EMERGENCY_CALL_HANDLER_FAILED: "紧急呼叫处理失败"
```

### 错误响应示例
```json
{
  "code": 400,
  "message": "Bad Request",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_PARAMETERS",
    "details": "用户ID格式错误",
    "field": "user_id",
    "value": "invalid_id"
  },
  "timestamp": "2025-11-18T15:19:03.000Z"
}
```

### 业务错误处理
```json
{
  "code": 422,
  "message": "Unprocessable Entity",
  "error": {
    "type": "BusinessError",
    "code": "HEALTH_DATA_ABNORMAL",
    "details": "检测到异常健康数据",
    "health_metrics": {
      "blood_pressure": {
        "value": "200/120",
        "status": "danger",
        "normal_range": "90-140/60-90"
      }
    },
    "recommendations": [
      "立即就医",
      "监测血压变化"
    ]
  },
  "timestamp": "2025-11-18T15:19:03.000Z"
}
```

---

## 限流策略

### 限流配置
```yaml
按用户限流:
  普通API: 1000次/小时
  健康数据上传: 100次/分钟
  设备状态查询: 500次/小时

按IP限流:
  公共API: 5000次/小时
  登录API: 10次/分钟

按设备限流:
  健康数据上传: 10次/分钟
  设备控制: 20次/小时
```

### 限流响应
```json
{
  "code": 429,
  "message": "Rate limit exceeded",
  "error": {
    "type": "RateLimitError",
    "details": "API调用频率超过限制",
    "limit": 1000,
    "window": 3600,
    "retry_after": 600
  },
  "timestamp": "2025-11-18T15:19:03.000Z"
}
```

### 突破流量处理
```yaml
短期突发: 允许50%超额，5分钟窗口
长期超额: 返回429状态码
异常流量: 自动加入黑名单
```

---

## API版本管理

### 版本控制策略
- **主版本**: 不兼容的API变更
- **次版本**: 功能性更新，向后兼容
- **修订版本**: Bug修复和小改进

### 版本兼容性
- v1: 当前稳定版本
- v2: 规划中的版本
- 旧版本API将提供6个月过渡期

### 版本头信息
```http
API-Version: v1
Accept: application/json; version=v1
```

---

## API监控与调试

### 性能指标
- **响应时间**: P95 < 500ms
- **错误率**: < 0.1%
- **可用性**: 99.9%
- **吞吐量**: 支持5000并发

### 调试工具
- **API文档**: Swagger/OpenAPI 3.0
- **测试环境**: `https://api-staging.eldercare.ai/v1`
- **调试工具**: Postman集合
- **SDK**: JavaScript、Python、iOS、Android

### 日志记录
- **请求日志**: 记录所有API调用
- **错误日志**: 详细错误堆栈
- **性能日志**: 接口响应时间
- **审计日志**: 敏感操作记录

---

## 数据安全

### 数据加密
- **传输加密**: TLS 1.3
- **存储加密**: AES-256
- **端到端加密**: 敏感数据传输

### 隐私保护
- **数据脱敏**: 按角色级别脱敏
- **数据最小化**: 只收集必要数据
- **用户控制**: 用户可控制数据使用
- **合规性**: 符合GDPR、等保要求

### 访问控制
- **RBAC**: 基于角色的访问控制
- **ABAC**: 基于属性的访问控制
- **最小权限**: 用户只获得必要权限
- **定期审计**: 权限使用情况审计

---

## 总结

本API接口规范文档为养老智能体系统提供了完整的接口标准，确保：

1. **标准化**: 统一的API设计和响应格式
2. **安全性**: 多层安全防护和权限控制
3. **可扩展性**: 支持业务快速增长
4. **易用性**: 清晰的文档和SDK支持
5. **可靠性**: 高可用性和错误处理机制

通过遵循本规范，可以确保系统各组件之间的无缝集成，为用户提供稳定可靠的服务体验。
