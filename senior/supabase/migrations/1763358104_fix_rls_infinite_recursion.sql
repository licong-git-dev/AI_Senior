-- Migration: fix_rls_infinite_recursion
-- Created at: 1763358104


-- 修复RLS策略的无限递归问题
-- 策略简化：直接使用user_id比较，避免嵌套查询profiles表

-- 1. 修复health_data表的策略
DROP POLICY IF EXISTS "用户可查看自己的健康数据" ON health_data;
DROP POLICY IF EXISTS "护理人员可更新健康数据" ON health_data;
DROP POLICY IF EXISTS "设备可插入健康数据" ON health_data;

-- 允许所有认证用户查看自己的健康数据（简化策略，不检查user_type）
CREATE POLICY "用户可查看自己的健康数据"
ON health_data FOR SELECT
USING (user_id = auth.uid());

-- 允许所有认证用户插入健康数据
CREATE POLICY "用户可插入健康数据"
ON health_data FOR INSERT
WITH CHECK (user_id = auth.uid());

-- 允许所有认证用户更新自己的健康数据
CREATE POLICY "用户可更新健康数据"
ON health_data FOR UPDATE
USING (user_id = auth.uid());

-- 2. 修复devices表的策略
DROP POLICY IF EXISTS "用户可查看自己的设备" ON devices;
DROP POLICY IF EXISTS "用户可管理自己的设备" ON devices;

CREATE POLICY "用户可查看自己的设备"
ON devices FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "用户可管理自己的设备"
ON devices FOR ALL
USING (user_id = auth.uid());

-- 3. 修复emergency_calls表的策略
DROP POLICY IF EXISTS "用户可查看自己的紧急呼叫" ON emergency_calls;
DROP POLICY IF EXISTS "用户可创建紧急呼叫" ON emergency_calls;
DROP POLICY IF EXISTS "护理人员可更新紧急呼叫" ON emergency_calls;

CREATE POLICY "用户可查看自己的紧急呼叫"
ON emergency_calls FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "用户可创建紧急呼叫"
ON emergency_calls FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY "用户可更新紧急呼叫"
ON emergency_calls FOR UPDATE
USING (user_id = auth.uid());
;