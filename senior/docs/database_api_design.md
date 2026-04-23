# 养老智能体系统数据库结构和API规范设计

## 1. 系统概述

养老智能体系统是一个面向老年人群的智能化综合服务平台，包含用户管理、健康监测、设备管理、服务记录等核心功能模块。系统采用微服务架构，支持高并发、高可用和数据安全。

## 2. 数据库设计

### 2.1 核心实体设计

#### 2.1.1 用户信息表 (users)
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    real_name VARCHAR(50) NOT NULL,
    id_card VARCHAR(18) UNIQUE,
    gender TINYINT DEFAULT 0 COMMENT '0-未知 1-男 2-女',
    birth_date DATE,
    age INT,
    region_code VARCHAR(20),
    address TEXT,
    emergency_contact_name VARCHAR(50),
    emergency_contact_phone VARCHAR(20),
    blood_type VARCHAR(5),
    chronic_diseases JSON,
    allergies JSON,
    current_medications JSON,
    user_type TINYINT DEFAULT 1 COMMENT '1-普通用户 2-护理对象 3-服务提供方 4-管理员',
    status TINYINT DEFAULT 1 COMMENT '1-正常 2-禁用 3-待审核',
    avatar_url VARCHAR(255),
    language_preference VARCHAR(10) DEFAULT 'zh-CN',
    data_retention_period INT DEFAULT 2555 COMMENT '数据保留天数，默认7年',
    privacy_consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_region_type (region_code, user_type),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='用户信息表';
