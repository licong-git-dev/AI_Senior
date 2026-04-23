-- 智能预防性干预系统数据库迁移脚本
-- 创建日期: 2025-11-19

-- 1. 用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  age INTEGER CHECK (age >= 0 AND age <= 150),
  gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
  height DECIMAL(5,2) CHECK (height > 0 AND height <= 300),
  weight DECIMAL(5,2) CHECK (weight > 0 AND weight <= 500),
  medical_history JSONB DEFAULT '{}',
  current_medications JSONB DEFAULT '[]',
  lifestyle_data JSONB DEFAULT '{}',
  preferences JSONB DEFAULT '{}',
  emergency_contact JSONB DEFAULT '{}',
  risk_factors JSONB DEFAULT '[]',
  baseline_health_data JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_age ON user_profiles(age);
CREATE INDEX idx_user_profiles_gender ON user_profiles(gender);

-- 2. 健康记录表
CREATE TABLE IF NOT EXISTS health_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  record_type VARCHAR(50) NOT NULL,
  record_value JSONB NOT NULL,
  recorded_at TIMESTAMP NOT NULL,
  source_device VARCHAR(50) DEFAULT 'manual',
  source_type VARCHAR(20) DEFAULT 'user_input' CHECK (source_type IN ('user_input', 'device', 'api', 'import')),
  data_quality_score DECIMAL(3,2) DEFAULT 1.0 CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
  validation_status VARCHAR(20) DEFAULT 'validated' CHECK (validation_status IN ('pending', 'validated', 'flagged', 'invalid')),
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_health_records_user_id ON health_records(user_id);
CREATE INDEX idx_health_records_type ON health_records(record_type);
CREATE INDEX idx_health_records_recorded_at ON health_records(recorded_at);
CREATE INDEX idx_health_records_source ON health_records(source_device);

-- 3. 干预记录表
CREATE TABLE IF NOT EXISTS intervention_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  intervention_type VARCHAR(50) NOT NULL,
  priority VARCHAR(20) DEFAULT 'routine' CHECK (priority IN ('urgent', 'routine', 'follow_up')),
  generated_advice JSONB,
  risk_assessment JSONB,
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed_successfully', 'completed_partially', 'needs_adjustment', 'low_effectiveness', 'cancelled')),
  effectiveness_score DECIMAL(3,2) CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
  adherence_rate DECIMAL(3,2) DEFAULT 0,
  satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 10),
  completion_rate DECIMAL(3,2) DEFAULT 0,
  adjustment_count INTEGER DEFAULT 0,
  scheduled_completion_date DATE,
  actual_completion_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_intervention_records_user_id ON intervention_records(user_id);
CREATE INDEX idx_intervention_records_type ON intervention_records(intervention_type);
CREATE INDEX idx_intervention_records_status ON intervention_records(status);
CREATE INDEX idx_intervention_records_created_at ON intervention_records(created_at);
CREATE INDEX idx_intervention_records_priority ON intervention_records(priority);

-- 4. 干预反馈表
CREATE TABLE IF NOT EXISTS intervention_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  intervention_id UUID REFERENCES intervention_records(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  adherence_score INTEGER NOT NULL CHECK (adherence_score >= 1 AND adherence_score <= 10),
  satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 10),
  difficulties TEXT,
  additional_comments TEXT,
  emotional_state JSONB DEFAULT '{}',
  physical_symptoms JSONB DEFAULT '{}',
  behavioral_changes JSONB DEFAULT '{}',
  support_needed JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_intervention_feedback_intervention_id ON intervention_feedback(intervention_id);
CREATE INDEX idx_intervention_feedback_user_id ON intervention_feedback(user_id);
CREATE INDEX idx_intervention_feedback_created_at ON intervention_feedback(created_at);
CREATE INDEX idx_intervention_feedback_adherence ON intervention_feedback(adherence_score);
CREATE INDEX idx_intervention_feedback_satisfaction ON intervention_feedback(satisfaction_score);

-- 5. 健康知识库表
CREATE TABLE IF NOT EXISTS health_knowledge_base (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category VARCHAR(100) NOT NULL,
  subcategory VARCHAR(100),
  condition VARCHAR(200) NOT NULL,
  evidence_level CHAR(1) CHECK (evidence_level IN ('A', 'B', 'C', 'D')) DEFAULT 'C',
  title VARCHAR(300) NOT NULL,
  content TEXT NOT NULL,
  recommendations JSONB DEFAULT '[]',
  supporting_evidence JSONB DEFAULT '[]',
  risk_factors JSONB DEFAULT '[]',
  prevention_strategies JSONB DEFAULT '[]',
  target_populations JSONB DEFAULT '[]',
  last_updated TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  version INTEGER DEFAULT 1
);

