-- Migration: fix_rls_policies_ambiguous_parameter
-- Created at: 1763357956


-- 修复RLS策略的参数引用问题
-- 删除现有策略并重新创建，使用更明确的引用方式

-- 修复health_data表的SELECT策略
DROP POLICY IF EXISTS "用户可查看自己的健康数据" ON health_data;
CREATE POLICY "用户可查看自己的健康数据"
ON health_data FOR SELECT
USING (
    user_id = auth.uid() 
    OR EXISTS (
        SELECT 1 FROM profiles p
        WHERE p.id = auth.uid() 
        AND p.user_type IN (3, 4)
    )
);

-- 修复devices表的SELECT策略
DROP POLICY IF EXISTS "用户可查看自己的设备" ON devices;
CREATE POLICY "用户可查看自己的设备"
ON devices FOR SELECT
USING (
    user_id = auth.uid()
    OR EXISTS (
        SELECT 1 FROM profiles p
        WHERE p.id = auth.uid()
        AND p.user_type IN (3, 4)
    )
);

-- 修复emergency_calls表的SELECT策略
DROP POLICY IF EXISTS "用户可查看自己的紧急呼叫" ON emergency_calls;
CREATE POLICY "用户可查看自己的紧急呼叫"
ON emergency_calls FOR SELECT
USING (
    user_id = auth.uid()
    OR EXISTS (
        SELECT 1 FROM profiles p
        WHERE p.id = auth.uid()
        AND p.user_type IN (3, 4)
    )
);
;