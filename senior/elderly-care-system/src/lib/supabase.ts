import { createClient } from '@supabase/supabase-js'

const supabaseUrl = "https://bmaarkhvsuqsnvvbtcsa.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// 数据类型定义
export interface Profile {
  id: string;
  user_id?: string;
  real_name?: string;
  phone?: string;
  email?: string;
  gender?: number;
  birth_date?: string;
  age?: number;
  region_code?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  blood_type?: string;
  chronic_diseases?: string[];
  allergies?: string[];
  current_medications?: string[];
  user_type?: number;
  status?: number;
  avatar_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface HealthData {
  id: string;
  user_id: string;
  device_id?: string;
  data_type: string;
  data_value?: number;
  unit?: string;
  systolic_pressure?: number;
  diastolic_pressure?: number;
  heart_rate?: number;
  blood_sugar?: number;
  temperature?: number;
  fall_detected?: boolean;
  fall_severity?: number;
  location_latitude?: number;
  location_longitude?: number;
  measurement_time: string;
  abnormal_flag?: number;
  ai_analysis_result?: any;
  alert_sent?: boolean;
  reviewed_by?: string;
  reviewed_at?: string;
  created_at?: string;
}

export interface Device {
  id: string;
  user_id: string;
  device_type: string;
  device_name: string;
  manufacturer?: string;
  serial_number?: string;
  mac_address?: string;
  firmware_version?: string;
  battery_level?: number;
  last_heartbeat?: string;
  connection_status?: number;
  configuration?: any;
  geo_region?: string;
  status?: number;
  assigned_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface EmergencyCall {
  id: string;
  user_id: string;
  device_id?: string;
  call_type: string;
  trigger_source?: string;
  severity_level?: number;
  location_latitude?: number;
  location_longitude?: number;
  location_address?: string;
  call_time: string;
  response_status?: number;
  responder_id?: string;
  response_time?: string;
  arrival_time?: string;
  completion_time?: string;
  response_notes?: string;
  health_data_snapshot?: any;
  created_at?: string;
  updated_at?: string;
}

export interface CarePlan {
  id: string;
  user_id: string;
  plan_name: string;
  plan_type: number;
  description?: string;
  goals?: any[];
  interventions?: any[];
  schedule?: any;
  monitoring_params?: any;
  responsible_caregiver_id?: string;
  start_date: string;
  end_date?: string;
  status?: number;
  review_frequency_days?: number;
  last_review_date?: string;
  next_review_date?: string;
  risk_level?: number;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}