```

#### 2.1.2 健康数据表 (health_records)
```sql
CREATE TABLE health_records (
    record_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    device_id VARCHAR(36),
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型：blood_pressure, heart_rate, blood_sugar, weight, temperature等',
    data_value DECIMAL(10,3),
    unit VARCHAR(20),
    systolic_pressure DECIMAL(5,1),
    diastolic_pressure DECIMAL(5,1),
    measurement_time TIMESTAMP NOT NULL,
    device_location VARCHAR(50),
    sensor_accuracy DECIMAL(3,2),
    abnormal_flag TINYINT DEFAULT 0 COMMENT '0-正常 1-异常 2-预警',
    ai_analysis_result JSON,
    manual_review_required BOOLEAN DEFAULT FALSE,
    reviewed_by BIGINT,
    reviewed_at TIMESTAMP,
    tags JSON,
    data_source TINYINT DEFAULT 1 COMMENT '1-设备自动采集 2-手动录入 3-第三方API',
    partition_key VARCHAR(20) GENERATED ALWAYS AS (DATE_FORMAT(measurement_time, '%Y%m')) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_time (user_id, measurement_time),
    INDEX idx_type_time (data_type, measurement_time),
    INDEX idx_partition (partition_key),
    INDEX idx_abnormal (abnormal_flag)
) ENGINE=InnoDB COMMENT='健康数据表'
PARTITION BY RANGE (YEAR(measurement_time)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 2.1.3 设备数据表 (devices)
```sql
CREATE TABLE devices (
    device_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    device_type VARCHAR(50) NOT NULL COMMENT '设备类型：smartwatch, blood_pressure_monitor, glucometer等',
    device_model VARCHAR(100),
    device_name VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    mac_address VARCHAR(17),
    firmware_version VARCHAR(50),
    battery_level DECIMAL(5,2),
    last_heartbeat TIMESTAMP,
    connection_status TINYINT DEFAULT 0 COMMENT '0-离线 1-在线 2-错误',
    configuration JSON,
    calibration_date DATE,
    maintenance_schedule JSON,
    data_transmission_interval INT DEFAULT 300 COMMENT '数据传输间隔秒数',
    geo_region VARCHAR(20),
    status TINYINT DEFAULT 1 COMMENT '1-正常 2-维护 3-故障 4-报废',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_device (user_id, device_type),
    INDEX idx_status_type (status, device_type),
    INDEX idx_region (geo_region)
) ENGINE=InnoDB COMMENT='设备信息表';
```

#### 2.1.4 服务记录表 (service_records)
```sql
CREATE TABLE service_records (
    record_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    service_provider_id BIGINT,
    service_type VARCHAR(50) NOT NULL COMMENT '服务类型：medical_consultation, home_care, emergency_service等',
    service_category TINYINT NOT NULL COMMENT '1-医疗健康 2-生活照料 3-精神慰藉 4-紧急救援',
    service_name VARCHAR(100) NOT NULL,
    service_description TEXT,
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    service_status TINYINT DEFAULT 1 COMMENT '1-待开始 2-进行中 3-已完成 4-已取消 5-异常',
    service_quality_score DECIMAL(3,1),
    service_fee DECIMAL(10,2),
    payment_status TINYINT DEFAULT 1 COMMENT '1-未支付 2-部分支付 3-已支付 4-已退款',
    notes TEXT,
    attachments JSON,
    satisfaction_rating TINYINT COMMENT '满意度评分1-5',
    complaint_status TINYINT DEFAULT 0 COMMENT '0-无投诉 1-处理中 2-已解决',
    geo_location POINT,
    address TEXT,
    region_code VARCHAR(20),
    service_duration_minutes INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_service (user_id, service_type),
    INDEX idx_provider_time (service_provider_id, scheduled_start),
    INDEX idx_time_region (scheduled_start, region_code),
    INDEX idx_status (service_status),
    SPATIAL INDEX idx_location (geo_location)
) ENGINE=InnoDB COMMENT='服务记录表';
```

#### 2.1.5 护理计划表 (care_plans)
```sql
CREATE TABLE care_plans (
    plan_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    plan_type TINYINT NOT NULL COMMENT '1-健康护理 2-生活照料 3-康复训练 4-心理关怀',
    description TEXT,
    goals JSON,
    interventions JSON,
    schedule JSON,
    responsible_caregiver_id BIGINT,
    start_date DATE NOT NULL,
    end_date DATE,
    status TINYINT DEFAULT 1 COMMENT '1-草稿 2-激活 3-暂停 4-完成 5-终止',
    review_frequency_days INT DEFAULT 30,
    last_review_date DATE,
    next_review_date DATE,
    risk_level TINYINT DEFAULT 1 COMMENT '1-低风险 2-中风险 3-高风险',
    auto_adjustment_enabled BOOLEAN DEFAULT FALSE,
    version INT DEFAULT 1,
    parent_plan_id BIGINT,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (parent_plan_id) REFERENCES care_plans(plan_id),
    INDEX idx_user_status (user_id, status),
    INDEX idx_type_time (plan_type, start_date)
) ENGINE=InnoDB COMMENT='护理计划表';
```

### 2.2 数据分区策略

#### 2.2.1 时间分区
- **健康数据表**: 按月分区，便于查询和归档
- **服务记录表**: 按季度分区，平衡查询性能和存储效率
- **系统日志表**: 按周分区，便于快速清理历史数据

#### 2.2.2 地区分区
- **用户数据表**: 按省份/城市分区，支持区域化管理
- **设备数据表**: 按设备部署地区分区，优化设备管理

#### 2.2.3 用户类型分区
- **高优先级用户**: 独立分区，确保服务质量
- **服务提供者**: 单独分区，便于管理和审计

### 2.3 数据模型扩展和版本管理

#### 2.3.1 扩展字段设计
```sql
-- 通用扩展字段表
CREATE TABLE entity_extensions (
    extension_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    extension_key VARCHAR(100) NOT NULL,
    extension_value LONGTEXT,
    data_type VARCHAR(20) DEFAULT 'json' COMMENT 'json, string, number, boolean, date',
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_entity_ext (entity_type, entity_id, extension_key),
    INDEX idx_type_entity (entity_type, entity_id)
) ENGINE=InnoDB COMMENT='实体扩展字段表';
```

#### 2.3.2 版本管理表
```sql
-- 数据版本管理表
CREATE TABLE data_versions (
    version_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    version_number INT NOT NULL,
    change_type TINYINT NOT NULL COMMENT '1-创建 2-更新 3-删除',
    change_description TEXT,
    old_data JSON,
    new_data JSON,
    changed_by BIGINT,
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity_version (entity_type, entity_id, version_number),
    INDEX idx_timestamp (change_timestamp)
) ENGINE=InnoDB COMMENT='数据版本管理表';
```

## 3. API设计规范

### 3.1 RESTful API设计

#### 3.1.1 API基础规范
```yaml
API基础信息:
  版本: v1
  基础URL: https://api.eldercare.ai/v1
  认证方式: Bearer Token + API Key
  内容类型: application/json; charset=utf-8
  字符编码: UTF-8
  日期格式: ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ)
  
响应格式:
  成功响应:
    code: 200
    message: "Success"
    data: {业务数据}
    timestamp: "2025-11-17T12:28:59.000Z"
    
  错误响应:
    code: 400/401/403/404/500
    message: "错误描述"
    error: {详细错误信息}
    timestamp: "2025-11-17T12:28:59.000Z"
```

#### 3.1.2 核心API端点

##### 用户管理API
```yaml
# 获取用户信息
GET /users/{userId}
参数:
  - include: string (可选) - include=health_records,devices,care_plans

# 创建用户
POST /users
请求体:
  {
    "real_name": "张三",
    "phone": "13800138000",
    "birth_date": "1950-01-01",
    "gender": 1,
    "region_code": "420102"
  }

# 更新用户信息
PUT /users/{userId}
请求体:
  {
    "address": "新地址",
    "emergency_contact_name": "李四"
  }

# 获取用户健康数据
GET /users/{userId}/health-records
参数:
  - start_date: string (YYYY-MM-DD)
  - end_date: string (YYYY-MM-DD)
  - data_type: string
  - limit: integer (默认100，最大1000)
  - offset: integer (默认0)
```

##### 健康数据API
```yaml
# 上传健康数据
POST /health-records
请求体:
  {
    "user_id": 12345,
    "device_id": "device-uuid",
    "data_type": "blood_pressure",
    "systolic_pressure": 120.5,
    "diastolic_pressure": 80.0,
    "measurement_time": "2025-11-17T12:28:59.000Z"
  }

# 批量上传健康数据
POST /health-records/batch
请求体:
  {
    "records": [
      {
        "user_id": 12345,
        "data_type": "heart_rate",
        "data_value": 75,
        "unit": "bpm",
        "measurement_time": "2025-11-17T12:28:59.000Z"
      }
    ]
  }

# 获取健康数据分析
GET /health-records/{recordId}/analysis
```

##### 设备管理API
```yaml
# 获取用户设备列表
GET /users/{userId}/devices

# 注册设备
POST /devices
请求体:
  {
    "user_id": 12345,
    "device_type": "smartwatch",
    "device_name": "Apple Watch Series 8",
    "serial_number": "ABC123456",
    "geo_region": "420102"
  }

# 更新设备状态
PUT /devices/{deviceId}/status
请求体:
  {
    "connection_status": 1,
    "battery_level": 85.5,
    "last_heartbeat": "2025-11-17T12:28:59.000Z"
  }
```

##### 服务记录API
```yaml
# 创建服务记录
POST /service-records
请求体:
  {
    "user_id": 12345,
    "service_type": "medical_consultation",
    "service_category": 1,
    "service_name": "在线问诊",
    "scheduled_start": "2025-11-17T14:00:00.000Z",
    "scheduled_end": "2025-11-17T14:30:00.000Z",
    "service_provider_id": 67890
  }

# 获取服务记录
GET /users/{userId}/service-records
参数:
  - start_date: string
  - end_date: string
  - service_type: string
  - status: integer
```

### 3.2 GraphQL API设计

#### 3.2.1 Schema定义
```graphql
scalar DateTime
scalar JSON

type User {
  userId: ID!
  uuid: String!
  realName: String!
  phone: String
  email: String
  gender: Gender
  birthDate: Date
  age: Int
  regionCode: String
  address: String
  healthRecords(limit: Int, offset: Int): [HealthRecord!]!
  devices: [Device!]!
  carePlans: [CarePlan!]!
  createdAt: DateTime!
}

type HealthRecord {
  recordId: ID!
  uuid: String!
  userId: ID!
  deviceId: String
  dataType: String!
  dataValue: Float
  unit: String
  systolicPressure: Float
  diastolicPressure: Float
  measurementTime: DateTime!
  abnormalFlag: Int!
  aiAnalysisResult: JSON
  createdAt: DateTime!
}

type Device {
  deviceId: ID!
  uuid: String!
  userId: ID!
  deviceType: String!
  deviceName: String!
  manufacturer: String
  connectionStatus: Int!
  batteryLevel: Float
  lastHeartbeat: DateTime
  createdAt: DateTime!
}

type ServiceRecord {
  recordId: ID!
  uuid: String!
  userId: ID!
  serviceProviderId: ID
  serviceType: String!
  serviceCategory: Int!
  serviceName: String!
  scheduledStart: DateTime!
  scheduledEnd: DateTime!
  actualStart: DateTime
  actualEnd: DateTime
  serviceStatus: Int!
  serviceFee: Float
  createdAt: DateTime!
}

enum Gender {
  UNKNOWN
  MALE
  FEMALE
}

input CreateUserInput {
  realName: String!
  phone: String
  email: String
  gender: Gender
  birthDate: Date
  regionCode: String
  address: String
}

input CreateHealthRecordInput {
  userId: ID!
  deviceId: String
  dataType: String!
  dataValue: Float
  unit: String
  systolicPressure: Float
  diastolicPressure: Float
  measurementTime: DateTime!
}

input CreateServiceRecordInput {
  userId: ID!
  serviceProviderId: ID
  serviceType: String!
  serviceCategory: Int!
  serviceName: String!
  scheduledStart: DateTime!
  scheduledEnd: DateTime!
  serviceFee: Float
}

type Query {
  # 用户查询
  user(id: ID!): User
  users(limit: Int, offset: Int, regionCode: String): [User!]!
  
  # 健康数据查询
  healthRecord(id: ID!): HealthRecord
  healthRecords(userId: ID!, dataType: String, startDate: Date, endDate: Date, limit: Int, offset: Int): [HealthRecord!]!
  
  # 设备查询
  device(id: ID!): Device
  devices(userId: ID!, deviceType: String): [Device!]!
  
  # 服务记录查询
  serviceRecord(id: ID!): ServiceRecord
  serviceRecords(userId: ID!, serviceType: String, startDate: Date, endDate: Date): [ServiceRecord!]!
}

type Mutation {
  # 用户管理
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: CreateUserInput!): User!
  
  # 健康数据
  createHealthRecord(input: CreateHealthRecordInput!): HealthRecord!
  batchCreateHealthRecords(records: [CreateHealthRecordInput!]!): [HealthRecord!]!
  
  # 服务记录
  createServiceRecord(input: CreateServiceRecordInput!): ServiceRecord!
  updateServiceRecordStatus(id: ID!, status: Int!): ServiceRecord!
}

type Subscription {
  # 健康数据实时更新
  healthRecordCreated(userId: ID!): HealthRecord!
  healthRecordUpdated(userId: ID!): HealthRecord!
  
  # 设备状态实时更新
  deviceStatusChanged(userId: ID!): Device!
  
  # 服务状态实时更新
  serviceRecordStatusChanged(userId: ID!): ServiceRecord!
}
```

### 3.3 实时通信API

#### 3.3.1 WebSocket协议设计
```javascript
// WebSocket连接建立
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

// 订阅设备状态更新
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'device_status',
  user_id: 12345
}));

// 接收消息
ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'health_data':
      // 处理健康数据更新
      handleHealthDataUpdate(message.data);
      break;
    case 'device_status':
      // 处理设备状态更新
      handleDeviceStatusUpdate(message.data);
      break;
    case 'alert':
      // 处理告警信息
      handleAlert(message.data);
      break;
  }
};
```

#### 3.3.2 消息格式规范
```json
{
  "id": "msg-uuid-123",
  "type": "health_data|device_status|alert|system",
  "channel": "health_data|device_status|service_records",
  "user_id": 12345,
  "timestamp": "2025-11-17T12:28:59.000Z",
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

## 4. API安全设计

### 4.1 认证授权机制

#### 4.1.1 JWT Token设计
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT",
    "kid": "eldercare-key-1"
  },
  "payload": {
    "iss": "eldercare-ai",
    "sub": "user_id_12345",
    "aud": "eldercare-api",
    "exp": 1640995200,
    "iat": 1640991600,
    "jti": "token-uuid-123",
    "user_type": "elderly|caregiver|admin",
    "permissions": [
      "health:read",
      "health:write",
      "device:manage",
      "service:book"
    ],
    "region_code": "420102",
    "data_access_level": "personal|family|emergency"
  }
}
```

#### 4.1.2 API Key管理
```yaml
API Key格式: ecak_live_[user_type]_[hash]
权限级别:
  - read_only: 只读权限
  - read_write: 读写权限  
  - admin: 管理权限
  
密钥轮换:
  - 主密钥: 每年轮换一次
  - 从密钥: 每季度轮换一次
  - 临时密钥: 24小时有效期
```

### 4.2 数据加密

#### 4.2.1 传输加密
```yaml
TLS版本: TLS 1.3
加密算法: AES-256-GCM
证书管理:
  - 证书有效期: 1年
  - 自动续期: 提前30天
  - 证书透明度: 支持CT日志
```

#### 4.2.2 存储加密
```sql
-- 敏感字段加密示例
CREATE TABLE sensitive_data_demo (
    id BIGINT PRIMARY KEY,
    -- 身份证号使用AES加密
    id_card_encrypted VARBINARY(512),
    -- 病历信息使用列级加密
    medical_history_encrypted VARBINARY(1024),
    -- 电话号码部分脱敏存储
    phone_masked VARCHAR(11),
    -- 密钥标识，用于解密
    encryption_key_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 加密函数示例
SELECT 
    AES_DECRYPT(id_card_encrypted, encryption_key_id) as id_card,
    AES_DECRYPT(medical_history_encrypted, encryption_key_id) as medical_history,
    phone_masked
FROM sensitive_data_demo 
WHERE id = 12345;
```

### 4.3 访问控制

#### 4.3.1 角色权限矩阵
```yaml
角色定义:
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
    
  admin:
    权限:
      - read:all_data
      - write:system_config
      - manage:users
      - audit:access_logs
    数据范围: 系统全部数据
```

#### 4.3.2 数据脱敏规则
```yaml
数据脱敏级别:
  level_0: 无脱敏 - 系统管理员
  level_1: 部分脱敏 - 医护人员
    - 姓名: 张*三
    - 手机: 138****8000
    - 身份证: 420102********1234
  
  level_2: 详细脱敏 - 护理人员
    - 姓名: 用户*** 
    - 手机: 138****8000
    - 详细地址: 武汉市江岸区*
    
  level_3: 最高脱敏 - 一般服务人员
    - 所有个人标识信息
    - 仅显示健康数据数值
```

### 4.4 API限流

#### 4.4.1 限流策略
```yaml
限流算法: 漏桶算法 + 令牌桶算法
默认限流配置:
  按用户限流:
    - 普通API: 1000次/小时
    - 健康数据上传: 100次/分钟
    - 设备状态查询: 500次/小时
  
  按IP限流:
    - 公共API: 5000次/小时
    - 登录API: 10次/分钟
  
  按设备限流:
    - 健康数据上传: 10次/分钟
    - 设备控制: 20次/小时

突发流量处理:
  - 短期突发: 允许50%超额，5分钟窗口
  - 长期超额: 返回429状态码
  - 异常流量: 自动加入黑名单
```

#### 4.4.2 限流响应格式
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
  "timestamp": "2025-11-17T12:28:59.000Z"
}
```

## 5. 数据一致性设计

### 5.1 分布式事务管理

#### 5.1.1 事务模式选择
```yaml
事务模式: Saga模式 + 补偿事务
适用场景:
  - 健康数据上传 + 设备状态更新
  - 服务记录创建 + 支付处理
  - 用户注册 + 设备绑定

