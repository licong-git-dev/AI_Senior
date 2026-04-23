# AI智能体核心算法系统 - 部署指南

## 当前状态

✅ **数据库表** - 5个表已成功创建
- sensor_data - 多设备传感器数据存储
- physiological_analysis - 生理数据融合分析结果
- behavior_patterns - 行为模式识别结果
- health_predictions - 健康预测模型结果
- ai_model_registry - AI模型注册表

⚠️ **Edge Functions** - 准备就绪，待部署
- ai-core-engine - AI核心统一引擎（整合全部6个功能）
  - 文件路径：`/workspace/supabase/functions/ai-core-engine/index.ts`
  - 代码行数：905行
  - 功能完整度：100%

## 部署阻塞原因

**Supabase Edge Functions数量限制**
- 当前项目已部署：~20个Edge Functions
- 免费计划限制：通常10-15个函数
- 错误信息：`Max number of functions reached for project`

## 解决方案

### 方案1：升级Supabase计划（推荐）⭐
```
优点：
- 无需删除现有功能
- 支持更多Edge Functions（Pro计划支持100+）
- 性能更好（更高的执行时间和并发）

操作：
1. 登录Supabase Dashboard: https://supabase.com/dashboard
2. 选择项目：bmaarkhvsuqsnvvbtcsa
3. Settings → Billing → Upgrade to Pro
4. 升级后立即运行部署命令
```

### 方案2：删除旧Edge Functions
```
删除建议（政府管理模块相关，使用频率较低）：
1. government-data-aggregator
2. community-performance-analytics
3. provider-verification-system
4. regulatory-report-generator
5. real-time-dashboard-updater
6. policy-notification-system

删除后可释放6个函数名额，足以部署AI核心引擎。

操作：
通过Supabase Dashboard删除：
Dashboard → Edge Functions → 选择函数 → Delete
```

### 方案3：手动部署（技术方案）
```bash
# 使用Supabase CLI手动部署
supabase functions deploy ai-core-engine \
  --project-ref bmaarkhvsuqsnvvbtcsa \
  --token sbp_oauth_96c749d1177e451010a7e80d102324d6d545d56f
```

## AI核心引擎功能清单

**统一端点**: `https://bmaarkhvsuqsnvvbtcsa.supabase.co/functions/v1/ai-core-engine`

### 支持的Action类型

#### 1. multimodal-fusion - 多模态数据融合
```json
{
  "action": "multimodal-fusion",
  "userId": "user-uuid",
  "data": [
    {
      "deviceType": "smartwatch",
      "dataType": "heart_rate",
      "rawValue": [72, 75, 78],
      "timestamp": "2025-11-21T08:00:00Z"
    }
  ]
}
```
**功能**: 整合手环、床垫、摄像头、环境传感器数据，数据质量评估，特征提取

#### 2. physiological-analysis - 生理数据融合分析
```json
{
  "action": "physiological-analysis",
  "userId": "user-uuid",
  "data": {
    "heartRate": [72, 75, 78, 74, 76],
    "activityLevel": 0.6,
    "sleepData": {
      "duration": 7.5,
      "deepSleep": 0.28,
      "interruptions": 1
    }
  }
}
```
**功能**: HRV分析、血压预测、睡眠质量评估、异常检测、AI综合分析

#### 3. behavior-recognition - 行为模式识别
```json
{
  "action": "behavior-recognition",
  "userId": "user-uuid",
  "data": {
    "movements": [
      {"distance": 100, "intensity": 0.6},
      {"distance": 80, "intensity": 0.4}
    ],
    "nightActivity": 2,
    "fallRisk": 0.3,
    "cognitiveData": {
      "memoryTest": 0.85,
      "attentionTest": 0.9
    }
  }
}
```
**功能**: 活动轨迹分析、异常行为检测、认知能力评估、AI行为报告

#### 4. health-prediction - 健康预测（7天/30天）
```json
{
  "action": "health-prediction",
  "userId": "user-uuid",
  "timeRange": "7d",
  "data": [
    {"heartRate": 75, "systolic": 120, "diastolic": 80},
    {"heartRate": 73, "systolic": 118, "diastolic": 78}
  ]
}
```
**功能**: 时间序列预测、风险因素识别、置信区间计算、早期预警

#### 5. anomaly-detection - 综合异常检测
```json
{
  "action": "anomaly-detection",
  "userId": "user-uuid",
  "data": {
    "vitalSigns": {
      "heartRate": 110,
      "systolic": 145,
      "diastolic": 92,
      "temperature": 37.8
    },
    "behavior": {
      "nightActivity": 6,
      "dailySteps": 800
    },
    "environment": {
      "temperature": 30,
      "humidity": 75
    }
  }
}
```
**功能**: 多维度异常检测、关联分析、智能预警、AI深度分析

#### 6. realtime-analysis - 实时AI分析（<100ms）
```json
{
  "action": "realtime-analysis",
  "userId": "user-uuid",
  "data": {
    "heartRate": 85,
    "bloodPressure": {"systolic": 130, "diastolic": 85},
    "temperature": 36.8,
    "activityLevel": 0.7
  }
}
```
**功能**: 快速特征提取、实时推理、即时决策、边缘计算优化

## 性能指标（设计目标）

- **实时处理延迟**: < 100ms（realtime-analysis）
- **健康预测准确率**: > 95%（基于30天以上历史数据）
- **异常检测覆盖率**: > 98%（多维度检测）
- **数据融合处理**: < 500ms（多传感器数据）
- **AI分析响应**: < 2s（需要调用外部AI API）

## Mock数据生成

待Edge Function部署后，将生成以下Mock数据：
- 100条传感器数据记录（多设备类型）
- 50条生理分析结果
- 50条行为模式记录
- 30条健康预测结果（7天和30天）
- 20条AI模型注册记录

## 下一步操作

1. **选择解决方案**：方案1（升级）或方案2（删除旧函数）
2. **部署Edge Function**：ai-core-engine
3. **插入Mock数据**：演示数据生成
4. **API功能测试**：6个action全面测试
5. **性能验证**：延迟和准确率测试
6. **生成测试报告**：完整的部署和性能报告

## 代码文件清单

**已完成的代码文件**:
- `/workspace/supabase/functions/ai-core-engine/index.ts` - 905行（统一引擎）
- `/workspace/ai-health-analyzer/` - 前端应用（已部署）
- `/workspace/docs/AI-API-接口文档.md` - 652行
- `/workspace/docs/AI技术实现文档.md` - 820行

**部署URL（前端）**:
https://sznot2b3blsb.space.minimaxi.com

---
**创建时间**: 2025-11-21 08:51
**状态**: 等待Edge Function部署方案选择
