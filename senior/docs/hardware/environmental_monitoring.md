# 环境监测设备适配方案

## 1. 系统概述

本方案设计了一套完整的环境监测设备适配系统，集成温湿度传感器、空气质量检测器、门磁、烟雾检测器和智能家电控制功能，为智慧养老环境提供全方位监测与控制能力。

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    环境监测适配层                             │
├─────────────────────────────────────────────────────────────┤
│  数据采集引擎  │  设备控制引擎  │  告警处理引擎  │  数据分析引擎  │
├─────────────────────────────────────────────────────────────┤
│               协议适配层 (MQTT/HTTP/WebSocket)               │
├─────────────────────────────────────────────────────────────┤
│  温湿度传感器  │  空气质量监测  │  门磁开关  │  烟雾检测器  │  智能家电  │
└─────────────────────────────────────────────────────────────┘
```

## 2. 传感器协议设计

### 2.1 温湿度传感器协议

#### 2.1.1 硬件规格
- **传感器型号**: DHT22/DHT11/SHT30
- **通信协议**: I2C/UART/单总线
- **数据格式**: JSON
- **采集频率**: 30秒/次

#### 2.1.2 数据协议格式

```json
{
  "device_id": "temp_humidity_001",
  "device_type": "temperature_humidity_sensor",
  "timestamp": "2025-11-18T14:21:24Z",
  "data": {
    "temperature": {
      "value": 22.5,
      "unit": "°C",
      "accuracy": "±0.3°C"
    },
    "humidity": {
      "value": 65.2,
      "unit": "%",
      "accuracy": "±2%RH"
    }
  },
  "battery_level": 85,
  "signal_strength": -45,
  "status": "normal"
}
```

#### 2.1.3 通信协议

```python
# 温湿度传感器数据采集协议
class TemperatureHumidityProtocol:
    def __init__(self):
        self.command_map = {
            'READ_DATA': 'RD',
            'CALIBRATE': 'CAL',
            'RESET': 'RST',
            'SLEEP': 'SLP'
        }
    
    def parse_response(self, raw_data):
        """解析传感器返回数据"""
        if raw_data.startswith('TH:'):
            temp_humidity = raw_data[3:].split(',')
            return {
                'temperature': float(temp_humidity[0]),
                'humidity': float(temp_humidity[1])
            }
```

### 2.2 空气质量传感器协议

#### 2.2.1 硬件规格
- **传感器型号**: PMS5003/BME680/SGP30
- **检测项目**: PM2.5, PM10, CO2, VOC, HCHO
- **通信协议**: UART/USB
- **数据格式**: CSV/JSON

#### 2.2.2 数据协议格式

```json
{
  "device_id": "air_quality_001",
  "device_type": "air_quality_sensor",
  "timestamp": "2025-11-18T14:21:24Z",
  "data": {
    "pm2_5": {
      "value": 15.6,
      "unit": "μg/m³",
      "level": "良好"
    },
    "pm10": {
      "value": 28.3,
      "unit": "μg/m³",
      "level": "良好"
    },
    "co2": {
      "value": 450,
      "unit": "ppm",
      "level": "优秀"
    },
    "voc": {
      "value": 0.15,
      "unit": "mg/m³",
      "level": "正常"
    },
    "hcho": {
      "value": 0.02,
      "unit": "mg/m³",
      "level": "正常"
    }
  },
  "air_quality_index": {
    "aqi": 42,
    "level": "优",
    "primary_pollutant": "无"
  }
}
```

#### 2.2.3 数据传输协议

```python
# 空气质量传感器协议实现
class AirQualityProtocol:
    def __init__(self):
        self.baud_rate = 9600
        self.data_format = 'UTF-8'
        
    def send_command(self, command):
        """发送指令到传感器"""
        commands = {
            'READ_ALL': b'\x42\x4D\xE2\x00\x00\x01\x71',
            'SLEEP': b'\x42\x4D\xE4\x00\x00\x01\x73',
            'WAKEUP': b'\x42\x4D\xE4\x00\x00\x01\x74'
        }
        return commands.get(command)
    
    def parse_pms_data(self, raw_data):
        """解析PM2.5/PM10数据"""
        if len(raw_data) >= 32:
            pm1_0 = (raw_data[8] << 8) | raw_data[9]
            pm2_5 = (raw_data[10] << 8) | raw_data[11]
            pm10 = (raw_data[12] << 8) | raw_data[13]
            return {'pm1_0': pm1_0, 'pm2_5': pm2_5, 'pm10': pm10}
```

### 2.3 门磁传感器协议

#### 2.3.1 硬件规格
- **传感器类型**: 干簧管/霍尔效应传感器
- **通信协议**: Zigbee/蓝牙/WiFi
- **响应时间**: <100ms
- **检测距离**: 5-20mm

#### 2.3.2 数据协议格式

```json
{
  "device_id": "door_sensor_001",
  "device_type": "door_magnet_sensor",
  "timestamp": "2025-11-18T14:21:24Z",
  "data": {
    "door_status": "closed",  // open/closed
    "door_position": 0,       // 0-100% (0=完全关闭, 100=完全开启)
    "motion_detected": false,
    "tamper_alert": false
  },
  "event_type": "state_change",  // state_change/motion_detected/tamper
  "event_duration": 0  // 状态持续时间(秒)
}
```

#### 2.3.3 事件处理协议

```python
# 门磁传感器事件处理
class DoorSensorProtocol:
    def __init__(self):
        self.state_mapping = {
            0x00: "closed",
            0x01: "open",
            0x02: "ajar"
        }
    
    def process_event(self, raw_data):
        """处理门磁事件数据"""
        status = raw_data[0] & 0x03
        tamper = (raw_data[0] & 0x04) >> 2
        battery = raw_data[1]
        
        return {
            'door_status': self.state_mapping.get(status, "unknown"),
            'tamper_alert': bool(tamper),
            'battery_level': battery,
            'event_time': time.time()
        }
```

### 2.4 烟雾检测器协议

#### 2.4.1 硬件规格
- **检测原理**: 光电式/离子式
- **灵敏度**: 0.1dB/m
- **通信协议**: 独立/联网型
- **报警延迟**: <30秒

#### 2.4.2 数据协议格式

```json
{
  "device_id": "smoke_detector_001",
  "device_type": "smoke_detector",
  "timestamp": "2025-11-18T14:21:24Z",
  "data": {
    "smoke_level": 0.02,
    "smoke_density": "low",  // low/normal/high/critical
    "detector_status": "normal",  // normal/warning/alarm/fault
    "chamber_status": "clean",  // clean/dirty/fault
    "temperature": 25.3
  },
  "alarm_level": "none",  // none/warning/alarm
  "self_test_result": "pass"
}
```

#### 2.4.3 告警处理协议

```python
# 烟雾检测器告警处理
class SmokeDetectorProtocol:
    def __init__(self):
        self.alarm_thresholds = {
            'warning': 0.05,
            'alarm': 0.10,
            'critical': 0.20
        }
    
    def check_alarm_level(self, smoke_level):
        """检查告警级别"""
        if smoke_level >= self.alarm_thresholds['critical']:
            return 'critical'
        elif smoke_level >= self.alarm_thresholds['alarm']:
            return 'alarm'
        elif smoke_level >= self.alarm_thresholds['warning']:
            return 'warning'
        else:
            return 'normal'
    
    def generate_alert(self, device_data):
        """生成告警信息"""
        alarm_level = self.check_alarm_level(device_data['smoke_level'])
        
        if alarm_level in ['warning', 'alarm', 'critical']:
            return {
                'alert_id': f"smoke_{device_data['device_id']}_{int(time.time())}",
                'device_id': device_data['device_id'],
                'alert_type': 'SMOKE_DETECTED',
                'severity': alarm_level,
                'message': f"检测到烟雾，密度级别: {device_data['smoke_density']}",
                'timestamp': time.time(),
                'action_required': True
            }
