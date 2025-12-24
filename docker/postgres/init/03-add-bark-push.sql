-- ============================================
-- Bark 推送功能数据库初始化
-- 创建时间: 2025-12-24
-- 说明: 为 Nitter X 添加 iOS Bark 推送功能相关的表
-- ============================================

-- 设置时区为 UTC
SET TIME ZONE 'UTC';

-- ============================================
-- 1. Bark Keys 配置表
-- ============================================

CREATE TABLE IF NOT EXISTS bark_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    bark_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_push_at TIMESTAMP WITH TIME ZONE,
    push_count INT DEFAULT 0,
    notes TEXT,
    UNIQUE(bark_url)
);

COMMENT ON TABLE bark_keys IS 'Bark推送密钥配置表';
COMMENT ON COLUMN bark_keys.key_name IS 'Key名称（用于界面显示）';
COMMENT ON COLUMN bark_keys.bark_url IS '完整Bark URL或key';
COMMENT ON COLUMN bark_keys.is_active IS '是否启用推送';
COMMENT ON COLUMN bark_keys.priority IS '优先级（预留）';
COMMENT ON COLUMN bark_keys.last_push_at IS '最后推送时间';
COMMENT ON COLUMN bark_keys.push_count IS '推送次数统计';
COMMENT ON COLUMN bark_keys.notes IS '备注信息';

-- 索引
CREATE INDEX IF NOT EXISTS idx_bark_keys_is_active ON bark_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_bark_keys_created_at ON bark_keys(created_at DESC);

-- 更新时间触发器
DROP TRIGGER IF EXISTS update_bark_keys_updated_at ON bark_keys;
CREATE TRIGGER update_bark_keys_updated_at
    BEFORE UPDATE ON bark_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 2. 推送配置表
-- ============================================

CREATE TABLE IF NOT EXISTS push_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE push_settings IS '推送功能配置表';
COMMENT ON COLUMN push_settings.setting_key IS '配置键';
COMMENT ON COLUMN push_settings.setting_value IS '配置值';
COMMENT ON COLUMN push_settings.description IS '配置说明';

-- 初始化默认配置
INSERT INTO push_settings (setting_key, setting_value, description) VALUES
    ('push_enabled', 'true', '全局推送开关'),
    ('push_grades', 'P0,P1,P2', '推送的级别（逗号分隔）'),
    ('push_icon', 'https://em-content.zobj.net/source/apple/391/coin_1fa99.png', '推送使用的icon（加密货币）')
ON CONFLICT (setting_key) DO NOTHING;

-- 索引
CREATE INDEX IF NOT EXISTS idx_push_settings_key ON push_settings(setting_key);

-- 更新时间触发器
DROP TRIGGER IF EXISTS update_push_settings_updated_at ON push_settings;
CREATE TRIGGER update_push_settings_updated_at
    BEFORE UPDATE ON push_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3. 推送历史表
-- ============================================

CREATE TABLE IF NOT EXISTS push_history (
    id BIGSERIAL PRIMARY KEY,
    tweet_id VARCHAR(100) NOT NULL,
    bark_key_id INT REFERENCES bark_keys(id) ON DELETE SET NULL,
    grade VARCHAR(2) NOT NULL,
    push_status VARCHAR(20) NOT NULL,
    error_message TEXT,
    response_data JSONB,
    pushed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE push_history IS 'Bark推送历史记录表';
COMMENT ON COLUMN push_history.tweet_id IS '推文ID';
COMMENT ON COLUMN push_history.bark_key_id IS '使用的Bark key';
COMMENT ON COLUMN push_history.grade IS '推文级别';
COMMENT ON COLUMN push_history.push_status IS '推送状态：success/failed';
COMMENT ON COLUMN push_history.error_message IS '错误信息';
COMMENT ON COLUMN push_history.response_data IS 'Bark API响应';

-- 索引
CREATE INDEX IF NOT EXISTS idx_push_history_tweet_id ON push_history(tweet_id);
CREATE INDEX IF NOT EXISTS idx_push_history_pushed_at ON push_history(pushed_at DESC);
CREATE INDEX IF NOT EXISTS idx_push_history_status ON push_history(push_status);
CREATE INDEX IF NOT EXISTS idx_push_history_bark_key_id ON push_history(bark_key_id);

-- ============================================
-- 初始化完成
-- ============================================

-- 显示创建的表
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE tablename IN ('bark_keys', 'push_settings', 'push_history')
ORDER BY tablename;
