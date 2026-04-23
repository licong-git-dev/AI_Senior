-- Migration: create_medication_management_table
-- Created at: 1763370850

CREATE TABLE IF NOT EXISTS medication_management (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  chronic_condition_id UUID,
  medication_name VARCHAR(200) NOT NULL,
  dosage VARCHAR(100) NOT NULL,
  frequency VARCHAR(50) NOT NULL,
  intake_time VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE,
  stock_quantity INTEGER DEFAULT 0,
  low_stock_threshold INTEGER DEFAULT 10,
  side_effects TEXT,
  precautions TEXT,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medication_user ON medication_management(user_id);
CREATE INDEX IF NOT EXISTS idx_medication_status ON medication_management(status);;