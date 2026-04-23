-- Migration: create_appointments_table
-- Created at: 1763365299

CREATE TABLE IF NOT EXISTS appointments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  elderly_id UUID NOT NULL,
  elderly_name VARCHAR(100),
  elderly_phone VARCHAR(20),
  appointment_time TIMESTAMP NOT NULL,
  hospital_name VARCHAR(200),
  hospital_address TEXT,
  department VARCHAR(100),
  doctor_name VARCHAR(100),
  service_type VARCHAR(50) NOT NULL,
  urgency_level INTEGER DEFAULT 1,
  special_needs TEXT,
  status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Enable read access for all users" ON appointments FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON appointments FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON appointments FOR UPDATE USING (true);
CREATE POLICY "Enable delete for authenticated users" ON appointments FOR DELETE USING (true);;