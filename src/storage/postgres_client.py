"""
PostgreSQL 数据库客户端
"""

import logging
from typing import List, Dict, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from src.config.settings import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """PostgreSQL 客户端类"""

    def __init__(self):
        self.pool = None
        self._init_pool()

    def _init_pool(self):
        """初始化连接池"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                options="-c timezone=UTC",  # 设置连接时区为UTC
            )
            logger.info("PostgreSQL 连接池初始化成功 (timezone=UTC)")
        except Exception as e:
            logger.error(f"PostgreSQL 连接池初始化失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询并返回结果

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        执行更新操作

        Args:
            query: SQL 更新语句
            params: 更新参数

        Returns:
            影响的行数
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount

    def insert_tweet(self, tweet_data: Dict) -> Optional[int]:
        """
        插入推文数据

        Args:
            tweet_data: 推文数据字典，支持字段：
                - tweet_id: 推文ID（必填）
                - author: 作者用户名（必填）
                - author_id: 作者ID（可选）
                - content: 推文内容（必填）
                - published_at: 发布时间（必填）
                - tweet_url: 推文URL（可选）
                - media_urls: 媒体URL列表（可选）
                - has_media: 是否包含媒体（可选，自动根据media_urls计算）

        Returns:
            插入的记录 ID，如果失败返回 None
        """
        # 自动设置 has_media 标志
        if "media_urls" in tweet_data and tweet_data["media_urls"]:
            tweet_data["has_media"] = True
        else:
            tweet_data.setdefault("has_media", False)

        # 确保 media_urls 是 JSON 格式
        if "media_urls" in tweet_data:
            import json
            if isinstance(tweet_data["media_urls"], list):
                tweet_data["media_urls"] = json.dumps(tweet_data["media_urls"])

        query = """
        INSERT INTO tweets (
            tweet_id, author, author_id, content, published_at,
            tweet_url, media_urls, has_media
        )
        VALUES (
            %(tweet_id)s, %(author)s, %(author_id)s, %(content)s, %(published_at)s,
            %(tweet_url)s, %(media_urls)s::jsonb, %(has_media)s
        )
        ON CONFLICT (tweet_id) DO NOTHING
        RETURNING id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, tweet_data)
                    result = cur.fetchone()
                    if result:
                        media_info = f"（含 {len(tweet_data.get('media_urls', '[]'))} 个媒体）" if tweet_data.get('has_media') else ""
                        logger.info(f"成功插入推文: {tweet_data['tweet_id']} {media_info}")
                        return result[0]
                    else:
                        logger.debug(f"推文已存在: {tweet_data['tweet_id']}")
                        return None
        except Exception as e:
            logger.error(f"插入推文失败: {e}")
            return None

    def get_latest_tweet_id(self, author: str) -> Optional[str]:
        """
        获取指定作者的最新推文 ID

        Args:
            author: 作者用户名

        Returns:
            最新推文 ID，如果没有返回 None
        """
        query = """
        SELECT tweet_id FROM tweets
        WHERE author = %s
        ORDER BY published_at DESC
        LIMIT 1
        """
        try:
            result = self.execute_query(query, (author,))
            if result:
                return result[0]["tweet_id"]
            return None
        except Exception as e:
            logger.error(f"获取最新推文 ID 失败: {e}")
            return None

    def get_watched_users(
        self, active_only: bool = True, min_interval_seconds: int = None
    ) -> List[Dict]:
        """
        获取关注用户列表

        Args:
            active_only: 是否只获取活跃用户
            min_interval_seconds: 最小采集间隔（秒），只返回距上次采集超过此时间的用户

        Returns:
            用户列表
        """
        query = "SELECT * FROM watched_users"
        conditions = []

        if active_only:
            conditions.append("is_active = TRUE")

        if min_interval_seconds is not None:
            # 只获取从未采集过的用户，或距上次采集超过指定时间的用户
            conditions.append(
                f"(last_crawled_at IS NULL OR EXTRACT(EPOCH FROM (NOW() - last_crawled_at)) > {min_interval_seconds})"
            )

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY priority DESC, username"

        return self.execute_query(query)

    def add_watched_user(self, username: str, display_name: str = "", priority: int = 0) -> bool:
        """
        添加关注用户

        Args:
            username: 用户名
            display_name: 显示名称
            priority: 优先级

        Returns:
            是否添加成功
        """
        query = """
        INSERT INTO watched_users (username, display_name, priority)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        """
        try:
            rows = self.execute_update(query, (username, display_name, priority))
            if rows > 0:
                logger.info(f"成功添加关注用户: {username}")
                return True
            else:
                logger.debug(f"用户已存在: {username}")
                return False
        except Exception as e:
            logger.error(f"添加关注用户失败: {e}")
            return False

    def update_watched_user(
        self,
        username: str,
        display_name: str = None,
        priority: int = None,
        is_active: bool = None,
        notes: str = None,
    ) -> bool:
        """
        更新关注用户信息

        Args:
            username: 用户名
            display_name: 显示名称（可选）
            priority: 优先级（可选）
            is_active: 是否启用（可选）
            notes: 备注（可选）

        Returns:
            是否更新成功
        """
        # 构建动态 UPDATE 语句
        updates = []
        params = []

        if display_name is not None:
            updates.append("display_name = %s")
            params.append(display_name)

        if priority is not None:
            updates.append("priority = %s")
            params.append(priority)

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)

        if not updates:
            logger.warning(f"更新用户 {username} 时没有提供任何更新字段")
            return False

        # 添加 username 作为 WHERE 条件参数
        params.append(username)

        query = f"""
        UPDATE watched_users
        SET {', '.join(updates)}
        WHERE username = %s
        """

        try:
            rows = self.execute_update(query, tuple(params))
            if rows > 0:
                logger.info(f"成功更新关注用户: {username}")
                return True
            else:
                logger.debug(f"用户不存在或未更新: {username}")
                return False
        except Exception as e:
            logger.error(f"更新关注用户失败: {e}")
            return False

    def delete_watched_user(self, username: str) -> bool:
        """
        删除关注用户

        Args:
            username: 用户名

        Returns:
            是否删除成功
        """
        query = "DELETE FROM watched_users WHERE username = %s"

        try:
            rows = self.execute_update(query, (username,))
            if rows > 0:
                logger.info(f"成功删除关注用户: {username}")
                return True
            else:
                logger.debug(f"用户不存在: {username}")
                return False
        except Exception as e:
            logger.error(f"删除关注用户失败: {e}")
            return False

    def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL 连接池已关闭")


# 全局单例
_pg_client = None


def get_postgres_client() -> PostgresClient:
    """获取 PostgreSQL 客户端单例"""
    global _pg_client
    if _pg_client is None:
        _pg_client = PostgresClient()
    return _pg_client
