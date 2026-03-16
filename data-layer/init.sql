-- 数据库初始化脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_trade_data_year_hs ON trade_data(year, hs_code);
CREATE INDEX IF NOT EXISTS idx_trade_data_partner ON trade_data(trade_partner);
CREATE INDEX IF NOT EXISTS idx_trade_data_status ON trade_data(status);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_status ON crawler_tasks(status);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_script ON crawler_tasks(script_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- 插入默认管理员用户 (密码: admin123)
-- 密码哈希使用 bcrypt
INSERT INTO users (username, email, hashed_password, full_name, role, is_active, is_superuser)
SELECT 'admin', 'admin@example.com', 
       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1m', 
       '系统管理员', 'admin', true, true
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- 插入默认爬虫脚本
INSERT INTO crawler_scripts (name, description, code, hs_codes, periods, is_active, auto_run, version)
SELECT 
    'UN Comtrade 爬虫',
    '从UN Comtrade获取中国手机维修配件出口数据',
    '',  -- 代码将在运行时加载
    '851762,851770',
    '2022,2023,2024',
    true,
    false,
    '1.0.0'
WHERE NOT EXISTS (SELECT 1 FROM crawler_scripts WHERE name = 'UN Comtrade 爬虫');
