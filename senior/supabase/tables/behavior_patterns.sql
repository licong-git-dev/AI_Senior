CREATE TABLE behavior_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    activity_trajectory JSONB,
    abnormal_behaviors JSONB,
    cognitive_assessment JSONB,
    social_interaction_score DECIMAL(3,2),
    risk_level VARCHAR(20),
    ai_insights TEXT,
    detection_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);