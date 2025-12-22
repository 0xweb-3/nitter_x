"""
主程序入口 - 推文采集任务（持续运行版本）
"""

import sys
import time
import signal
import logging
from typing import List

from src.config.settings import settings
from src.utils.logger import setup_logger
from src.crawler.nitter_crawler import NitterCrawler
from src.storage.postgres_client import get_postgres_client
from src.storage.redis_client import get_redis_client

# 设置日志
logger = setup_logger("main", log_file="logs/crawler.log")

# 全局运行状态标志
running = True


def signal_handler(sig, frame):
    """处理终止信号（Ctrl+C）"""
    global running
    logger.info("\n" + "=" * 80)
    logger.info("收到终止信号，正在优雅退出...")
    logger.info("=" * 80)
    running = False


def crawl_user(username: str, crawler: NitterCrawler, pg_client, redis_client) -> int:
    """
    采集单个用户的推文

    Args:
        username: 用户名
        crawler: 爬虫实例
        pg_client: PostgreSQL 客户端
        redis_client: Redis 客户端

    Returns:
        新增推文数量

    Raises:
        Exception: 当所有 Nitter 实例都失败时抛出异常
    """
    logger.info(f"开始采集用户: {username}")

    # 获取该用户最新的推文 ID（用于去重和截断）
    latest_tweet_id = pg_client.get_latest_tweet_id(username)
    logger.info(f"用户 {username} 最新推文 ID: {latest_tweet_id}")

    # 从 Nitter 获取推文
    tweets = crawler.fetch_user_timeline(username, max_tweets=50)

    # 如果返回 None，说明所有实例都失败
    if tweets is None:
        logger.error(f"用户 {username} 所有 Nitter 实例都失败，无法获取推文")
        raise Exception(f"所有 Nitter 实例都失败")

    # 如果返回空列表，说明成功但没有推文
    if not tweets:
        logger.info(f"用户 {username} 成功获取，但没有新推文")
        return 0

    new_count = 0

    for tweet in tweets:
        tweet_id = tweet["tweet_id"]

        # 如果遇到已存在的推文，停止采集（增量采集）
        if tweet_id == latest_tweet_id:
            logger.info(f"遇到已存在推文 {tweet_id}，停止采集")
            break

        # Redis 去重检查
        if redis_client.is_duplicate(tweet_id):
            logger.debug(f"推文 {tweet_id} 已在缓存中，跳过")
            continue

        # 插入数据库
        result = pg_client.insert_tweet(tweet)

        if result:
            # 推送到处理队列
            redis_client.push_to_queue(settings.REDIS_QUEUE_PROCESS, tweet_id)
            new_count += 1
            logger.info(f"新增推文: {tweet_id}")

    logger.info(f"用户 {username} 采集完成，新增 {new_count} 条推文")
    return new_count


