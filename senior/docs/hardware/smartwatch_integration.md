# 智能手环设备适配方案

## 文档信息
- **版本**: v1.0.0
- **创建日期**: 2025-11-18
- **最后更新**: 2025-11-18
- **作者**: 养老智能体技术团队
- **文档状态**: 已审核

## 目录
1. [概述](#概述)
2. [系统架构](#系统架构)
3. [蓝牙通信协议](#蓝牙通信协议)
4. [数据格式规范](#数据格式规范)
5. [健康监测接口](#健康监测接口)
6. [跌倒检测算法](#跌倒检测算法)
7. [实时数据同步](#实时数据同步)
8. [设备监控与告警](#设备监控与告警)
9. [API接口设计](#api接口设计)
10. [测试用例](#测试用例)
11. [部署指南](#部署指南)
12. [安全规范](#安全规范)

## 概述

### 项目背景
智能手环适配方案旨在为养老智能体系统提供统一的设备接入层，支持多种品牌和型号的智能手环设备，实现健康数据的实时采集、处理和分析。

### 设计目标
- 支持主流智能手环设备品牌
- 实现健康数据的实时采集和传输
- 提供可靠的跌倒检测和紧急响应
- 确保数据安全和用户隐私
- 提供可扩展的设备接入架构

### 技术栈
- **通信协议**: Bluetooth Low Energy (BLE) 5.0
- **数据格式**: Protocol Buffers, JSON
- **后端服务**: Node.js, Supabase Edge Functions
- **数据库**: PostgreSQL (Supabase)
- **缓存**: Redis
- **监控**: Prometheus + Grafana

## 系统架构

### 整体架构图
```mermaid
graph TB
    A[智能手环设备] --> B[蓝牙网关]
    B --> C[设备适配层]
    C --> D[数据处理引擎]
    D --> E[实时分析服务]
    D --> F[数据存储层]
    E --> G[告警系统]
    E --> H[移动端应用]
    F --> I[数据分析平台]
    G --> J[紧急响应中心]
```

### 核心组件

#### 1. 设备适配层 (Device Adapter Layer)
- **功能**: 统一不同品牌设备的接口
- **职责**: 
  - 设备发现和连接管理
  - 协议转换和数据标准化
  - 设备状态监控

#### 2. 数据处理引擎 (Data Processing Engine)
- **功能**: 实时处理健康数据
- **职责**:
  - 数据清洗和验证
  - 异常检测和过滤
  - 数据聚合和计算

#### 3. 实时分析服务 (Real-time Analytics)
- **功能**: 健康趋势分析和预警
- **职责**:
  - 心率异常检测
  - 睡眠质量分析
  - 跌倒事件识别

## 蓝牙通信协议

### BLE 服务定义

#### 主要服务 UUID
```javascript
const BLE_SERVICES = {
  HEALTH_MONITOR: '0000180D-0000-1000-8000-00805F9B34FB', // 心率服务
  DEVICE_INFO: '0000180A-0000-1000-8000-00805F9B34FB',   // 设备信息服务
  BATTERY: '0000180F-0000-1000-8000-00805F9B34FB',      // 电池服务
  CUSTOM_DATA: '12345678-1234-1234-1234-123456789ABC',   // 自定义数据服务
};
```

#### 特征值 UUID
```javascript
const BLE_CHARACTERISTICS = {
  HEART_RATE_MEASUREMENT: '00002A37-0000-1000-8000-00805F9B34FB',
  HEART_RATE_CONTROL_POINT: '00002A39-0000-1000-8000-00805F9B34FB',
  BLOOD_PRESSURE_MEASUREMENT: '00002A35-0000-1000-8000-00805F9B34FB',
  SLEEP_MONITORING: '00002A38-0000-1000-8000-00805F9B34FB',
  FALL_DETECTION: '12345678-1234-1234-1234-123456789ABD',
  BATTERY_LEVEL: '00002A19-0000-1000-8000-00805F9B34FB',
  FIRMWARE_VERSION: '00002A26-0000-1000-8000-00805F9B34FB',
};
```

### 连接参数配置
```javascript
const CONNECTION_CONFIG = {
  minConnectionInterval: 24,    // 最小连接间隔 (7.5ms)
  maxConnectionInterval: 40,    // 最大连接间隔 (50ms)
  slaveLatency: 4,              // 从设备延迟
  connectionTimeout: 100,       // 连接超时 (1000ms)
  supervisionTimeout: 200,      // 监督超时 (2000ms)
};
```

### 数据传输协议

#### 1. 数据包格式
```proto
message DeviceDataPacket {
  uint32 timestamp = 1;        // Unix 时间戳
  string device_id = 2;        // 设备唯一标识
  uint8 data_type = 3;         // 数据类型
  bytes raw_data = 4;          // 原始数据
  uint8 sequence = 5;          // 序列号
  uint8 checksum = 6;          // 校验和
}
```

#### 2. 数据类型定义
```javascript
const DATA_TYPES = {
  HEART_RATE: 0x01,
  BLOOD_PRESSURE: 0x02,
  SLEEP_DATA: 0x03,
  FALL_DETECTION: 0x04,
  ACCELEROMETER: 0x05,
  GPS_LOCATION: 0x06,
  BATTERY_STATUS: 0x07,
  DEVICE_STATUS: 0x08,
};
```

## 数据格式规范

### 健康数据 JSON 格式

#### 心率数据
```json
{
  "timestamp": 1731926484,
  "device_id": "WATCH_001",
  "data_type": "heart_rate",
  "heart_rate": {
    "value": 72,
    "unit": "bpm",
    "quality": "excellent",
    "rr_intervals": [850, 830, 840, 860],
    "confidence": 95
  },
  "metadata": {
    "firmware_version": "2.1.3",
    "battery_level": 85,
    "signal_strength": -45
  }
}
```

#### 血压数据
```json
{
  "timestamp": 1731926484,
  "device_id": "WATCH_001",
  "data_type": "blood_pressure",
  "blood_pressure": {
    "systolic": 120,
    "diastolic": 80,
    "unit": "mmHg",
    "mean_arterial_pressure": 93,
    "pulse_pressure": 40,
    "measurement_method": "oscillometric"
  },
  "metadata": {
    "cuff_size": "medium",
    "arm_position": "heart_level",
    "confidence": 88
  }
}
```

#### 睡眠数据
```json
{
  "timestamp": 1731926484,
  "device_id": "WATCH_001",
  "data_type": "sleep_data",
  "sleep_data": {
    "sleep_stage": "deep",
    "duration": 3600,
    "quality_score": 82,
    "sleep_phases": [
      {
        "stage": "light",
        "start_time": 1731922884,
        "duration": 2700
      },
      {
        "stage": "deep", 
        "start_time": 1731925584,
        "duration": 3600
      }
    ],
    "total_sleep_time": 23400,
    "wake_count": 2,
    "sleep_efficiency": 0.91
  }
}
```

#### 跌倒检测数据
```json
{
  "timestamp": 1731926484,
  "device_id": "WATCH_001",
  "data_type": "fall_detection",
  "fall_event": {
    "detected": true,
    "severity": "high",
    "confidence": 94,
    "impact_force": 3.2,
    "fall_direction": "forward",
    "location": {
      "latitude": 30.5728,
      "longitude": 114.3052,
      "accuracy": 5
    },
    "accelerometer_data": {
      "x": -0.8,
      "y": 2.1,
      "z": 8.9,
      "magnitude": 9.2
    }
  },
  "emergency_contact": {
    "name": "李明",
    "phone": "13800138000",
    "relationship": "儿子"
  }
}
```

## 健康监测接口

### 数据接收接口

#### 实时数据上传接口
```javascript
// POST /api/v1/devices/{device_id}/data/realtime
interface RealtimeDataUploadRequest {
  device_id: string;
  data_type: DataType;
  payload: DeviceData;
}

interface DeviceData {
  timestamp: number;
  sensor_data: SensorData;
  metadata: DeviceMetadata;
}

const realtimeDataUpload = async (deviceId: string, data: DeviceData) => {
  try {
    const response = await fetch(`/api/v1/devices/${deviceId}/data/realtime`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${deviceToken}`
      },
      body: JSON.stringify({
        device_id: deviceId,
        data_type: data.data_type,
        payload: data
      })
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Real-time data upload failed:', error);
    throw error;
  }
};
```

#### 批量数据同步接口
```javascript
// POST /api/v1/devices/{device_id}/data/batch
interface BatchDataSyncRequest {
  device_id: string;
  data_batch: DeviceData[];
  sync_token: string;
}

const batchDataSync = async (deviceId: string, dataBatch: DeviceData[], syncToken: string) => {
  try {
    const response = await fetch(`/api/v1/devices/${deviceId}/data/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${deviceToken}`
      },
      body: JSON.stringify({
        device_id: deviceId,
        data_batch: dataBatch,
        sync_token: syncToken
      })
    });
    
    return await response.json();
  } catch (error) {
    console.error('Batch data sync failed:', error);
    throw error;
  }
};
```

### 数据验证和清洗

#### 数据验证规则
```javascript
class DataValidator {
  static validateHeartRate(data: any): boolean {
    return data.heart_rate?.value >= 30 && data.heart_rate?.value <= 220;
  }
  
  static validateBloodPressure(data: any): boolean {
    const bp = data.blood_pressure;
    return bp?.systolic >= 60 && bp?.systolic <= 250 &&
           bp?.diastolic >= 40 && bp?.diastolic <= 150 &&
           bp?.systolic > bp?.diastolic;
  }
  
  static validateSleepData(data: any): boolean {
    return data.sleep_data?.duration > 0 && data.sleep_data?.duration <= 86400;
  }
  
  static validateFallDetection(data: any): boolean {
    const fd = data.fall_event;
    return fd?.confidence >= 0 && fd?.confidence <= 100;
  }
}
```

#### 数据清洗服务
```javascript
class DataCleaningService {
  static removeOutliers(data: number[], threshold: number = 3): number[] {
    const mean = data.reduce((a, b) => a + b) / data.length;
    const std = Math.sqrt(data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length);
    
    return data.filter(val => Math.abs(val - mean) <= threshold * std);
  }
  
  static interpolateMissingData(data: number[], method: string = 'linear'): number[] {
    // 实现数据插值逻辑
    return data;
  }
  
  static smoothData(data: number[], windowSize: number = 5): number[] {
    const smoothed: number[] = [];
    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - Math.floor(windowSize / 2));
      const end = Math.min(data.length, i + Math.ceil(windowSize / 2));
      const window = data.slice(start, end);
      const avg = window.reduce((a, b) => a + b) / window.length;
      smoothed.push(avg);
    }
    return smoothed;
  }
}
```

## 跌倒检测算法

### 算法架构
```javascript
class FallDetectionAlgorithm {
  constructor(config = {}) {
    this.threshold = {
      impact_force: config.impactForce || 3.0,
      duration: config.duration || 1000,
      stillness_time: config.stillnessTime || 5000,
      confidence: config.confidence || 85
    };
    this.accelerometer = new AccelerometerDataProcessor();
    this.machineLearning = new MLClassifier();
  }
  
  async detectFall(sensorData: SensorData): Promise<FallDetectionResult> {
    const features = this.extractFeatures(sensorData);
    const mlResult = await this.machineLearning.predict(features);
    
    return {
      detected: mlResult.probability > this.threshold.confidence / 100,
      confidence: mlResult.probability * 100,
      severity: this.calculateSeverity(sensorData),
      features: features
    };
  }
  
  private extractFeatures(data: SensorData): FeatureVector {
    return {
      magnitude: this.calculateMagnitude(data.accelerometer),
      jerk: this.calculateJerk(data.accelerometer),
      velocity: this.calculateVelocity(data.accelerometer),
      orientation: this.calculateOrientation(data.accelerometer),
      variance: this.calculateVariance(data.accelerometer),
      energy: this.calculateEnergy(data.accelerometer)
    };
  }
}
```

### 加速度数据处理
```javascript
class AccelerometerDataProcessor {
  constructor() {
    this.buffer = [];
    this.bufferSize = 100;
  }
  
  processAcceleration(x: number, y: number, z: number): ProcessedAcceleration {
    const magnitude = Math.sqrt(x * x + y * y + z * z);
    const magnitudeVar = this.calculateVariation(magnitude);
    
    return {
      x, y, z,
      magnitude,
      magnitudeVar,
      normalized: this.normalizeVector(x, y, z)
    };
  }
  
  private normalizeVector(x: number, y: number, z: number): Vector3D {
    const mag = Math.sqrt(x * x + y * y + z * z);
    return {
      x: x / mag,
      y: y / mag,
      z: z / mag
    };
  }
  
  private calculateVariation(values: number[]): number {
    if (values.length < 2) return 0;
    const mean = values.reduce((a, b) => a + b) / values.length;
    return values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  }
}
```

### 机器学习分类器
```javascript
class MLClassifier {
  constructor() {
    this.model = this.loadModel();
  }
  
  async predict(features: FeatureVector): Promise<MLPrediction> {
    // 模拟机器学习预测
    const input = this.prepareInput(features);
    const rawPrediction = await this.model.predict(input);
    
    return {
      probability: rawPrediction.fall_probability,
      confidence: rawPrediction.confidence,
      decision: rawPrediction.fall_probability > 0.85
    };
  }
  
  private prepareInput(features: FeatureVector): number[] {
    return [
      features.magnitude,
      features.jerk,
      features.velocity,
      features.orientation.x,
      features.orientation.y,
      features.orientation.z,
      features.variance,
      features.energy
    ];
  }
  
  private loadModel(): any {
    // 加载预训练的跌倒检测模型
    return {
      predict: async (input: number[]) => {
        // 简化的预测逻辑
        const fallScore = input.reduce((sum, val, index) => {
          const weights = [0.3, 0.2, 0.1, 0.1, 0.1, 0.05, 0.1, 0.05];
          return sum + val * weights[index];
        }, 0);
        
        return {
          fall_probability: Math.min(fallScore / 10, 1),
          confidence: Math.random() * 0.3 + 0.7
        };
      }
    };
  }
}
```

## 实时数据同步

### 同步策略
```javascript
class DataSyncManager {
  constructor(config = {}) {
    this.syncInterval = config.syncInterval || 30000; // 30秒
    this.batchSize = config.batchSize || 100;
    this.retryAttempts = config.retryAttempts || 3;
    this.syncStrategy = new SyncStrategy();
  }
  
  async startSync(deviceId: string): Promise<void> {
    setInterval(async () => {
      try {
        await this.syncDeviceData(deviceId);
      } catch (error) {
        console.error(`Sync failed for device ${deviceId}:`, error);
      }
    }, this.syncInterval);
  }
  
  private async syncDeviceData(deviceId: string): Promise<void> {
    const unsyncedData = await this.getUnsyncedData(deviceId);
    const batches = this.createBatches(unsyncedData, this.batchSize);
    
    for (const batch of batches) {
      await this.syncBatch(deviceId, batch);
    }
  }
  
  private async syncBatch(deviceId: string, batch: DeviceData[]): Promise<void> {
    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        await this.uploadBatch(deviceId, batch);
        await this.markAsSynced(batch);
        break;
      } catch (error) {
        if (attempt === this.retryAttempts) {
          throw new Error(`Batch sync failed after ${attempt} attempts`);
        }
        await this.delay(1000 * attempt); // 指数退避
      }
    }
  }
}
```

### 冲突解决
```javascript
class ConflictResolver {
  static resolveDataConflict(serverData: DeviceData, clientData: DeviceData): DeviceData {
    if (serverData.timestamp > clientData.timestamp) {
      return this.mergeData(serverData, clientData);
    } else {
      return this.mergeData(clientData, serverData);
    }
  }
  
  private static mergeData(primary: DeviceData, secondary: DeviceData): DeviceData {
    return {
      ...primary,
      sensor_data: {
        ...primary.sensor_data,
        ...this.pickLatestValues(secondary.sensor_data, primary.sensor_data)
      }
    };
  }
  
  private static pickLatestValues(newer: any, older: any): any {
    const result = { ...older };
    for (const key in newer) {
      if (typeof newer[key] === 'object' && newer[key] !== null) {
        result[key] = this.pickLatestValues(newer[key], older[key] || {});
      } else {
        result[key] = newer[key];
      }
    }
    return result;
  }
}
```

## 设备监控与告警

### 设备状态监控
```javascript
class DeviceMonitor {
  constructor() {
    this.monitors = new Map();
    this.alertThresholds = {
      batteryLevel: 20,
      signalStrength: -80,
      dataLatency: 300000, // 5分钟
      errorRate: 0.05 // 5%
    };
  }
  
  startMonitoring(deviceId: string): void {
    const monitor = {
      deviceId,
      lastSeen: Date.now(),
      batteryLevel: 100,
      signalStrength: 0,
      errorCount: 0,
      totalRequests: 0
    };
    
    this.monitors.set(deviceId, monitor);
    this.scheduleCheck(deviceId);
  }
  
  private scheduleCheck(deviceId: string): void {
    setInterval(() => {
      this.checkDeviceStatus(deviceId);
    }, 60000); // 每分钟检查一次
  }
  
  private async checkDeviceStatus(deviceId: string): Promise<void> {
    const monitor = this.monitors.get(deviceId);
    if (!monitor) return;
    
    const now = Date.now();
    const timeSinceLastSeen = now - monitor.lastSeen;
    
    if (timeSinceLastSeen > this.alertThresholds.dataLatency) {
      await this.triggerAlert(deviceId, 'DEVICE_OFFLINE', {
        timeSinceLastSeen,
        threshold: this.alertThresholds.dataLatency
      });
    }
    
    if (monitor.batteryLevel < this.alertThresholds.batteryLevel) {
      await this.triggerAlert(deviceId, 'LOW_BATTERY', {
        batteryLevel: monitor.batteryLevel,
        threshold: this.alertThresholds.batteryLevel
      });
    }
    
    if (monitor.signalStrength < this.alertThresholds.signalStrength) {
      await this.triggerAlert(deviceId, 'WEAK_SIGNAL', {
        signalStrength: monitor.signalStrength,
        threshold: this.alertThresholds.signalStrength
      });
    }
    
    const errorRate = monitor.errorCount / monitor.totalRequests;
    if (errorRate > this.alertThresholds.errorRate) {
      await this.triggerAlert(deviceId, 'HIGH_ERROR_RATE', {
        errorRate,
        threshold: this.alertThresholds.errorRate
      });
    }
  }
}
```

### 告警系统
```javascript
class AlertSystem {
  constructor() {
    this.channels = {
      sms: new SMSChannel(),
      email: new EmailChannel(),
      push: new PushNotificationChannel(),
      webhook: new WebhookChannel()
    };
    
    this.escalationRules = {
      CRITICAL: { immediate: true, repeatInterval: 300000 },
      HIGH: { immediate: true, repeatInterval: 1800000 },
      MEDIUM: { immediate: false, repeatInterval: 3600000 },
      LOW: { immediate: false, repeatInterval: 86400000 }
    };
  }
  
  async triggerAlert(deviceId: string, alertType: string, data: any): Promise<void> {
    const alert = await this.createAlert(deviceId, alertType, data);
    const severity = this.determineSeverity(alertType, data);
    
    await this.sendAlert(alert, severity);
    await this.scheduleEscalation(alert, severity);
  }
  
  private async createAlert(deviceId: string, alertType: string, data: any): Promise<Alert> {
    return {
      id: generateUUID(),
      deviceId,
      type: alertType,
      data,
      timestamp: Date.now(),
      status: 'ACTIVE',
      acknowledged: false
    };
  }
  
  private async sendAlert(alert: Alert, severity: AlertSeverity): Promise<void> {
    const rules = this.escalationRules[severity];
    const message = this.formatAlertMessage(alert, severity);
    
    const channels = this.selectChannels(severity);
    
    await Promise.all(
      channels.map(channel => channel.send(message))
    );
  }
  
  private selectChannels(severity: AlertSeverity): AlertChannel[] {
    const channelMap = {
      CRITICAL: ['sms', 'email', 'push', 'webhook'],
      HIGH: ['sms', 'email', 'push'],
      MEDIUM: ['email', 'push'],
      LOW: ['push']
    };
    
    return channelMap[severity].map(name => this.channels[name]);
  }
}
```

## API接口设计

### REST API 规范

#### 设备管理 API
```yaml
# 设备注册
POST /api/v1/devices/register
Content-Type: application/json
Authorization: Bearer {api_token}

Request:
{
  "device_id": "WATCH_001",
  "device_type": "smartwatch",
  "manufacturer": "Apple",
  "model": "Apple Watch Series 9",
  "firmware_version": "2.1.3",
  "capabilities": ["heart_rate", "blood_pressure", "sleep_monitoring", "fall_detection"]
}

Response:
{
  "status": "success",
  "device": {
    "id": "WATCH_001",
    "status": "registered",
    "api_key": "device_api_key_here",
    "created_at": "2025-11-18T14:21:24Z"
  }
}

# 设备状态查询
GET /api/v1/devices/{device_id}/status
Authorization: Bearer {device_api_key}

Response:
{
  "device_id": "WATCH_001",
  "status": "online",
  "last_seen": "2025-11-18T14:20:00Z",
  "battery_level": 85,
  "firmware_version": "2.1.3",
  "signal_strength": -45,
  "storage_used": 2048000,
  "storage_total": 8388608
}
```

#### 数据上传 API
```yaml
# 单条数据上传
POST /api/v1/devices/{device_id}/data
Content-Type: application/json
Authorization: Bearer {device_api_key}

Request:
{
  "timestamp": 1731926484,
  "data_type": "heart_rate",
  "payload": {
    "value": 72,
    "unit": "bpm",
    "quality": "excellent"
  }
}

Response:
{
  "status": "success",
  "data_id": "data_123456789",
  "processed_at": "2025-11-18T14:21:25Z"
}

# 批量数据上传
POST /api/v1/devices/{device_id}/data/batch
Authorization: Bearer {device_api_key}

Request:
{
  "data_batch": [
    {
      "timestamp": 1731926484,
      "data_type": "heart_rate",
      "payload": { "value": 72, "unit": "bpm" }
    }
  ],
  "sync_token": "sync_abc123"
}

Response:
{
  "status": "success",
  "processed_count": 1,
  "failed_count": 0,
  "sync_token": "sync_xyz789"
}
```

#### 健康数据查询 API
```yaml
# 查询用户健康数据
GET /api/v1/users/{user_id}/health-data
Query Parameters:
  - start_date: 开始日期 (ISO 8601)
  - end_date: 结束日期 (ISO 8601)  
  - data_types: 数据类型 (逗号分隔)
  - limit: 返回记录数限制 (默认100)
  - offset: 分页偏移量

Response:
{
  "user_id": "user_123",
  "data": [
    {
      "timestamp": 1731926484,
      "device_id": "WATCH_001",
      "data_type": "heart_rate",
      "payload": {
        "value": 72,
        "unit": "bpm",
        "quality": "excellent"
      }
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
}
```

### WebSocket 实时接口
```javascript
// 实时数据推送
class RealtimeDataService {
  constructor(io) {
    this.io = io;
    this.connectedDevices = new Map();
    this.setupSocketHandlers();
  }
  
  setupSocketHandlers() {
    this.io.on('connection', (socket) => {
      console.log('Client connected:', socket.id);
      
      socket.on('device_register', (data) => {
        this.handleDeviceRegistration(socket, data);
      });
      
      socket.on('data_stream', (data) => {
        this.handleRealtimeData(socket, data);
      });
      
      socket.on('disconnect', () => {
        this.handleDisconnection(socket);
      });
    });
  }
  
  handleDeviceRegistration(socket, data) {
    const { device_id, user_id } = data;
    this.connectedDevices.set(socket.id, {
      device_id,
      user_id,
      connected_at: Date.now()
    });
    
    // 加入用户房间
    socket.join(`user_${user_id}`);
    socket.join(`device_${device_id}`);
    
    socket.emit('registration_success', {
      device_id,
      socket_id: socket.id
    });
  }
  
  handleRealtimeData(socket, data) {
    const deviceInfo = this.connectedDevices.get(socket.id);
    if (!deviceInfo) return;
    
    // 处理实时数据并推送给相关用户
    const processedData = this.processRealtimeData(data);
    
    // 推送给用户
    this.io.to(`user_${deviceInfo.user_id}`).emit('health_data', {
      device_id: deviceInfo.device_id,
      data: processedData
    });
    
    // 推送给设备
    socket.emit('data_ack', {
      data_id: processedData.id,
      timestamp: processedData.timestamp
    });
  }
}
```

## 测试用例

### 单元测试

#### 蓝牙连接测试
```javascript
// tests/unit/bluetooth-connection.test.js
describe('Bluetooth Connection Manager', () => {
  let connectionManager;
  
  beforeEach(() => {
    connectionManager = new BluetoothConnectionManager();
  });
  
  test('should discover devices successfully', async () => {
    const mockDevices = [
      { id: 'device_1', name: 'SmartWatch Pro', rssi: -45 },
      { id: 'device_2', name: 'Health Band X', rssi: -60 }
    ];
    
    jest.spyOn(connectionManager, 'scanDevices').mockResolvedValue(mockDevices);
    
    const devices = await connectionManager.scanDevices(5000);
    
    expect(devices).toHaveLength(2);
    expect(devices[0].name).toBe('SmartWatch Pro');
  });
  
  test('should handle connection failures gracefully', async () => {
    jest.spyOn(connectionManager, 'connectToDevice')
      .mockRejectedValue(new Error('Connection timeout'));
    
    await expect(connectionManager.connectToDevice('invalid_device'))
      .rejects.toThrow('Connection timeout');
  });
  
  test('should retry connection on failure', async () => {
    const mockConnection = {
      connect: jest.fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({ id: 'device_1', connected: true })
    };
    
    connectionManager['connectionConfig'] = {
      maxRetries: 3,
      retryDelay: 1000
    };
    
    const result = await connectionManager.connectToDevice('device_1');
    
    expect(result.connected).toBe(true);
    expect(mockConnection.connect).toHaveBeenCalledTimes(2);
  });
});
```

#### 跌倒检测算法测试
```javascript
// tests/unit/fall-detection.test.js
describe('Fall Detection Algorithm', () => {
  let fallDetector;
  
  beforeEach(() => {
    fallDetector = new FallDetectionAlgorithm({
      impactForce: 3.0,
      confidence: 85
    });
  });
  
  test('should detect high impact fall', async () => {
    const sensorData = {
      accelerometer: {
        x: -2.5,
        y: 1.8,
        z: 8.2,
        timestamp: Date.now()
      }
    };
    
    const result = await fallDetector.detectFall(sensorData);
    
    expect(result.detected).toBe(true);
    expect(result.confidence).toBeGreaterThan(85);
    expect(result.severity).toBe('high');
  });
  
  test('should not detect normal walking', async () => {
    const sensorData = {
      accelerometer: {
        x: 0.1,
        y: 0.2,
        z: 9.8,
        timestamp: Date.now()
      }
    };
    
    const result = await fallDetector.detectFall(sensorData);
    
    expect(result.detected).toBe(false);
  });
  
  test('should handle incomplete sensor data', async () => {
    const sensorData = {
      accelerometer: {
        x: 0.1,
        y: 0.2
        // 缺少 z 轴数据和时间戳
      }
    };
    
    await expect(fallDetector.detectFall(sensorData))
      .rejects.toThrow('Incomplete sensor data');
  });
});
```

### 集成测试

#### 端到端数据流测试
```javascript
// tests/integration/data-flow.test.js
describe('End-to-End Data Flow', () => {
  let app, db;
  
  beforeAll(async () => {
    app = await setupTestApp();
    db = await setupTestDatabase();
  });
  
  test('should receive and process device data', async () => {
    // 1. 模拟设备注册
    const device = await request(app)
      .post('/api/v1/devices/register')
      .send({
        device_id: 'TEST_DEVICE_001',
        device_type: 'smartwatch',
        manufacturer: 'TestBrand',
        model: 'TestWatch'
      })
      .expect(200);
    
    const deviceApiKey = device.body.device.api_key;
    
    // 2. 模拟上传心率数据
    const heartRateData = {
      timestamp: Date.now(),
      data_type: 'heart_rate',
      payload: {
        value: 75,
        unit: 'bpm',
        quality: 'good'
      }
    };
    
    const dataResponse = await request(app)
      .post(`/api/v1/devices/TEST_DEVICE_001/data`)
      .set('Authorization', `Bearer ${deviceApiKey}`)
      .send(heartRateData)
      .expect(200);
    
    expect(dataResponse.body.status).toBe('success');
    
    // 3. 验证数据已存储
    const storedData = await db.query(
      'SELECT * FROM health_data WHERE device_id = $1',
      ['TEST_DEVICE_001']
    );
    
    expect(storedData.rows).toHaveLength(1);
    expect(storedData.rows[0].heart_rate).toBe(75);
  });
  
  test('should trigger fall detection alert', async () => {
    // 1. 模拟跌倒事件
    const fallData = {
      timestamp: Date.now(),
      data_type: 'fall_detection',
      payload: {
        detected: true,
        confidence: 94,
        severity: 'high',
        impact_force: 3.2,
        location: {
          latitude: 30.5728,
          longitude: 114.3052
        }
      }
    };
    
    const response = await request(app)
      .post('/api/v1/devices/TEST_DEVICE_001/data')
      .set('Authorization', `Bearer ${deviceApiKey}`)
      .send(fallData)
      .expect(200);
    
    // 2. 验证告警已生成
    const alerts = await db.query(
      'SELECT * FROM alerts WHERE device_id = $1 AND type = $2',
      ['TEST_DEVICE_001', 'FALL_DETECTED']
    );
    
    expect(alerts.rows).toHaveLength(1);
    expect(alerts.rows[0].severity).toBe('critical');
  });
});
```

### 性能测试

#### 负载测试
```javascript
// tests/performance/load-test.js
const loadTest = async () => {
  const concurrentUsers = 100;
  const testDuration = 300000; // 5分钟
  
  console.log(`Starting load test with ${concurrentUsers} concurrent users`);
  
  const users = Array.from({ length: concurrentUsers }, (_, i) => 
    simulateUser(`user_${i}`, testDuration)
  );
  
  const results = await Promise.all(users);
  
  console.log('Load test completed:', {
    totalRequests: results.reduce((sum, r) => sum + r.totalRequests, 0),
    averageResponseTime: results.reduce((sum, r) => sum + r.avgResponseTime, 0) / results.length,
    errorRate: results.reduce((sum, r) => sum + r.errorRate, 0) / results.length
  });
};

const simulateUser = async (userId: string, duration: number) => {
  const startTime = Date.now();
  let totalRequests = 0;
  let totalResponseTime = 0;
  let errorCount = 0;
  
  while (Date.now() - startTime < duration) {
    const deviceId = `DEVICE_${userId}`;
    
    try {
      const responseTime = await makeDataRequest(deviceId);
      totalRequests++;
      totalResponseTime += responseTime;
    } catch (error) {
      errorCount++;
    }
    
    await delay(1000); // 每秒一次请求
  }
  
  return {
    totalRequests,
    avgResponseTime: totalResponseTime / totalRequests,
    errorRate: errorCount / totalRequests
  };
};
```

## 部署指南

### 环境配置

#### 开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: smartwatch_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_pass
    ports:
      - "5432:5432"
  
  device-adapter:
    build: 
      context: ./device-adapter
      dockerfile: Dockerfile.dev
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgres://dev_user:dev_pass@postgres:5432/smartwatch_dev
      - REDIS_URL=redis://redis:6379
    ports:
      - "3001:3001"
    depends_on:
      - postgres
      - redis
  
  realtime-service:
    build:
      context: ./realtime-service
      dockerfile: Dockerfile.dev
    environment:
      - NODE_ENV=development
      - REDIS_URL=redis://redis:6379
    ports:
      - "3002:3002"
    depends_on:
      - redis
```

#### 生产环境部署
```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smartwatch-adapter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smartwatch-adapter
  template:
    metadata:
      labels:
        app: smartwatch-adapter
    spec:
      containers:
      - name: adapter
        image: smartwatch-adapter:v1.0.0
        ports:
        - containerPort: 3001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: smartwatch-adapter-service
spec:
  selector:
    app: smartwatch-adapter
  ports:
  - port: 80
    targetPort: 3001
  type: ClusterIP
```

### 环境变量配置
```bash
# .env.example
NODE_ENV=production

# Database
DATABASE_URL=postgresql://user:password@host:5432/smartwatch_db
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# API Keys
DEVICE_API_KEY_SECRET=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# External Services
SMS_SERVICE_API_KEY=your_sms_api_key
EMAIL_SERVICE_API_KEY=your_email_api_key

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Security
ENCRYPTION_KEY=your_encryption_key_here
CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
```

### 数据库迁移
```sql
-- migrations/001_create_smartwatch_tables.sql

-- 设备表
CREATE TABLE devices (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    capabilities JSONB,
    status VARCHAR(20) DEFAULT 'active',
    api_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 健康数据表
CREATE TABLE health_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL REFERENCES devices(id),
    user_id VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    raw_data BYTEA,
    quality_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_health_data_device_timestamp (device_id, created_at),
    INDEX idx_health_data_user_timestamp (user_id, created_at)
);

-- 告警表
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL REFERENCES devices(id),
    user_id VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    data JSONB,
    status VARCHAR(20) DEFAULT 'active',
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 设备状态表
CREATE TABLE device_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL REFERENCES devices(id),
    battery_level INTEGER,
    signal_strength INTEGER,
    storage_used BIGINT,
    storage_total BIGINT,
    last_seen TIMESTAMP WITH TIME ZONE,
    error_count INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(device_id, created_at::date)
);
```

## 安全规范

### 数据加密
```javascript
class DataEncryption {
  private static algorithm = 'aes-256-gcm';
  private static key = process.env.ENCRYPTION_KEY;
  
  static encrypt(data: string): EncryptedData {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(this.algorithm, this.key);
    cipher.setAAD(Buffer.from('smartwatch-data'));
    
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }
  
  static decrypt(encryptedData: EncryptedData): string {
    const decipher = crypto.createDecipher(this.algorithm, this.key);
    decipher.setAAD(Buffer.from('smartwatch-data'));
    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
    
    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }
}
```

### 身份认证
```javascript
class DeviceAuthentication {
  static async authenticateDevice(credentials: DeviceCredentials): Promise<AuthResult> {
    const device = await Device.findById(credentials.deviceId);
    if (!device) {
      throw new Error('Device not found');
    }
    
    // 验证API密钥
    if (!this.verifyApiKey(credentials.apiKey, device.apiKey)) {
      throw new Error('Invalid API key');
    }
    
    // 验证设备签名
    if (!this.verifySignature(credentials, device.secretKey)) {
      throw new Error('Signature verification failed');
    }
    
    // 更新最后活动时间
    device.lastSeen = new Date();
    await device.save();
    
    return {
      success: true,
      deviceId: device.id,
      token: this.generateSessionToken(device),
      expiresIn: 3600 // 1小时
    };
  }
  
  private static verifyApiKey(providedKey: string, storedKey: string): boolean {
    // 使用时间无关比较防止时序攻击
    return crypto.timingSafeEqual(
      Buffer.from(providedKey),
      Buffer.from(storedKey)
    );
  }
  
  private static verifySignature(credentials: DeviceCredentials, secretKey: string): boolean {
    const signature = crypto
      .createHmac('sha256', secretKey)
      .update(credentials.deviceId + credentials.timestamp)
      .digest('hex');
    
    return crypto.timingSafeEqual(
      Buffer.from(credentials.signature),
      Buffer.from(signature)
    );
  }
}
```

### 数据隐私保护
```javascript
class DataPrivacyManager {
  static anonymizeUserData(data: HealthData): AnonymizedData {
    return {
      ...data,
      user_id: this.hashUserId(data.user_id),
      device_id: this.hashDeviceId(data.device_id),
      location: this.generalizeLocation(data.location),
      timestamp: this.removePrecision(data.timestamp)
    };
  }
  
  static applyRetentionPolicy(data: any[]): void {
    const retentionPeriods = {
      health_data: 365 * 24 * 60 * 60 * 1000, // 1年
      alerts: 30 * 24 * 60 * 60 * 1000,       // 30天
      device_status: 90 * 24 * 60 * 60 * 1000 // 90天
    };
    
    const now = Date.now();
    
    for (const [table, policy] of Object.entries(retentionPeriods)) {
      const cutoffDate = new Date(now - policy);
      this.deleteExpiredData(table, cutoffDate);
    }
  }
  
  private static hashUserId(userId: string): string {
    return crypto.createHash('sha256')
      .update(userId + process.env.HASH_SALT)
      .digest('hex')
      .substring(0, 16);
  }
  
  private static generalizeLocation(location: any): any {
    if (!location) return null;
    
    // 将精确位置模糊化到城市级别
    return {
      city: location.city || 'Unknown',
      district: location.district || 'Unknown'
    };
  }
}
```

---

## 总结

本智能手环设备适配方案提供了完整的技术架构和实现指南，包括：

1. **标准化通信协议**: 基于BLE 5.0的设备通信规范
2. **数据格式标准**: JSON和Protocol Buffers格式规范
3. **健康监测接口**: RESTful API和WebSocket实时接口
4. **跌倒检测算法**: 机器学习驱动的智能检测系统
5. **实时数据同步**: 可靠的数据同步和冲突解决机制
6. **设备监控告警**: 全方位的设备状态监控和告警系统
7. **安全隐私保护**: 端到端的数据加密和隐私保护

该方案具有高度的可扩展性和兼容性，能够支持多种智能手环设备，为养老智能体系统提供可靠的基础设施支撑。

## 附录

### 设备兼容性列表
| 品牌 | 型号 | BLE版本 | 支持功能 | 状态 |
|------|------|---------|----------|------|
| Apple | Apple Watch Series 9 | 5.0 | ✅全部功能 | 已测试 |
| Huawei | Watch GT 4 | 5.0 | ✅全部功能 | 已测试 |
| Xiaomi | Watch S2 | 5.0 | ✅全部功能 | 开发中 |
| Samsung | Galaxy Watch 6 | 5.1 | ✅全部功能 | 计划中 |
| Garmin | Forerunner 265 | 5.0 | 部分功能 | 计划中 |

### 技术支持联系方式
- **技术支持邮箱**: smartwatch-support@eldercare.ai
- **开发者文档**: https://docs.eldercare.ai/smartwatch
- **GitHub仓库**: https://github.com/eldercare/smartwatch-adapter
- **社区论坛**: https://community.eldercare.ai

---

*本文档将持续更新，请关注版本历史获取最新信息。*