事务执行流程:
  1. 开始事务(TBegin)
  2. 执行主操作
  3. 执行补偿操作(如果失败)
  4. 提交/回滚事务(TCommit/TRollback)
```

#### 5.1.2 事务实现示例
```sql
-- 事务表
CREATE TABLE distributed_transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    transaction_type VARCHAR(50) NOT NULL,
    status TINYINT NOT NULL COMMENT '1-开始 2-成功 3-失败 4-补偿中 5-补偿完成',
    payload JSON,
    compensation_payload JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_type (transaction_type)
) ENGINE=InnoDB COMMENT='分布式事务表';

-- 事务步骤表
CREATE TABLE transaction_steps (
    step_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    transaction_id VARCHAR(64) NOT NULL,
    step_order INT NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    request_payload JSON,
    response_payload JSON,
    status TINYINT NOT NULL COMMENT '1-待执行 2-执行成功 3-执行失败 4-补偿成功 5-补偿失败',
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES distributed_transactions(transaction_id),
    INDEX idx_transaction (transaction_id, step_order)
) ENGINE=InnoDB COMMENT='事务步骤表';
```

### 5.2 数据同步机制

#### 5.2.1 读写分离
```yaml
数据库架构: 主从复制 + 读写分离
配置:
  主库:
    - 作用: 处理所有写操作
    - 延迟要求: < 1秒
    - 备份策略: 实时备份
  
  从库:
    - 作用: 处理所有读操作
    - 数量: 至少2个从库
    - 负载均衡: 轮询 + 权重
  
