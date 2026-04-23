CREATE TABLE cognitive_games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_name VARCHAR(255) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
    description TEXT,
    game_config JSONB NOT NULL,
    cognitive_area VARCHAR(100),
    recommended_duration INTEGER,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    play_count INTEGER DEFAULT 0
);