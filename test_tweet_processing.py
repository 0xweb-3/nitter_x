"""
测试推文处理流程

验证从数据库读取推文 → 处理 → 保存结果的完整流程
"""

import sys
from src.processor.tweet_processor import get_tweet_processor
from src.storage.postgres_client import get_postgres_client
from src.utils.logger import setup_logger

logger = setup_logger("test_processing", log_file="logs/test_processing.log")


def test_single_tweet():
    """测试单条推文处理"""
    print("=" * 80)
    print("推文处理流程测试")
    print("=" * 80)

    # 1. 获取客户端
    print("\n1. 初始化客户端...")
    try:
        pg = get_postgres_client()
        processor = get_tweet_processor()
        print("  ✓ PostgresClient 初始化成功")
        print("  ✓ TweetProcessor 初始化成功")
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return False

    # 2. 获取待处理推文
    print("\n2. 获取待处理推文...")
    try:
        pending_tweets = pg.get_pending_tweets(limit=1)
        if not pending_tweets:
            print("  ⚠ 没有待处理推文")
            print("  💡 提示：先运行 main.py 采集一些推文")
            return False

        tweet = pending_tweets[0]
        print(f"  ✓ 获取到推文: {tweet['tweet_id']}")
        print(f"    作者: {tweet['author']}")
        print(f"    内容: {tweet['content'][:100] if len(tweet['content']) > 100 else tweet['content']}...")

    except Exception as e:
        import traceback
        print(f"  ✗ 获取推文失败: {e}")
        traceback.print_exc()
        return False

    # 3. 更新状态为 processing
    print("\n3. 更新推文状态为 processing...")
    try:
        pg.update_tweet_processing_status(tweet['tweet_id'], 'processing')
        print(f"  ✓ 状态已更新")
    except Exception as e:
        print(f"  ✗ 更新状态失败: {e}")

    # 4. 处理推文
    print("\n4. 处理推文（调用 LLM）...")
    print("  ⏱ 这可能需要几秒钟，请稍候...")
    try:
        result = processor.process_tweet(
            tweet_id=tweet['tweet_id'],
            content=tweet['content'],
            author=tweet['author']
        )

        print(f"\n  ✓ 处理完成！")
        print(f"    分级: {result['grade']}")
        print(f"    耗时: {result['processing_time_ms']} ms")

        if result['grade'] in ['A', 'B', 'C']:
            print(f"    摘要: {result.get('summary_cn', '未生成')}")
            print(f"    关键词: {', '.join(result.get('keywords', []))}")
            if result.get('translated_content'):
                print(f"    翻译: {result['translated_content'][:100]}...")
            if result.get('embedding'):
                print(f"    向量维度: {len(result['embedding'])}")

    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        pg.update_tweet_processing_status(tweet['tweet_id'], 'failed')
        return False

    # 5. 保存处理结果
    print("\n5. 保存处理结果到数据库...")
    try:
        record_id = pg.insert_processed_tweet(result)
        if record_id:
            print(f"  ✓ 处理结果已保存，记录 ID: {record_id}")
        else:
            print(f"  ✗ 保存处理结果失败")
            return False

    except Exception as e:
        print(f"  ✗ 保存失败: {e}")
        return False

    # 6. 更新推文状态为 completed 或 skipped
    print("\n6. 更新推文最终状态...")
    try:
        final_status = 'completed' if result['grade'] in ['A', 'B', 'C', 'D', 'E'] else 'skipped'
        pg.update_tweet_processing_status(tweet['tweet_id'], final_status)
        print(f"  ✓ 推文状态已更新为: {final_status}")
    except Exception as e:
        print(f"  ✗ 更新状态失败: {e}")

    # 7. 验证结果
    print("\n7. 验证处理结果...")
    try:
        processed_tweets = pg.get_processed_tweets(limit=1)
        if processed_tweets:
            pt = processed_tweets[0]
            print(f"  ✓ 成功从数据库读取处理结果")
            print(f"    推文 ID: {pt['tweet_id']}")
            print(f"    分级: {pt['grade']}")
            print(f"    摘要: {pt.get('summary_cn', 'N/A')}")

        else:
            print(f"  ⚠ 未能读取到处理结果")

    except Exception as e:
        print(f"  ✗ 验证失败: {e}")

    print("\n" + "=" * 80)
    print("✓ 测试完成！")
    print("=" * 80)

    return True


def main():
    """主函数"""
    try:
        success = test_single_tweet()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}", exc_info=True)
        print(f"\n✗ 测试失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
