# AI智能体核心算法系统 - API接口文档

## 系统概述

AI智能体核心算法系统是一个完整的多模态健康分析平台，为老年健康监控提供智能分析能力。

### 核心功能模块
1. 多模态数据融合处理
2. 生理数据融合分析
3. 行为模式识别
4. 健康预测模型
5. 实时AI分析引擎
6. 综合异常检测系统

---

## Edge Functions API接口

### 基础信息
- **Base URL**: `https://bmaarkhvsuqsnvvbtcsa.supabase.co/functions/v1`
- **认证**: Bearer Token (Supabase Anon Key)
- **Content-Type**: `application/json`

---

## 1. 多模态数据融合处理

### 接口
```
POST /multimodal-data-fusion
```

### 功能说明
整合手环、床垫、摄像头、环境传感器等多设备数据，执行时间对齐、数据清洗、特征提取。

### 请求参数
```json
{
  "user_id": "uuid",
  "data_sources": [
    { "type": "wristband" },
    { "type": "mattress" },
    { "type": "camera" },
    { "type": "environment" }
  ],
  "time_range": {
    "start": "2025-11-20T00:00:00Z",
    "end": "2025-11-20T23:59:59Z"
  }
}
```

### 响应示例
```json
{
  "data": {
    "fusion_id": "uuid",
    "fused_data": {
      "vital_signs": {
        "heart_rate": 72,
        "respiratory_rate": 16
      },
      "activity": {
        "steps": 5000,
        "calories": 300
      },
      "sleep": {
        "turn_count": 8,
        "sleep_stage": "deep"
      },
      "environment": {
        "temperature": 22,
        "humidity": 50,
        "light_level": 300
      }
    },
    "features": {
      "physiological": {...},
      "activity": {...},
      "sleep": {...},
      "environment": {...}
    },
    "quality_report": {
      "overall_quality": 0.95,
      "device_qualities": [...]
    },
    "message": "多模态数据融合成功"
  }
}
```

---

## 2. 生理数据融合分析

### 接口
```
POST /physiological-analyzer
```

### 功能说明
执行心率变异分析、血压预测、睡眠质量评估、生理指标异常检测，并生成AI综合分析报告。

### 请求参数
```json
{
  "user_id": "uuid",
  "analysis_type": "comprehensive",
  "time_range": {
    "start": "2025-11-13T00:00:00Z",
    "end": "2025-11-20T23:59:59Z"
  }
}
```

### 响应示例
```json
{
  "data": {
    "analysis_id": "uuid",
    "heart_rate_variability": {
      "status": "analyzed",
      "sdnn": 45.2,
      "rmssd": 38.5,
      "hrv_score": 72,
      "interpretation": "良好：整体状况不错，继续保持",
      "avg_heart_rate": 68,
      "heart_rate_range": { "min": 55, "max": 85 }
    },
    "blood_pressure_prediction": {
      "status": "predicted",
      "current": { "systolic": 120, "diastolic": 80 },
      "trend": { "systolic": "stable", "diastolic": "stable" },
      "predictions": [
        {
          "day": 1,
          "predicted_systolic": 121,
          "predicted_diastolic": 81,
          "confidence": 0.92
        }
      ],
      "risk_assessment": "正常范围：继续保持"
    },
    "sleep_quality": {
      "status": "assessed",
      "score": 0.78,
      "avg_sleep_hours": 7.5,
      "consistency_score": 0.85,
      "interpretation": "睡眠质量良好"
    },
    "anomaly_detection": {
      "detected": false,
      "count": 0,
      "details": []
    },
    "risk_level": "low",
    "confidence_score": 0.90,
    "ai_insights": "健康状况总体良好...",
    "data_points_analyzed": 250,
    "message": "生理数据分析完成"
  }
}
```

---

## 3. 行为模式识别

### 接口
```
POST /behavior-recognizer
```

### 功能说明
分析活动轨迹、检测异常行为、评估认知能力、识别日常活动模式。

