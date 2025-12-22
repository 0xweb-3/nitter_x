"""
Nitter 实例健康检测模块
检测实例的可用性和响应时间
"""

import time
import logging
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from src.utils.logger import setup_logger
from src.crawler.instance_sources import get_default_sources
from src.crawler.constants import KNOWN_INSTANCES

logger = setup_logger("nitter_discovery", log_file="logs/nitter_discovery.log")


class NitterInstanceChecker:
    """Nitter 实例健康检测器"""

    def __init__(self, timeout: int = 10, max_workers: int = 20):
        """
        初始化健康检测器

        Args:
            timeout: 请求超时时间（秒）
            max_workers: 并发检测线程数
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
        })

    def check_instance(self, instance_url: str) -> Tuple[str, bool, float]:
        """
        检查单个实例的健康状态

        Args:
            instance_url: 实例 URL

        Returns:
            (URL, 是否可用, 响应时间)
        """
        try:
            start_time = time.time()

            # 访问实例首页
            response = self.session.get(
                instance_url,
                timeout=self.timeout,
                allow_redirects=True
            )

            elapsed = time.time() - start_time

            # 判断是否可用
            if response.status_code == 200:
                # 检查是否包含 Nitter 特征（更严格的判断）
                content = response.text.lower()

                # 排除明显不是 Nitter 的网站
                if "github" in instance_url.lower():
                    return (instance_url, False, elapsed)

                # 检查 Nitter 特征
                nitter_indicators = ["nitter", "instance", "bird", "unofficial"]
                has_indicator = any(keyword in content for keyword in nitter_indicators)

                # 或者 URL 中包含 nitter 相关关键词
                has_nitter_url = any(
                    keyword in instance_url.lower()
                    for keyword in ["nitter", "bird", "twitter", "xcancel"]
                )

                is_nitter = has_indicator or has_nitter_url

                if is_nitter:
                    logger.info(f"✓ {instance_url} 可用 (响应时间: {elapsed:.2f}s)")
                    return (instance_url, True, elapsed)

            logger.debug(f"✗ {instance_url} 不可用 (状态码: {response.status_code})")
            return (instance_url, False, elapsed)

        except requests.exceptions.Timeout:
            logger.debug(f"✗ {instance_url} 超时")
            return (instance_url, False, self.timeout)

        except Exception as e:
            logger.debug(f"✗ {instance_url} 错误: {e}")
            return (instance_url, False, 0)

    def check_instances_batch(self, instances: List[str]) -> List[Dict[str, any]]:
        """
        并发检测多个实例

        Args:
            instances: 实例 URL 列表

        Returns:
            可用实例列表，按响应时间排序
        """
        logger.info(f"开始检测 {len(instances)} 个实例的健康状态...")

        available_instances = []

        # 并发检测所有实例
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.check_instance, url): url
                for url in instances
            }

            for future in as_completed(futures):
                url, is_available, response_time = future.result()

                if is_available:
                    available_instances.append({
                        "url": url,
                        "response_time": response_time,
                        "status": "available"
                    })

        # 按响应时间排序
        available_instances.sort(key=lambda x: x["response_time"])

        logger.info(f"发现 {len(available_instances)} 个可用实例")
        return available_instances


class NitterInstanceDiscovery:
    """Nitter 实例发现与管理（整合来源获取和健康检测）"""

    def __init__(self, timeout: int = 10, max_workers: int = 20):
        """
        初始化实例发现器

        Args:
            timeout: 请求超时时间（秒）
            max_workers: 并发检测线程数
        """
        self.checker = NitterInstanceChecker(timeout, max_workers)
        self.source_manager = get_default_sources()

    def discover_available_instances(
        self,
        use_external_sources: bool = True,
        min_instances: int = 5
    ) -> List[Dict[str, any]]:
        """
        发现所有可用的 Nitter 实例

        Args:
            use_external_sources: 是否从第三方来源获取实例
            min_instances: 最少返回的实例数

        Returns:
            可用实例列表，按响应时间排序
        """
        # 合并配置的实例和第三方实例
        instances_to_check = set(KNOWN_INSTANCES)  # 从配置开始
        logger.info(f"使用配置的 {len(KNOWN_INSTANCES)} 个内置实例")

        # 如果启用，从第三方来源获取更多实例
        if use_external_sources:
            external_instances = self.source_manager.fetch_all_instances()
            instances_to_check.update(external_instances)
            logger.info(f"合并后共 {len(instances_to_check)} 个待检测实例")
        else:
            logger.info("仅使用内置实例，跳过第三方来源")

        # 健康检测
        available_instances = self.checker.check_instances_batch(list(instances_to_check))

        # 如果可用实例太少，警告
        if len(available_instances) < min_instances:
            logger.warning(
                f"可用实例仅 {len(available_instances)} 个，少于期望的 {min_instances} 个"
            )

        return available_instances

    def get_available_urls(
        self,
        max_count: int = 10,
        max_response_time: float = 5.0
    ) -> List[str]:
        """
        获取可用实例 URL 列表

        Args:
            max_count: 最多返回的实例数
            max_response_time: 最大响应时间（秒）

        Returns:
            URL 列表
        """
        instances = self.discover_available_instances()

        # 过滤响应时间
        filtered = [
            inst["url"] for inst in instances
            if inst["response_time"] <= max_response_time
        ]

        return filtered[:max_count]


def update_env_file(instances: List[str], env_file: str = ".env"):
    """
    更新 .env 文件中的 NITTER_INSTANCES

    Args:
        instances: 实例列表
        env_file: .env 文件路径
    """
    import os

    if not instances:
        logger.warning("没有可用实例，不更新 .env 文件")
        return

    instances_str = ",".join(instances)

    # 读取现有文件
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 更新 NITTER_INSTANCES 行
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("NITTER_INSTANCES="):
                lines[i] = f"NITTER_INSTANCES={instances_str}\n"
                updated = True
                break

        if not updated:
            lines.append(f"\nNITTER_INSTANCES={instances_str}\n")

        # 写回文件
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info(f"已更新 {env_file} 文件，共 {len(instances)} 个实例")
    else:
        logger.error(f"{env_file} 文件不存在")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Nitter 实例发现与健康检测")
    parser.add_argument("--count", type=int, default=10, help="返回的最大实例数")
    parser.add_argument("--timeout", type=int, default=10, help="请求超时时间（秒）")
    parser.add_argument("--update-env", action="store_true", help="更新 .env 文件")
    parser.add_argument("--max-response-time", type=float, default=5.0, help="最大响应时间（秒）")
    parser.add_argument("--no-sources", action="store_true", help="不从第三方来源获取，只使用内置列表")

    args = parser.parse_args()

    # 创建发现器
    discovery = NitterInstanceDiscovery(timeout=args.timeout)

    # 发现可用实例
    print("\n" + "=" * 80)
    print("Nitter 实例健康检测")
    print("=" * 80 + "\n")

    available_urls = discovery.get_available_urls(
        max_count=args.count,
        max_response_time=args.max_response_time
    )

    if available_urls:
        print(f"✓ 发现 {len(available_urls)} 个可用实例:\n")
        for i, url in enumerate(available_urls, 1):
            print(f"  {i}. {url}")

        # 更新 .env 文件
        if args.update_env:
            print("\n正在更新 .env 文件...")
            update_env_file(available_urls)
            print("✓ .env 文件已更新")
        else:
            print("\n提示: 使用 --update-env 参数可以自动更新 .env 文件")

    else:
        print("✗ 未发现可用实例")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
