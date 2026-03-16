-- 数据库初始化脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 创建表结构
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(10) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    email_subscribed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE
);

-- 外贸数据表
CREATE TABLE IF NOT EXISTS trade_data (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    hs_code VARCHAR(20) NOT NULL,
    hs_description VARCHAR(255),
    trade_partner VARCHAR(100) NOT NULL,
    export_quantity NUMERIC(20, 4),
    quantity_unit VARCHAR(20),
    export_value_usd NUMERIC(20, 2) NOT NULL,
    unit_value_usd NUMERIC(20, 4),
    trade_mode VARCHAR(50),
    data_source VARCHAR(50) DEFAULT 'UN Comtrade',
    status VARCHAR(20) DEFAULT 'confirmed',
    confirmed_by INTEGER,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 爬虫脚本表
CREATE TABLE IF NOT EXISTS crawler_scripts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    hs_codes VARCHAR(500),
    periods VARCHAR(200),
    partners TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    auto_run BOOLEAN DEFAULT FALSE,
    cron_expression VARCHAR(50),
    version VARCHAR(20) DEFAULT '1.0.0',
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 爬虫任务表
CREATE TABLE IF NOT EXISTS crawler_tasks (
    id SERIAL PRIMARY KEY,
    script_id INTEGER NOT NULL,
    script_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 2),
    total_records INTEGER DEFAULT 0,
    new_records INTEGER DEFAULT 0,
    updated_records INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    logs TEXT,
    error_message TEXT,
    triggered_by INTEGER,
    trigger_type VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(50),
    user_id INTEGER,
    username VARCHAR(50),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    old_values JSONB,
    new_values JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 创建索引
-- ============================================

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE INDEX IF NOT EXISTS idx_trade_data_year ON trade_data(year);
CREATE INDEX IF NOT EXISTS idx_trade_data_hs_code ON trade_data(hs_code);
CREATE INDEX IF NOT EXISTS idx_trade_data_trade_partner ON trade_data(trade_partner);
CREATE INDEX IF NOT EXISTS idx_trade_data_status ON trade_data(status);
CREATE INDEX IF NOT EXISTS idx_trade_data_created ON trade_data(created_at);

CREATE INDEX IF NOT EXISTS idx_crawler_scripts_name ON crawler_scripts(name);
CREATE INDEX IF NOT EXISTS idx_crawler_scripts_is_active ON crawler_scripts(is_active);

CREATE INDEX IF NOT EXISTS idx_crawler_tasks_script_id ON crawler_tasks(script_id);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_status ON crawler_tasks(status);
CREATE INDEX IF NOT EXISTS idx_crawler_tasks_created ON crawler_tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- ============================================
-- 插入初始数据
-- ============================================

-- 插入默认管理员用户 (密码: admin123)
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
    '',
    '851762,851770',
    '2022,2023,2024',
    true,
    false,
    '1.0.0'
WHERE NOT EXISTS (SELECT 1 FROM crawler_scripts WHERE name = 'UN Comtrade 爬虫');
