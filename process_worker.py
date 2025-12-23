"""
推文处理 Worker

持续从数据库获取待处理推文并进行 LLM 处理
"""

import sys
import time
import signal
import logging
from typing import List, Dict

from src.config.settings import settings
from src.utils.logger import setup_logger
from src.processor.tweet_processor import get_tweet_processor
from src.storage.postgres_client import get_postgres_client
from src.storage.redis_client import get_redis_client

# 设置日志
logger = setup_logger("process_worker", log_file="logs/process_worker.log")

# 全局运行状态标志
running = True


def signal_handler(sig, frame):
    """处理终止信号（Ctrl+C）"""
    global running
    logger.info("\n" + "=" * 80)
    logger.info("收到终止信号，正在优雅退出...")
    logger.info("=" * 80)
    running = False


def process_single_tweet(tweet: Dict, processor, pg_client) -> bool:
    """
    处理单条推文

    Args:
        tweet: 推文数据
        processor: 推文处理器
        pg_client: PostgreSQL 客户端

    Returns:
        是否处理成功
    """
    tweet_id = tweet["tweet_id"]

    try:
        # 1. 更新状态为 processing
        pg_client.update_tweet_processing_status(tweet_id, "processing")

        # 2. 处理推文
        result = processor.process_tweet(
            tweet_id=tweet_id,
            content=tweet["content"],
            author=tweet["author"]
        )

        # 3. 保存处理结果（仅 P0/P1/P2）
        grade = result["grade"]
        if grade in ["P0", "P1", "P2"]:
            # P0/P1/P2 级推文需要保存到 processed_tweets 表
            record_id = pg_client.insert_processed_tweet(result)
            if not record_id:
                logger.error(f"保存处理结果失败: {tweet_id}")
                pg_client.update_tweet_processing_status(tweet_id, "failed")
                return False

            logger.info(
                f"✓ 推文处理完成: {tweet_id} | 分级: {grade} | "
                f"耗时: {result['processing_time_ms']}ms | 已保存到 processed_tweets"
            )
        else:
            # P3/P4/P5/P6 级推文不需要保存，仅记录分级
            logger.info(
                f"✓ 推文处理完成: {tweet_id} | 分级: {grade} | "
                f"耗时: {result['processing_time_ms']}ms | 未保存（低级别）"
            )

        # 4. 更新推文状态为 completed
        pg_client.update_tweet_processing_status(tweet_id, "completed")

        return True

    except Exception as e:
        logger.error(f"✗ 推文处理失败: {tweet_id}, 错误: {e}")
        pg_client.update_tweet_processing_status(tweet_id, "failed")
        return False


def main():
    """主函数 - 持续处理推文"""
    global running

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 80)
    logger.info("推文处理 Worker 启动")
    logger.info(f"批次大小: 10 条/批")
    logger.info(f"处理间隔: 5 秒")
    logger.info("按 Ctrl+C 优雅退出")
    logger.info("=" * 80)

    # 初始化客户端
    try:
        processor = get_tweet_processor()
        pg_client = get_postgres_client()
        redis_client = get_redis_client()
        logger.info("✓ 所有客户端初始化成功")
    except Exception as e:
        logger.error(f"✗ 初始化失败: {e}")
        return 1

    # 统计信息
    total_processed = 0
    total_success = 0
    total_failed = 0
    cycle_count = 0

    try:
        while running:
            cycle_count += 1
            cycle_start_time = time.time()

            logger.info("=" * 80)
            logger.info(f"开始第 {cycle_count} 轮处理")
            logger.info("=" * 80)

            # 1. 获取待处理推文
            try:
                pending_tweets = pg_client.get_pending_tweets(limit=10)

                if not pending_tweets:
                    logger.info("暂无待处理推文，等待 5 秒后重试...")
                    time.sleep(5)
                    continue

                logger.info(f"获取到 {len(pending_tweets)} 条待处理推文")

            except Exception as e:
                logger.error(f"获取待处理推文失败: {e}")
                time.sleep(5)
                continue

            # 2. 批量处理推文
            batch_success = 0
            batch_failed = 0

            for i, tweet in enumerate(pending_tweets, 1):
                if not running:  # 检查是否收到退出信号
                    break

                logger.info(f"\n[{i}/{len(pending_tweets)}] 处理推文: {tweet['tweet_id']}")
                logger.info(f"  作者: {tweet['author']}")
                logger.info(f"  内容: {tweet['content'][:100]}...")

                success = process_single_tweet(tweet, processor, pg_client)

                if success:
                    batch_success += 1
                    total_success += 1
                else:
                    batch_failed += 1
                    total_failed += 1

                total_processed += 1

                # 推文间延迟（避免API限流）
                if i < len(pending_tweets) and running:
                    time.sleep(1)

            # 3. 本批次统计
            cycle_duration = time.time() - cycle_start_time
            logger.info("=" * 80)
            logger.info(f"第 {cycle_count} 轮处理完成")
            logger.info(f"  耗时: {cycle_duration:.1f} 秒")
            logger.info(f"  成功: {batch_success} 条")
            logger.info(f"  失败: {batch_failed} 条")
            logger.info(f"累计统计:")
            logger.info(f"  总处理: {total_processed} 条")
            logger.info(f"  总成功: {total_success} 条")
            logger.info(f"  总失败: {total_failed} 条")
            logger.info("=" * 80)

            if not running:  # 如果收到退出信号，不再等待
                break

            # 等待下一轮
            logger.info("等待 5 秒后开始下一轮处理...\n")
            wait_time = 5
            while wait_time > 0 and running:
                sleep_chunk = min(1, wait_time)
                time.sleep(sleep_chunk)
                wait_time -= sleep_chunk

    except Exception as e:
        logger.error(f"Worker 异常: {e}", exc_info=True)
        return 1

    finally:
        # 清理资源
        logger.info("正在清理资源...")
        pg_client.close()
        redis_client.close()
        logger.info("=" * 80)
        logger.info(f"推文处理 Worker 已停止")
        logger.info(f"共处理 {total_processed} 条推文（成功: {total_success}, 失败: {total_failed}）")
        logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
