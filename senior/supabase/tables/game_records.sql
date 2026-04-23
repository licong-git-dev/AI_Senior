CREATE TABLE game_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    game_id UUID NOT NULL REFERENCES cognitive_games(id),
    score INTEGER NOT NULL,
    accuracy_rate DECIMAL(5,2),
    completion_time INTEGER,
    difficulty_level VARCHAR(20),
    cognitive_performance JSONB,
    played_at TIMESTAMP DEFAULT NOW()
);