同步策略:
  - 强一致性: 健康数据写入
  - 最终一致性: 用户信息同步
  - 弱一致性: 日志数据同步
```

#### 5.2.2 数据一致性检查
```sql
-- 数据一致性检查表
CREATE TABLE consistency_checks (
    check_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    source_data JSON,
    target_data JSON,
    consistency_status TINYINT NOT NULL COMMENT '1-一致 2-不一致 3-检查中',
    last_check_time TIMESTAMP,
    next_check_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_status_time (consistency_status, last_check_time)
) ENGINE=InnoDB COMMENT='数据一致性检查表';

-- 定期一致性检查存储过程
DELIMITER $$
CREATE PROCEDURE CheckDataConsistency()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE entity_id BIGINT;
    DECLARE entity_type VARCHAR(50);
    
    -- 游标遍历需要检查的数据
    DECLARE check_cursor CURSOR FOR 
        SELECT entity_id, entity_type 
        FROM consistency_checks 
        WHERE consistency_status = 3 OR last_check_time < DATE_SUB(NOW(), INTERVAL 1 DAY);
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN check_cursor;
    
    check_loop: LOOP
        FETCH check_cursor INTO entity_id, entity_type;
        IF done THEN
            LEAVE check_loop;
        END IF;
        
        -- 执行一致性检查逻辑
        -- 这里需要根据具体的业务逻辑实现检查算法
        
        UPDATE consistency_checks 
        SET consistency_status = CASE 
            WHEN source_data = target_data THEN 1 
            ELSE 2 
        END,
        last_check_time = NOW(),
        next_check_time = DATE_ADD(NOW(), INTERVAL 1 DAY)
        WHERE entity_id = entity_id AND entity_type = entity_type;
        
    END LOOP;
    
    CLOSE check_cursor;
