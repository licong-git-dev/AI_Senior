-- 风险预测日志表
CREATE TABLE risk_prediction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    prediction_result JSONB NOT NULL,
    model_version VARCHAR(20) DEFAULT '1.0',
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_risk_prediction_logs_user_id ON risk_prediction_logs(user_id);
CREATE INDEX idx_risk_prediction_logs_created_at ON risk_prediction_logs(created_at DESC);

-- 启用RLS
ALTER TABLE risk_prediction_logs ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略
CREATE POLICY "Users can view their own prediction logs" ON risk_prediction_logs
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Edge functions can insert prediction logs" ON risk_prediction_logs
FOR INSERT TO edge_functions_role
WITH CHECK (true);

-- 授权访问
GRANT ALL ON risk_prediction_logs TO edge_functions_role;