-- 创建索引
CREATE INDEX idx_health_knowledge_category ON health_knowledge_base(category);
CREATE INDEX idx_health_knowledge_condition ON health_knowledge_base(condition);
CREATE INDEX idx_health_knowledge_evidence ON health_knowledge_base(evidence_level);
CREATE INDEX idx_health_knowledge_active ON health_knowledge_base(is_active);

-- 6. 多模态内容表
CREATE TABLE IF NOT EXISTS multimodal_content (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  intervention_id UUID REFERENCES intervention_records(id) ON DELETE CASCADE,
  content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('image', 'audio', 'video', 'interactive', 'text', 'comprehensive')),
  content_url TEXT,
  content_data JSONB DEFAULT '{}',
  generation_metadata JSONB DEFAULT '{}',
  accessibility_features JSONB DEFAULT '{}',
  quality_score DECIMAL(3,2) DEFAULT 0,
  file_size_bytes BIGINT,
  duration_seconds INTEGER,
  format VARCHAR(20),
  language VARCHAR(10) DEFAULT 'zh-CN',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_multimodal_content_intervention_id ON multimodal_content(intervention_id);
CREATE INDEX idx_multimodal_content_type ON multimodal_content(content_type);
CREATE INDEX idx_multimodal_content_active ON multimodal_content(is_active);

-- 7. 干预调整记录表
CREATE TABLE IF NOT EXISTS intervention_adjustments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  intervention_id UUID REFERENCES intervention_records(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  adjustment_type VARCHAR(30) NOT NULL CHECK (adjustment_type IN ('optimization', 'correction', 'escalation', 'simplification')),
  adjustment_reason VARCHAR(100) NOT NULL,
  original_effectiveness DECIMAL(3,2),
  new_effectiveness DECIMAL(3,2),
  adjustment_suggestions JSONB DEFAULT '[]',
  implementation_notes TEXT,
  adjustment_date TIMESTAMP DEFAULT NOW(),
  applied_at TIMESTAMP,
  is_successful BOOLEAN,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_intervention_adjustments_intervention_id ON intervention_adjustments(intervention_id);
CREATE INDEX idx_intervention_adjustments_user_id ON intervention_adjustments(user_id);
CREATE INDEX idx_intervention_adjustments_type ON intervention_adjustments(adjustment_type);
CREATE INDEX idx_intervention_adjustments_date ON intervention_adjustments(adjustment_date);

-- 8. 进展报告表
CREATE TABLE IF NOT EXISTS progress_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  intervention_id UUID REFERENCES intervention_records(id) ON DELETE CASCADE,
  report_type VARCHAR(30) DEFAULT 'standard' CHECK (report_type IN ('standard', 'detailed', 'summary', 'comparative')),
  report_data JSONB NOT NULL,
  report_period JSONB DEFAULT '{}',
  key_findings JSONB DEFAULT '[]',
  recommendations JSONB DEFAULT '[]',
  generated_at TIMESTAMP DEFAULT NOW(),
  shared_with JSONB DEFAULT '[]',
  is_archived BOOLEAN DEFAULT false
);

-- 创建索引
CREATE INDEX idx_progress_reports_user_id ON progress_reports(user_id);
CREATE INDEX idx_progress_reports_intervention_id ON progress_reports(intervention_id);
CREATE INDEX idx_progress_reports_generated_at ON progress_reports(generated_at);
CREATE INDEX idx_progress_reports_type ON progress_reports(report_type);

-- 9. 风险评估历史表
CREATE TABLE IF NOT EXISTS risk_assessment_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  assessment_date TIMESTAMP DEFAULT NOW(),
  overall_risk_level VARCHAR(20) CHECK (overall_risk_level IN ('low', 'medium', 'high', 'critical')),
  overall_risk_score DECIMAL(4,3) CHECK (overall_risk_score >= 0 AND overall_risk_score <= 1),
  risk_factors JSONB DEFAULT '[]',
  confidence_level DECIMAL(3,2) DEFAULT 0.8,
  assessment_method VARCHAR(50) DEFAULT 'automated',
  assessment_data JSONB DEFAULT '{}',
  recommendations JSONB DEFAULT '[]',
  next_assessment_date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_risk_assessment_user_id ON risk_assessment_history(user_id);
CREATE INDEX idx_risk_assessment_date ON risk_assessment_history(assessment_date);
CREATE INDEX idx_risk_assessment_level ON risk_assessment_history(overall_risk_level);

