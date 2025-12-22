"""
Nitter 推文爬虫
负责从 Nitter 实例获取用户推文信息
"""

import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.config.settings import settings

logger = logging.getLogger(__name__)


class NitterCrawler:
    """Nitter 推文爬虫类"""

    def __init__(self):
        self.instances = settings.NITTER_INSTANCES
        self.timeout = settings.CRAWLER_TIMEOUT
        self.retry = settings.CRAWLER_RETRY
        self.delay = settings.CRAWLER_DELAY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def get_random_instance(self) -> str:
        """随机选择一个 Nitter 实例"""
        return random.choice(self.instances)

    def fetch_user_timeline(self, username: str, max_tweets: int = 20) -> List[Dict]:
        """
        获取用户时间线推文

        Args:
            username: Twitter 用户名
            max_tweets: 最大获取推文数量

        Returns:
            推文列表，每个推文为字典格式
        """
        tweets = []

        for attempt in range(self.retry):
            try:
                instance = self.get_random_instance()
                url = f"{instance}/{username}"

                logger.info(f"尝试从 {instance} 获取用户 {username} 的推文 (第 {attempt + 1} 次)")

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                # 解析 HTML
                tweets = self._parse_timeline(response.text, username)

                logger.info(f"成功获取 {len(tweets)} 条推文")
                return tweets[:max_tweets]

            except requests.RequestException as e:
                logger.warning(f"请求失败 (第 {attempt + 1} 次): {e}")
                if attempt < self.retry - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    logger.error(f"重试 {self.retry} 次后仍然失败")

            except Exception as e:
                logger.error(f"解析失败: {e}")
                break

        return tweets

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