```

## 3. 智能家电控制接口

### 3.1 空调控制系统

#### 3.1.1 控制协议

```json
{
  "device_id": "air_conditioner_001",
  "device_type": "air_conditioner",
  "command": "set_mode",
  "timestamp": "2025-11-18T14:21:24Z",
  "parameters": {
    "power": true,
    "mode": "auto",  // auto/cool/heat/fan/dry
    "target_temperature": 24,
    "fan_speed": "auto",  // low/medium/high/auto
    "swing": "auto"  // off/horizontal/vertical/auto
  }
}
```

#### 3.1.2 响应协议

```json
{
  "device_id": "air_conditioner_001",
  "command": "set_mode",
  "timestamp": "2025-11-18T14:21:25Z",
  "status": "success",
  "current_state": {
    "power": true,
    "mode": "auto",
    "current_temperature": 26.5,
    "target_temperature": 24,
    "fan_speed": "auto"
  }
}
```

### 3.2 空气净化器控制

```json
{
  "device_id": "air_purifier_001",
  "device_type": "air_purifier",
  "command": "set_auto_mode",
  "timestamp": "2025-11-18T14:21:24Z",
  "parameters": {
    "power": true,
    "auto_mode": true,
    "filter_life": 85,
    "child_lock": false
  }
}
```

### 3.3 智能照明控制

```json
{
  "device_id": "smart_light_001",
  "device_type": "smart_light",
  "command": "set_scene",
  "timestamp": "2025-11-18T14:21:24Z",
  "parameters": {
    "power": true,
    "brightness": 80,  // 0-100
    "color_temperature": 4000,  // Kelvin
    "scene": "reading",  // reading/sleep/relax/work
    "motion_sensor": true
  }
}
```

### 3.4 家电控制接口实现

```python
# 智能家电控制接口
class SmartApplianceController:
    def __init__(self):
        self.device_protocols = {
            'air_conditioner': self.control_air_conditioner,
            'air_purifier': self.control_air_purifier,
            'smart_light': self.control_smart_light,
            'humidifier': self.control_humidifier
        }
    
    def control_air_conditioner(self, device_id, command_data):
        """控制空调"""
        if command_data['command'] == 'auto_control':
            # 基于环境数据自动调节
            temp = command_data.get('current_temperature', 25)
            humidity = command_data.get('current_humidity', 50)
            
            if temp > 26:
                return self.set_ac_mode(device_id, {
                    'power': True,
                    'mode': 'cool',
                    'target_temperature': 24
                })
            elif temp < 18:
                return self.set_ac_mode(device_id, {
                    'power': True,
                    'mode': 'heat',
                    'target_temperature': 22
                })
            else:
                return self.set_ac_mode(device_id, {
                    'power': True,
                    'mode': 'auto',
                    'target_temperature': 22
                })
    
    def control_air_purifier(self, device_id, command_data):
        """控制空气净化器"""
        pm2_5 = command_data.get('pm2_5', 0)
        
        if pm2_5 > 35:  # AQI > 100
            return self.set_purifier_mode(device_id, {
                'power': True,
                'speed': 'high'
            })
        elif pm2_5 > 15:  # AQI > 50
            return self.set_purifier_mode(device_id, {
                'power': True,
                'speed': 'medium'
            })
        else:
            return self.set_purifier_mode(device_id, {
                'power': False
            })
```

## 4. 数据采集系统

### 4.1 数据采集架构

```python
# 数据采集引擎
class DataCollectionEngine:
    def __init__(self):
        self.sensors = {}
        self.data_queue = Queue()
        self.collection_threads = {}
        self.is_running = False
    
    def register_sensor(self, sensor_type, device_id, protocol_handler):
        """注册传感器"""
        self.sensors[device_id] = {
            'type': sensor_type,
            'handler': protocol_handler,
            'status': 'inactive',
            'last_data': None,
            'last_update': None
        }
    
    def start_collection(self, device_id, interval=30):
        """开始数据采集"""
        if device_id not in self.sensors:
            raise ValueError(f"Device {device_id} not registered")
        
        thread = threading.Thread(
            target=self._collect_data_loop,
            args=(device_id, interval)
        )
        thread.daemon = True
        thread.start()
        
        self.collection_threads[device_id] = thread
        self.sensors[device_id]['status'] = 'active'
    
    def _collect_data_loop(self, device_id, interval):
        """数据采集循环"""
        while self.is_running and device_id in self.collection_threads:
            try:
                sensor_info = self.sensors[device_id]
                handler = sensor_info['handler']
                
                # 获取传感器数据
                data = handler.read_data()
                if data:
                    # 添加时间戳和设备信息
                    data['collection_time'] = time.time()
                    data['device_id'] = device_id
                    
                    # 放入队列
                    self.data_queue.put(data)
                    sensor_info['last_data'] = data
                    sensor_info['last_update'] = time.time()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Data collection error for {device_id}: {e}")
                sensor_info['status'] = 'error'
                time.sleep(5)  # 错误时等待5秒后重试
```

### 4.2 数据预处理模块

```python
# 数据预处理
class DataPreprocessor:
    def __init__(self):
        self.filters = {
            'temperature': self._temperature_filter,
            'humidity': self._humidity_filter,
            'pm2_5': self._pm25_filter,
            'door_status': self._door_status_filter
        }
        self.outlier_detection = OutlierDetector()
    
    def process_sensor_data(self, raw_data):
        """处理传感器原始数据"""
        processed_data = raw_data.copy()
        
        # 数据验证
        if not self._validate_data(processed_data):
            logger.warning(f"Invalid data format: {processed_data}")
            return None
        
        # 异常值检测
        processed_data = self.outlier_detection.check_and_filter(processed_data)
        
        # 数据滤波
        for data_type, handler in self.filters.items():
            if data_type in processed_data.get('data', {}):
                processed_data['data'][data_type] = handler(
                    processed_data['data'][data_type]
                )
        
        # 添加数据质量标记
        processed_data['data_quality'] = self._assess_data_quality(processed_data)
        
        return processed_data
    
    def _temperature_filter(self, temp_data):
        """温度数据滤波"""
        # 中位数滤波
        if 'history' in temp_data:
            values = [d['value'] for d in temp_data['history'][-5:]]
            median_value = statistics.median(values)
            
            # 如果当前值与中位数偏差超过3度，进行校正
            if abs(temp_data['value'] - median_value) > 3:
                temp_data['value'] = median_value
                temp_data['filtered'] = True
        
        return temp_data
    
    def _validate_data(self, data):
        """数据验证"""
        required_fields = ['device_id', 'timestamp', 'data']
        
        for field in required_fields:
            if field not in data:
                return False
        
        # 验证时间戳格式
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except:
            return False
        
        return True