-- 10. 用户偏好设置表
CREATE TABLE IF NOT EXISTS user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  content_preferences JSONB DEFAULT '{}',
  notification_settings JSONB DEFAULT '{}',
  accessibility_settings JSONB DEFAULT '{}',
  privacy_settings JSONB DEFAULT '{}',
  ui_customization JSONB DEFAULT '{}',
  language_preference VARCHAR(10) DEFAULT 'zh-CN',
  timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_language ON user_preferences(language_preference);

-- 11. 系统配置表
CREATE TABLE IF NOT EXISTS system_configuration (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  config_key VARCHAR(100) NOT NULL UNIQUE,
  config_value JSONB NOT NULL,
  config_type VARCHAR(30) DEFAULT 'general' CHECK (config_type IN ('general', 'ai_model', 'content_generation', 'notification', 'security')),
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_system_configuration_key ON system_configuration(config_key);
CREATE INDEX idx_system_configuration_type ON system_configuration(config_type);
CREATE INDEX idx_system_configuration_active ON system_configuration(is_active);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加更新时间触发器
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_records_updated_at BEFORE UPDATE ON health_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_intervention_records_updated_at BEFORE UPDATE ON intervention_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_intervention_feedback_updated_at BEFORE UPDATE ON intervention_feedback FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_multimodal_content_updated_at BEFORE UPDATE ON multimodal_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_configuration_updated_at BEFORE UPDATE ON system_configuration FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入初始系统配置
INSERT INTO system_configuration (config_key, config_value, config_type, description) VALUES
('qianwen_api_config', '{"model": "qwen-max", "max_tokens": 2000, "temperature": 0.7, "top_p": 0.8}', 'ai_model', '通义千问API配置参数'),
('multimodal_generation', '{"enable_images": true, "enable_audio": true, "enable_video": false, "enable_interactive": true}', 'content_generation', '多模态内容生成开关'),
('risk_assessment_thresholds', '{"low": 0.3, "medium": 0.6, "high": 0.8, "critical": 1.0}', 'general', '风险评估阈值配置'),
('effectiveness_scoring', '{"minimum_viable": 0.4, "good": 0.7, "excellent": 0.85, "adjustment_threshold": 0.6}', 'general', '有效性评分标准'),
('notification_intervals', '{"daily_reminder": "09:00", "weekly_report": "monday", "monthly_review": "first_monday"}', 'notification', '通知提醒时间间隔'),
('content_generation_limits', '{"max_images_per_intervention": 5, "max_audio_duration": 300, "max_video_duration": 180}', 'content_generation', '内容生成限制配置')
ON CONFLICT (config_key) DO NOTHING;

-- 创建视图：用户干预效果汇总
CREATE OR REPLACE VIEW intervention_effectiveness_summary AS
SELECT 
    ir.user_id,
    ir.intervention_type,
    COUNT(*) as total_interventions,
    AVG(ir.effectiveness_score) as avg_effectiveness,
    AVG(ir.adherence_rate) as avg_adherence,
    AVG(ir.satisfaction_score) as avg_satisfaction,
    AVG(ir.completion_rate) as avg_completion,
    SUM(CASE WHEN ir.status = 'completed_successfully' THEN 1 ELSE 0 END) as successful_completions,
    SUM(CASE WHEN ir.status = 'needs_adjustment' THEN 1 ELSE 0 END) as needs_adjustment,
    MIN(ir.created_at) as first_intervention,
    MAX(ir.created_at) as latest_intervention
FROM intervention_records ir
WHERE ir.created_at >= NOW() - INTERVAL '90 days'
GROUP BY ir.user_id, ir.intervention_type;

-- 创建视图：风险趋势分析
CREATE OR REPLACE VIEW risk_trend_analysis AS
SELECT 
    rah.user_id,
    rah.assessment_date::date as assessment_date,
    rah.overall_risk_level,
    rah.overall_risk_score,
    jsonb_array_length(rah.risk_factors) as risk_factor_count,
    LAG(rah.overall_risk_score) OVER (PARTITION BY rah.user_id ORDER BY rah.assessment_date) as previous_risk_score,
    rah.overall_risk_score - LAG(rah.overall_risk_score) OVER (PARTITION BY rah.user_id ORDER BY rah.assessment_date) as risk_score_change
FROM risk_assessment_history rah
ORDER BY rah.user_id, rah.assessment_date;

-- 创建视图：多模态内容使用统计
CREATE OR REPLACE VIEW multimodal_content_stats AS
SELECT 
    ir.user_id,
    ir.intervention_type,
    COUNT(mc.id) as total_content_items,
    SUM(CASE WHEN mc.content_type = 'image' THEN 1 ELSE 0 END) as image_count,
    SUM(CASE WHEN mc.content_type = 'audio' THEN 1 ELSE 0 END) as audio_count,
    SUM(CASE WHEN mc.content_type = 'video' THEN 1 ELSE 0 END) as video_count,
    SUM(CASE WHEN mc.content_type = 'interactive' THEN 1 ELSE 0 END) as interactive_count,
    AVG(mc.quality_score) as avg_quality_score,
    COUNT(DISTINCT mc.id) FILTER (WHERE mc.is_active = true) as active_content_items
FROM intervention_records ir
LEFT JOIN multimodal_content mc ON ir.id = mc.intervention_id
WHERE ir.created_at >= NOW() - INTERVAL '30 days'
GROUP BY ir.user_id, ir.intervention_type;

-- 创建函数：计算用户健康风险趋势
CREATE OR REPLACE FUNCTION calculate_user_risk_trend(user_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    trend_direction VARCHAR(20),
    risk_change DECIMAL,
    assessment_count INTEGER,
    current_risk_level VARCHAR(20),
    previous_risk_level VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    WITH user_assessments AS (
        SELECT 
            overall_risk_score,
            overall_risk_level,
            assessment_date,
            LAG(overall_risk_score) OVER (ORDER BY assessment_date) as prev_score,
            LAG(overall_risk_level) OVER (ORDER BY assessment_date) as prev_level,
            ROW_NUMBER() OVER (ORDER BY assessment_date DESC) as rn
        FROM risk_assessment_history
        WHERE user_id = user_uuid
        AND assessment_date >= NOW() - (days_back || ' days')::INTERVAL
    )
    SELECT 
        CASE 
            WHEN current_assessment.overall_risk_score > prev_assessment.prev_score THEN 'increasing'
            WHEN current_assessment.overall_risk_score < prev_assessment.prev_score THEN 'decreasing'
            ELSE 'stable'
        END::VARCHAR(20),
        current_assessment.overall_risk_score - COALESCE(prev_assessment.prev_score, current_assessment.overall_risk_score),
        COUNT(*)::INTEGER,
        current_assessment.overall_risk_level::VARCHAR(20),
        COALESCE(prev_assessment.prev_level, current_assessment.overall_risk_level)::VARCHAR(20)
    FROM (
        SELECT * FROM user_assessments WHERE rn = 1
    ) current_assessment
    LEFT JOIN (
        SELECT * FROM user_assessments WHERE rn = 2
    ) prev_assessment ON true
    CROSS JOIN (
        SELECT COUNT(*) FROM user_assessments
    ) assessment_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 创建函数：生成个性化建议摘要
CREATE OR REPLACE FUNCTION generate_intervention_summary(intervention_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    intervention_data RECORD;
    feedback_data JSONB;
    health_improvement JSONB;
BEGIN
    -- 获取干预基本信息
    SELECT * INTO intervention_data 
    FROM intervention_records 
    WHERE id = intervention_uuid;
    
    -- 获取反馈统计
    SELECT jsonb_build_object(
        'total_feedback', COUNT(*),
        'avg_adherence', ROUND(AVG(adherence_score), 1),
        'avg_satisfaction', ROUND(AVG(satisfaction_score), 1),
        'common_difficulties', (
            SELECT jsonb_agg(difficulty) 
            FROM (
                SELECT difficulties as difficulty
                FROM intervention_feedback 
                WHERE intervention_id = intervention_uuid 
                AND difficulties IS NOT NULL
                LIMIT 5
            ) difficulties
        )
    ) INTO feedback_data
    FROM intervention_feedback 
    WHERE intervention_id = intervention_uuid;
    
    -- 构建结果
    SELECT jsonb_build_object(
        'intervention_id', intervention_data.id,
        'intervention_type', intervention_data.intervention_type,
        'status', intervention_data.status,
        'effectiveness_score', intervention_data.effectiveness_score,
        'duration_days', DATE_PART('day', NOW() - intervention_data.created_at),
        'feedback_summary', feedback_data,
        'next_actions', CASE 
            WHEN intervention_data.effectiveness_score < 0.6 THEN '需要调整方案'
            WHEN intervention_data.status = 'active' THEN '继续执行当前方案'
            ELSE '方案执行完成'
        END,
        'generated_at', NOW()
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 授予必要的权限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- 为Edge Functions创建专用权限
GRANT EXECUTE ON FUNCTION calculate_user_risk_trend(UUID, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION generate_intervention_summary(UUID) TO service_role;

-- 备注：此迁移脚本创建了完整的智能预防性干预系统数据库结构
-- 包含用户画像、健康记录、干预管理、效果跟踪、多模态内容等核心功能模块
-- 同时建立了必要的索引、触发器和视图以支持高效的查询和分析