### 请求参数
```json
{
  "user_id": "uuid",
  "analysis_period": "week"
}
```

### 响应示例
```json
{
  "data": {
    "pattern_id": "uuid",
    "activity_trajectory": {
      "status": "analyzed",
      "total_activities": 156,
      "activity_by_hour": [0, 0, 0, 0, 0, 0, 5, 12, ...],
      "peak_hours": [8, 14, 18],
      "activity_diversity": 6,
      "most_common_activity": { "type": "walking", "count": 45 },
      "mobility_score": 0.75
    },
    "behavior_timeline": {
      "events": [...],
      "daily_patterns": {
        "morning_routine": [...],
        "afternoon_routine": [...],
        "evening_routine": [...]
      },
      "pattern_consistency": 0.82
    },
    "abnormal_behaviors": {
      "detected": false,
      "count": 0,
      "details": []
    },
    "cognitive_assessment": {
      "score": 0.85,
      "level": "优秀",
      "factors": [...],
      "recommendation": "认知功能良好，建议继续保持活跃生活方式"
    },
    "ai_insights": "行为模式整体正常...",
    "pattern_confidence": 0.88,
    "message": "行为模式识别完成"
  }
}
```

---

## 4. 健康预测模型

### 接口
```
POST /health-predictor
```

### 功能说明
执行7天/30天时间序列预测，识别风险因素，计算个性化动态阈值，评估提前预警。

### 请求参数
```json
{
  "user_id": "uuid",
  "prediction_horizon": "7days",
  "prediction_types": ["heart_rate", "blood_pressure", "sleep_quality", "activity_level"]
}
```

### 响应示例
```json
{
  "data": {
    "predictions": {
      "heart_rate": {
        "status": "predicted",
        "current_value": 72,
        "trend": "stable",
        "trend_rate": 0.05,
        "volatility": 5.2,
        "predictions": [
          {
            "day": 1,
            "date": "2025-11-21",
            "predicted_value": 72.5,
            "lower_bound": 67.3,
            "upper_bound": 77.7,
            "confidence": 0.95
          }
        ],
        "model_accuracy": 0.89,
        "data_points": 100
      },
      "blood_pressure": {...},
      "sleep_quality": {...},
      "activity_level": {...}
    },
    "risk_factors": {
      "heart_rate": [],
      "blood_pressure": [],
      "sleep_quality": [],
      "activity_level": []
    },
    "personalized_thresholds": {
      "heart_rate": {
        "baseline": 72,
        "lower_threshold": 62,
        "upper_threshold": 82,
        "std_deviation": 5,
        "calculation_method": "personalized_2std"
      }
    },
    "early_warning": {
      "triggered": false,
      "types": [],
      "details": {},
      "urgency": "low",
      "recommended_actions": ["继续保持当前健康管理方式"]
    },
    "ai_report": "预测结果显示整体健康趋势平稳...",
    "prediction_horizon": "7days",
    "model_info": {
      "name": "time_series_arima_v1",
      "accuracy": "85-95%"
    },
    "message": "健康预测完成"
  }
}
```

---

## 5. 实时AI分析引擎

### 接口
```
POST /real-time-ai-engine
```

### 功能说明
实时推理引擎，边缘计算优化，目标延迟<100ms，快速健康状态评估和异常检测。

### 请求参数
```json
{
  "user_id": "uuid",
  "real_time_data": {
    "heart_rate": 72,
    "blood_pressure": { "systolic": 120, "diastolic": 80 },
    "spo2": 98,
    "temperature": 36.5,
    "activity": { "type": "walking", "intensity": 0.6, "steps": 150 }
  },
  "analysis_type": "all"
}
```

