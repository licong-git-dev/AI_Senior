CREATE TABLE data_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value DECIMAL(18,2) NOT NULL,
    time_period VARCHAR(50) NOT NULL,
    source_community UUID REFERENCES communities(id),
    metadata JSONB,
    analysis_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);