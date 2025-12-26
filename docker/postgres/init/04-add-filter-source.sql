-- 添加筛选来源字段，用于追踪推文是被 Ollama 筛选还是远程 LLM 分级
-- 创建时间: 2025-12-26

-- 添加筛选来源字段
ALTER TABLE processed_tweets
ADD COLUMN IF NOT EXISTS filter_source VARCHAR(50) DEFAULT 'remote_llm';

-- 添加字段注释
COMMENT ON COLUMN processed_tweets.filter_source IS '筛选来源：expired（推文已过期）/ ollama_filtered（被Ollama过滤）/ remote_llm（远程LLM分级）';

-- 创建索引以便查询统计
CREATE INDEX IF NOT EXISTS idx_processed_tweets_filter_source
ON processed_tweets(filter_source);

-- 验证字段创建
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'processed_tweets'
        AND column_name = 'filter_source'
    ) THEN
        RAISE NOTICE '✓ filter_source 字段已成功添加到 processed_tweets 表';
    ELSE
        RAISE EXCEPTION '✗ filter_source 字段添加失败';
    END IF;
END $$;
