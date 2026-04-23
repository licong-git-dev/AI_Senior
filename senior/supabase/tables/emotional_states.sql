CREATE TABLE emotional_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    emotion_type VARCHAR(50) NOT NULL,
    emotion_intensity DECIMAL(3,2) NOT NULL,
    trigger_event TEXT,
    psychological_state VARCHAR(100),
    companionship_need_level VARCHAR(20),
    ai_analysis TEXT,
    support_suggestions TEXT,
    recorded_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);