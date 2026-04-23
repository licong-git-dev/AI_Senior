# 智能养老平台数据库API文档

## Supabase项目信息

- **项目ID**: bmaarkhvsuqsnvvbtcsa
- **项目URL**: https://bmaarkhvsuqsnvvbtcsa.supabase.co
- **API Key**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw

## 核心数据表

### 1. sensor_data (传感器数据)
```sql
CREATE TABLE sensor_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  device_type VARCHAR(50),
  sensor_type VARCHAR(50),
  value DECIMAL,
  unit VARCHAR(20),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. health_alerts (健康告警)
```sql
CREATE TABLE health_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  alert_type VARCHAR(50),
  severity VARCHAR(20),
  message TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. health_predictions (健康预测)
```sql
CREATE TABLE health_predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  prediction_type VARCHAR(50),
  risk_level DECIMAL,
  confidence_score DECIMAL,
  prediction_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4. emergency_calls (紧急呼叫)
```sql
CREATE TABLE emergency_calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  emergency_type VARCHAR(50),
  location_data JSONB,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5. physiological_analysis (生理分析)
```sql
CREATE TABLE physiological_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  analysis_type VARCHAR(50),
  analysis_result JSONB,
  confidence_score DECIMAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6. behavior_patterns (行为模式)
```sql
CREATE TABLE behavior_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  pattern_type VARCHAR(50),
  pattern_data JSONB,
  confidence_score DECIMAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Edge Functions API

### 1. ai-core-engine
- **URL**: https://bmaarkhvsuqsnvvbtcsa.supabase.co/functions/v1/ai-core-engine
- **方法**: POST
- **功能**: AI核心引擎，支持多种分析模式

```javascript
// 请求示例
const response = await fetch('/functions/v1/ai-core-engine', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${supabaseKey}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mode: 'health_analysis',
    data: { /* 健康数据 */ }
  })
});
```

### 2. health-analysis
- **URL**: https://bmaarkhvsuqsnvvbtcsa.supabase.co/functions/v1/health-analysis
- **功能**: 健康数据分析

### 3. behavior-recognizer  
- **URL**: https://bmaarkhvsuqsnvvbtcsa.supabase.co/functions/v1/behavior-recognizer
- **功能**: 行为模式识别

### 4. anomaly-detector
- **URL**: https://bmaarkhvsuqsnvvbtcsa.supabase.co/functions/v1/anomaly-detector
- **功能**: 异常检测

## 实时订阅

### 数据订阅示例
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(url, key)

// 订阅传感器数据
const subscription = supabase
  .channel('sensor_data')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'sensor_data',
    filter: `user_id=eq.${userId}`
  }, (payload) => {
    console.log('新传感器数据:', payload)
  })
  .subscribe()
```

## 数据查询示例

### 获取用户健康数据
```sql
SELECT 
  sd.*,
  ha.alert_type,
  ha.severity as alert_severity
FROM sensor_data sd
LEFT JOIN health_alerts ha ON sd.user_id = ha.user_id
WHERE sd.user_id = 'user-uuid'
ORDER BY sd.timestamp DESC
LIMIT 100;
```

### 获取健康预测
```sql
SELECT 
  hp.*,
  pa.analysis_result,
  bp.pattern_data
FROM health_predictions hp
LEFT JOIN physiological_analysis pa ON hp.user_id = pa.user_id
LEFT JOIN behavior_patterns bp ON hp.user_id = bp.user_id
WHERE hp.user_id = 'user-uuid'
AND hp.created_at >= NOW() - INTERVAL '7 days'
ORDER BY hp.created_at DESC;
```

## 安全策略 (RLS)

### 传感器数据策略
```sql
CREATE POLICY "用户只能访问自己的传感器数据"
ON sensor_data FOR ALL
USING (auth.uid() = user_id);
```

### 健康告警策略
```sql
CREATE POLICY "用户只能查看自己的健康告警"
ON health_alerts FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "系统可以插入健康告警"
ON health_alerts FOR INSERT
WITH CHECK (true);
```

## 性能优化

### 索引建议
```sql
-- 传感器数据查询优化
CREATE INDEX idx_sensor_data_user_timestamp ON sensor_data(user_id, timestamp DESC);

-- 健康告警查询优化
CREATE INDEX idx_health_alerts_user_created ON health_alerts(user_id, created_at DESC);

-- 健康预测查询优化
CREATE INDEX idx_health_predictions_user_created ON health_predictions(user_id, created_at DESC);
```

### 查询优化
- 使用LIMIT限制查询结果
- 合理使用索引
- 避免N+1查询问题
- 使用实时订阅减少轮询

## 错误处理

### 常见错误码
- `PGRST116`: 表不存在
- `PGRST301`: 权限不足
- `23505`: 唯一约束冲突
- `42P01`: 表未定义

### 错误示例
```javascript
try {
  const { data, error } = await supabase
    .from('sensor_data')
    .insert(newData)
  
  if (error) {
    console.error('数据库错误:', error)
    throw error
  }
} catch (error) {
  console.error('操作失败:', error)
}
```

## 数据备份

### 定期备份策略
```bash
# 导出数据库
pg_dump -h db.bmaarkhvsuqsnvvbtcsa.supabase.co -U postgres -d postgres > backup.sql

# 恢复数据库
psql -h db.bmaarkhvsuqsnvvbtcsa.supabase.co -U postgres -d postgres < backup.sql
```

---
*API文档由MiniMax Agent生成*
