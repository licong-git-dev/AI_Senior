-- Migration: create_escort_workers_table
-- Created at: 1763365303

CREATE TABLE IF NOT EXISTS escort_workers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  avatar_url TEXT,
  gender VARCHAR(10),
  age INTEGER,
  certification_level VARCHAR(50),
  certifications JSONB,
  service_areas JSONB,
  rating DECIMAL(3,2) DEFAULT 0,
  total_orders INTEGER DEFAULT 0,
  completed_orders INTEGER DEFAULT 0,
  work_status VARCHAR(50) DEFAULT 'available',
  location_latitude DECIMAL(10,8),
  location_longitude DECIMAL(11,8),
  last_location_update TIMESTAMP,
  skills JSONB,
  experience_years INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE escort_workers ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Enable read access for all users" ON escort_workers FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON escort_workers FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON escort_workers FOR UPDATE USING (true);
CREATE POLICY "Enable delete for authenticated users" ON escort_workers FOR DELETE USING (true);;