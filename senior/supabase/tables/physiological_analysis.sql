CREATE TABLE physiological_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    heart_rate_variability JSONB,
    blood_pressure_prediction JSONB,
    sleep_quality_score DECIMAL(3,2),
    respiratory_pattern JSONB,
    anomalies JSONB,
    ai_summary TEXT,
    confidence_score DECIMAL(3,2),
    analysis_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);