END$$
DELIMITER ;
```

### 5.3 缓存策略

#### 5.3.1 多级缓存架构
```yaml
缓存层级:
  L1缓存 - 应用内存缓存:
    - 缓存内容: 用户基本信息、设备配置
    - 过期策略: 5分钟TTL
    - 容量限制: 1GB
    
  L2缓存 - Redis集群:
    - 缓存内容: 健康数据实时数据、查询结果
    - 过期策略: 1小时TTL，热点数据延长至24小时
    - 容量限制: 100GB
    
  L3缓存 - CDN:
    - 缓存内容: 静态资源、API响应
    - 过期策略: 1小时TTL
    - 分布式节点: 10个节点

缓存更新策略:
  - 主动更新: 数据变更时立即更新缓存
  - 被动更新: 缓存失效时重新加载
  - 预热策略: 系统启动时预加载热点数据
```

#### 5.3.2 缓存一致性保证
```java
// 缓存更新示例
@Component
public class CacheManager {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private UserRepository userRepository;
    
    public User updateUser(User user) {
        // 1. 更新数据库
        User updatedUser = userRepository.save(user);
        
        // 2. 更新多级缓存
        // L1缓存更新
        l1Cache.put("user:" + user.getId(), updatedUser);
        
        // L2缓存更新
        String cacheKey = "user:detail:" + user.getId();
        redisTemplate.opsForValue().set(cacheKey, updatedUser, Duration.ofHours(1));
        
        // 3. 通知其他节点更新缓存
        redisTemplate.convertAndSend("cache_invalidate", "user:" + user.getId());
        
        return updatedUser;
    }
    
