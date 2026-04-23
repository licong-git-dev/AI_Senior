CREATE TABLE voice_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    interaction_type VARCHAR(50) NOT NULL,
    voice_text TEXT,
    user_input TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    emotion_detected VARCHAR(50),
    emotion_score DECIMAL(3,2),
    conversation_context JSONB,
    interaction_time TIMESTAMP DEFAULT NOW(),
    duration_seconds INTEGER
);