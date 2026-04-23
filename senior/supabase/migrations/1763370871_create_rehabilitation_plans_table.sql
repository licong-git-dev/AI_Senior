-- Migration: create_rehabilitation_plans_table
-- Created at: 1763370871

CREATE TABLE IF NOT EXISTS rehabilitation_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  chronic_condition_id UUID,
  plan_name VARCHAR(200) NOT NULL,
  exercise_type VARCHAR(100) NOT NULL,
  intensity_level VARCHAR(20) NOT NULL,
  duration_minutes INTEGER NOT NULL,
  frequency_per_week INTEGER NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE,
  completion_rate DECIMAL(5,2) DEFAULT 0,
  video_url TEXT,
  instructions TEXT,
  precautions TEXT,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rehab_plans_user ON rehabilitation_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_rehab_plans_status ON rehabilitation_plans(status);;