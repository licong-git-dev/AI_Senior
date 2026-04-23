CREATE TABLE health_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    time_range VARCHAR(20) NOT NULL,
    predicted_values JSONB NOT NULL,
    risk_factors JSONB,
    confidence_interval JSONB,
    early_warning JSONB,
    model_version VARCHAR(20),
    accuracy_rate DECIMAL(5,2),
    prediction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);