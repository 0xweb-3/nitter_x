"""
数据库查询辅助函数
提供 Streamlit 页面所需的数据查询接口
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import pandas as pd

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.storage.postgres_client import get_postgres_client
from src.storage.redis_client import get_redis_client
from src.config.settings import settings


class DatabaseHelper:
    """数据库查询辅助类"""

    def __init__(self):
        self.pg_client = get_postgres_client()
        self.redis_client = get_redis_client()

    # ==================== 用户管理相关 ====================

    def get_all_users(self) -> pd.DataFrame:
        """
        获取所有监听用户列表

        Returns:
            DataFrame: 用户列表数据
        """
        query = """
            SELECT
                username,
                display_name,
                priority,
                is_active,
                last_crawled_at,
                created_at,
                notes,
                (SELECT COUNT(*) FROM tweets WHERE author = username) as tweet_count
            FROM watched_users
            ORDER BY priority DESC, username
        """
        results = self.pg_client.execute_query(query)
        return pd.DataFrame(results)

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            用户信息字典，不存在返回 None
        """
        query = "SELECT * FROM watched_users WHERE username = %s"
        results = self.pg_client.execute_query(query, (username,))
        return results[0] if results else None

    def add_user(self, username: str, priority: int = 1, notes: str = "", display_name: str = "") -> bool:
        """
        添加监听用户

        Args:
            username: 用户名（必填）
            priority: 优先级 (1-10)
            notes: 备注（选填）
            display_name: 展示名称（选填）

        Returns:
            是否成功
        """
        query = """
            INSERT INTO watched_users (username, display_name, priority, notes, is_active, created_at)
            VALUES (%s, %s, %s, %s, TRUE, NOW())
            ON CONFLICT (username) DO NOTHING
        """
        return self.pg_client.execute_update(query, (username, display_name, priority, notes))

    def update_user(
        self, username: str, priority: int = None, notes: str = None, display_name: str = None, is_active: bool = None
    ) -> bool:
        """
        更新用户信息

        Args:
            username: 用户名
            priority: 优先级（可选）
            notes: 备注（可选）
            display_name: 展示名称（可选）
            is_active: 是否启用（可选）

        Returns:
            是否成功
        """
        return self.pg_client.update_watched_user(
            username=username,
            priority=priority,
            notes=notes,
            display_name=display_name,
            is_active=is_active,
        )

    def delete_user(self, username: str) -> bool:
        """
        删除监听用户

        Args:
            username: 用户名

        Returns:
            是否成功
        """
        return self.pg_client.delete_watched_user(username)

    # ==================== 推文查询相关 ====================

    def get_tweets(
        self,
        limit: int = 50,
        offset: int = 0,
        username: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        keyword: str = None,
    ) -> pd.DataFrame:
        """
        获取推文列表（支持筛选）

        Args:
            limit: 返回数量
            offset: 偏移量
            username: 按用户筛选（可选）
            start_date: 开始时间（可选）
            end_date: 结束时间（可选）
            keyword: 关键词搜索（可选）

        Returns:
            DataFrame: 推文列表
        """
        conditions = []
        params = []

        if username:
            conditions.append("t.author = %s")
            params.append(username)

        if start_date:
            conditions.append("t.published_at >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("t.published_at <= %s")
            params.append(end_date)

        if keyword:
            conditions.append("t.content ILIKE %s")
            params.append(f"%{keyword}%")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT
                t.tweet_id,
                t.author,
                COALESCE(u.display_name, '') as display_name,
                t.content,
                t.published_at,
                t.tweet_url,
                t.created_at,
                t.media_urls,
                t.has_media
            FROM tweets t
            LEFT JOIN watched_users u ON t.author = u.username
            WHERE {where_clause}
            ORDER BY t.published_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        results = self.pg_client.execute_query(query, tuple(params))
        return pd.DataFrame(results)

    def get_tweet_count(
        self,
        username: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        keyword: str = None,
    ) -> int:
        """
        获取推文总数（支持筛选）

        Args:
            username: 按用户筛选（可选）
            start_date: 开始时间（可选）
            end_date: 结束时间（可选）
            keyword: 关键词搜索（可选）

        Returns:
            推文总数
        """
        conditions = []
        params = []

        if username:
            conditions.append("author = %s")
            params.append(username)

        if start_date:
            conditions.append("published_at >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("published_at <= %s")
            params.append(end_date)

        if keyword:
            conditions.append("content ILIKE %s")
            params.append(f"%{keyword}%")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"SELECT COUNT(*) as count FROM tweets WHERE {where_clause}"
        result = self.pg_client.execute_query(query, tuple(params))
        return result[0]["count"] if result else 0

    # ==================== 统计数据相关 ====================

    def get_system_stats(self) -> Dict:
        """
        获取系统统计数据

        Returns:
            统计数据字典
        """
        # 监听用户总数
        user_count_query = "SELECT COUNT(*) as count FROM watched_users WHERE is_active = TRUE"
        user_count = self.pg_client.execute_query(user_count_query)[0]["count"]

        # 推文总数
        tweet_count_query = "SELECT COUNT(*) as count FROM tweets"
        tweet_count = self.pg_client.execute_query(tweet_count_query)[0]["count"]

        # 今日新增推文
        today_query = """
            SELECT COUNT(*) as count FROM tweets
            WHERE created_at >= CURRENT_DATE
        """
        today_count = self.pg_client.execute_query(today_query)[0]["count"]

        # 最近采集时间
        last_crawl_query = """
            SELECT MAX(last_crawled_at) as last_time
            FROM watched_users
            WHERE last_crawled_at IS NOT NULL
        """
        last_crawl = self.pg_client.execute_query(last_crawl_query)[0]["last_time"]

        # 待处理推文数量（processing_status = 'pending'）
        pending_query = """
            SELECT COUNT(*) as count FROM tweets
            WHERE processing_status = 'pending'
        """
        pending_count = self.pg_client.execute_query(pending_query)[0]["count"]

        return {
            "user_count": user_count,
            "tweet_count": tweet_count,
            "today_count": today_count,
            "last_crawl_time": last_crawl,
            "pending_count": pending_count,
        }

    def get_daily_tweet_stats(self, days: int = 7) -> pd.DataFrame:
        """
        获取每日推文统计（最近 N 天）

        Args:
            days: 天数

        Returns:
            DataFrame: 每日统计数据
        """
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM tweets
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
        results = self.pg_client.execute_query(query, (days,))
        return pd.DataFrame(results)

    def get_user_tweet_stats(self, limit: int = 10) -> pd.DataFrame:
        """
        获取用户推文统计（Top N 活跃用户）

        Args:
            limit: 返回数量

        Returns:
            DataFrame: 用户统计数据
        """
        query = """
            SELECT
                author,
                COUNT(*) as tweet_count,
                MAX(published_at) as last_tweet_time
            FROM tweets
            GROUP BY author
            ORDER BY tweet_count DESC
            LIMIT %s
        """
        results = self.pg_client.execute_query(query, (limit,))
        return pd.DataFrame(results)

    # ==================== Redis 相关 ====================

    def check_redis_connection(self) -> bool:
        """检查 Redis 连接状态"""
        try:
            self.redis_client.client.ping()
            return True
        except Exception:
            return False

    def get_nitter_instances(self) -> List[Dict]:
        """
        从 Redis 获取可用 Nitter 实例

        Returns:
            实例列表
        """
        try:
            import json
            from src.config.redis_keys import REDIS_KEY_NITTER_INSTANCES

            cache = self.redis_client.get_cache(REDIS_KEY_NITTER_INSTANCES)
            if cache:
                return json.loads(cache)
            return []
        except Exception:
            return []

    def close(self):
        """关闭数据库连接"""
        self.pg_client.close()
        self.redis_client.close()


# 单例模式
_db_helper_instance = None


def get_db_helper() -> DatabaseHelper:
    """获取 DatabaseHelper 单例"""
    global _db_helper_instance
    if _db_helper_instance is None:
        _db_helper_instance = DatabaseHelper()
    return _db_helper_instance