```

### 4.3 数据存储模块

```python
# 数据存储
class DataStorage:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection_pool = self._create_connection_pool()
        self.batch_size = 100
        self.cache = {}
    
    def store_sensor_data(self, data_list):
        """批量存储传感器数据"""
        if not data_list:
            return
        
        # 预处理数据
        processed_data = []
        for data in data_list:
            processed_data.append(self._format_for_storage(data))
        
        # 批量插入数据库
        with self.connection_pool.get() as conn:
            cursor = conn.cursor()
            
            # 插入环境数据表
            insert_query = """
                INSERT INTO environmental_data 
                (device_id, sensor_type, data_value, unit, timestamp, data_quality)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, processed_data)
            conn.commit()
        
        # 更新缓存
        self._update_cache(processed_data)
    
    def _format_for_storage(self, data):
        """格式化数据用于存储"""
        device_id = data['device_id']
        timestamp = data['timestamp']
        data_quality = data.get('data_quality', 'good')
        
        formatted_records = []
        for sensor_type, sensor_data in data['data'].items():
            if isinstance(sensor_data, dict) and 'value' in sensor_data:
                formatted_records.append((
                    device_id,
                    sensor_type,
                    sensor_data['value'],
                    sensor_data.get('unit', ''),
                    timestamp,
                    data_quality
                ))
        
        return formatted_records
    
    def query_historical_data(self, device_id, start_time, end_time, sensor_type=None):
        """查询历史数据"""
        query = """
            SELECT device_id, sensor_type, data_value, unit, timestamp, data_quality
            FROM environmental_data
            WHERE device_id = %s AND timestamp BETWEEN %s AND %s
        """
        params = [device_id, start_time, end_time]
        
        if sensor_type:
            query += " AND sensor_type = %s"
            params.append(sensor_type)
        
        query += " ORDER BY timestamp"
        
        with self.connection_pool.get() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
```

## 5. 环境异常告警机制

### 5.1 告警规则引擎

```python
# 环境告警规则引擎
class EnvironmentalAlertEngine:
    def __init__(self):
        self.alert_rules = {
            'high_temperature': {
                'threshold': 28,
                'duration': 300,  # 5分钟
                'severity': 'warning',
                'action': 'turn_on_ac'
            },
            'low_temperature': {
                'threshold': 16,
                'duration': 300,
                'severity': 'warning',
                'action': 'turn_on_heater'
            },
            'high_humidity': {
                'threshold': 70,
                'duration': 600,  # 10分钟
                'severity': 'warning',
                'action': 'activate_dehumidifier'
            },
            'low_humidity': {
                'threshold': 30,
                'duration': 600,
                'severity': 'warning',
                'action': 'activate_humidifier'
            },
            'high_pm25': {
                'threshold': 35,
                'duration': 60,  # 1分钟
                'severity': 'warning',
                'action': 'turn_on_purifier'
            },
            'smoke_detected': {
                'threshold': 0.05,
                'duration': 10,
                'severity': 'critical',
                'action': 'emergency_evacuation'
            },
            'door_opened_night': {
                'condition': 'time_between 22:00 and 06:00',
                'severity': 'warning',
                'action': 'notify_guardian'
            }
        }
        self.active_alerts = {}
        self.alert_history = []
    
    def check_conditions(self, sensor_data):
        """检查告警条件"""
        alerts = []
        
        for alert_type, rule in self.alert_rules.items():
            alert = self._check_single_condition(alert_type, rule, sensor_data)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def _check_single_condition(self, alert_type, rule, sensor_data):
        """检查单个告警条件"""
        data = sensor_data.get('data', {})
        timestamp = sensor_data.get('timestamp')
        device_id = sensor_data.get('device_id')
        
        # 温度告警
        if alert_type in ['high_temperature', 'low_temperature'] and 'temperature' in data:
            temp_value = data['temperature'].get('value')
            if temp_value is not None:
                threshold = rule['threshold']
                
                if alert_type == 'high_temperature' and temp_value > threshold:
                    return self._create_alert(alert_type, rule, device_id, timestamp, {
                        'current_value': temp_value,
                        'threshold': threshold,
                        'unit': '°C'
                    })
                
                elif alert_type == 'low_temperature' and temp_value < threshold:
                    return self._create_alert(alert_type, rule, device_id, timestamp, {
                        'current_value': temp_value,
                        'threshold': threshold,
                        'unit': '°C'
                    })
        
        # 湿度告警
        elif alert_type in ['high_humidity', 'low_humidity'] and 'humidity' in data:
            hum_value = data['humidity'].get('value')
            if hum_value is not None:
                threshold = rule['threshold']
                
                if alert_type == 'high_humidity' and hum_value > threshold:
                    return self._create_alert(alert_type, rule, device_id, timestamp, {
                        'current_value': hum_value,
                        'threshold': threshold,
                        'unit': '%'
                    })
                
                elif alert_type == 'low_humidity' and hum_value < threshold:
                    return self._create_alert(alert_type, rule, device_id, timestamp, {
                        'current_value': hum_value,
                        'threshold': threshold,
                        'unit': '%'
                    })
        
        # PM2.5告警
        elif alert_type == 'high_pm25' and 'pm2_5' in data:
            pm25_value = data['pm2_5'].get('value')
            if pm25_value is not None and pm25_value > rule['threshold']:
                return self._create_alert(alert_type, rule, device_id, timestamp, {
                    'current_value': pm25_value,
                    'threshold': rule['threshold'],
                    'unit': data['pm2_5'].get('unit', 'μg/m³')
                })
        
        # 烟雾告警
        elif alert_type == 'smoke_detected' and 'smoke_level' in data:
            smoke_value = data.get('smoke_level', 0)
            if smoke_value > rule['threshold']:
                return self._create_alert(alert_type, rule, device_id, timestamp, {
                    'current_value': smoke_value,
                    'threshold': rule['threshold'],
                    'smoke_density': data.get('smoke_density', 'unknown')
                })
        
        # 夜间门磁告警
        elif alert_type == 'door_opened_night' and 'door_status' in data:
            door_status = data['door_status'].get('value')
            current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = current_time.hour
            
            if door_status == 'open' and (hour >= 22 or hour <= 6):
                return self._create_alert(alert_type, rule, device_id, timestamp, {
                    'door_status': door_status,
                    'current_time': current_time.strftime('%H:%M:%S')
                })
        
        return None
    
    def _create_alert(self, alert_type, rule, device_id, timestamp, details):
        """创建告警对象"""
        alert_id = f"{alert_type}_{device_id}_{int(time.time())}"
        
        alert = {
            'alert_id': alert_id,
            'alert_type': alert_type,
            'device_id': device_id,
            'timestamp': timestamp,
            'severity': rule['severity'],
            'message': self._generate_alert_message(alert_type, details),
            'details': details,
            'action_required': rule['action'],
            'status': 'active',
            'created_at': time.time()
        }
        
        return alert
```

### 5.2 告警处理系统

```python
# 告警处理系统
class AlertProcessor:
    def __init__(self, alert_engine, appliance_controller):
        self.alert_engine = alert_engine
        self.appliance_controller = appliance_controller
        self.notification_service = NotificationService()
        self.action_handlers = {
            'turn_on_ac': self._handle_ac_control,
            'turn_on_heater': self._handle_heater_control,
            'turn_on_purifier': self._handle_purifier_control,
            'activate_dehumidifier': self._handle_dehumidifier_control,
            'activate_humidifier': self._handle_humidifier_control,
            'emergency_evacuation': self._handle_emergency_evacuation,
            'notify_guardian': self._handle_guardian_notification
        }
    
    def process_alerts(self, sensor_data):
        """处理告警"""
        alerts = self.alert_engine.check_conditions(sensor_data)
        
        for alert in alerts:
            # 检查是否是重复告警
            if self._is_duplicate_alert(alert):
                continue
            
            # 执行告警处理
            self._execute_alert_action(alert)
            
            # 发送通知
            self._send_notifications(alert)
            
            # 记录告警
            self._log_alert(alert)
            
            # 添加到活跃告警列表
            self.alert_engine.active_alerts[alert['alert_id']] = alert
    
    def _execute_alert_action(self, alert):
        """执行告警动作"""
        action = alert['action_required']
        handler = self.action_handlers.get(action)
        
        if handler:
            try:
                handler(alert)
                alert['action_executed'] = True
                alert['action_executed_at'] = time.time()
            except Exception as e:
                logger.error(f"Failed to execute action {action}: {e}")
                alert['action_error'] = str(e)
        else:
            logger.warning(f"No handler for action: {action}")
    
    def _handle_ac_control(self, alert):
        """处理空调控制"""
        if alert['alert_type'] == 'high_temperature':
            # 开启制冷模式
            self.appliance_controller.control_air_conditioner(
                'ac_001',
                {'command': 'set_mode', 'mode': 'cool', 'power': True}
            )
        elif alert['alert_type'] == 'low_temperature':
            # 开启制热模式
            self.appliance_controller.control_air_conditioner(
                'ac_001',
                {'command': 'set_mode', 'mode': 'heat', 'power': True}
            )
    
    def _handle_purifier_control(self, alert):
        """处理空气净化器控制"""
        self.appliance_controller.control_air_purifier(
            'purifier_001',
            {'command': 'set_auto_mode', 'power': True}
        )
    
    def _handle_emergency_evacuation(self, alert):
        """处理紧急疏散"""
        # 关闭所有电气设备
        self.appliance_controller.emergency_shutdown()
        
        # 发送紧急通知
        self.notification_service.send_emergency_alert({
            'title': '烟雾告警 - 紧急疏散',
            'message': f"检测到烟雾，密度: {alert['details'].get('smoke_density', 'unknown')}",
            'severity': 'critical',
            'urgent': True
        })
    
    def _send_notifications(self, alert):
        """发送告警通知"""
        if alert['severity'] == 'critical':
            # 紧急告警发送短信、邮件、推送
            self.notification_service.send_multi_channel_alert(alert)
        elif alert['severity'] == 'warning':
            # 一般告警发送推送和邮件
            self.notification_service.send_push_notification(alert)
```

### 5.3 通知服务

```python
# 通知服务
class NotificationService:
    def __init__(self):
        self.channels = {
            'push': PushNotificationChannel(),
            'sms': SMSChannel(),
            'email': EmailChannel(),
            'wechat': WeChatChannel()
        }
        self.notification_rules = {
            'critical': ['push', 'sms', 'email', 'wechat'],
            'warning': ['push', 'email'],
            'info': ['push']
        }
    
    def send_emergency_alert(self, alert_data):
        """发送紧急告警"""
        recipients = self._get_emergency_recipients()
        
        for channel_name, channel in self.channels.items():
            try:
                channel.send_emergency(recipients, alert_data)
            except Exception as e:
                logger.error(f"Failed to send emergency alert via {channel_name}: {e}")
    
    def send_push_notification(self, alert):
        """发送推送通知"""
        if self._should_send_notification(alert):
            message = {
                'title': self._get_notification_title(alert),
                'body': alert['message'],
                'data': {
                    'alert_id': alert['alert_id'],
                    'severity': alert['severity'],
                    'device_id': alert['device_id']
                }
            }
            
            # 发送到APP
            self.channels['push'].send_to_app_users(message)
            
            # 发送到微信小程序
            self.channels['wechat'].send_to_wechat_users(message)
```

## 6. 数据分析与智能控制

### 6.1 环境数据分析

```python
# 环境数据分析
class EnvironmentalDataAnalyzer:
    def __init__(self):
        self.data_aggregator = DataAggregator()
        self.pattern_detector = PatternDetector()
        self.predictor = EnvironmentPredictor()
    
    def analyze_environmental_trends(self, device_id, time_range='24h'):
        """分析环境趋势"""
        # 获取历史数据
        historical_data = self.data_aggregator.get_historical_data(
            device_id, time_range
        )
        
        # 趋势分析
        trends = {
            'temperature_trend': self._analyze_temperature_trend(historical_data),
            'humidity_trend': self._analyze_humidity_trend(historical_data),
            'air_quality_trend': self._analyze_air_quality_trend(historical_data)
        }
        
        # 模式识别
        patterns = self.pattern_detector.detect_patterns(historical_data)
        
        # 预测分析
        predictions = self.predictor.predict_future_conditions(historical_data)
        
        return {
            'trends': trends,
            'patterns': patterns,
            'predictions': predictions,
            'analysis_time': time.time()
        }
    
    def _analyze_temperature_trend(self, data):
        """分析温度趋势"""
        temp_data = [record['temperature'] for record in data if 'temperature' in record]
        
        if len(temp_data) < 2:
            return {'trend': 'insufficient_data'}
        
        # 计算线性回归
        x = list(range(len(temp_data)))
        slope = np.polyfit(x, temp_data, 1)[0]
        
        if slope > 0.1:
            trend = 'rising'
        elif slope < -0.1:
            trend = 'falling'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'slope': slope,
            'average': statistics.mean(temp_data),
            'min': min(temp_data),
            'max': max(temp_data),
            'variance': statistics.variance(temp_data)
        }
    
    def get_comfort_index(self, temperature, humidity, pm2_5):
        """计算舒适度指数"""
        # 温度舒适度 (基于22-26°C范围)
        temp_score = 100 - abs(temperature - 24) * 10
        temp_score = max(0, min(100, temp_score))
        
        # 湿度舒适度 (基于40-60%范围)
        hum_score = 100 - abs(humidity - 50) * 2
        hum_score = max(0, min(100, hum_score))
        
        # 空气质量舒适度
        if pm2_5 <= 15:
            air_score = 100
        elif pm2_5 <= 35:
            air_score = 80
        elif pm2_5 <= 75:
            air_score = 60
        else:
            air_score = 30
        
        # 综合舒适度指数
        comfort_index = (temp_score * 0.4 + hum_score * 0.3 + air_score * 0.3)
        
        return {
            'overall_comfort': comfort_index,
            'temperature_score': temp_score,
            'humidity_score': hum_score,
            'air_quality_score': air_score,
            'comfort_level': self._get_comfort_level(comfort_index)
        }
    
    def _get_comfort_level(self, comfort_index):
        """获取舒适度等级"""
        if comfort_index >= 80:
            return 'excellent'
        elif comfort_index >= 65:
            return 'good'
        elif comfort_index >= 50:
            return 'acceptable'
        elif comfort_index >= 35:
            return 'poor'
        else:
            return 'very_poor'
```

### 6.2 智能控制决策引擎

```python
# 智能控制决策引擎
class IntelligentControlEngine:
    def __init__(self, data_analyzer, appliance_controller):
        self.data_analyzer = data_analyzer
        self.appliance_controller = appliance_controller
        self.control_rules = self._load_control_rules()
        self.user_preferences = UserPreferenceManager()
    
    def make_intelligent_decisions(self, current_conditions, user_context=None):
        """做出智能控制决策"""
        decisions = []
        
        # 分析当前环境状况
        analysis = self.data_analyzer.analyze_environmental_trends(
            'all_devices', '1h'
        )
        
        # 获取用户偏好
        preferences = self.user_preferences.get_user_preferences(user_context)
        
        # 基于舒适度指数的决策
        comfort_index = self.data_analyzer.get_comfort_index(
            current_conditions.get('temperature', 22),
            current_conditions.get('humidity', 50),
            current_conditions.get('pm2_5', 15)
        )
        
        # 温度控制决策
        temp_decision = self._make_temperature_decision(
            current_conditions, analysis, preferences, comfort_index
        )
        if temp_decision:
            decisions.append(temp_decision)
        
        # 空气质量控制决策
        air_decision = self._make_air_quality_decision(
            current_conditions, analysis, preferences, comfort_index
        )
        if air_decision:
            decisions.append(air_decision)
        
        # 湿度控制决策
        humidity_decision = self._make_humidity_decision(
            current_conditions, analysis, preferences, comfort_index
        )
        if humidity_decision:
            decisions.append(humidity_decision)
        
        return decisions
    
    def _make_temperature_decision(self, current_data, analysis, preferences, comfort_index):
        """温度控制决策"""
        current_temp = current_data.get('temperature', 22)
        temp_preference = preferences.get('preferred_temperature', 24)
        
        # 如果温度舒适度较低，进行调节
        if comfort_index['temperature_score'] < 70:
            if current_temp > temp_preference + 2:
                return {
                    'action': 'cool',
                    'device': 'air_conditioner',
                    'target_temp': temp_preference,
                    'reason': f"当前温度{current_temp}°C高于偏好温度{temp_preference}°C",
                    'priority': 'medium'
                }
            elif current_temp < temp_preference - 2:
                return {
                    'action': 'heat',
                    'device': 'air_conditioner',
                    'target_temp': temp_preference,
                    'reason': f"当前温度{current_temp}°C低于偏好温度{temp_preference}°C",
                    'priority': 'medium'
                }
        
        return None
    
    def _make_air_quality_decision(self, current_data, analysis, preferences, comfort_index):
        """空气质量控制决策"""
        pm2_5 = current_data.get('pm2_5', 15)
        
        # 如果PM2.5超过阈值，开启空气净化器
        if pm2_5 > preferences.get('air_quality_threshold', 35):
            return {
                'action': 'purify_air',
                'device': 'air_purifier',
                'speed': 'auto' if pm2_5 > 75 else 'medium',
                'reason': f"PM2.5浓度{pm2_5}μg/m³超过阈值",
                'priority': 'high'
            }
        
        return None
    
    def execute_decisions(self, decisions):
        """执行控制决策"""
        executed_actions = []
        
        for decision in decisions:
            try:
                if decision['device'] == 'air_conditioner':
                    self.appliance_controller.control_air_conditioner(
                        'ac_001',
                        {
                            'command': 'set_mode',
                            'mode': decision['action'],
                            'target_temperature': decision.get('target_temp', 24)
                        }
                    )
                elif decision['device'] == 'air_purifier':
                    self.appliance_controller.control_air_purifier(
                        'purifier_001',
                        {
                            'command': 'set_speed',
                            'speed': decision.get('speed', 'auto')
                        }
                    )
                
                executed_actions.append({
                    'decision': decision,
                    'status': 'success',
                    'executed_at': time.time()
                })
                
            except Exception as e:
                executed_actions.append({
                    'decision': decision,
                    'status': 'failed',
                    'error': str(e),
                    'executed_at': time.time()
                })
        
        return executed_actions
```

### 6.3 用户偏好管理

```python
# 用户偏好管理
class UserPreferenceManager:
    def __init__(self):
        self.preferences_cache = {}
    
    def get_user_preferences(self, user_id=None):
        """获取用户偏好"""
        if user_id in self.preferences_cache:
            return self.preferences_cache[user_id]
        
        # 从数据库或配置文件加载偏好
        default_preferences = {
            'preferred_temperature': 24,
            'temperature_range': (20, 28),
            'preferred_humidity': 50,
            'humidity_range': (40, 60),
            'air_quality_threshold': 35,
            'night_mode_start': '22:00',
            'night_mode_end': '06:00',
            'energy_saving_mode': False,
            'auto_control_enabled': True,
            'notification_preferences': {
                'temperature_alerts': True,
                'air_quality_alerts': True,
                'security_alerts': True
            }
        }
        
        # 如果有特定用户偏好，合并默认偏好
        if user_id:
            user_specific = self._load_user_specific_preferences(user_id)
            default_preferences.update(user_specific)
        
        self.preferences_cache[user_id] = default_preferences
        return default_preferences
    
    def _load_user_specific_preferences(self, user_id):
        """加载用户特定偏好"""
        # 这里应该从数据库加载用户特定偏好
        # 暂时返回示例数据
        return {
            'preferred_temperature': 26,  # 老年人可能偏好稍高的温度
            'temperature_range': (22, 30),
            'energy_saving_mode': True,
            'night_mode_start': '21:00',
            'night_mode_end': '07:00'
        }
    
    def update_user_preference(self, user_id, preference_name, value):
        """更新用户偏好"""
        if user_id not in self.preferences_cache:
            self.preferences_cache[user_id] = self.get_user_preferences(user_id)
        
        self.preferences_cache[user_id][preference_name] = value
        
        # 保存到数据库
        self._save_to_database(user_id, preference_name, value)
```

## 7. 系统部署与配置

### 7.1 硬件设备配置

```yaml
# 设备配置文件: config/devices.yaml
devices:
  temperature_humidity_sensors:
    - device_id: "temp_humidity_001"
      location: "living_room"
      protocol: "uart"
      port: "/dev/ttyUSB0"
      baud_rate: 9600
      sampling_interval: 30
      
  air_quality_sensors:
    - device_id: "air_quality_001"
      location: "bedroom"
      protocol: "uart"
      port: "/dev/ttyUSB1"
      baud_rate: 9600
      sampling_interval: 60
      
  door_sensors:
    - device_id: "door_sensor_001"
      location: "front_door"
      protocol: "zigbee"
      network_id: "zigbee_network_1"
      sampling_interval: 1
      
  smoke_detectors:
    - device_id: "smoke_detector_001"
      location: "kitchen"
      protocol: "wireless"
      frequency: 433MHz
      sampling_interval: 5
      
  smart_appliances:
    air_conditioner:
      device_id: "ac_001"
      location: "living_room"
      protocol: "wifi"
      ip_address: "192.168.1.100"
      control_interface: "ir_blaster"
      
    air_purifier:
      device_id: "purifier_001"
      location: "bedroom"
      protocol: "wifi"
      ip_address: "192.168.1.101"
      
    smart_lights:
      - device_id: "light_001"
        location: "living_room"
        protocol: "zigbee"
        network_id: "zigbee_network_1"
```

### 7.2 系统配置

```python
# 系统配置文件
SYSTEM_CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'database': 'environmental_monitoring',
        'username': 'env_user',
        'password': 'env_password',
        'pool_size': 10
    },
    'mqtt_broker': {
        'host': 'localhost',
        'port': 1883,
        'username': 'mqtt_user',
        'password': 'mqtt_password',
        'client_id': 'environmental_monitoring_system'
    },
    'data_collection': {
        'batch_size': 100,
        'batch_timeout': 30,
        'retry_attempts': 3,
        'data_retention_days': 365
    },
    'alert_system': {
        'check_interval': 10,
        'duplicate_alert_cooldown': 300,  # 5分钟
        'max_alerts_per_hour': 10
    },
    'notifications': {
        'push_service': {
            'api_key': 'your_push_api_key',
            'api_url': 'https://api.push.com/send'
        },
        'sms_service': {
            'provider': 'aliyun',
            'access_key': 'your_access_key',
            'secret_key': 'your_secret_key'
        },
        'email_service': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your_email@gmail.com',
            'password': 'your_app_password'
        }
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': '/var/log/environmental_monitoring.log',
        'max_file_size': 100 * 1024 * 1024,  # 100MB
        'backup_count': 5
    }
}
```

### 7.3 启动脚本

```python
# 系统启动脚本: start_monitoring_system.py
#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from pathlib import Path

from data_collection import DataCollectionEngine
from alert_system import AlertProcessor, EnvironmentalAlertEngine
from smart_control import IntelligentControlEngine
from data_analysis import EnvironmentalDataAnalyzer
from storage import DataStorage

class EnvironmentalMonitoringSystem:
    def __init__(self, config_path="config/system.yaml"):
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # 初始化各个组件
        self.data_storage = DataStorage(self.config['database'])
        self.alert_engine = EnvironmentalAlertEngine()
        self.data_analyzer = EnvironmentalDataAnalyzer()
        self.control_engine = IntelligentControlEngine(
            self.data_analyzer, 
            SmartApplianceController()
        )
        self.alert_processor = AlertProcessor(
            self.alert_engine,
            self.control_engine.appliance_controller
        )
        
        self.data_collection = DataCollectionEngine()
        self.is_running = False
        
    def _load_config(self, config_path):
        """加载系统配置"""
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/environmental_monitoring.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def register_devices(self):
        """注册设备"""
        # 注册温湿度传感器
        temp_sensor = TemperatureHumiditySensor(
            device_id="temp_humidity_001",
            port="/dev/ttyUSB0",
            protocol_handler=TemperatureHumidityProtocol()
        )
        self.data_collection.register_sensor(
            "temperature_humidity", 
            "temp_humidity_001", 
            temp_sensor
        )
        
        # 注册空气质量传感器
        air_sensor = AirQualitySensor(
            device_id="air_quality_001",
            port="/dev/ttyUSB1",
            protocol_handler=AirQualityProtocol()
        )
        self.data_collection.register_sensor(
            "air_quality",
            "air_quality_001",
            air_sensor
        )
        
        # 注册门磁传感器
        door_sensor = DoorSensor(
            device_id="door_sensor_001",
            protocol_handler=DoorSensorProtocol()
        )
        self.data_collection.register_sensor(
            "door_magnet",
            "door_sensor_001",
            door_sensor
        )
        
        # 注册烟雾检测器
        smoke_detector = SmokeDetector(
            device_id="smoke_detector_001",
            protocol_handler=SmokeDetectorProtocol()
        )
        self.data_collection.register_sensor(
            "smoke_detector",
            "smoke_detector_001",
            smoke_detector
        )
    
    def start(self):
        """启动系统"""
        try:
            self.logger.info("启动环境监测系统...")
            
            # 设置信号处理器
            self.setup_signal_handlers()
            
            # 注册设备
            self.register_devices()
            
            # 启动数据采集
            self.data_collection.start_collection("temp_humidity_001", 30)
            self.data_collection.start_collection("air_quality_001", 60)
            self.data_collection.start_collection("door_sensor_001", 5)
            self.data_collection.start_collection("smoke_detector_001", 10)
            
            self.is_running = True
            self.logger.info("系统启动完成，开始监控...")
            
            # 主循环
            self.main_loop()
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            raise
    
    def main_loop(self):
        """主循环"""
        while self.is_running:
            try:
                # 从数据队列获取数据
                if not self.data_collection.data_queue.empty():
                    sensor_data = self.data_collection.data_queue.get()
                    
                    # 数据预处理
                    processed_data = DataPreprocessor().process_sensor_data(sensor_data)
                    if processed_data:
                        # 存储数据
                        self.data_storage.store_sensor_data([processed_data])
                        
                        # 处理告警
                        self.alert_processor.process_alerts(processed_data)
                        
                        # 智能控制决策
                        decisions = self.control_engine.make_intelligent_decisions(
                            processed_data.get('data', {})
                        )
                        if decisions:
                            self.control_engine.execute_decisions(decisions)
                
                # 清理过期告警
                self.alert_engine.cleanup_expired_alerts()
                
                # 短暂休眠
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                time.sleep(5)  # 错误时等待5秒
    
    def stop(self):
        """停止系统"""
        self.logger.info("正在停止系统...")
        self.is_running = False
        
        # 停止数据采集
        self.data_collection.is_running = False
        
        # 等待所有线程结束
        for thread in self.data_collection.collection_threads.values():
            thread.join(timeout=5)
        
        self.logger.info("系统已停止")

if __name__ == "__main__":
    system = EnvironmentalMonitoringSystem()
    system.start()
```

### 7.4 安装与部署脚本

```bash
#!/bin/bash
# install_monitoring_system.sh

echo "开始安装环境监测系统..."

# 创建必要目录
sudo mkdir -p /opt/environmental_monitoring
sudo mkdir -p /var/log/environmental_monitoring
sudo mkdir -p /var/lib/environmental_monitoring
sudo mkdir -p /etc/environmental_monitoring

# 复制系统文件
sudo cp -r src/ /opt/environmental_monitoring/
sudo cp config/ /opt/environmental_monitoring/
sudo cp requirements.txt /opt/environmental_monitoring/

# 安装Python依赖
cd /opt/environmental_monitoring
sudo pip3 install -r requirements.txt

# 设置权限
sudo chown -R environmental:environmental /opt/environmental_monitoring
sudo chown -R environmental:environmental /var/log/environmental_monitoring
sudo chown -R environmental:environmental /var/lib/environmental_monitoring

# 创建systemd服务
sudo cp deployment/environmental-monitoring.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable environmental-monitoring

# 创建数据库
sudo -u postgres createdb environmental_monitoring
sudo -u postgres psql -d environmental_monitoring -f deployment/init_database.sql

echo "系统安装完成！"
echo "启动命令: sudo systemctl start environmental-monitoring"
echo "查看状态: sudo systemctl status environmental-monitoring"
echo "查看日志: sudo journalctl -u environmental-monitoring -f"
```

## 8. 监控面板与可视化

### 8.1 Web监控面板

```html
<!-- 环境监测监控面板: monitoring_dashboard.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>环境监测系统</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <link rel="stylesheet" href="dashboard.css">
</head>
<body>
    <div class="dashboard-container">
        <!-- 顶部状态栏 -->
        <header class="dashboard-header">
            <h1>环境监测系统</h1>
            <div class="system-status">
                <span id="system-status-indicator" class="status-indicator online"></span>
                <span id="system-status-text">系统正常</span>
            </div>
        </header>

        <!-- 主要内容区域 -->
        <main class="dashboard-main">
            <!-- 左侧图表区域 -->
            <div class="charts-section">
                <!-- 温湿度图表 -->
                <div class="chart-card">
                    <h3>温湿度趋势</h3>
                    <canvas id="temperatureChart"></canvas>
                </div>

                <!-- 空气质量图表 -->
                <div class="chart-card">
                    <h3>空气质量监测</h3>
                    <canvas id="airQualityChart"></canvas>
                </div>

                <!-- 舒适度指数 -->
                <div class="chart-card">
                    <h3>舒适度指数</h3>
                    <div id="comfortGauge"></div>
                </div>
            </div>

            <!-- 右侧状态面板 -->
            <div class="status-panel">
                <!-- 实时数据 -->
                <div class="status-card">
                    <h3>实时数据</h3>
                    <div class="data-item">
                        <label>温度:</label>
                        <span id="current-temperature">--°C</span>
                    </div>
                    <div class="data-item">
                        <label>湿度:</label>
                        <span id="current-humidity">--%</span>
                    </div>
                    <div class="data-item">
                        <label>PM2.5:</label>
                        <span id="current-pm25">--μg/m³</span>
                    </div>
                    <div class="data-item">
                        <label>CO2:</label>
                        <span id="current-co2">--ppm</span>
                    </div>
                </div>

                <!-- 设备状态 -->
                <div class="status-card">
                    <h3>设备状态</h3>
                    <div class="device-status">
                        <div class="device-item">
                            <span class="device-name">温湿度传感器</span>
                            <span id="temp-sensor-status" class="device-indicator online"></span>
                        </div>
                        <div class="device-item">
                            <span class="device-name">空气质量传感器</span>
                            <span id="air-sensor-status" class="device-indicator online"></span>
                        </div>
                        <div class="device-item">
                            <span class="device-name">门磁传感器</span>
                            <span id="door-sensor-status" class="device-indicator online"></span>
                        </div>
                        <div class="device-item">
                            <span class="device-name">烟雾检测器</span>
                            <span id="smoke-sensor-status" class="device-indicator online"></span>
                        </div>
                    </div>
                </div>

                <!-- 告警信息 -->
                <div class="status-card">
                    <h3>活跃告警</h3>
                    <div id="active-alerts" class="alerts-container">
                        <!-- 动态添加告警信息 -->
                    </div>
                </div>

                <!-- 智能控制状态 -->
                <div class="status-card">
                    <h3>智能控制</h3>
                    <div class="control-status">
                        <div class="control-item">
                            <label>空调:</label>
                            <span id="ac-status">关闭</span>
                        </div>
                        <div class="control-item">
                            <label>空气净化器:</label>
                            <span id="purifier-status">关闭</span>
                        </div>
                        <div class="control-item">
                            <label>智能照明:</label>
                            <span id="light-status">自动</span>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script src="dashboard.js"></script>
</body>
</html>
```

### 8.2 监控面板JavaScript

```javascript
// dashboard.js - 监控面板脚本
class EnvironmentalMonitoringDashboard {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.initCharts();
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
    }

    initCharts() {
        // 温湿度图表
        const tempCtx = document.getElementById('temperatureChart').getContext('2d');
        this.charts.temperature = new Chart(tempCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '温度 (°C)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    yAxisID: 'y'
                }, {
                    label: '湿度 (%)',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '时间'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '温度 (°C)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '湿度 (%)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });

        // 空气质量图表
        const airCtx = document.getElementById('airQualityChart').getContext('2d');
        this.charts.airQuality = new Chart(airCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'PM2.5 (μg/m³)',
                    data: [],
                    borderColor: 'rgb(255, 205, 86)',
                    backgroundColor: 'rgba(255, 205, 86, 0.2)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'PM2.5 浓度'
                        }
                    }
                }
            }
        });

        // 舒适度仪表盘
        this.initComfortGauge();
    }

    initComfortGauge() {
        const gaugeDom = document.getElementById('comfortGauge');
        const gaugeChart = echarts.init(gaugeDom);

        const option = {
            series: [{
                name: '舒适度',
                type: 'gauge',
                progress: {
                    show: true,
                    width: 18
                },
                axisLine: {
                    lineStyle: {
                        width: 18,
                        color: [
                            [0.3, '#FF6E76'],
                            [0.7, '#FDDD60'],
                            [1, '#7CFFB2']
                        ]
                    }
                },
                axisTick: {
                    show: false
                },
                splitLine: {
                    length: 15,
                    lineStyle: {
                        width: 2,
                        color: '#999'
                    }
                },
                axisLabel: {
                    distance: 25,
                    color: '#999',
                    fontSize: 20
                },
                anchor: {
                    show: true,
                    showAbove: true,
                    size: 25,
                    itemStyle: {
                        borderWidth: 10
                    }
                },
                title: {
                    show: false
                },
                detail: {
                    valueAnimation: true,
                    fontSize: 60,
                    offsetCenter: [0, '70%'],
                    formatter: '{value}分'
                },
                data: [{
                    value: 0,
                    name: '舒适度'
                }]
            }]
        };

        gaugeChart.setOption(option);
        this.charts.comfortGauge = gaugeChart;
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/environmental-data`;
        
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            this.updateConnectionStatus(true);
        };

        this.ws.onclose = () => {
            console.log('WebSocket连接已断开');
            this.updateConnectionStatus(false);
            // 尝试重连
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealTimeData(data);
        };
    }

    handleRealTimeData(data) {
        switch (data.type) {
            case 'sensor_data':
                this.updateSensorData(data.payload);
                this.updateCharts(data.payload);
                break;
            case 'alert':
                this.handleAlert(data.payload);
                break;
            case 'device_status':
                this.updateDeviceStatus(data.payload);
                break;
            case 'control_status':
                this.updateControlStatus(data.payload);
                break;
        }
    }

    updateSensorData(data) {
        document.getElementById('current-temperature').textContent = 
            `${data.temperature?.value || '--'}°C`;
        document.getElementById('current-humidity').textContent = 
            `${data.humidity?.value || '--'}%`;
        document.getElementById('current-pm25').textContent = 
            `${data.pm2_5?.value || '--'}μg/m³`;
        document.getElementById('current-co2').textContent = 
            `${data.co2?.value || '--'}ppm`;
    }

    updateCharts(data) {
        const timestamp = new Date().toLocaleTimeString();

        // 更新温湿度图表
        if (this.charts.temperature.data.labels.length >= 20) {
            this.charts.temperature.data.labels.shift();
            this.charts.temperature.data.datasets[0].data.shift();
            this.charts.temperature.data.datasets[1].data.shift();
        }

        this.charts.temperature.data.labels.push(timestamp);
        this.charts.temperature.data.datasets[0].data.push(data.temperature?.value);
        this.charts.temperature.data.datasets[1].data.push(data.humidity?.value);
        this.charts.temperature.update('none');

        // 更新空气质量图表
        if (this.charts.airQuality.data.labels.length >= 20) {
            this.charts.airQuality.data.labels.shift();
            this.charts.airQuality.data.datasets[0].data.shift();
        }

        this.charts.airQuality.data.labels.push(timestamp);
        this.charts.airQuality.data.datasets[0].data.push(data.pm2_5?.value);
        this.charts.airQuality.update('none');

        // 更新舒适度仪表盘
        if (data.comfortIndex) {
            this.charts.comfortGauge.setOption({
                series: [{
                    data: [{
                        value: data.comfortIndex.overall_comfort,
                        name: '舒适度'
                    }]
                }]
            });
        }
    }

    handleAlert(alert) {
        const alertsContainer = document.getElementById('active-alerts');
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert-item ${alert.severity}`;
        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-type">${alert.alert_type}</span>
                <span class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="alert-message">${alert.message}</div>
        `;

        alertsContainer.insertBefore(alertElement, alertsContainer.firstChild);

        // 限制显示的告警数量
        while (alertsContainer.children.length > 5) {
            alertsContainer.removeChild(alertsContainer.lastChild);
        }

        // 显示告警提示
        if (alert.severity === 'critical') {
            this.showCriticalAlert(alert);
        }
    }

    updateDeviceStatus(deviceStatus) {
        Object.keys(deviceStatus).forEach(deviceId => {
            const statusElement = document.getElementById(`${deviceId.replace('_', '-')}-status`);
            if (statusElement) {
                statusElement.className = `device-indicator ${deviceStatus[deviceId].status}`;
            }
        });
    }

    updateControlStatus(controlStatus) {
        Object.keys(controlStatus).forEach(deviceId => {
            const statusElement = document.getElementById(`${deviceId.replace('_', '-')}-status`);
            if (statusElement) {
                statusElement.textContent = controlStatus[deviceId].status;
            }
        });
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById('system-status-indicator');
        const statusText = document.getElementById('system-status-text');
        
        if (connected) {
            indicator.className = 'status-indicator online';
            statusText.textContent = '系统正常';
        } else {
            indicator.className = 'status-indicator offline';
            statusText.textContent = '连接断开';
        }
    }

    showCriticalAlert(alert) {
        // 显示关键告警提示
        const alertModal = document.createElement('div');
        alertModal.className = 'critical-alert-modal';
        alertModal.innerHTML = `
            <div class="alert-modal-content">
                <h2>🚨 紧急告警</h2>
                <p>${alert.message}</p>
                <button onclick="this.parentElement.parentElement.remove()">确认</button>
            </div>
        `;
        document.body.appendChild(alertModal);
    }

    loadInitialData() {
        // 加载初始数据
        fetch('/api/environmental-data/recent')
            .then(response => response.json())
            .then(data => {
                // 初始化图表数据
                this.initializeChartsWithHistoricalData(data);
            })
            .catch(error => {
                console.error('加载初始数据失败:', error);
            });
    }

    initializeChartsWithHistoricalData(data) {
        // 使用历史数据初始化图表
        data.forEach(record => {
            const timestamp = new Date(record.timestamp).toLocaleTimeString();
            
            this.charts.temperature.data.labels.push(timestamp);
            this.charts.temperature.data.datasets[0].data.push(record.temperature);
            this.charts.temperature.data.datasets[1].data.push(record.humidity);
            
            this.charts.airQuality.data.labels.push(timestamp);
            this.charts.airQuality.data.datasets[0].data.push(record.pm2_5);
        });
        
        this.charts.temperature.update();
        this.charts.airQuality.update();
    }
}

// 页面加载完成后初始化仪表盘
document.addEventListener('DOMContentLoaded', () => {
    new EnvironmentalMonitoringDashboard();
});
```

## 9. 移动端应用

### 9.1 React Native移动端组件

```javascript
// MobileApp.js - 移动端环境监测应用
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

const EnvironmentalMonitoringApp = () => {
  const [sensorData, setSensorData] = useState({
    temperature: 0,
    humidity: 0,
    pm2_5: 0,
    co2: 0
  });
  
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [comfortIndex, setComfortIndex] = useState(0);

  useEffect(() => {
    initializeApp();
    setupWebSocket();
  }, []);

  const initializeApp = async () => {
    try {
      // 加载本地缓存数据
      const cachedData = await AsyncStorage.getItem('sensor_data');
      if (cachedData) {
        setSensorData(JSON.parse(cachedData));
      }

      // 加载告警历史
      const alertHistory = await AsyncStorage.getItem('alert_history');
      if (alertHistory) {
        setAlerts(JSON.parse(alertHistory));
      }

    } catch (error) {
      console.error('初始化应用失败:', error);
    }
  };

  const setupWebSocket = () => {
    // 这里应该连接到实际的WebSocket服务器
    const ws = new WebSocket('ws://your-server.com/ws/environmental-data');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleRealtimeData(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };
  };

  const handleRealtimeData = (data) => {
    setSensorData(data.sensorData);
    setComfortIndex(data.comfortIndex);
    
    if (data.alerts && data.alerts.length > 0) {
      handleNewAlerts(data.alerts);
    }
    
    // 保存到本地
    AsyncStorage.setItem('sensor_data', JSON.stringify(data.sensorData));
  };

  const handleNewAlerts = (newAlerts) => {
    const criticalAlerts = newAlerts.filter(alert => alert.severity === 'critical');
    
    if (criticalAlerts.length > 0) {
      Alert.alert(
        '🚨 紧急告警',
        criticalAlerts[0].message,
        [
          { text: '查看详情', onPress: () => setAlerts([...criticalAlerts, ...alerts]) },
          { text: '忽略', style: 'cancel' }
        ]
      );
    }
    
    setAlerts(prev => [...newAlerts, ...prev]);
  };

  const renderDashboard = () => (
    <ScrollView style={styles.container}>
      {/* 实时数据卡片 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>实时环境数据</Text>
        <View style={styles.dataGrid}>
          <DataItem 
            label="温度" 
            value={sensorData.temperature} 
            unit="°C" 
            color="#FF6E76" 
          />
          <DataItem 
            label="湿度" 
            value={sensorData.humidity} 
            unit="%" 
            color="#54A0FF" 
          />
          <DataItem 
            label="PM2.5" 
            value={sensorData.pm2_5} 
            unit="μg/m³" 
            color="#FFA726" 
          />
          <DataItem 
            label="CO2" 
            value={sensorData.co2} 
            unit="ppm" 
            color="#AB47BC" 
          />
        </View>
      </View>

      {/* 舒适度指数 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>舒适度指数</Text>
        <ComfortIndexGauge comfortIndex={comfortIndex} />
      </View>

      {/* 设备状态 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>设备状态</Text>
        <DeviceStatusList devices={devices} />
      </View>

      {/* 活跃告警 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>活跃告警</Text>
        <AlertList alerts={alerts} />
      </View>

      {/* 快速控制 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>快速控制</Text>
        <QuickControlPanel />
      </View>
    </ScrollView>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>环境监测</Text>
        <TouchableOpacity 
          style={styles.settingsButton}
          onPress={() => navigation.navigate('Settings')}
        >
          <Text style={styles.settingsButtonText}>设置</Text>
        </TouchableOpacity>
      </View>
      {renderDashboard()}
    </SafeAreaView>
  );
};

const DataItem = ({ label, value, unit, color }) => (
  <View style={styles.dataItem}>
    <Text style={[styles.dataValue, { color }]}>{value || '--'}</Text>
    <Text style={styles.dataUnit}>{unit}</Text>
    <Text style={styles.dataLabel}>{label}</Text>
  </View>
);

const ComfortIndexGauge = ({ comfortIndex }) => {
  const getComfortLevel = (index) => {
    if (index >= 80) return { text: '优秀', color: '#4CAF50' };
    if (index >= 65) return { text: '良好', color: '#8BC34A' };
    if (index >= 50) return { text: '一般', color: '#FFC107' };
    if (index >= 35) return { text: '较差', color: '#FF9800' };
    return { text: '很差', color: '#F44336' };
  };

  const level = getComfortLevel(comfortIndex);

  return (
    <View style={styles.comfortGauge}>
      <View style={[styles.comfortIndicator, { backgroundColor: level.color }]}>
        <Text style={styles.comfortValue}>{comfortIndex || '--'}</Text>
        <Text style={styles.comfortLabel}>分</Text>
      </View>
      <Text style={[styles.comfortLevel, { color: level.color }]}>{level.text}</Text>
    </View>
  );
};

const AlertList = ({ alerts }) => {
  if (alerts.length === 0) {
    return <Text style={styles.noDataText}>暂无活跃告警</Text>;
  }

  return (
    <View>
      {alerts.slice(0, 5).map((alert, index) => (
        <AlertItem key={index} alert={alert} />
      ))}
    </View>
  );
};

const AlertItem = ({ alert }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#F44336';
      case 'warning': return '#FF9800';
      case 'info': return '#2196F3';
      default: return '#757575';
    }
  };

  return (
    <View style={[styles.alertItem, { borderLeftColor: getSeverityColor(alert.severity) }]}>
      <View style={styles.alertHeader}>
        <Text style={styles.alertType}>{alert.alert_type}</Text>
        <Text style={styles.alertTime}>
          {new Date(alert.timestamp).toLocaleTimeString()}
        </Text>
      </View>
      <Text style={styles.alertMessage}>{alert.message}</Text>
    </View>
  );
};

const QuickControlPanel = () => (
  <View style={styles.controlPanel}>
    <TouchableOpacity style={styles.controlButton}>
      <Text style={styles.controlButtonText}>空调模式</Text>
    </TouchableOpacity>
    <TouchableOpacity style={styles.controlButton}>
      <Text style={styles.controlButtonText}>空气净化</Text>
    </TouchableOpacity>
    <TouchableOpacity style={styles.controlButton}>
      <Text style={styles.controlButtonText}>智能照明</Text>
    </TouchableOpacity>
  </View>
);

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0'
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333'
  },
  settingsButton: {
    padding: 8,
    backgroundColor: '#2196F3',
    borderRadius: 4
  },
  settingsButtonText: {
    color: '#fff',
    fontWeight: '500'
  },
  container: {
    flex: 1,
    padding: 16
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333'
  },
  dataGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between'
  },
  dataItem: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 16
  },
  dataValue: {
    fontSize: 24,
    fontWeight: 'bold'
  },
  dataUnit: {
    fontSize: 12,
    color: '#666',
    marginTop: 4
  },
  dataLabel: {
    fontSize: 14,
    color: '#999',
    marginTop: 4
  },
  comfortGauge: {
    alignItems: 'center'
  },
  comfortIndicator: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8
  },
  comfortValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff'
  },
  comfortLabel: {
    fontSize: 12,
    color: '#fff'
  },
  comfortLevel: {
    fontSize: 16,
    fontWeight: '500'
  },
  alertItem: {
    padding: 12,
    borderLeftWidth: 4,
    backgroundColor: '#fafafa',
    marginBottom: 8,
    borderRadius: 4
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4
  },
  alertType: {
    fontWeight: 'bold',
    color: '#333'
  },
  alertTime: {
    fontSize: 12,
    color: '#666'
  },
  alertMessage: {
    fontSize: 14,
    color: '#666'
  },
  controlPanel: {
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  controlButton: {
    flex: 1,
    backgroundColor: '#2196F3',
    paddingVertical: 12,
    marginHorizontal: 4,
    borderRadius: 4,
    alignItems: 'center'
  },
  controlButtonText: {
    color: '#fff',
    fontWeight: '500'
  },
  noDataText: {
    textAlign: 'center',
    color: '#999',
    fontStyle: 'italic'
  }
});

export default EnvironmentalMonitoringApp;
```

## 10. 系统维护与监控

### 10.1 系统健康监控

```python
# 系统健康监控
class SystemHealthMonitor:
    def __init__(self):
        self.health_checks = {
            'database': self.check_database_health,
            'mqtt_broker': self.check_mqtt_health,
            'sensor_devices': self.check_sensor_health,
            'data_collection': self.check_collection_health,
            'alert_system': self.check_alert_health,
            'storage_space': self.check_storage_health
        }
        self.health_status = {}
        self.alert_thresholds = {
            'sensor_offline_minutes': 10,
            'database_response_time': 5.0,
            'storage_usage_percent': 80,
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85
        }
    
    def run_health_checks(self):
        """运行健康检查"""
        results = {}
        
        for check_name, check_function in self.health_checks.items():
            try:
                result = check_function()
                results[check_name] = result
                
                # 如果检查失败，发送告警
                if not result['healthy']:
                    self.handle_health_alert(check_name, result)
                    
            except Exception as e:
                results[check_name] = {
                    'healthy': False,
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        self.health_status = results
        return results
    
    def check_database_health(self):
        """检查数据库健康状况"""
        try:
            start_time = time.time()
            
            # 执行简单查询测试
            result = execute_sql("SELECT 1")
            response_time = time.time() - start_time
            
            return {
                'healthy': response_time < self.alert_thresholds['database_response_time'],
                'response_time': response_time,
                'timestamp': time.time(),
                'details': 'Database connection OK'
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def check_sensor_health(self):
        """检查传感器设备健康状况"""
        sensor_status = {}
        overall_healthy = True
        
        # 检查所有注册的传感器
        for device_id, sensor_info in data_collection.sensors.items():
            last_update = sensor_info.get('last_update')
            if last_update:
                minutes_since_update = (time.time() - last_update) / 60
                is_healthy = minutes_since_update < self.alert_thresholds['sensor_offline_minutes']
            else:
                is_healthy = False
            
            sensor_status[device_id] = {
                'healthy': is_healthy,
                'last_update': last_update,
                'minutes_offline': (time.time() - last_update) / 60 if last_update else None
            }
            
            if not is_healthy:
                overall_healthy = False
        
        return {
            'healthy': overall_healthy,
            'sensor_status': sensor_status,
            'timestamp': time.time()
        }
    
    def check_storage_health(self):
        """检查存储空间健康状况"""
        try:
            # 检查磁盘使用情况
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            return {
                'healthy': usage_percent < self.alert_thresholds['storage_usage_percent'],
                'usage_percent': usage_percent,
                'free_gb': disk_usage.free / (1024**3),
                'total_gb': disk_usage.total / (1024**3),
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def generate_health_report(self):
        """生成健康报告"""
        health_data = self.run_health_checks()
        
        report = {
            'report_time': time.time(),
            'overall_health': all(check.get('healthy', False) for check in health_data.values()),
            'checks': health_data,
            'system_info': {
                'uptime': self.get_system_uptime(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'process_count': len(psutil.pids())
            }
        }
        
        return report
    
    def get_system_uptime(self):
        """获取系统运行时间"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            return uptime_seconds
        except:
            return 0
