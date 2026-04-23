-- 智能健康风险预测系统 V2.0 数据库增强
-- 创建时间: 2025-11-19

-- 1. 创建增强的风险预测模型配置表
CREATE TABLE IF NOT EXISTS ml_model_config_enhanced (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'cardiovascular', 'diabetes', 'fall', 'cognitive'
    model_version VARCHAR(20) DEFAULT '2.0',
    algorithm_type VARCHAR(50) DEFAULT 'ensemble', -- 'ensemble', 'random_forest', 'gradient_boosting', 'neural_network'
    model_parameters JSONB NOT NULL,
    feature_weights JSONB, -- 特征权重配置
    performance_metrics JSONB,
    training_data_version VARCHAR(50),
    accuracy_threshold DECIMAL(5,4) DEFAULT 0.95, -- 最低准确率要求
    confidence_threshold DECIMAL(5,4) DEFAULT 0.85, -- 最低置信度要求
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'deprecated', 'training', 'validation'
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 创建实时预测结果表
CREATE TABLE IF NOT EXISTS real_time_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    prediction_session_id UUID NOT NULL,
    risk_type VARCHAR(50) NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    feature_values JSONB, -- 使用的特征值
    model_version VARCHAR(20),
    prediction_time_ms INTEGER NOT NULL,
    data_quality_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 创建风险因子权重配置表
CREATE TABLE IF NOT EXISTS risk_factor_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_type VARCHAR(50) NOT NULL,
    factor_name VARCHAR(100) NOT NULL,
    factor_category VARCHAR(50) NOT NULL, -- 'physiological', 'demographic', 'lifestyle', 'medical_history', 'genetic'
    base_weight DECIMAL(5,4) NOT NULL,
    age_adjustment JSONB, -- 年龄调整参数
    gender_adjustment JSONB, -- 性别调整参数
    interaction_effects JSONB, -- 交互效应配置
    confidence_multiplier DECIMAL(5,4) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 创建数据质量评估表
CREATE TABLE IF NOT EXISTS data_quality_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    data_source VARCHAR(50) NOT NULL, -- 'health_data', 'device_data', 'profile_data'
    completeness_score INTEGER NOT NULL, -- 0-100
    accuracy_score INTEGER, -- 0-100
    consistency_score INTEGER, -- 0-100
    timeliness_score INTEGER, -- 0-100
    total_quality_score INTEGER NOT NULL, -- 0-100
    quality_factors JSONB, -- 质量评估详细因素
    assessment_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- 质量评估有效期
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 创建预测性能监控表
CREATE TABLE IF NOT EXISTS prediction_performance_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type VARCHAR(50) NOT NULL,
    prediction_date DATE NOT NULL,
    total_predictions INTEGER NOT NULL,
    successful_predictions INTEGER NOT NULL,
    avg_response_time_ms INTEGER NOT NULL,
    avg_confidence_score DECIMAL(5,4),
    accuracy_rate DECIMAL(5,4),
    data_quality_avg DECIMAL(5,2),
    performance_issues JSONB, -- 性能问题记录
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 创建个性化建议配置表
CREATE TABLE IF NOT EXISTS personalized_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_type VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    recommendation_category VARCHAR(50) NOT NULL, -- 'lifestyle', 'medical', 'monitoring', 'emergency'
    recommendation_title VARCHAR(200) NOT NULL,
    recommendation_content TEXT NOT NULL,
    priority_level INTEGER DEFAULT 1, -- 1-5, 5为最高优先级
    evidence_level VARCHAR(20) DEFAULT 'B', -- 'A', 'B', 'C', 'D' 证据等级
    target_audience JSONB, -- 目标人群配置
    implementation_steps JSONB, -- 实施步骤
    expected_outcome TEXT,
    monitoring_indicators JSONB, -- 监控指标
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 创建风险阈值配置表
CREATE TABLE IF NOT EXISTS risk_threshold_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_type VARCHAR(50) NOT NULL,
    low_threshold_max INTEGER NOT NULL, -- 低风险最大值
    medium_threshold_max INTEGER NOT NULL, -- 中风险最大值
    high_threshold_max INTEGER NOT NULL, -- 高风险最大值
    critical_threshold_min INTEGER NOT NULL, -- 极高风险最小值
    age_group_adjustments JSONB, -- 年龄组调整
    gender_adjustments JSONB, -- 性别调整
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_ml_model_config_enhanced_model_type ON ml_model_config_enhanced(model_type);
CREATE INDEX IF NOT EXISTS idx_ml_model_config_enhanced_status ON ml_model_config_enhanced(status);
CREATE INDEX IF NOT EXISTS idx_real_time_predictions_user_id ON real_time_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_real_time_predictions_session_id ON real_time_predictions(prediction_session_id);
CREATE INDEX IF NOT EXISTS idx_risk_factor_weights_risk_type ON risk_factor_weights(risk_type);
CREATE INDEX IF NOT EXISTS idx_data_quality_user_id ON data_quality_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_prediction_performance_model_date ON prediction_performance_monitoring(model_type, prediction_date);
CREATE INDEX IF NOT EXISTS idx_personalized_recommendations_risk_type_level ON personalized_recommendations(risk_type, risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_threshold_config_risk_type ON risk_threshold_config(risk_type);

-- 启用行级安全策略
ALTER TABLE ml_model_config_enhanced ENABLE ROW LEVEL SECURITY;
ALTER TABLE real_time_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_factor_weights ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_quality_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_performance_monitoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE personalized_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_threshold_config ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略
-- 增强模型配置策略
CREATE POLICY "Users can view active enhanced model configs" ON ml_model_config_enhanced
FOR SELECT USING (status = 'active');

CREATE POLICY "Administrators can manage enhanced model configs" ON ml_model_config_enhanced
FOR ALL USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

-- 实时预测结果策略
CREATE POLICY "Users can view their own real-time predictions" ON real_time_predictions
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Edge functions can insert real-time predictions" ON real_time_predictions
FOR INSERT TO edge_functions_role
WITH CHECK (true);

-- 风险因子权重策略
CREATE POLICY "Users can view risk factor weights" ON risk_factor_weights
FOR SELECT USING (is_active = true);

CREATE POLICY "Administrators can manage risk factor weights" ON risk_factor_weights
FOR ALL USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

-- 数据质量评估策略
CREATE POLICY "Users can view their own data quality assessments" ON data_quality_assessments
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Edge functions can manage data quality assessments" ON data_quality_assessments
FOR ALL TO edge_functions_role
WITH CHECK (true);

-- 预测性能监控策略
CREATE POLICY "Administrators can view prediction performance monitoring" ON prediction_performance_monitoring
FOR SELECT USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

-- 个性化建议策略
CREATE POLICY "Users can view active personalized recommendations" ON personalized_recommendations
FOR SELECT USING (is_active = true);

CREATE POLICY "Administrators can manage personalized recommendations" ON personalized_recommendations
FOR ALL USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

-- 风险阈值配置策略
CREATE POLICY "Users can view default risk threshold config" ON risk_threshold_config
FOR SELECT USING (is_default = true);

CREATE POLICY "Administrators can manage risk threshold config" ON risk_threshold_config
FOR ALL USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

-- 授权访问
GRANT ALL ON ml_model_config_enhanced TO edge_functions_role;
GRANT ALL ON real_time_predictions TO edge_functions_role;
GRANT ALL ON risk_factor_weights TO edge_functions_role;
GRANT ALL ON data_quality_assessments TO edge_functions_role;
GRANT ALL ON prediction_performance_monitoring TO edge_functions_role;
GRANT ALL ON personalized_recommendations TO edge_functions_role;
GRANT ALL ON risk_threshold_config TO edge_functions_role;

-- 插入默认的风险阈值配置
INSERT INTO risk_threshold_config (risk_type, low_threshold_max, medium_threshold_max, high_threshold_max, critical_threshold_min, is_default) VALUES
('cardiovascular', 30, 60, 80, 80, true),
('diabetes', 25, 55, 75, 75, true),
('fall', 20, 50, 70, 70, true),
('cognitive', 25, 50, 70, 70, true);

-- 插入默认的风险因子权重配置
INSERT INTO risk_factor_weights (risk_type, factor_name, factor_category, base_weight, confidence_multiplier) VALUES
-- 心血管风险因子
('cardiovascular', 'blood_pressure', 'physiological', 0.35, 1.2),
('cardiovascular', 'age', 'demographic', 0.25, 1.0),
('cardiovascular', 'blood_sugar', 'physiological', 0.20, 1.1),
('cardiovascular', 'smoking_status', 'lifestyle', 0.20, 1.3),
('cardiovascular', 'bmi', 'physiological', 0.15, 1.0),
('cardiovascular', 'family_history', 'genetic', 0.20, 1.1),
('cardiovascular', 'chronic_diseases', 'medical_history', 0.25, 1.2),
('cardiovascular', 'activity_level', 'lifestyle', 0.10, 0.9),

-- 糖尿病风险因子
('diabetes', 'blood_sugar', 'physiological', 0.40, 1.3),
('diabetes', 'bmi', 'physiological', 0.25, 1.2),
('diabetes', 'age', 'demographic', 0.20, 1.0),
('diabetes', 'family_history', 'genetic', 0.25, 1.2),
('diabetes', 'activity_level', 'lifestyle', 0.15, 1.1),
('diabetes', 'blood_pressure', 'physiological', 0.15, 1.0),
('diabetes', 'chronic_diseases', 'medical_history', 0.30, 1.4),

-- 跌倒风险因子
('fall', 'age', 'demographic', 0.30, 1.2),
('fall', 'fall_history', 'medical_history', 0.40, 1.5),
('fall', 'activity_level', 'lifestyle', 0.25, 1.1),
('fall', 'chronic_diseases', 'medical_history', 0.20, 1.3),
('fall', 'medication_count', 'medical_history', 0.15, 1.2),
('fall', 'balance_indicators', 'physiological', 0.30, 1.4),
('fall', 'environmental_factors', 'lifestyle', 0.10, 1.0),

-- 认知功能风险因子
('cognitive', 'age', 'demographic', 0.35, 1.3),
('cognitive', 'chronic_diseases', 'medical_history', 0.25, 1.2),
('cognitive', 'sleep_quality', 'physiological', 0.20, 1.1),
('cognitive', 'social_activity', 'lifestyle', 0.15, 1.0),
('cognitive', 'education_level', 'demographic', 0.10, 0.9),
('cognitive', 'family_history', 'genetic', 0.20, 1.2),
('cognitive', 'cardiovascular_health', 'physiological', 0.15, 1.1);

-- 插入默认的个性化建议
INSERT INTO personalized_recommendations (risk_type, risk_level, recommendation_category, recommendation_title, recommendation_content, priority_level, evidence_level) VALUES
-- 心血管建议
('cardiovascular', 'high', 'medical', '立即心血管专科就诊', '建议尽快预约心血管专科医生进行详细检查，包括心电图、超声心动图、血脂全套等检查。', 5, 'A'),
('cardiovascular', 'medium', 'lifestyle', '血压监测与生活方式调整', '每天定时测量血压，记录血压变化。建议减少钠盐摄入，增加钾的摄入，规律的有氧运动。', 3, 'A'),
('cardiovascular', 'low', 'monitoring', '定期心血管健康检查', '每年进行心血管健康体检，包括血压、血脂、血糖等指标的监测。', 2, 'B'),

-- 糖尿病建议
('diabetes', 'critical', 'medical', '立即内分泌科就诊', '血糖水平严重异常，需要立即就医进行糖尿病诊断和治疗。', 5, 'A'),
('diabetes', 'high', 'medical', '糖尿病专科评估', '建议内分泌科医生评估，制定个体化的血糖管理方案。', 4, 'A'),
('diabetes', 'medium', 'lifestyle', '饮食运动干预', '严格控制饮食，减少精制糖类摄入，增加膳食纤维。每周至少150分钟中等强度运动。', 3, 'A'),
('diabetes', 'low', 'monitoring', '血糖定期监测', '建议每月检测1-2次空腹血糖，注意体重控制。', 2, 'B'),

-- 跌倒建议
('fall', 'critical', 'emergency', '居家安全改造', '跌倒风险极高，建议立即进行居家环境安全评估和改造，安装扶手、防滑垫等设施。', 5, 'A'),
('fall', 'high', 'medical', '平衡能力专业评估', '建议康复医学科进行专业平衡能力评估，制定个性化平衡训练方案。', 4, 'A'),
('fall', 'medium', 'lifestyle', '增强平衡训练', '进行平衡训练，如太极、瑜伽等，增强身体平衡能力和肌肉力量。', 3, 'B'),
('fall', 'low', 'monitoring', '预防性措施', '注意居家安全，保持适当运动，定期视力检查。', 2, 'C'),

-- 认知功能建议
('cognitive', 'high', 'medical', '认知功能专业评估', '建议神经内科或老年科进行详细认知功能评估，排除认知障碍。', 4, 'A'),
('cognitive', 'medium', 'lifestyle', '认知训练与社交活动', '进行认知训练游戏，保持社交活动，控制慢性疾病发展。', 3, 'B'),
('cognitive', 'low', 'monitoring', '预防性认知保健', '保持良好的睡眠质量，适度运动，增加智力活动。', 2, 'C');

-- 创建性能监控触发器
CREATE OR REPLACE FUNCTION update_prediction_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新预测性能监控数据
    INSERT INTO prediction_performance_monitoring (
        model_type,
        prediction_date,
        total_predictions,
        successful_predictions,
        avg_response_time_ms,
        avg_confidence_score,
        accuracy_rate,
        data_quality_avg
    ) VALUES (
        NEW.risk_type,
        CURRENT_DATE,
        1,
        1,
        NEW.prediction_time_ms,
        NEW.confidence_score,
        CASE WHEN NEW.confidence_score >= 0.85 THEN 1.0 ELSE 0.0 END,
        NEW.data_quality_score
    )
    ON CONFLICT (model_type, prediction_date) 
    DO UPDATE SET
        total_predictions = prediction_performance_monitoring.total_predictions + 1,
        successful_predictions = prediction_performance_monitoring.successful_predictions + 1,
        avg_response_time_ms = (
            prediction_performance_monitoring.avg_response_time_ms * (total_predictions - 1) + NEW.prediction_time_ms
        ) / total_predictions,
        avg_confidence_score = (
            prediction_performance_monitoring.avg_confidence_score * (total_predictions - 1) + NEW.confidence_score
        ) / total_predictions,
        accuracy_rate = CASE 
            WHEN NEW.confidence_score >= 0.85 THEN 
                (prediction_performance_monitoring.accuracy_rate * (total_predictions - 1) + 1.0) / total_predictions
            ELSE 
                (prediction_performance_monitoring.accuracy_rate * (total_predictions - 1) + 0.0) / total_predictions
        END,
        data_quality_avg = (
            prediction_performance_monitoring.data_quality_avg * (total_predictions - 1) + COALESCE(NEW.data_quality_score, 0)
        ) / total_predictions;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER trigger_update_prediction_performance
    AFTER INSERT ON real_time_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_prediction_performance();