#!/usr/bin/env python3
"""
快速测试脚本 - 测试 Nitter 爬虫和数据库连接
"""

import sys
import logging

from src.utils.logger import setup_logger
from src.crawler.nitter_crawler import NitterCrawler
from src.storage.postgres_client import get_postgres_client
from src.storage.redis_client import get_redis_client

logger = setup_logger("test", level="DEBUG")


def test_nitter_crawler():
    """测试 Nitter 爬虫"""
    print("\n" + "=" * 80)
    print("测试 Nitter 爬虫")
    print("=" * 80)

    try:
        crawler = NitterCrawler()
        tweets = crawler.fetch_user_timeline("elonmusk", max_tweets=3)

        if tweets:
            print(f"✓ 成功获取 {len(tweets)} 条推文\n")
            for i, tweet in enumerate(tweets, 1):
                print(f"推文 {i}:")
                print(f"  ID: {tweet['tweet_id']}")
                print(f"  作者: {tweet['author']}")
                print(f"  内容: {tweet['content'][:100]}...")
                print(f"  时间: {tweet['published_at']}")
                print()
        else:
            print("✗ 未获取到推文")
            return False

        return True

    except Exception as e:
        print(f"✗ 爬虫测试失败: {e}")
        logger.exception(e)
        return False


def test_postgres():
    """测试 PostgreSQL 连接"""
    print("\n" + "=" * 80)
    print("测试 PostgreSQL 连接")
    print("=" * 80)

    try:
        pg_client = get_postgres_client()

        # 测试查询
        result = pg_client.execute_query("SELECT version()")
        print(f"✓ PostgreSQL 连接成功")
        print(f"  版本: {result[0]['version'][:50]}...\n")

        # 测试表查询
        users = pg_client.get_watched_users()
        print(f"  关注用户数: {len(users)}")

        pg_client.close()
        return True

    except Exception as e:
        print(f"✗ PostgreSQL 连接失败: {e}")
        logger.exception(e)
        return False


def test_redis():
    """测试 Redis 连接"""
    print("\n" + "=" * 80)
    print("测试 Redis 连接")
    print("=" * 80)

    try:
        redis_client = get_redis_client()

        # 测试 ping
        redis_client.client.ping()
        print(f"✓ Redis 连接成功\n")

        # 测试队列操作
        test_data = {"test": "data", "timestamp": "2025-12-22"}
        redis_client.push_to_queue("test_queue", test_data)
        print(f"  ✓ 推送测试数据到队列")

        popped = redis_client.pop_from_queue("test_queue", timeout=1)
        print(f"  ✓ 从队列弹出数据: {popped}")

        redis_client.close()
        return True

    except Exception as e:
        print(f"✗ Redis 连接失败: {e}")
        logger.exception(e)
        return False


def main():
    print("\n" + "=" * 80)
    print("Nitter X 系统测试")
    print("=" * 80)

    results = []

    # 测试 PostgreSQL
    results.append(("PostgreSQL", test_postgres()))

    # 测试 Redis
    results.append(("Redis", test_redis()))

    # 测试 Nitter 爬虫
    results.append(("Nitter 爬虫", test_nitter_crawler()))

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name:<20} {status}")

    all_passed = all(result[1] for result in results)

    print("=" * 80)

    if all_passed:
        print("✓ 所有测试通过")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
