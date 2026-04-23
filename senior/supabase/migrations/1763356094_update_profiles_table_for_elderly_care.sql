-- Migration: update_profiles_table_for_elderly_care
-- Created at: 1763356094

-- 扩展profiles表以支持养老监护系统
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS real_name VARCHAR(50);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email VARCHAR(100);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS birth_date DATE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS region_code VARCHAR(20) DEFAULT '420102';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS emergency_contact_name VARCHAR(50);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS emergency_contact_phone VARCHAR(20);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS blood_type VARCHAR(5);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS chronic_diseases JSONB DEFAULT '[]'::jsonb;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS allergies JSONB DEFAULT '[]'::jsonb;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS current_medications JSONB DEFAULT '[]'::jsonb;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS user_type INTEGER DEFAULT 2;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS status INTEGER DEFAULT 1;

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user_type ON profiles(user_type);
CREATE INDEX IF NOT EXISTS idx_profiles_region_code ON profiles(region_code);
CREATE INDEX IF NOT EXISTS idx_health_data_user_id ON health_data(user_id);
CREATE INDEX IF NOT EXISTS idx_health_data_measurement_time ON health_data(measurement_time DESC);
CREATE INDEX IF NOT EXISTS idx_health_data_data_type ON health_data(data_type);
CREATE INDEX IF NOT EXISTS idx_health_data_fall_detected ON health_data(fall_detected) WHERE fall_detected = TRUE;
CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_emergency_calls_user_id ON emergency_calls(user_id);
CREATE INDEX IF NOT EXISTS idx_emergency_calls_call_time ON emergency_calls(call_time DESC);
CREATE INDEX IF NOT EXISTS idx_emergency_calls_response_status ON emergency_calls(response_status);
CREATE INDEX IF NOT EXISTS idx_care_plans_user_id ON care_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_care_plans_status ON care_plans(status);;