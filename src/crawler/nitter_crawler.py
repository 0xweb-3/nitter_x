"""
Nitter 推文爬虫
负责从 Nitter 实例获取用户推文信息（从 Redis 获取可用实例）
"""

import time
import logging
from typing import List, Dict, Optional

from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.crawler.constants import KNOWN_INSTANCES

logger = logging.getLogger(__name__)


class NitterCrawler:
    """Nitter 推文爬虫类"""

    def __init__(self, use_redis_instances: bool = True, max_instances: int = 20):
        """
        初始化爬虫

        Args:
            use_redis_instances: 是否从 Redis 获取实例列表（推荐）
            max_instances: 最多使用的实例数量（默认20个）
        """
        self.use_redis_instances = use_redis_instances
        self.max_instances = max_instances
        self.timeout = settings.CRAWLER_TIMEOUT
        self.retry = settings.CRAWLER_RETRY
        self.delay = settings.CRAWLER_DELAY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

        # 初始化实例列表
        self._instances_cache = []
        self._last_refresh = 0
        self._refresh_instances()

    def _refresh_instances(self):
        """刷新实例列表（获取前 N 个最快的实例）"""
        current_time = time.time()

        # 每 10 分钟最多刷新一次
        if current_time - self._last_refresh < 600:
            return

        if self.use_redis_instances:
            # 从 Redis 获取可用实例
            try:
                from src.crawler.instance_discovery import NitterInstanceDiscovery

                discovery = NitterInstanceDiscovery()
                instances_data = discovery.get_available_instances(force_refresh=False)

                if instances_data:
                    # 提取 URL，已按响应时间排序，取前 N 个
                    self._instances_cache = [
                        inst["url"] for inst in instances_data[:self.max_instances]
                    ]
                    logger.info(
                        f"从 Redis 加载前 {len(self._instances_cache)} 个可用实例"
                    )
                else:
                    logger.warning("Redis 中没有可用实例，使用内置列表")
                    self._instances_cache = KNOWN_INSTANCES[:self.max_instances].copy()

            except Exception as e:
                logger.error(f"从 Redis 获取实例失败: {e}，使用内置列表")
                self._instances_cache = KNOWN_INSTANCES[:self.max_instances].copy()
        else:
            # 使用配置文件中的实例
            self._instances_cache = settings.NITTER_INSTANCES[:self.max_instances]

        self._last_refresh = current_time

    def fetch_user_timeline(
        self, username: str, max_tweets: int = 20
    ) -> Optional[List[Dict]]:
        """
        获取用户时间线推文（按顺序尝试所有可用实例）

        Args:
            username: Twitter 用户名
            max_tweets: 最大获取推文数量

        Returns:
            推文列表，每个推文为字典格式
            如果所有实例都失败，返回 None
            如果成功但没有推文，返回空列表 []
        """
        # 刷新实例列表
        self._refresh_instances()

        if not self._instances_cache:
            logger.error("没有可用的 Nitter 实例")
            return None

        tweets = []

        # 按顺序尝试每个实例
        for instance_index, instance in enumerate(self._instances_cache, 1):
            try:
                url = f"{instance}/{username}"

                logger.info(
                    f"尝试从实例 {instance_index}/{len(self._instances_cache)}: "
                    f"{instance} 获取用户 {username} 的推文"
                )

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                # 解析 HTML
                tweets = self._parse_timeline(response.text, username)

                if tweets:
                    logger.info(
                        f"✓ 成功从 {instance} 获取 {len(tweets)} 条推文"
                    )
                    return tweets[:max_tweets]
                else:
                    logger.warning(f"✗ {instance} 返回空推文列表，尝试下一个实例")
                    continue

            except requests.RequestException as e:
                logger.warning(
                    f"✗ 实例 {instance} 请求失败: {e}，"
                    f"尝试下一个实例 ({instance_index}/{len(self._instances_cache)})"
                )
                # 短暂延迟后尝试下一个实例
                if instance_index < len(self._instances_cache):
                    time.sleep(self.delay)
                continue

            except Exception as e:
                logger.error(f"✗ 实例 {instance} 解析失败: {e}，尝试下一个实例")
                if instance_index < len(self._instances_cache):
                    time.sleep(self.delay)
                continue

        # 所有实例都失败
        logger.error(
            f"所有 {len(self._instances_cache)} 个实例都无法获取用户 {username} 的推文"
        )
        return None

    def _parse_timeline(self, html: str, username: str) -> List[Dict]:
        """
        解析时间线 HTML，提取推文信息

        Args:
            html: HTML 内容
            username: 用户名

        Returns:
            推文列表
        """
        soup = BeautifulSoup(html, "html.parser")
        tweets = []

        # 查找所有推文容器
        tweet_items = soup.find_all("div", class_="timeline-item")

        for item in tweet_items:
            try:
                tweet_data = self._extract_tweet_data(item, username)
                if tweet_data:
                    tweets.append(tweet_data)
            except Exception as e:
                logger.warning(f"解析单条推文失败: {e}")
                continue

        return tweets

    def _extract_tweet_data(self, item, username: str) -> Optional[Dict]:
        """
        从推文元素中提取数据

        Args:
            item: BeautifulSoup 推文元素
            username: 用户名

        Returns:
            推文数据字典
        """
        # 提取推文链接和 ID
        link = item.find("a", class_="tweet-link")
        if not link:
            return None

        tweet_url = link.get("href", "")
        # tweet_id 通常在 URL 最后: /username/status/1234567890
        parts = tweet_url.split("/")
        if len(parts) < 4 or parts[-2] != "status":
            return None

        tweet_id = parts[-1].split("#")[0]  # 去除可能的锚点

        # 提取推文内容
        content_div = item.find("div", class_="tweet-content")
        content = content_div.get_text(strip=True) if content_div else ""

        # 提取发布时间
        time_span = item.find("span", class_="tweet-date")
        published_at = self._parse_timestamp(time_span) if time_span else datetime.now()

        # 提取作者信息
        author_div = item.find("a", class_="username")
        author = author_div.get_text(strip=True) if author_div else username

        return {
            "tweet_id": tweet_id,
            "author": author.lstrip("@"),
            "author_id": "",  # Nitter 通常不提供 author_id
            "content": content,
            "published_at": published_at,
            "tweet_url": tweet_url,
        }

    def _parse_timestamp(self, time_element) -> datetime:
        """
        解析时间戳

        Args:
            time_element: 时间元素

        Returns:
            datetime 对象
        """
        try:
            # 尝试从 title 属性获取完整时间
            title = time_element.get("title", "")
            if title:
                # 格式: "Dec 22, 2025 · 9:00 AM UTC"
                # 这里需要根据实际格式调整
                return datetime.strptime(title.split("·")[0].strip(), "%b %d, %Y")
        except Exception:
            pass

        # 默认返回当前时间
        return datetime.now()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    crawler = NitterCrawler()
    tweets = crawler.fetch_user_timeline("elonmusk", max_tweets=5)

    for tweet in tweets:
        print(f"Tweet ID: {tweet['tweet_id']}")
        print(f"Author: {tweet['author']}")
        print(f"Content: {tweet['content'][:100]}...")
        print(f"Published: {tweet['published_at']}")
        print("-" * 80)
