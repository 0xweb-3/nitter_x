"""
Bark 推送功能测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.notification.bark_client import get_bark_client
from src.storage.postgres_client import get_postgres_client

def test_bark_client():
    """测试 Bark 客户端"""
    print("=" * 80)
    print("测试 1: Bark 客户端")
    print("=" * 80)

    bark_client = get_bark_client()

    # 测试 key（用户提供）
    test_key = "https://api.day.app/rHptkyHMnXTwb479svYRoV/"

    print(f"\n使用测试 key: {test_key}")
    print("发送测试推送...")

    result = bark_client.test_notification(test_key)

    if result['success']:
        print("✅ 测试推送成功！")
        print(f"响应: {result['response']}")
    else:
        print(f"❌ 测试推送失败: {result['message']}")

    print()
    return result['success']


def test_add_bark_key():
    """测试添加 Bark key 到数据库"""
    print("=" * 80)
    print("测试 2: 添加 Bark Key 到数据库")
    print("=" * 80)

    pg_client = get_postgres_client()

    # 测试 key
    test_key_url = "https://api.day.app/rHptkyHMnXTwb479svYRoV/"
    key_name = "测试设备"

    print(f"\n添加 Bark key: {key_name}")
    print(f"URL: {test_key_url}")

    # 先删除可能存在的旧记录
    delete_query = "DELETE FROM bark_keys WHERE bark_url = %s"
    pg_client.execute_update(delete_query, (test_key_url,))

    # 插入新记录
    query = """
    INSERT INTO bark_keys (key_name, bark_url, priority, notes, is_active)
    VALUES (%s, %s, %s, %s, TRUE)
    RETURNING id
    """

    try:
        with pg_client.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (key_name, test_key_url, 5, "测试用 Bark key"))
                key_id = cur.fetchone()[0]

        print(f"✅ 成功添加 Bark key，ID: {key_id}")

        # 验证
        verify_query = "SELECT * FROM bark_keys WHERE id = %s"
        result = pg_client.execute_query(verify_query, (key_id,))
        if result:
            print(f"验证成功: {result[0]}")

        print()
        return True
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        print()
        return False


def test_push_settings():
    """测试推送配置"""
    print("=" * 80)
    print("测试 3: 推送配置")
    print("=" * 80)

    pg_client = get_postgres_client()

    query = "SELECT * FROM push_settings ORDER BY setting_key"
    results = pg_client.execute_query(query)

    print(f"\n当前推送配置:")
    for row in results:
        print(f"  {row['setting_key']}: {row['setting_value']} ({row['description']})")

    print()
    return len(results) > 0


def test_push_service():
    """测试推送服务"""
    print("=" * 80)
    print("测试 4: 推送服务完整流程")
    print("=" * 80)

    from src.notification.push_service import get_push_service

    push_service = get_push_service()

    # 模拟推文数据
    test_tweet = {
        "tweet_id": "test_tweet_001",
        "grade": "P0",
        "summary": "比特币突破10万美元！市场情绪高涨",
        "keywords": ["比特币", "BTC", "突破", "10万美元"],
        "tweet_url": "https://x.com/test/status/123456789",
        "author": "test_user"
    }

    print(f"\n模拟推文推送:")
    print(f"  级别: {test_tweet['grade']}")
    print(f"  摘要: {test_tweet['summary']}")
    print(f"  关键词: {', '.join(test_tweet['keywords'])}")
    print(f"  作者: @{test_tweet['author']}")
    print()

    print("开始推送...")
    result = push_service.push_tweet(
        tweet_id=test_tweet["tweet_id"],
        grade=test_tweet["grade"],
        summary=test_tweet["summary"],
        keywords=test_tweet["keywords"],
        tweet_url=test_tweet["tweet_url"],
        author=test_tweet["author"]
    )

    print(f"\n推送结果:")
    print(f"  是否推送: {result['pushed']}")
    if result['pushed']:
        print(f"  成功: {result['success_count']}/{result['total_keys']}")
        print(f"  失败: {result['failed_count']}/{result['total_keys']}")
    else:
        print(f"  原因: {result.get('reason', '未知')}")

    print()
    return result['pushed'] and result['success_count'] > 0


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("Bark 推送功能完整测试")
    print("=" * 80 + "\n")

    tests = [
        ("Bark 客户端", test_bark_client),
        ("添加 Bark Key", test_add_bark_key),
        ("推送配置", test_push_settings),
        ("推送服务", test_push_service),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))

    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
