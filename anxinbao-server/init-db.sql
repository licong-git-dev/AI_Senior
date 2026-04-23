-- 安心宝数据库初始化脚本
-- PostgreSQL

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用于模糊搜索

-- 创建索引优化查询
-- 对话记录索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_created
    ON conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_session
    ON conversations(session_id);

-- 健康通知索引
CREATE INDEX IF NOT EXISTS idx_notifications_user_read
    ON health_notifications(user_id, is_read, created_at DESC);

-- 审计日志索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created
    ON audit_logs(user_id, created_at DESC);

-- 刷新令牌索引（用于清理）
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires
    ON refresh_tokens(expires_at) WHERE is_revoked = false;

-- 创建定时清理函数
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- 创建清理过期审计日志函数（保留90天）
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- 授予权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anxinbao;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anxinbao;
