"""
Redis 客户端
用于队列管理和去重缓存
"""

import json
import logging
import uuid
from typing import List, Optional, Any

import redis

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 客户端类"""

    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """连接到 Redis"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
            # 测试连接
            self.client.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            raise

    def push_to_queue(self, queue_name: str, data: Any) -> bool:
        """
        推送数据到队列

        Args:
            queue_name: 队列名称
            data: 数据（字典会自动转为 JSON）

        Returns:
            是否成功
        """
        try:
            if isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False)

            self.client.rpush(queue_name, data)
            logger.debug(f"推送到队列 {queue_name}: {data}")
            return True
        except Exception as e:
            logger.error(f"推送到队列失败: {e}")
            return False

    def pop_from_queue(self, queue_name: str, timeout: int = 0) -> Optional[str]:
        """
        从队列弹出数据

        Args:
            queue_name: 队列名称
            timeout: 超时时间（秒），0 表示阻塞

        Returns:
            数据字符串，如果队列为空返回 None
        """
        try:
            result = self.client.blpop(queue_name, timeout=timeout)
            if result:
                _, data = result
                logger.debug(f"从队列 {queue_name} 弹出: {data}")
                return data
            return None
        except Exception as e:
            logger.error(f"从队列弹出失败: {e}")
            return None

    def get_queue_length(self, queue_name: str) -> int:
        """获取队列长度"""
        try:
            return self.client.llen(queue_name)
        except Exception as e:
            logger.error(f"获取队列长度失败: {e}")
            return 0

    def is_duplicate(self, tweet_id: str, expire: int = 86400) -> bool:
        """
        检查推文 ID 是否重复

        Args:
            tweet_id: 推文 ID
            expire: 过期时间（秒），默认 24 小时

        Returns:
            是否重复
        """
        try:
            key = f"{settings.REDIS_SET_DEDUP}:{tweet_id}"
            exists = self.client.exists(key)

            if not exists:
                # 不存在，设置并标记为不重复
                self.client.setex(key, expire, "1")
                return False

            return True
        except Exception as e:
            logger.error(f"检查重复失败: {e}")
            return False

    def set_cache(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        设置缓存

        Args:
            key: 键
            value: 值
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            self.client.setex(key, expire, value)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False

    def get_cache(self, key: str) -> Optional[str]:
        """获取缓存"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None

    def delete(self, key: str) -> bool:
        """删除键"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除键失败: {e}")
            return False

    def clear_queue(self, queue_name: str) -> bool:
        """清空队列"""
        try:
            self.client.delete(queue_name)
            logger.info(f"队列 {queue_name} 已清空")
            return True
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return False

    def acquire_lock(
        self, lock_name: str, expire: int = 300, timeout: int = 0
    ) -> Optional[str]:
        """
        尝试获取分布式锁

        Args:
            lock_name: 锁名称
            expire: 锁的过期时间（秒），防止死锁，默认 5 分钟
            timeout: 等待获取锁的超时时间（秒），0 表示不等待直接返回

        Returns:
            锁的唯一标识（用于释放锁），如果获取失败返回 None
        """
        try:
            lock_key = f"lock:{lock_name}"
            lock_value = str(uuid.uuid4())  # 生成唯一标识

            # 尝试获取锁（NX: 仅在键不存在时设置，EX: 设置过期时间）
            acquired = self.client.set(lock_key, lock_value, nx=True, ex=expire)

            if acquired:
                logger.debug(f"成功获取锁: {lock_name}")
                return lock_value
            else:
                logger.debug(f"锁已被占用: {lock_name}")
                return None

        except Exception as e:
            logger.error(f"获取锁失败: {e}")
            return None

    def release_lock(self, lock_name: str, lock_value: str) -> bool:
        """
        释放分布式锁

        Args:
            lock_name: 锁名称
            lock_value: 获取锁时返回的唯一标识

        Returns:
            是否成功释放
        """
        try:
            lock_key = f"lock:{lock_name}"

            # 使用 Lua 脚本原子性地检查并删除锁
            # 只有当锁的值匹配时才删除，防止释放别人的锁
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = self.client.eval(lua_script, 1, lock_key, lock_value)

            if result:
                logger.debug(f"成功释放锁: {lock_name}")
                return True
            else:
                logger.warning(f"释放锁失败，锁可能已过期或被其他进程持有: {lock_name}")
                return False

        except Exception as e:
            logger.error(f"释放锁异常: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            logger.info("Redis 连接已关闭")


# 全局单例
_redis_client = None


def get_redis_client() -> RedisClient:
    """获取 Redis 客户端单例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
