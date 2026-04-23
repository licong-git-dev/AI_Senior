import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://bmaarkhvsuqsnvvbtcsa.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtYWFya2h2c3Vxc252dmJ0Y3NhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc5MzQsImV4cCI6MjA3Nzg5MzkzNH0.kc3ecE-L5VUjiaM46H0Q90Z65KoHROsAXE7zTp3HgFw'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
})

// 数据库类型定义
export interface HealthData {
  id?: string
  user_id: string
  data_type: string
  value: number
  unit: string
  timestamp: string
  device_id?: string
  notes?: string
}

export interface SensorData {
  id?: string
  user_id: string
  device_type: string
  sensor_type: string
  value: number
  unit: string
  timestamp: string
  metadata?: any
}

export interface HealthAlert {
  id?: string
  user_id: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  indicator_name: string
  abnormal_value: number
  normal_range: string
  risk_assessment: string
  recommended_actions: string
  resolved: boolean
  created_at: string
}

export interface HealthPrediction {
  id?: string
  user_id: string
  prediction_type: string
  prediction_date: string
  confidence: number
  risk_factors: string[]
  recommendations: string[]
  created_at: string
}

export interface EmergencyCall {
  id?: string
  user_id: string
  call_type: string
  status: 'pending' | 'accepted' | 'completed' | 'cancelled'
  location?: {
    latitude: number
    longitude: number
    address?: string
  }
  notes?: string
  created_at: string
  responded_at?: string
}