### 响应示例
```json
{
  "data": {
    "real_time_inference": {
      "model_version": "lightweight_v1",
      "inference_time_ms": 35,
      "results": {
        "health_status": {
          "score": 0.92,
          "status": "excellent",
          "confidence": 0.95
        },
        "anomaly_detection": {
          "anomalies_detected": 0,
          "anomalies": [],
          "requires_attention": false
        },
        "activity_assessment": {
          "level": "moderate",
          "recommendation": "活动强度适中，继续保持",
          "suitable_for_age_group": "elderly"
        }
      }
    },
    "risk_assessment": {
      "overall_risk_level": "low",
      "risk_score": 0.1,
      "alert_required": false,
      "immediate_actions": [],
      "monitoring_recommendations": []
    },
    "alert_triggered": false,
    "processing_time_ms": 45,
    "performance": {
      "target_met": true,
      "latency_ms": 45,
      "optimization_level": "edge_computing"
    },
    "message": "实时分析完成"
  }
}
```

---

## 6. 综合异常检测系统

### 接口
```
POST /anomaly-detector
```

### 功能说明
多维度异常检测（生命体征、行为、生理、环境、时间模式），关联分析，智能预警，覆盖率>98%。

### 请求参数
```json
{
  "user_id": "uuid",
  "detection_scope": "comprehensive",
  "time_window": 24
}
```

### 响应示例
```json
{
  "data": {
    "detection_summary": {
      "total_anomalies": 3,
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 1
    },
    "anomalies": [
      {
        "type": "tachycardia",
        "category": "vital_signs",
        "parameter": "heart_rate",
        "value": 125,
        "threshold": 120,
        "severity": "high",
        "timestamp": "2025-11-20T14:30:00Z",
        "description": "心率过高"
      },
      {
        "type": "poor_sleep",
        "category": "physiological",
        "parameter": "sleep_quality",
        "value": 0.42,
        "threshold": 0.5,
        "severity": "medium",
        "timestamp": "2025-11-20T08:00:00Z",
        "description": "睡眠质量较差"
      }
    ],
    "correlations": [
      {
        "pattern": "cardiovascular_risk",
        "involved_anomalies": ["blood_pressure", "poor_sleep"],
        "confidence": 0.70,
        "recommendation": "建议监测心血管健康"
      }
    ],
    "anomaly_report": {
      "summary": {...},
      "top_concerns": [...],
      "overall_risk": "medium",
      "recommendations": [...]
    },
    "ai_analysis": "检测到部分健康指标异常，建议关注...",
    "alerts_triggered": 1,
    "detection_scope": "comprehensive",
    "time_window_hours": 24,
    "data_sources": {
      "health_data_points": 250,
      "sensor_data_points": 180,
      "physiological_analyses": 7,
      "behavior_patterns": 3
    },
    "message": "异常检测完成"
  }
}
```

---

## 数据库表结构

### 1. sensor_data (传感器数据表)
```sql
- id: UUID (主键)
- user_id: UUID
- device_type: VARCHAR(50) (wristband, mattress, camera, environment)
- device_id: VARCHAR(100)
- sensor_type: VARCHAR(50)
- data_value: JSONB
- unit: VARCHAR(20)
- quality_score: DECIMAL(3,2)
- timestamp: TIMESTAMP
- created_at: TIMESTAMP
```

### 2. physiological_analysis (生理分析结果表)
```sql
- id: UUID (主键)
- user_id: UUID
- analysis_type: VARCHAR(50)
- heart_rate_variability: JSONB
- blood_pressure_prediction: JSONB
- sleep_quality_score: DECIMAL(3,2)
- anomaly_detected: BOOLEAN
- anomaly_details: JSONB
- risk_level: VARCHAR(20)
- confidence_score: DECIMAL(3,2)
- analyzed_at: TIMESTAMP
- data_range_start: TIMESTAMP
- data_range_end: TIMESTAMP
```

