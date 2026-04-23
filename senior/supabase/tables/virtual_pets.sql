CREATE TABLE virtual_pets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    pet_type VARCHAR(50) NOT NULL,
    pet_name VARCHAR(100) NOT NULL,
    appearance_config JSONB,
    personality_traits JSONB,
    mood_state VARCHAR(50) DEFAULT 'happy',
    growth_level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    last_interaction TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    bond_strength INTEGER DEFAULT 0
);