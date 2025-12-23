"""
数据库迁移：创建推文处理结果表

添加 processed_tweets 表用于存储 LLM 处理结果
更新 tweets 表添加处理状态字段
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.storage.postgres_client import get_postgres_client
from src.utils.logger import setup_logger

logger = setup_logger("migration", log_file="logs/migration.log")


def migrate():
    """执行迁移"""
    pg = get_postgres_client()

    logger.info("开始数据库迁移：创建推文处理结果表")

    try:
        # 1. 给 tweets 表添加处理状态字段
        logger.info("1. 添加 tweets.processing_status 字段")
        query1 = """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'processing_status_enum'
            ) THEN
                CREATE TYPE processing_status_enum AS ENUM (
                    'pending',      -- 待处理
                    'processing',   -- 处理中
                    'completed',    -- 已完成
                    'failed',       -- 失败
                    'skipped'       -- 跳过（F级推文）
                );
            END IF;
        END$$;
        """
        pg.execute_update(query1)
        logger.info("  ✓ 处理状态枚举类型已创建")

        query2 = """
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS processing_status processing_status_enum DEFAULT 'pending'
        """
        pg.execute_update(query2)
        logger.info("  ✓ processing_status 字段已添加")

        # 2. 删除旧的 processed_tweets 视图（如果存在）
        logger.info("2. 删除旧的 processed_tweets 视图")
        query2_5 = "DROP VIEW IF EXISTS processed_tweets CASCADE"
        pg.execute_update(query2_5)
        logger.info("  ✓ 旧视图已删除（如果存在）")

        # 3. 创建推文处理结果表
        logger.info("3. 创建 processed_tweets 表")
        query3 = """
        CREATE TABLE IF NOT EXISTS processed_tweets (
            id SERIAL PRIMARY KEY,
            tweet_id VARCHAR(100) UNIQUE NOT NULL,
            grade CHAR(1) NOT NULL CHECK (grade IN ('A', 'B', 'C', 'D', 'E', 'F')),
            summary_cn VARCHAR(100),
            keywords JSONB DEFAULT '[]'::jsonb,
            embedding JSONB,
            translated_content TEXT,
            processing_time_ms INTEGER,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (tweet_id) REFERENCES tweets(tweet_id) ON DELETE CASCADE
        )
        """
        pg.execute_update(query3)
        logger.info("  ✓ processed_tweets 表已创建")

        # 4. 创建索引
        logger.info("4. 创建索引")

        # 按分级查询索引
        query4 = """
        CREATE INDEX IF NOT EXISTS idx_processed_tweets_grade
        ON processed_tweets(grade)
        """
        pg.execute_update(query4)
        logger.info("  ✓ idx_processed_tweets_grade 索引已创建")

        # 按处理时间查询索引
        query5 = """
        CREATE INDEX IF NOT EXISTS idx_processed_tweets_processed_at
        ON processed_tweets(processed_at DESC)
        """
        pg.execute_update(query5)
        logger.info("  ✓ idx_processed_tweets_processed_at 索引已创建")

        # tweets 表处理状态索引
        query6 = """
        CREATE INDEX IF NOT EXISTS idx_tweets_processing_status
        ON tweets(processing_status)
        WHERE processing_status = 'pending'
        """
        pg.execute_update(query6)
        logger.info("  ✓ idx_tweets_processing_status 索引已创建")

        # 5. 添加触发器自动更新 updated_at
        logger.info("5. 创建 updated_at 自动更新触发器")
        query7 = """
        CREATE OR REPLACE FUNCTION update_processed_tweets_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        pg.execute_update(query7)

        query8 = """
        DROP TRIGGER IF EXISTS trigger_update_processed_tweets_updated_at
        ON processed_tweets;

        CREATE TRIGGER trigger_update_processed_tweets_updated_at
        BEFORE UPDATE ON processed_tweets
        FOR EACH ROW
        EXECUTE FUNCTION update_processed_tweets_updated_at();
        """
        pg.execute_update(query8)
        logger.info("  ✓ updated_at 触发器已创建")

        logger.info("✓ 数据库迁移成功完成")
        print("\n✓ 数据库迁移成功完成\n")
        return True

    except Exception as e:
        logger.error(f"✗ 数据库迁移失败: {e}")
        print(f"\n✗ 数据库迁移失败: {e}\n")
        return False


def rollback():
    """回滚迁移"""
    pg = get_postgres_client()

    logger.info("开始回滚数据库迁移")

    try:
        # 删除触发器
        logger.info("1. 删除触发器")
        query1 = """
        DROP TRIGGER IF EXISTS trigger_update_processed_tweets_updated_at
        ON processed_tweets;
        DROP FUNCTION IF EXISTS update_processed_tweets_updated_at();
        """
        pg.execute_update(query1)
        logger.info("  ✓ 触发器已删除")

        # 删除索引
        logger.info("2. 删除索引")
        query2 = """
        DROP INDEX IF EXISTS idx_processed_tweets_grade;
        DROP INDEX IF EXISTS idx_processed_tweets_processed_at;
        DROP INDEX IF EXISTS idx_tweets_processing_status;
        """
        pg.execute_update(query2)
        logger.info("  ✓ 索引已删除")

        # 删除 processed_tweets 表
        logger.info("3. 删除 processed_tweets 表")
        query3 = "DROP TABLE IF EXISTS processed_tweets"
        pg.execute_update(query3)
        logger.info("  ✓ processed_tweets 表已删除")

        # 删除 tweets 表的 processing_status 字段
        logger.info("4. 删除 tweets.processing_status 字段")
        query4 = """
        ALTER TABLE tweets DROP COLUMN IF EXISTS processing_status;
        DROP TYPE IF EXISTS processing_status_enum;
        """
        pg.execute_update(query4)
        logger.info("  ✓ processing_status 字段和枚举类型已删除")

        logger.info("✓ 数据库回滚成功完成")
        print("\n✓ 数据库回滚成功完成\n")
        return True

    except Exception as e:
        logger.error(f"✗ 数据库回滚失败: {e}")
        print(f"\n✗ 数据库回滚失败: {e}\n")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback()
    else:
        migrate()