```

### 10.2 日志管理系统

```python
# 日志管理系统
class LoggingManager:
    def __init__(self, log_config):
        self.log_config = log_config
        self.setup_logging()
        self.log_buffer = []
        self.max_buffer_size = 1000
    
    def setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = Path(self.log_config['file']).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        formatter = logging.Formatter(self.log_config['format'])
        
        # 文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_config['file'],
            maxBytes=self.log_config['max_file_size'],
            backupCount=self.log_config['backup_count']
        )
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 配置根日志器
        logging.basicConfig(
            level=getattr(logging, self.log_config['level']),
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def log_sensor_data(self, device_id, sensor_data, data_quality='good'):
        """记录传感器数据"""
        log_entry = {
            'timestamp': time.time(),
            'event_type': 'sensor_data',
            'device_id': device_id,
            'data': sensor_data,
            'quality': data_quality
        }
        
        self.logger.info(f"Sensor data - Device: {device_id}, "
                        f"Data: {sensor_data}, Quality: {data_quality}")
        
        self.add_to_buffer(log_entry)
    
    def log_alert(self, alert_data):
        """记录告警信息"""
        log_entry = {
            'timestamp': time.time(),
            'event_type': 'alert',
            'alert_data': alert_data
        }
        
        severity = alert_data.get('severity', 'unknown')
        if severity == 'critical':
            self.logger.critical(f"CRITICAL ALERT: {alert_data['message']}")
        elif severity == 'warning':
            self.logger.warning(f"WARNING ALERT: {alert_data['message']}")
        else:
            self.logger.info(f"INFO ALERT: {alert_data['message']}")
        
        self.add_to_buffer(log_entry)
    
    def log_system_event(self, event_type, details):
        """记录系统事件"""
        log_entry = {
            'timestamp': time.time(),
            'event_type': 'system_event',
            'event_type_name': event_type,
            'details': details
        }
        
        self.logger.info(f"System event - {event_type}: {details}")
        self.add_to_buffer(log_entry)
    
    def log_error(self, error_type, error_message, context=None):
        """记录错误信息"""
        log_entry = {
            'timestamp': time.time(),
            'event_type': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'context': context
        }
        
        self.logger.error(f"Error - {error_type}: {error_message}")
        if context:
            self.logger.error(f"Context: {context}")
        
        self.add_to_buffer(log_entry)
    
    def add_to_buffer(self, log_entry):
        """添加到日志缓冲区"""
        self.log_buffer.append(log_entry)
        
        if len(self.log_buffer) >= self.max_buffer_size:
            self.flush_buffer()
    
    def flush_buffer(self):
        """刷新缓冲区到数据库或文件"""
        if not self.log_buffer:
            return
        
        try:
            # 将日志保存到数据库
            self.save_logs_to_database(self.log_buffer)
            self.log_buffer.clear()
        except Exception as e:
            self.logger.error(f"Failed to flush log buffer: {e}")
    
    def save_logs_to_database(self, log_entries):
        """保存日志到数据库"""
        query = """
            INSERT INTO system_logs 
            (timestamp, event_type, device_id, data, quality, alert_data, 
             system_event, error_type, error_message, context)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.data_storage.connection_pool.get() as conn:
            cursor = conn.cursor()
            
            for entry in log_entries:
                cursor.execute(query, (
                    entry['timestamp'],
                    entry['event_type'],
                    entry.get('device_id'),
                    json.dumps(entry.get('data')),
                    entry.get('quality'),
                    json.dumps(entry.get('alert_data')),
                    entry.get('event_type_name'),
                    entry.get('error_type'),
                    entry.get('error_message'),
                    json.dumps(entry.get('context'))
                ))
            
            conn.commit()
    
    def search_logs(self, start_time, end_time, event_type=None, device_id=None):
        """搜索日志"""
        query = """
            SELECT * FROM system_logs 
            WHERE timestamp BETWEEN %s AND %s
        """
        params = [start_time, end_time]
        
        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)
        
        if device_id:
            query += " AND device_id = %s"
            params.append(device_id)
        
        query += " ORDER BY timestamp DESC"
        
        with self.data_storage.connection_pool.get() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
```

## 总结

本环境监测设备适配方案提供了一个完整的企业级环境监测解决方案，具备以下核心特性：

### 1. **全面的设备支持**
- 支持多种传感器类型：温湿度、空气质量、门磁、烟雾检测器
- 兼容多种通信协议：UART、I2C、Zigbee、WiFi
- 统一的设备管理和配置系统

### 2. **智能数据分析**
- 实时数据采集和预处理
- 环境趋势分析和模式识别
- 舒适度指数计算
- 预测性维护分析

### 3. **智能控制引擎**
- 基于用户偏好的自动控制
- 环境参数自动调节
- 紧急情况自动响应
- 节能优化算法

### 4. **完善的告警系统**
- 多级告警机制
- 智能告警规则引擎
- 多渠道通知系统
- 告警历史管理

### 5. **可视化监控**
- Web端实时监控面板
- 移动端应用支持
- 数据图表展示
- 设备状态监控

### 6. **系统可靠性**
- 健康监控机制
- 自动故障恢复
- 数据备份策略
- 日志审计系统

该方案特别适用于智慧养老环境，能够为老年人提供安全、舒适、智能化的生活环境，同时为护理人员和家属提供实时监控和告警功能。