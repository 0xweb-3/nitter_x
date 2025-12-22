-- 创建推文表
CREATE TABLE IF NOT EXISTS tweets (
    id BIGSERIAL PRIMARY KEY,
    tweet_id VARCHAR(50) UNIQUE NOT NULL,
    author VARCHAR(100) NOT NULL,
    author_id VARCHAR(50),
    content TEXT NOT NULL,
    clean_content TEXT,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    tweet_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags JSONB,
    score DECIMAL(10, 2) DEFAULT 0,
    level VARCHAR(10),
    status VARCHAR(20) DEFAULT 'raw'
);

-- 创建关注用户表
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

-- 创建标签表（用于标签统计和管理）
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

-- 创建处理日志表
CREATE TABLE IF NOT EXISTS processing_logs (
    id BIGSERIAL PRIMARY KEY,
    tweet_id VARCHAR(50) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    processing_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tweets_tweet_id ON tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweets_author ON tweets(author);
CREATE INDEX IF NOT EXISTS idx_tweets_published_at ON tweets(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_status ON tweets(status);
CREATE INDEX IF NOT EXISTS idx_tweets_level ON tweets(level);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_tweet_url ON tweets(tweet_url);

CREATE INDEX IF NOT EXISTS idx_watched_users_username ON watched_users(username);
CREATE INDEX IF NOT EXISTS idx_watched_users_is_active ON watched_users(is_active);
CREATE INDEX IF NOT EXISTS idx_watched_users_priority ON watched_users(priority DESC);

CREATE INDEX IF NOT EXISTS idx_tag_definitions_category ON tag_definitions(category);
CREATE INDEX IF NOT EXISTS idx_tag_definitions_is_active ON tag_definitions(is_active);

CREATE INDEX IF NOT EXISTS idx_processing_logs_tweet_id ON processing_logs(tweet_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_stage ON processing_logs(stage);
CREATE INDEX IF NOT EXISTS idx_processing_logs_created_at ON processing_logs(created_at DESC);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 tweets 表添加更新时间触发器
DROP TRIGGER IF EXISTS update_tweets_updated_at ON tweets;
CREATE TRIGGER update_tweets_updated_at BEFORE UPDATE ON tweets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 为 watched_users 表添加更新时间触发器
DROP TRIGGER IF EXISTS update_watched_users_updated_at ON watched_users;
CREATE TRIGGER update_watched_users_updated_at BEFORE UPDATE ON watched_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建视图：展示处理完成的推文
CREATE OR REPLACE VIEW processed_tweets AS
SELECT
    t.id,
    t.tweet_id,
    t.author,
    t.content,
    t.clean_content,
    t.published_at,
    t.tags,
    t.score,
    t.level,
    t.created_at
FROM tweets t
WHERE t.status = 'DONE'
ORDER BY t.published_at DESC;

-- 添加注释
COMMENT ON TABLE tweets IS '推文主表，存储原始推文和处理结果';
COMMENT ON TABLE watched_users IS '关注用户列表';
COMMENT ON TABLE tag_definitions IS '标签定义表';
COMMENT ON TABLE processing_logs IS '处理日志表，记录每个推文的处理过程';
COMMENT ON VIEW processed_tweets IS '已处理完成的推文视图';