    @EventListener
    public void handleCacheInvalidation(CacheInvalidationEvent event) {
        // 处理缓存失效事件
        String cacheKey = event.getCacheKey();
        l1Cache.remove(cacheKey);
        redisTemplate.delete(cacheKey);
    }
}
```

## 6. 监控和审计

### 6.1 系统监控指标

#### 6.1.1 性能指标
```yaml
数据库性能:
  - QPS: 查询每秒次数 (目标: <10000)
  - TPS: 事务每秒次数 (目标: <5000)
  - 响应时间: P99 < 100ms
  - 连接数: < 80% 最大连接数
  - 慢查询: < 1% 比例

API性能:
  - 接口响应时间: P95 < 500ms
  - 错误率: < 0.1%
  - 可用性: 99.9%
  - 吞吐量: 支持5000并发

缓存性能:
  - 缓存命中率: > 95%
  - 缓存响应时间: < 10ms
  - 内存使用率: < 80%
```

#### 6.1.2 业务指标
```yaml
用户活跃度:
  - 日活跃用户数(DAU)
  - 月活跃用户数(MAU)
  - 用户留存率

健康数据:
  - 每日健康数据上报量
  - 数据质量评分
  - 异常数据占比

服务使用:
  - 服务订单量
  - 服务完成率
  - 用户满意度
