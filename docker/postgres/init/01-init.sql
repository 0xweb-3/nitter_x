-- ============================================
-- Nitter X 数据库初始化脚本
-- 版本: v3.0.0 (P0-P6 价格影响分级系统)
-- ============================================

-- 设置时区为 UTC
SET TIME ZONE 'UTC';

-- ============================================
-- 1. 创建枚举类型
-- ============================================

-- 推文处理状态枚举
DO $$ BEGIN
    CREATE TYPE processing_status_enum AS ENUM (
        'pending',      -- 待处理
        'processing',   -- 处理中
        'completed',    -- 处理完成
        'failed',       -- 处理失败
        'skipped'       -- 跳过处理
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================
-- 2. 创建主表
-- ============================================

-- 推文主表
CREATE TABLE IF NOT EXISTS tweets (
    id BIGSERIAL PRIMARY KEY,
    tweet_id VARCHAR(100) UNIQUE NOT NULL,
    author VARCHAR(100) NOT NULL,
    author_id VARCHAR(50),
    content TEXT NOT NULL,
    clean_content TEXT,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    tweet_url TEXT,
    media_urls JSONB DEFAULT '[]'::jsonb,
    has_media BOOLEAN DEFAULT FALSE,
    processing_status processing_status_enum DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags JSONB,
    score DECIMAL(10, 2) DEFAULT 0,
    level VARCHAR(10),
    status VARCHAR(20) DEFAULT 'raw'
);

COMMENT ON TABLE tweets IS '推文主表，存储原始推文和处理状态';
COMMENT ON COLUMN tweets.tweet_id IS '推文唯一ID';
COMMENT ON COLUMN tweets.author IS '作者用户名';
COMMENT ON COLUMN tweets.content IS '推文原始内容';
COMMENT ON COLUMN tweets.tweet_url IS 'x.com 原文链接';
COMMENT ON COLUMN tweets.media_urls IS '媒体URL列表（图片/视频/GIF）';
COMMENT ON COLUMN tweets.has_media IS '是否包含媒体资源';
COMMENT ON COLUMN tweets.processing_status IS '处理状态：pending/processing/completed/failed/skipped';

-- 关注用户表
CREATE TABLE IF NOT EXISTS watched_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50),
    display_name VARCHAR(200),
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE watched_users IS '关注用户列表';
COMMENT ON COLUMN watched_users.username IS '用户名';
COMMENT ON COLUMN watched_users.display_name IS '显示名称';
COMMENT ON COLUMN watched_users.priority IS '优先级 (1-10)';
COMMENT ON COLUMN watched_users.notes IS '备注信息';

