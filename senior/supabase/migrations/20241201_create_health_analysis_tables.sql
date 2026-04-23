-- 创建健康数据分析相关的数据库表

-- 健康数据类型表
CREATE TABLE IF NOT EXISTS health_data_types (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    unit VARCHAR(20),
    normal_range_min DECIMAL,
    normal_range_max DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 插入基本健康数据类型
INSERT INTO health_data_types (type_name, description, unit, normal_range_min, normal_range_max) VALUES
('heart_rate', '心率', 'bpm', 60, 100),
('systolic_bp', '收缩压', 'mmHg', 90, 140),
('diastolic_bp', '舒张压', 'mmHg', 60, 90),
('temperature', '体温', '°C', 36.0, 37.5),
('oxygen_saturation', '血氧饱和度', '%', 95, 100),
('activity_level', '活动水平', 'score', 0, 100),
('sleep_quality', '睡眠质量', 'score', 0, 100)
ON CONFLICT (type_name) DO NOTHING;

-- 用户基础健康档案表
CREATE TABLE IF NOT EXISTS user_health_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(10),
    height_cm INTEGER,
    weight_kg DECIMAL(5,2),
    medical_conditions JSONB DEFAULT '[]'::jsonb,
    medications JSONB DEFAULT '[]'::jsonb,
    emergency_contact JSONB,
    healthcare_provider JSONB,
    baseline_vitals JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 原始健康数据表
CREATE TABLE IF NOT EXISTS health_data_raw (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    data_type_id UUID REFERENCES health_data_types(id),
    device_type VARCHAR(50),
    device_id VARCHAR(100),
    value DECIMAL(10,4),
    unit VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE,
    location_data JSONB,
    metadata JSONB,
    data_quality_score DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 处理后的健康数据表
CREATE TABLE IF NOT EXISTS health_data_processed (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    data_type VARCHAR(50),
    processed_value JSONB,
    quality_score DECIMAL(3,2),
    analysis_features JSONB,
    anomaly_flags JSONB DEFAULT '[]'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HRV分析结果表
CREATE TABLE IF NOT EXISTS hrv_analysis_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    rr_intervals JSONB,
    time_domain_features JSONB,
    frequency_domain_features JSONB,
    stress_assessment JSONB,
    arrhythmia_detections JSONB,
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 睡眠分析结果表
CREATE TABLE IF NOT EXISTS sleep_analysis_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    sleep_session_id UUID,
    sleep_stages JSONB,
    sleep_quality_metrics JSONB,
    sleep_disorders_detected JSONB,
    sleep_score DECIMAL(5,2),
    recommendations JSONB DEFAULT '[]'::jsonb,
    analysis_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 行为模式分析表
CREATE TABLE IF NOT EXISTS behavior_pattern_analysis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    analysis_period_start TIMESTAMP WITH TIME ZONE,
    analysis_period_end TIMESTAMP WITH TIME ZONE,
    activity_patterns JSONB,
    routine_analysis JSONB,
    abnormality_detections JSONB DEFAULT '[]'::jsonb,
    habit_evolution JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 风险评估结果表
CREATE TABLE IF NOT EXISTS health_risk_assessments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    assessment_type VARCHAR(50),
    risk_scores JSONB,
    domain_risks JSONB,
    risk_factors JSONB,
    recommendations JSONB DEFAULT '[]'::jsonb,
    confidence_level DECIMAL(3,2),
    assessment_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 预测结果表
CREATE TABLE IF NOT EXISTS health_predictions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    prediction_type VARCHAR(50),
    prediction_horizon VARCHAR(20),
    predicted_values JSONB,
    confidence_intervals JSONB,
    model_version VARCHAR(20),
    actual_values JSONB,
    prediction_accuracy DECIMAL(3,2),
    prediction_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 健康预警表
CREATE TABLE IF NOT EXISTS health_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),
    severity VARCHAR(20), -- low, medium, high, critical
    title VARCHAR(200),
    message TEXT,
    trigger_data JSONB,
    alert_status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 设备数据同步表
CREATE TABLE IF NOT EXISTS device_data_sync (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    device_type VARCHAR(50),
    device_id VARCHAR(100),
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'success', -- success, failed, pending
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_health_data_raw_user_timestamp ON health_data_raw(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_health_data_processed_user_timestamp ON health_data_processed(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_hrv_analysis_user_timestamp ON hrv_analysis_results(user_id, analysis_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sleep_analysis_user_date ON sleep_analysis_results(user_id, analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_behavior_pattern_user_period ON behavior_pattern_analysis(user_id, analysis_period_start DESC);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_user_date ON health_risk_assessments(user_id, assessment_date DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_user_date ON health_predictions(user_id, prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_user_created ON health_alerts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_device_sync_user ON device_data_sync(user_id);

-- 创建触发器更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_health_profiles_updated_at 
    BEFORE UPDATE ON user_health_profiles 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_device_data_sync_updated_at 
    BEFORE UPDATE ON device_data_sync 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