```

### 6.2 审计日志设计

#### 6.2.1 操作审计表
```sql
CREATE TABLE audit_logs (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id BIGINT,
    session_id VARCHAR(64),
    action VARCHAR(100) NOT NULL COMMENT '操作类型：login, logout, create, update, delete等',
    resource_type VARCHAR(50) NOT NULL,
    resource_id BIGINT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(64),
    response_status INT,
    processing_time_ms INT,
    risk_level TINYINT DEFAULT 1 COMMENT '1-低风险 2-中风险 3-高风险',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, created_at),
    INDEX idx_action (action, created_at),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_risk (risk_level),
    INDEX idx_ip (ip_address)
) ENGINE=InnoDB COMMENT='审计日志表';
```

#### 6.2.2 数据访问审计
```yaml
审计范围:
  - 用户数据访问: 所有用户数据的读取和修改
  - 权限变更: 用户角色和权限的变更记录
  - 敏感操作: 支付信息、健康数据的访问
  - 系统配置: 系统参数的修改记录

审计内容:
  - 谁: 操作者身份
  - 何时: 操作时间戳
  - 做什么: 具体操作内容
  - 从哪里: 访问来源IP和设备
  - 结果如何: 操作结果和影响

合规要求:
  - 日志保留: 7年
  - 访问控制: 只有审计员可以查看
  - 防篡改: 使用数字签名
  - 实时监控: 异常行为实时告警
