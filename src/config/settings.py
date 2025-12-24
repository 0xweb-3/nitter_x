"""
系统配置管理
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """系统配置类"""

    # PostgreSQL 配置
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5433"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "nitter_x")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "nitter_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Nitter 配置
    NITTER_INSTANCES: List[str] = [
        url.strip()
        for url in os.getenv("NITTER_INSTANCES", "https://xcancel.com").split(",")
        if url.strip()
    ]

    # LLM 配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

    # 应用配置
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TZ: str = os.getenv("TZ", "Asia/Shanghai")

    # 爬虫配置
    CRAWLER_TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
    CRAWLER_RETRY: int = int(os.getenv("CRAWLER_RETRY", "3"))
    CRAWLER_DELAY: float = float(os.getenv("CRAWLER_DELAY", "1.0"))

    # HTTP 请求配置
    HTTP_RETRY_COUNT: int = int(os.getenv("HTTP_RETRY_COUNT", "3"))  # HTTP 请求重试次数
    HTTP_RETRY_DELAY: float = float(
        os.getenv("HTTP_RETRY_DELAY", "2")
    )  # HTTP 请求重试间隔（秒）

    # 采集循环配置
    CRAWL_INTERVAL: int = int(os.getenv("CRAWL_INTERVAL", "60"))  # 采集循环间隔（秒）
    CRAWL_USER_INTERVAL: int = int(
        os.getenv("CRAWL_USER_INTERVAL", "180")
    )  # 用户采集间隔（秒）
    ESTIMATED_TIME_PER_USER: int = int(
        os.getenv("ESTIMATED_TIME_PER_USER", "5")
    )  # 单个用户采集预估时间（秒）

    # 推文处理配置
    ENABLE_24H_EXPIRATION: bool = os.getenv("ENABLE_24H_EXPIRATION", "true").lower() in ("true", "1", "yes")  # 启用推文过期判断（默认启用）
    TWEET_EXPIRATION_HOURS: int = int(os.getenv("TWEET_EXPIRATION_HOURS", "24"))  # 推文过期时间阈值（小时）

    # Bark 推送配置
    BARK_PUSH_ENABLED: bool = os.getenv("BARK_PUSH_ENABLED", "true").lower() in ("true", "1", "yes")
    BARK_PUSH_GRADES: str = os.getenv("BARK_PUSH_GRADES", "P0,P1,P2")
    BARK_PUSH_ICON: str = os.getenv(
        "BARK_PUSH_ICON",
        "https://em-content.zobj.net/source/apple/391/money-bag_1f4b0.png"  # 💰 钱袋
    )

    @classmethod
    def calculate_lock_timeout(cls, user_count: int) -> int:
        """
        计算采集任务锁超时时间（动态计算，基于用户数量）

        公式：user_count * ESTIMATED_TIME_PER_USER + CRAWL_INTERVAL

        Args:
            user_count: 需要采集的用户数量

        Returns:
            锁超时时间（秒）
        """
        # 基础超时 = 用户数 × 单用户预估时间 + 一个循环间隔作为缓冲
        timeout = user_count * cls.ESTIMATED_TIME_PER_USER + cls.CRAWL_INTERVAL
        # 设置最小超时时间为 2 倍 CRAWL_INTERVAL，避免过小的超时
        min_timeout = cls.CRAWL_INTERVAL * 2
        return max(timeout, min_timeout)

    # Redis 队列名称
    REDIS_QUEUE_CRAWL: str = "queue:crawl"
    REDIS_QUEUE_PROCESS: str = "queue:process"
    REDIS_SET_DEDUP: str = "set:dedup"

    @classmethod
    def get_postgres_url(cls) -> str:
        """获取 PostgreSQL 连接 URL"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"

    @classmethod
    def get_redis_url(cls) -> str:
        """获取 Redis 连接 URL"""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"


settings = Settings()
