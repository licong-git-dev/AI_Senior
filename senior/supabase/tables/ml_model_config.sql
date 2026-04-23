-- 机器学习模型配置表
CREATE TABLE ml_model_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'cardiovascular', 'diabetes', 'fall', 'cognitive'
    model_version VARCHAR(20) DEFAULT '1.0',
    model_parameters JSONB NOT NULL,
    training_data_version VARCHAR(50),
    performance_metrics JSONB,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'deprecated', 'training'
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 模型评估历史表
CREATE TABLE model_evaluation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_config_id UUID REFERENCES ml_model_config(id) ON DELETE CASCADE,
    evaluation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    dataset_size INTEGER,
    accuracy_score DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_score DECIMAL(5,4),
    confusion_matrix JSONB,
    feature_importance JSONB,
    evaluation_notes TEXT
);

-- 创建索引
CREATE INDEX idx_ml_model_config_model_type ON ml_model_config(model_type);
CREATE INDEX idx_ml_model_config_status ON ml_model_config(status);
CREATE INDEX idx_model_evaluation_history_model_config_id ON model_evaluation_history(model_config_id);
CREATE INDEX idx_model_evaluation_history_evaluation_date ON model_evaluation_history(evaluation_date DESC);

-- 启用RLS
ALTER TABLE ml_model_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_evaluation_history ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略
CREATE POLICY "Users can view active model configs" ON ml_model_config
FOR SELECT USING (status = 'active');

CREATE POLICY "Administrators can manage model configs" ON ml_model_config
FOR ALL USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

CREATE POLICY "Users can view model evaluation history" ON model_evaluation_history
FOR SELECT USING (true);

-- 授权访问
GRANT ALL ON ml_model_config TO edge_functions_role;
GRANT ALL ON model_evaluation_history TO edge_functions_role;