```

## 7. 部署和维护

### 7.1 环境配置

#### 7.1.1 数据库集群配置
```yaml
生产环境:
  数据库: MySQL 8.0
  主从配置: 1主2从
  存储引擎: InnoDB
  字符集: utf8mb4
  时区: UTC+8
  
Redis集群:
  节点数: 6个(3主3从)
  内存: 64GB per节点
  持久化: RDB + AOF
  
监控工具:
  - 数据库监控: Prometheus + Grafana
  - 慢查询分析: pt-query-digest
  - 性能监控: PMM (Percona Monitoring and Management)
```

#### 7.1.2 备份策略
```yaml
数据库备份:
  全量备份: 每天凌晨2点，保留30天
  增量备份: 每4小时一次，保留7天
  -binlog备份: 实时备份，保留30天
  
异地备份:
  - 主备机房: 每小时同步一次
  - 云存储: 每日备份到阿里云OSS
  - 跨地域: 每月备份到北京和上海机房

恢复测试:
  - 每周进行一次备份恢复测试
  - 每月进行一次灾难恢复演练
  - 恢复时间目标(RTO): < 4小时
  - 恢复点目标(RPO): < 1小时
```

### 7.2 性能优化

#### 7.2.1 数据库优化
```sql
-- 分区表优化
CREATE TABLE health_records_optimized (
    record_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    -- 其他字段省略...
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB 
PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p202511 VALUES LESS THAN (UNIX_TIMESTAMP('2025-12-01')),
    PARTITION p202512 VALUES LESS THAN (UNIX_TIMESTAMP('2026-01-01')),
    PARTITION p202601 VALUES LESS THAN (UNIX_TIMESTAMP('2026-02-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 索引优化建议
CREATE INDEX idx_user_type_date ON users(user_type, created_at);
CREATE INDEX idx_health_user_type_time ON health_records(user_id, data_type, measurement_time);
CREATE INDEX idx_service_user_status ON service_records(user_id, service_status);

-- 查询优化
-- 使用覆盖索引避免回表
CREATE INDEX idx_user_health_cover ON health_records(user_id, data_type, measurement_time, data_value);

-- 分区裁剪优化
SELECT * FROM health_records 
WHERE user_id = 12345 
  AND measurement_time >= '2025-11-01' 
  AND measurement_time < '2025-12-01'
  AND partition_key = '202511';
```

#### 7.2.2 API性能优化
```yaml
响应优化:
  - 数据压缩: Gzip压缩，压缩比>70%
  - 内容协商: 支持ETag和Last-Modified
  - 分页加载: 默认100条，最大1000条
  - 字段过滤: 支持fields参数指定返回字段

缓存优化:
  - HTTP缓存: Cache-Control, ETag
  - 应用缓存: Redis多级缓存
  - CDN缓存: 静态资源和热点数据
  - 预加载: 预测性数据加载

并发优化:
  - 连接池: HikariCP连接池
  - 异步处理: 非关键路径异步执行
  - 批量处理: 合并小请求成大批次
  - 限流降级: 超载时优雅降级
```

## 8. 总结

本设计文档全面覆盖了养老智能体系统的数据库结构和API规范，主要特点包括：

1. **完整的实体设计**: 涵盖用户、健康数据、设备、服务记录等核心业务实体
2. **灵活的数据分区**: 支持时间、地区、用户类型的多维度分区
3. **多样化的API**: 同时提供RESTful、GraphQL和WebSocket实时通信接口
4. **严格的安全保障**: JWT认证、API限流、数据加密等多层安全防护
5. **强数据一致性**: 分布式事务、Saga模式、缓存一致性保证
6. **完善的监控审计**: 全面的性能监控和操作审计日志

该设计充分考虑了养老场景的特殊需求，确保系统的安全性、可靠性和可扩展性，为养老智能体系统提供坚实的技术基础。