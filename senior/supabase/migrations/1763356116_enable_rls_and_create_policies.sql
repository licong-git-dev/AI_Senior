-- Migration: enable_rls_and_create_policies
-- Created at: 1763356116

-- 启用行级安全性（RLS）
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE care_plans ENABLE ROW LEVEL SECURITY;

-- Profiles表策略：用户可以查看和更新自己的档案
CREATE POLICY "用户可查看自己的档案" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "用户可更新自己的档案" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "护理人员可查看所有档案" ON profiles
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND user_type = 3
    )
  );

-- Health_data表策略：用户和授权护理人员可查看
CREATE POLICY "用户可查看自己的健康数据" ON health_data
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND (id = health_data.user_id OR user_type IN (3, 4))
    )
  );

CREATE POLICY "设备可插入健康数据" ON health_data
  FOR INSERT WITH CHECK (true);

CREATE POLICY "护理人员可更新健康数据" ON health_data
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND user_type IN (3, 4)
    )
  );

-- Devices表策略
CREATE POLICY "用户可查看自己的设备" ON devices
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND (id = devices.user_id OR user_type IN (3, 4))
    )
  );

CREATE POLICY "用户可管理自己的设备" ON devices
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND id = devices.user_id
    )
  );

-- Emergency_calls表策略
CREATE POLICY "用户可查看自己的紧急呼叫" ON emergency_calls
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND (id = emergency_calls.user_id OR user_type IN (3, 4))
    )
  );

CREATE POLICY "用户可创建紧急呼叫" ON emergency_calls
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND id = emergency_calls.user_id
    )
  );

CREATE POLICY "护理人员可更新紧急呼叫" ON emergency_calls
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND user_type IN (3, 4)
    )
  );

-- Care_plans表策略
CREATE POLICY "用户可查看自己的护理计划" ON care_plans
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND (id = care_plans.user_id OR user_type IN (3, 4))
    )
  );

CREATE POLICY "护理人员可管理护理计划" ON care_plans
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND user_type IN (3, 4)
    )
  );;