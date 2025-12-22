"""
Nitter 实例来源获取模块
从第三方来源获取 Nitter 实例列表（不包含内置配置）
"""

import logging
from typing import List, Set
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

from src.utils.logger import setup_logger

logger = setup_logger("nitter_sources", log_file="logs/nitter_discovery.log")


class InstanceSource(ABC):
    """实例来源基类"""

    @abstractmethod
    def fetch_instances(self) -> List[str]:
        """
        获取实例列表

        Returns:
            实例 URL 列表
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        获取来源名称

        Returns:
            来源名称
        """
        pass


class StatusPageSource(InstanceSource):
    """从状态监控页面获取实例"""

    def __init__(self, url: str = "https://status.d420.de/", timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def get_source_name(self) -> str:
        return f"StatusPage({self.url})"

    def fetch_instances(self) -> List[str]:
        """
        从状态页面获取实例列表

        Returns:
            实例 URL 列表
        """
        try:
            logger.info(f"从 {self.url} 获取实例列表...")
            response = self.session.get(self.url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            instances = set()

            # 尝试多种可能的选择器
            selectors = [
                "a[href*='nitter']",
                "a[href*='twitter']",
                "a[href*='bird']",
                "table a",
                ".instance a",
                "td a",
            ]

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get("href", "")
                    if href and self._is_nitter_url(href):
                        base_url = self._extract_base_url(href)
                        if base_url:
                            instances.add(base_url)

            result = list(instances)
            logger.info(f"✓ 从状态页面发现 {len(result)} 个实例")
            return result

        except requests.RequestException as e:
            logger.warning(f"✗ 从状态页面获取失败: {e}")
            return []
        except Exception as e:
            logger.error(f"✗ 解析状态页面时出错: {e}")
            return []

    def _is_nitter_url(self, url: str) -> bool:
        """判断是否为 Nitter 相关 URL"""
        url_lower = url.lower()
        keywords = ["nitter", "twitter", "bird", "xcancel"]
        return any(keyword in url_lower for keyword in keywords)

    def _extract_base_url(self, url: str) -> str:
        """提取基础 URL"""
        try:
            if url.startswith("http"):
                parts = url.split("/")
                if len(parts) >= 3:
                    return f"{parts[0]}//{parts[2]}"
        except Exception:
            pass
        return ""


class InstanceSourceManager:
    """实例来源管理器，整合多个第三方来源"""

    def __init__(self):
        self.sources: List[InstanceSource] = []

    def add_source(self, source: InstanceSource):
        """添加第三方来源"""
        self.sources.append(source)

    def fetch_all_instances(self) -> Set[str]:
        """
        从所有第三方来源获取实例并去重

        Returns:
            去重后的实例集合
        """
        all_instances = set()

        for source in self.sources:
            try:
                logger.info(f"正在从 {source.get_source_name()} 获取实例...")
                instances = source.fetch_instances()
                all_instances.update(instances)
                logger.info(f"✓ 从 {source.get_source_name()} 获取到 {len(instances)} 个实例")
            except Exception as e:
                logger.error(f"✗ 从 {source.get_source_name()} 获取失败: {e}")
                continue

        logger.info(f"总计从 {len(self.sources)} 个第三方来源获取到 {len(all_instances)} 个不重复实例")
        return all_instances


def get_default_sources() -> InstanceSourceManager:
    """
    获取默认配置的第三方来源

    Returns:
        配置好的 InstanceSourceManager
    """
    manager = InstanceSourceManager()

    # 添加状态监控页面
    manager.add_source(StatusPageSource("https://status.d420.de/"))

    # 未来可以添加更多第三方来源
    # manager.add_source(GitHubSource("https://github.com/..."))
    # manager.add_source(CommunityAPISource("https://api.nitter.com/instances"))

    return manager

