"""
主程序入口 - 推文采集任务
"""

import time
import logging
from typing import List

from src.config.settings import settings
from src.utils.logger import setup_logger
from src.crawler.nitter_crawler import NitterCrawler
from src.storage.postgres_client import get_postgres_client
from src.storage.redis_client import get_redis_client

# 设置日志
logger = setup_logger("main", log_file="logs/crawler.log")


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
    """
    logger.info(f"开始采集用户: {username}")

    # 获取该用户最新的推文 ID（用于去重和截断）
    latest_tweet_id = pg_client.get_latest_tweet_id(username)
    logger.info(f"用户 {username} 最新推文 ID: {latest_tweet_id}")

    # 从 Nitter 获取推文
    tweets = crawler.fetch_user_timeline(username, max_tweets=50)

    if not tweets:
        logger.warning(f"用户 {username} 未获取到推文")
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
    """主函数"""
    logger.info("=" * 80)
    logger.info("推文采集任务启动")
    logger.info("=" * 80)

    # 初始化客户端
    crawler = NitterCrawler()
    pg_client = get_postgres_client()
    redis_client = get_redis_client()

    try:
        # 获取关注用户列表
        watched_users = pg_client.get_watched_users(active_only=True)
        logger.info(f"共有 {len(watched_users)} 个关注用户")

        if not watched_users:
            logger.warning("没有关注用户，请先添加用户到 watched_users 表")
            return

        total_new = 0

        # 遍历每个用户进行采集
        for user in watched_users:
            username = user["username"]

            try:
                new_count = crawl_user(username, crawler, pg_client, redis_client)
                total_new += new_count

                # 更新最后采集时间
                pg_client.execute_update(
                    "UPDATE watched_users SET last_crawled_at = NOW() WHERE username = %s",
                    (username,),
                )

                # 延迟，避免请求过快
                time.sleep(settings.CRAWLER_DELAY)

            except Exception as e:
                logger.error(f"采集用户 {username} 时出错: {e}", exc_info=True)
                continue

        logger.info("=" * 80)
        logger.info(f"采集任务完成，共新增 {total_new} 条推文")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"采集任务异常: {e}", exc_info=True)

    finally:
        # 清理资源
        pg_client.close()
        redis_client.close()


if __name__ == "__main__":
    main()