def main():
    """主函数 - 持续运行版本"""
    global running

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 80)
    logger.info("推文采集任务启动（持续运行模式）")
    logger.info(f"采集循环间隔: {settings.CRAWL_INTERVAL} 秒")
    logger.info(f"用户采集间隔: {settings.CRAWL_USER_INTERVAL} 秒")
    logger.info(
        f"采集任务锁超时: {settings.get_crawl_lock_timeout()} 秒 "
        f"({settings.CRAWL_INTERVAL} × {settings.CRAWL_LOCK_TIMEOUT_MULTIPLIER}，防止死锁）"
    )
    logger.info("按 Ctrl+C 优雅退出")
    logger.info("=" * 80)

    # 初始化客户端
    crawler = NitterCrawler()
    pg_client = get_postgres_client()
    redis_client = get_redis_client()

    cycle_count = 0  # 循环计数器

    try:
        while running:
            cycle_count += 1
            cycle_start_time = time.time()
            lock_value = None  # 初始化锁标识
            lock_name = "crawler:main"

            logger.info("=" * 80)
            logger.info(f"开始第 {cycle_count} 轮采集")
            logger.info("=" * 80)

            # 尝试获取采集锁
            lock_value = redis_client.acquire_lock(
                lock_name, expire=settings.get_crawl_lock_timeout()
            )

            if not lock_value:
                # 未能获取锁，说明上一轮还在执行
                logger.warning(
                    f"⚠️  无法获取采集锁，上一轮采集可能还在执行中，跳过本轮采集"
                )
                logger.info("=" * 80)

                # 等待下一轮
                if running:
                    logger.info(f"等待 {settings.CRAWL_INTERVAL} 秒后重试...")
                    wait_time = settings.CRAWL_INTERVAL
                    while wait_time > 0 and running:
                        sleep_chunk = min(1, wait_time)
                        time.sleep(sleep_chunk)
                        wait_time -= sleep_chunk
                continue

            # 成功获取锁，开始采集
            logger.info(f"✓ 成功获取采集锁，开始本轮采集")

            try:
                # 获取需要采集的用户列表（只获取距上次采集超过指定时间的用户）
                watched_users = pg_client.get_watched_users(
                    active_only=True, min_interval_seconds=settings.CRAWL_USER_INTERVAL
                )

                if not watched_users:
                    logger.info(
                        f"暂无需要采集的用户（所有用户都在 {settings.CRAWL_USER_INTERVAL} 秒采集间隔内）"
                    )
                    # 没有用户需要采集，立即释放锁
                    redis_client.release_lock(lock_name, lock_value)
                    lock_value = None  # 标记锁已释放，避免 finally 重复释放
                    logger.info(f"✓ 已释放采集锁（无用户需要采集）")
                    logger.info("=" * 80)

                    # 等待下一轮
                    if running:
                        logger.info(f"等待 {settings.CRAWL_INTERVAL} 秒后开始下一轮采集...")
                        wait_time = settings.CRAWL_INTERVAL
                        while wait_time > 0 and running:
                            sleep_chunk = min(1, wait_time)
                            time.sleep(sleep_chunk)
                            wait_time -= sleep_chunk
                    continue

                logger.info(
                    f"本轮需要采集 {len(watched_users)} 个用户: "
                    f"{', '.join([u['username'] for u in watched_users])}"
                )

                total_new = 0

                # 遍历每个用户进行采集
                for user in watched_users:
                    if not running:  # 检查是否收到退出信号
                        break

                    username = user["username"]

                    try:
                        new_count = crawl_user(
                            username, crawler, pg_client, redis_client
                        )
                        total_new += new_count

                        # 只有成功采集时才更新最后采集时间
                        pg_client.execute_update(
                            "UPDATE watched_users SET last_crawled_at = NOW() WHERE username = %s",
                            (username,),
                        )
                        logger.info(f"✓ 用户 {username} 采集成功，已更新采集时间")

                        # 延迟，避免请求过快
                        if running:  # 确保延迟时不阻塞退出
                            time.sleep(settings.CRAWLER_DELAY)

                    except Exception as e:
                        # 采集失败，不更新时间，下一轮会继续尝试
                        logger.error(
                            f"✗ 用户 {username} 采集失败: {e}，不更新采集时间，下一轮将继续尝试"
                        )
                        # 短暂延迟后继续下一个用户
                        if running:
                            time.sleep(settings.CRAWLER_DELAY)
                        continue

                cycle_duration = time.time() - cycle_start_time
                logger.info("=" * 80)
                logger.info(
                    f"第 {cycle_count} 轮采集完成，耗时 {cycle_duration:.1f} 秒，新增 {total_new} 条推文"
                )

                if not running:  # 如果收到退出信号，不再等待
                    break

                # 等待下一轮采集
                logger.info(f"等待 {settings.CRAWL_INTERVAL} 秒后开始下一轮采集...")
                logger.info("=" * 80)

                # 分段等待，以便更快响应退出信号
                wait_time = settings.CRAWL_INTERVAL
                while wait_time > 0 and running:
                    sleep_chunk = min(1, wait_time)  # 每次最多等待1秒
                    time.sleep(sleep_chunk)
                    wait_time -= sleep_chunk

            except Exception as e:
                logger.error(f"采集任务异常: {e}", exc_info=True)
                if running:
                    logger.info(f"等待 {settings.CRAWL_INTERVAL} 秒后重试...")
                    time.sleep(settings.CRAWL_INTERVAL)

            finally:
                # 无论成功还是异常，都要释放锁
                if lock_value:
                    redis_client.release_lock(lock_name, lock_value)
                    logger.info(f"✓ 已释放采集锁")

    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)

    finally:
        # 清理资源
        logger.info("正在清理资源...")
        pg_client.close()
        redis_client.close()
        logger.info("=" * 80)
        logger.info(f"推文采集任务已停止，共执行 {cycle_count} 轮采集")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
