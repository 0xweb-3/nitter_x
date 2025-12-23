"""
Nitter 推文爬虫
负责从 Nitter 实例获取用户推文信息（从 Redis 获取可用实例）
"""

import time
import logging
from typing import List, Dict, Optional

from datetime import datetime, timezone

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
        # 使用更完整的浏览器请求头，模拟真实浏览器
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
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

    def _request_with_retry(self, url: str, max_retries: int = None) -> Optional[requests.Response]:
        """
        带重试机制的 HTTP 请求

        Args:
            url: 请求 URL
            max_retries: 最大重试次数，默认使用配置

        Returns:
            Response 对象，失败返回 None
        """
        if max_retries is None:
            max_retries = settings.HTTP_RETRY_COUNT

        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"正在请求 {url} (尝试 {attempt}/{max_retries})")
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.debug(f"请求超时 {url} (尝试 {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(settings.HTTP_RETRY_DELAY)
                    continue

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.debug(f"连接错误 {url} (尝试 {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(settings.HTTP_RETRY_DELAY)
                    continue

            except requests.exceptions.HTTPError as e:
                # HTTP 错误（4xx, 5xx）通常不应该重试，除非是 5xx 服务器错误
                last_exception = e
                if e.response.status_code >= 500:
                    logger.debug(f"服务器错误 {url} (尝试 {attempt}/{max_retries}): {e.response.status_code}")
                    if attempt < max_retries:
                        time.sleep(settings.HTTP_RETRY_DELAY)
                        continue
                # 4xx 客户端错误不重试
                logger.debug(f"HTTP 错误 {url}: {e.response.status_code}")
                return None

            except requests.RequestException as e:
                last_exception = e
                logger.debug(f"请求异常 {url} (尝试 {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(settings.HTTP_RETRY_DELAY)
                    continue

        # 所有重试都失败
        logger.warning(f"请求失败 {url}，已重试 {max_retries} 次: {last_exception}")
        return None

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

                # 使用带重试的请求方法
                response = self._request_with_retry(url)

                if not response:
                    logger.warning(f"✗ {instance} 请求失败，尝试下一个实例")
                    if instance_index < len(self._instances_cache):
                        time.sleep(self.delay)
                    continue

                # 保存当前实例URL（用于补全媒体相对路径）
                self.current_instance = instance

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
        # 检查是否是置顶推文
        is_pinned = item.find("div", class_="pinned") is not None

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
        published_at = self._parse_timestamp(time_span) if time_span else datetime.now(timezone.utc)

        # 提取作者信息
        author_div = item.find("a", class_="username")
        author = author_div.get_text(strip=True) if author_div else username

        # 提取媒体信息（图片、视频、GIF）
        media_urls = self._extract_media_urls(item)

        # 构建 x.com 原始链接（用于溯源）
        twitter_url = f"https://x.com/{author.lstrip('@')}/status/{tweet_id}"

        return {
            "tweet_id": tweet_id,
            "author": author.lstrip("@"),
            "author_id": "",  # Nitter 通常不提供 author_id
            "content": content,
            "published_at": published_at,
            "tweet_url": twitter_url,  # 保存 x.com 原始链接
            "media_urls": media_urls,  # 媒体URL列表
            "is_pinned": is_pinned,  # 标记是否为置顶推文
        }

    def _extract_media_urls(self, item) -> List[str]:
        """
        从推文元素中提取媒体URL

        Args:
            item: BeautifulSoup 推文元素

        Returns:
            媒体URL列表
        """
        media_urls = []

        try:
            # 查找媒体附件容器
            attachments = item.find("div", class_="attachments")
            if not attachments:
                return media_urls

            # 提取图片
            images = attachments.find_all("a", class_="still-image")
            for img_link in images:
                # 获取高清图片链接
                img = img_link.find("img")
                if img:
                    # 尝试获取原图链接
                    src = img.get("src", "")
                    if src:
                        # Nitter 图片通常是相对路径，需要补全
                        if src.startswith("/"):
                            # 使用当前实例的域名
                            if hasattr(self, 'current_instance'):
                                src = f"{self.current_instance}{src}"
                        media_urls.append(src)

            # 提取视频/GIF
            videos = attachments.find_all("video")
            for video in videos:
                source = video.find("source")
                if source:
                    src = source.get("src", "")
                    if src:
                        if src.startswith("/"):
                            if hasattr(self, 'current_instance'):
                                src = f"{self.current_instance}{src}"
                        media_urls.append(src)

            # 提取 GIF（有时在单独的容器中）
            gif_containers = attachments.find_all("div", class_="gif")
            for gif_div in gif_containers:
                video = gif_div.find("video")
                if video:
                    source = video.find("source")
                    if source:
                        src = source.get("src", "")
                        if src:
                            if src.startswith("/"):
                                if hasattr(self, 'current_instance'):
                                    src = f"{self.current_instance}{src}"
                            media_urls.append(src)

        except Exception as e:
            logger.debug(f"提取媒体URL失败: {e}")

        return media_urls

    def _parse_timestamp(self, time_element) -> datetime:
        """
        解析时间戳

        Args:
            time_element: 时间元素

        Returns:
            datetime 对象
        """
        try:
            # 方法1: 从 a 标签的 title 属性获取完整时间
            link = time_element.find("a")
            if link:
                title = link.get("title", "")
                if title:
                    # 格式: "Dec 22, 2025 · 5:47 AM UTC"
                    # 分割并解析
                    parts = title.split("·")
                    if len(parts) >= 2:
                        date_part = parts[0].strip()  # "Dec 22, 2025"
                        time_part = parts[1].strip()  # "5:47 AM UTC"

                        # 组合完整时间字符串
                        datetime_str = f"{date_part} {time_part}"

                        # 尝试多种格式解析
                        formats = [
                            "%b %d, %Y %I:%M %p UTC",  # Dec 22, 2025 5:47 AM UTC
                            "%b %d, %Y %H:%M UTC",      # Dec 22, 2025 17:47 UTC
                        ]

                        for fmt in formats:
                            try:
                                # 解析时间并添加UTC时区信息
                                dt = datetime.strptime(datetime_str, fmt)
                                return dt.replace(tzinfo=timezone.utc)
                            except ValueError:
                                continue

            # 方法2: 从 span 的 title 属性直接获取
            title = time_element.get("title", "")
            if title and "·" in title:
                parts = title.split("·")
                date_part = parts[0].strip()
                time_part = parts[1].strip()
                datetime_str = f"{date_part} {time_part}"

                formats = [
                    "%b %d, %Y %I:%M %p UTC",
                    "%b %d, %Y %H:%M UTC",
                ]

                for fmt in formats:
                    try:
                        # 解析时间并添加UTC时区信息
                        dt = datetime.strptime(datetime_str, fmt)
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

        except Exception as e:
            logger.debug(f"解析时间戳失败: {e}")

        # 默认返回当前UTC时间
        logger.warning("无法解析时间戳，使用当前UTC时间")
        return datetime.now(timezone.utc)


if __name__ == "__main__":
    """调试入口"""
    import sys
    from bs4 import BeautifulSoup

    # 设置日志级别
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    print("=" * 80)
    print("Nitter 爬虫调试测试")
    print("=" * 80)
    print()

    # 测试参数
    test_instance = "https://nitter.tiekoetter.com"
    test_username = "by0x_1993"
    test_url = f"{test_instance}/{test_username}"

    print(f"测试实例: {test_instance}")
    print(f"测试用户: {test_username}")
    print(f"测试 URL: {test_url}")
    print()

    # 初始化爬虫
    crawler = NitterCrawler(use_redis_instances=False, max_instances=1)

    print("【测试 1】直接访问用户页面")
    print("-" * 80)

    try:
        # 直接访问测试
        print("\n1. 发送 HTTP 请求...")
        response = crawler._request_with_retry(test_url)

        if not response:
            print("   ✗ 请求失败")
            sys.exit(1)

        print(f"   ✓ 请求成功")
        print(f"   状态码: {response.status_code}")
        print(f"   实际 URL: {response.url}")
        print(f"   响应编码: {response.encoding}")
        print(f"   Content-Encoding: {response.headers.get('Content-Encoding', 'None')}")

        content = response.text
        print(f"   响应大小: {len(content)} 字符")
        print(f"   响应字节大小: {len(response.content)} 字节")

        # 保存响应内容
        debug_file = "/tmp/nitter_user_page_debug.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   响应内容已保存到: {debug_file}")

        # 显示内容预览
        print(f"\n2. 响应内容预览（前 500 字符）:")
        print("   " + "-" * 76)
        preview = content[:500].replace("\n", "\n   ")
        print(f"   {preview}")
        print("   " + "-" * 76)

        # HTML 结构检查
        print(f"\n3. HTML 结构检查:")
        soup = BeautifulSoup(content, "html.parser")

        timeline_items = soup.find_all("div", class_="timeline-item")
        print(f"   - 找到 timeline-item: {len(timeline_items)} 个")

        # 检查置顶推文
        pinned_items = [item for item in timeline_items if item.find("div", class_="pinned")]
        if pinned_items:
            print(f"   - 检测到 {len(pinned_items)} 条置顶推文 📌")

        if timeline_items:
            first_item = timeline_items[0]
            is_pinned = first_item.find("div", class_="pinned") is not None
            pinned_text = " (置顶推文 📌)" if is_pinned else ""
            print(f"\n   第一个 timeline-item 的结构{pinned_text}:")
            print(f"   - 包含 tweet-link: {'是' if first_item.find('a', class_='tweet-link') else '否'}")
            print(f"   - 包含 tweet-content: {'是' if first_item.find('div', class_='tweet-content') else '否'}")
            print(f"   - 包含 tweet-date: {'是' if first_item.find('span', class_='tweet-date') else '否'}")
            print(f"   - 包含 username: {'是' if first_item.find('a', class_='username') else '否'}")
            print(f"   - 是否置顶: {'是' if is_pinned else '否'}")

            # 显示第一个 item 的 HTML
            print(f"\n   第一个 timeline-item 的 HTML（前 300 字符）:")
            print("   " + "-" * 76)
            item_html = str(first_item)[:300].replace("\n", "\n   ")
            print(f"   {item_html}")
            print("   " + "-" * 76)

        # 检查其他关键元素
        print(f"\n4. 页面元素检查:")
        print(f"   - 包含 <html>: {'是' if '<html' in content.lower() else '否'}")
        print(f"   - 包含 <body>: {'是' if '<body' in content.lower() else '否'}")
        print(f"   - 包含 'timeline': {'是' if 'timeline' in content.lower() else '否'}")
        print(f"   - 包含 'tweet': {'是' if 'tweet' in content.lower() else '否'}")
        print(f"   - 包含用户名 '{test_username}': {'是' if test_username.lower() in content.lower() else '否'}")

    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print("【测试 2】使用 fetch_user_timeline 方法获取推文")
    print("-" * 80)

    try:
        # 临时设置实例缓存为测试实例
        crawler._instances_cache = [test_instance]

        tweets = crawler.fetch_user_timeline(test_username, max_tweets=5)

        if tweets is None:
            print("\n✗ 获取失败：所有实例都失败")
            sys.exit(1)
        elif not tweets:
            print("\n✓ 获取成功，但没有找到推文")
            print("\n可能原因：")
            print("  1. HTML 结构与预期不符（选择器不匹配）")
            print("  2. 页面使用 JavaScript 动态加载内容")
            print("  3. 用户没有推文或推文被隐藏")
            print(f"\n请检查保存的 HTML 文件: {debug_file}")
        else:
            print(f"\n✓ 成功获取到 {len(tweets)} 条推文:\n")
            for i, tweet in enumerate(tweets, 1):
                pinned_mark = " [📌 置顶]" if tweet.get("is_pinned", False) else ""
                print(f"【推文 {i}】{pinned_mark}")
                print(f"  Tweet ID: {tweet['tweet_id']}")
                print(f"  Author: {tweet['author']}")
                print(f"  Content: {tweet['content'][:150]}{'...' if len(tweet['content']) > 150 else ''}")
                print(f"  Published: {tweet['published_at']}")
                print(f"  URL: {tweet['tweet_url']}")
                print()

    except Exception as e:
        print(f"\n✗ 获取推文时出错: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80)
    print("测试完成")
    print("=" * 80)

