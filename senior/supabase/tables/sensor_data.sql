CREATE TABLE sensor_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    raw_value JSONB NOT NULL,
    processed_value JSONB,
    quality_score DECIMAL(3,2),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);