-- 机器学习训练数据集表
CREATE TABLE training_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name VARCHAR(100) NOT NULL,
    dataset_type VARCHAR(50) NOT NULL, -- 'cardiovascular', 'diabetes', 'fall', 'cognitive'
    version VARCHAR(20) DEFAULT '1.0',
    data_source VARCHAR(50), -- 'synthetic', 'clinical', 'historical'
    sample_size INTEGER,
    feature_count INTEGER,
    label_distribution JSONB,
    data_quality_score DECIMAL(5,2),
    training_features JSONB NOT NULL,
    training_labels JSONB NOT NULL,
    metadata JSONB, -- 包含数据来源、特征说明等
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 特征工程配置表
CREATE TABLE feature_engineering_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES training_datasets(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    feature_type VARCHAR(50) NOT NULL, -- 'numerical', 'categorical', 'derived'
    feature_extraction_method VARCHAR(100),
    feature_scaling_method VARCHAR(50), -- 'standardization', 'normalization', 'minmax'
    importance_score DECIMAL(5,4),
    feature_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_training_datasets_dataset_type ON training_datasets(dataset_type);
CREATE INDEX idx_training_datasets_is_active ON training_datasets(is_active);
CREATE INDEX idx_feature_engineering_config_dataset_id ON feature_engineering_config(dataset_id);
CREATE INDEX idx_feature_engineering_config_feature_type ON feature_engineering_config(feature_type);

-- 启用RLS
ALTER TABLE training_datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_engineering_config ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略
CREATE POLICY "Users can view active training datasets" ON training_datasets
FOR SELECT USING (is_active = true);

CREATE POLICY "Administrators can manage training datasets" ON training_datasets
FOR ALL USING (
    auth.uid() IN (
        SELECT user_id FROM profiles WHERE user_type = 1
    )
);

CREATE POLICY "Users can view feature engineering configs" ON feature_engineering_config
FOR SELECT USING (true);

-- 授权访问
GRANT ALL ON training_datasets TO edge_functions_role;
GRANT ALL ON feature_engineering_config TO edge_functions_role;