-- 推文处理结果表
CREATE TABLE IF NOT EXISTS processed_tweets (
    id BIGSERIAL PRIMARY KEY,
    tweet_id VARCHAR(100) UNIQUE NOT NULL REFERENCES tweets(tweet_id) ON DELETE CASCADE,
    grade VARCHAR(2) NOT NULL CHECK (grade IN ('P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6')),
    summary_cn VARCHAR(100),
    keywords JSONB DEFAULT '[]'::jsonb,
    translated_content TEXT,
    embedding JSONB,
    processing_time_ms INTEGER,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE processed_tweets IS '推文LLM处理结果表';
COMMENT ON COLUMN processed_tweets.grade IS '价格影响等级：P0(最高)/P1(强信号)/P2(结构性)/P3(宏观)/P4(叙事)/P5(噪音)/P6(舍弃)';
COMMENT ON COLUMN processed_tweets.summary_cn IS '中文摘要（≤30字，仅P0/P1/P2级）';
COMMENT ON COLUMN processed_tweets.keywords IS '关键词数组（仅P0/P1/P2级）';
COMMENT ON COLUMN processed_tweets.translated_content IS '翻译内容（非中文推文）';
COMMENT ON COLUMN processed_tweets.embedding IS '向量表示（384维，仅P0/P1/P2级）';
COMMENT ON COLUMN processed_tweets.processing_time_ms IS '处理耗时（毫秒）';

-- 标签定义表（预留）
CREATE TABLE IF NOT EXISTS tag_definitions (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    weight DECIMAL(5, 2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, name)
);

COMMENT ON TABLE tag_definitions IS '标签定义表（预留扩展）';

-- 处理日志表（预留）
CREATE TABLE IF NOT EXISTS processing_logs (
    id BIGSERIAL PRIMARY KEY,
    tweet_id VARCHAR(50) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    processing_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE processing_logs IS '处理日志表（预留）';

-- ============================================
-- 3. 创建索引
-- ============================================

-- tweets 表索引
CREATE INDEX IF NOT EXISTS idx_tweets_tweet_id ON tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweets_author ON tweets(author);
CREATE INDEX IF NOT EXISTS idx_tweets_published_at ON tweets(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_status ON tweets(status);
CREATE INDEX IF NOT EXISTS idx_tweets_level ON tweets(level);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_tweet_url ON tweets(tweet_url);
CREATE INDEX IF NOT EXISTS idx_tweets_has_media ON tweets(has_media) WHERE has_media = TRUE;
CREATE INDEX IF NOT EXISTS idx_tweets_processing_status ON tweets(processing_status) WHERE processing_status = 'pending';

-- processed_tweets 表索引
CREATE INDEX IF NOT EXISTS idx_processed_tweets_tweet_id ON processed_tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_processed_tweets_grade ON processed_tweets(grade);
CREATE INDEX IF NOT EXISTS idx_processed_tweets_processed_at ON processed_tweets(processed_at DESC);

-- watched_users 表索引
CREATE INDEX IF NOT EXISTS idx_watched_users_username ON watched_users(username);
CREATE INDEX IF NOT EXISTS idx_watched_users_is_active ON watched_users(is_active);
CREATE INDEX IF NOT EXISTS idx_watched_users_priority ON watched_users(priority DESC);

-- tag_definitions 表索引
CREATE INDEX IF NOT EXISTS idx_tag_definitions_category ON tag_definitions(category);
CREATE INDEX IF NOT EXISTS idx_tag_definitions_is_active ON tag_definitions(is_active);

-- processing_logs 表索引
CREATE INDEX IF NOT EXISTS idx_processing_logs_tweet_id ON processing_logs(tweet_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_stage ON processing_logs(stage);
CREATE INDEX IF NOT EXISTS idx_processing_logs_created_at ON processing_logs(created_at DESC);

-- ============================================
-- 4. 创建触发器
-- ============================================

-- 更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- tweets 表触发器
DROP TRIGGER IF EXISTS update_tweets_updated_at ON tweets;
CREATE TRIGGER update_tweets_updated_at
    BEFORE UPDATE ON tweets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- watched_users 表触发器
DROP TRIGGER IF EXISTS update_watched_users_updated_at ON watched_users;
CREATE TRIGGER update_watched_users_updated_at
    BEFORE UPDATE ON watched_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- processed_tweets 表触发器
DROP TRIGGER IF EXISTS update_processed_tweets_updated_at ON processed_tweets;
CREATE TRIGGER update_processed_tweets_updated_at
    BEFORE UPDATE ON processed_tweets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 5. 插入默认数据
-- ============================================

-- 插入默认标签定义
INSERT INTO tag_definitions (category, name, description, weight) VALUES
    ('主题', 'Crypto', '加密货币相关', 1.5),
    ('主题', 'AI', '人工智能相关', 1.5),
    ('主题', '宏观', '宏观经济相关', 1.2),
    ('主题', '项目', '具体项目相关', 1.3),
    ('情绪', '利好', '正面情绪', 1.2),
    ('情绪', '利空', '负面情绪', 1.0),
    ('情绪', '中性', '中性情绪', 0.8),
    ('类型', '新闻', '新闻资讯', 1.3),
    ('类型', '观点', '个人观点', 1.0),
    ('类型', '传言', '未证实消息', 0.7)
ON CONFLICT (category, name) DO NOTHING;

-- ============================================
-- 6. 数据库配置优化
-- ============================================

-- 设置默认时区为 UTC
ALTER DATABASE nitter_x SET timezone TO 'UTC';

-- ============================================
-- 初始化完成
-- ============================================
