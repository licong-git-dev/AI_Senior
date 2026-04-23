CREATE TABLE health_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    goal_type VARCHAR(50) NOT NULL,
    target_value VARCHAR(100) NOT NULL,
    current_value VARCHAR(100),
    unit VARCHAR(20),
    start_date DATE NOT NULL,
    target_date DATE,
    achievement_rate DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);