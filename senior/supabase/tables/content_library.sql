CREATE TABLE content_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content_url TEXT,
    content_data JSONB,
    category VARCHAR(100),
    tags TEXT[],
    target_age_group VARCHAR(50),
    emotional_tone VARCHAR(50),
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    view_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0
);