### 3. behavior_patterns (行为模式表)
```sql
- id: UUID (主键)
- user_id: UUID
- pattern_type: VARCHAR(50)
- activity_trajectory: JSONB
- behavior_timeline: JSONB
- cognitive_score: DECIMAL(3,2)
- abnormal_behaviors: JSONB
- pattern_confidence: DECIMAL(3,2)
- detection_timestamp: TIMESTAMP
- analysis_period: VARCHAR(20)
```

### 4. health_predictions (健康预测表)
```sql
- id: UUID (主键)
- user_id: UUID
- prediction_type: VARCHAR(50)
- prediction_horizon: VARCHAR(20)
- predicted_values: JSONB
- risk_factors: JSONB
- personalized_threshold: JSONB
- early_warning: BOOLEAN
- warning_details: JSONB
- model_name: VARCHAR(50)
- accuracy_score: DECIMAL(3,2)
- predicted_at: TIMESTAMP
- target_date: TIMESTAMP
```

### 5. ai_model_registry (AI模型注册表)
```sql
- id: UUID (主键)
- model_name: VARCHAR(100) UNIQUE
- model_type: VARCHAR(50)
- model_version: VARCHAR(20)
- description: TEXT
- architecture: VARCHAR(50)
- parameters: JSONB
- performance_metrics: JSONB
- training_date: TIMESTAMP
- last_updated: TIMESTAMP
- is_active: BOOLEAN
- update_frequency: VARCHAR(20)
```

---

## 错误码说明

### 通用错误码
- `MULTIMODAL_FUSION_FAILED`: 多模态数据融合失败
- `PHYSIOLOGICAL_ANALYSIS_FAILED`: 生理数据分析失败
- `BEHAVIOR_RECOGNITION_FAILED`: 行为模式识别失败
- `HEALTH_PREDICTION_FAILED`: 健康预测失败
- `REALTIME_ANALYSIS_FAILED`: 实时分析失败
- `ANOMALY_DETECTION_FAILED`: 异常检测失败

### 错误响应格式
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "详细错误信息"
  }
}
```

---

## 性能指标

### 系统性能标准
- **实时分析延迟**: <100ms (目标)
- **健康风险预测准确率**: >95%
- **异常检测覆盖率**: >98%
- **多模态数据融合成功率**: >99%
- **7天预测准确度**: 85-90%
- **30天预测准确度**: 75-85%

### 并发能力
- 支持1000+并发用户
- 单用户分析请求：每秒最多10次
- 批量数据处理：每次最多1000条记录

---

## 使用示例

### JavaScript/TypeScript示例
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://bmaarkhvsuqsnvvbtcsa.supabase.co',
  'YOUR_ANON_KEY'
)

// 执行生理数据分析
async function analyzePhysiologicalData(userId) {
  const { data, error } = await supabase.functions.invoke('physiological-analyzer', {
    body: {
      user_id: userId,
      analysis_type: 'comprehensive',
      time_range: {
        start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        end: new Date().toISOString()
      }
    }
  })

  if (error) {
    console.error('分析失败:', error)
    return null
  }

  return data.data
}

// 执行实时分析
async function performRealtimeAnalysis(userId, realtimeData) {
  const { data, error } = await supabase.functions.invoke('real-time-ai-engine', {
    body: {
      user_id: userId,
      real_time_data: realtimeData,
      analysis_type: 'all'
    }
  })

  if (error) {
    console.error('实时分析失败:', error)
    return null
  }

  console.log(`处理延迟: ${data.data.processing_time_ms}ms`)
  return data.data
}
```

---

## 注意事项

1. **数据隐私**: 所有健康数据严格加密，遵守HIPAA/GDPR规范
2. **实时性**: 实时分析Edge Function优先返回结果，异步保存数据
3. **历史数据**: 预测准确性与历史数据量正相关，建议至少30天数据
4. **AI模型**: 定期更新模型版本以提高准确性
5. **异常预警**: 危急异常自动触发health_alerts表记录
6. **并发限制**: 注意API调用频率限制，避免触发限流

---

## 联系支持

如有问题或建议，请联系技术支持团队。
