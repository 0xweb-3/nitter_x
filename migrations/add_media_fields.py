#!/usr/bin/env python3
"""
数据库迁移：添加推文媒体字段
添加 media_urls（JSONB）和 has_media（BOOLEAN）字段
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.postgres_client import get_postgres_client


def migrate():
    """执行迁移"""
    pg_client = get_postgres_client()

    print("=" * 60)
    print("数据库迁移：添加推文媒体字段")
    print("=" * 60)

    # 1. 添加 media_urls 字段（JSONB）
    print("\n[1/3] 添加 media_urls 字段...")
    try:
        query1 = """
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS media_urls JSONB DEFAULT '[]'::jsonb
        """
        pg_client.execute_update(query1)
        print("✅ media_urls 字段添加成功")
    except Exception as e:
        print(f"⚠️  media_urls 字段可能已存在: {e}")

    # 2. 添加 has_media 字段（BOOLEAN）
    print("\n[2/3] 添加 has_media 字段...")
    try:
        query2 = """
        ALTER TABLE tweets
        ADD COLUMN IF NOT EXISTS has_media BOOLEAN DEFAULT FALSE
        """
        pg_client.execute_update(query2)
        print("✅ has_media 字段添加成功")
    except Exception as e:
        print(f"⚠️  has_media 字段可能已存在: {e}")

    # 3. 更新现有数据（将 NULL 转换为空数组）
    print("\n[3/3] 更新现有数据...")
    try:
        query3 = """
        UPDATE tweets
        SET media_urls = '[]'::jsonb
        WHERE media_urls IS NULL
        """
        rows = pg_client.execute_update(query3)
        print(f"✅ 已更新 {rows} 条记录")
    except Exception as e:
        print(f"⚠️  更新数据时出错: {e}")

    # 4. 创建索引（可选，用于快速筛选有媒体的推文）
    print("\n[4/4] 创建索引...")
    try:
        query4 = """
        CREATE INDEX IF NOT EXISTS idx_tweets_has_media ON tweets(has_media)
        WHERE has_media = TRUE
        """
        pg_client.execute_update(query4)
        print("✅ has_media 索引创建成功")
    except Exception as e:
        print(f"⚠️  索引创建失败: {e}")

    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


def rollback():
    """回滚迁移"""
    pg_client = get_postgres_client()

    print("=" * 60)
    print("回滚迁移：删除推文媒体字段")
    print("=" * 60)

    # 删除索引
    print("\n[1/3] 删除索引...")
    try:
        query1 = "DROP INDEX IF EXISTS idx_tweets_has_media"
        pg_client.execute_update(query1)
        print("✅ 索引已删除")
    except Exception as e:
        print(f"❌ 删除索引失败: {e}")

    # 删除字段
    print("\n[2/3] 删除 has_media 字段...")
    try:
        query2 = "ALTER TABLE tweets DROP COLUMN IF EXISTS has_media"
        pg_client.execute_update(query2)
        print("✅ has_media 字段已删除")
    except Exception as e:
        print(f"❌ 删除字段失败: {e}")

    print("\n[3/3] 删除 media_urls 字段...")
    try:
        query3 = "ALTER TABLE tweets DROP COLUMN IF EXISTS media_urls"
        pg_client.execute_update(query3)
        print("✅ media_urls 字段已删除")
    except Exception as e:
        print(f"❌ 删除字段失败: {e}")

    print("\n" + "=" * 60)
    print("回滚完成！")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="推文媒体字段迁移")
    parser.add_argument(
        "--rollback", action="store_true", help="回滚迁移（删除字段）"
    )
    args = parser.parse_args()

    if args.rollback:
        confirm = input("⚠️  确认回滚迁移？这将删除 media_urls 和 has_media 字段 (yes/no): ")
        if confirm.lower() == "yes":
            rollback()
        else:
            print("已取消回滚")
    else:
        migrate()
