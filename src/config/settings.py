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
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

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
    CRAWL_LOCK_TIMEOUT_MULTIPLIER: int = int(
        os.getenv("CRAWL_LOCK_TIMEOUT_MULTIPLIER", "3")
    )  # 锁超时倍数

    @classmethod
    def get_crawl_lock_timeout(cls) -> int:
        """获取采集任务锁超时时间（CRAWL_INTERVAL * CRAWL_LOCK_TIMEOUT_MULTIPLIER）"""
        return cls.CRAWL_INTERVAL * cls.CRAWL_LOCK_TIMEOUT_MULTIPLIER

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
