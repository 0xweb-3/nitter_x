"""
数据库迁移脚本：添加 tweet_url 字段
执行方式: python migrations/add_tweet_url_field.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.postgres_client import get_postgres_client

def main():
    """执行迁移"""
    print("=" * 80)
    print("数据库迁移：添加 tweet_url 字段到 tweets 表")
    print("=" * 80)
    print()

    pg_client = get_postgres_client()

    try:
        # 检查字段是否已存在
        check_sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'tweets' AND column_name = 'tweet_url'
        """
        result = pg_client.execute_query(check_sql)

        if result:
            print("✓ tweet_url 字段已存在，无需迁移")
            return

        print("→ 正在添加 tweet_url 字段...")

        # 添加 tweet_url 字段
        add_column_sql = """
        ALTER TABLE tweets
        ADD COLUMN tweet_url TEXT;
        """
        pg_client.execute_update(add_column_sql)

        print("✓ 成功添加 tweet_url 字段")
        print()

        # 添加索引（可选，如果经常按 URL 查询）
        print("→ 添加索引...")
        add_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_tweets_tweet_url ON tweets(tweet_url);
        """
        pg_client.execute_update(add_index_sql)
        print("✓ 成功添加索引")
        print()

        # 验证
        print("→ 验证表结构...")
        verify_sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'tweets'
        ORDER BY ordinal_position
        """
        columns = pg_client.execute_query(verify_sql)

        print("\n当前 tweets 表结构:")
        print("-" * 80)
        for col in columns:
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            print(f"  {col['column_name']:<20} {col['data_type']:<20} {nullable}")
        print("-" * 80)
        print()
        print("✓ 迁移完成!")

    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        raise

    finally:
        pg_client.close()
        print("=" * 80)


if __name__ == "__main__":
    main()
