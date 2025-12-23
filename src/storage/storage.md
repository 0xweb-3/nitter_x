# storage 目录

## 目录作用

数据存储层，提供 PostgreSQL 和 Redis 的客户端封装。

## 文件说明

### postgres_client.py
PostgreSQL 数据库客户端，提供：
- 连接池管理（SimpleConnectionPool，1-10 连接）
- 推文数据操作（插入、查询、更新）
- 用户数据操作（获取、添加、修改、删除监听用户）
- 统计查询（推文数量、用户推文数等）
- 时区配置：所有连接默认使用 UTC 时区

**主要方法**：
- `insert_tweet()`: 插入推文数据
- `get_latest_tweet_id()`: 获取用户最新推文 ID
- `get_watched_users()`: 获取监听用户列表
- `add_watched_user()`: 添加监听用户
- `update_watched_user()`: 更新用户信息（优先级、状态、备注等）
- `delete_watched_user()`: 删除监听用户
- `execute_query()`: 执行通用 SQL 查询
- `execute_update()`: 执行更新操作

### redis_client.py
Redis 客户端，提供：
- 连接管理（单例模式）
- 队列操作（推送、消费）
- 缓存操作（设置、获取、删除）
- 去重检查（推文 ID 去重）
- 分布式锁（防止并发冲突）

**主要方法**：
- `push_to_queue()`: 推送数据到队列
- `pop_from_queue()`: 从队列消费数据
- `is_duplicate()`: 检查推文是否重复
- `get_available_instances()`: 获取可用 Nitter 实例列表
- `cache_instances()`: 缓存 Nitter 实例列表
- `acquire_lock()`: 获取分布式锁
- `release_lock()`: 释放分布式锁

## 使用示例

### PostgreSQL

```python
from src.storage.postgres_client import get_postgres_client

# 获取客户端实例
pg = get_postgres_client()

# 插入推文
tweet_data = {
    "tweet_id": "123456",
    "author": "elonmusk",
    "content": "Tweet content",
    "published_at": datetime.now(timezone.utc),
    "tweet_url": "https://x.com/elonmusk/status/123456",
    "media_urls": [
        "https://pbs.twimg.com/media/image1.jpg",
        "https://pbs.twimg.com/media/image2.jpg"
    ]
}
pg.insert_tweet(tweet_data)  # 自动设置 has_media=True

# 查询用户
users = pg.get_watched_users()

# 添加监听用户
pg.add_watched_user(
    username="elonmusk",
    display_name="Elon Musk",
    priority=8
)

# 更新用户信息
pg.update_watched_user(
    username="elonmusk",
    priority=10,
    notes="重点关注",
    is_active=True
)

# 删除用户
pg.delete_watched_user("test_user")
```

### Redis

```python
from src.storage.redis_client import get_redis_client

# 获取客户端实例
redis = get_redis_client()

# 检查去重
if not redis.is_duplicate("tweet_123"):
    # 处理新推文
    pass

# 获取可用实例
instances = redis.get_available_instances()
```

## 数据库表结构

### tweets 表
推文主表，字段包括：
- `id`: 主键
- `tweet_id`: 推文 ID（唯一）
- `author`: 作者用户名
- `content`: 推文内容
- `published_at`: 发布时间（UTC）
- `tweet_url`: 推文原始链接（x.com）
- `media_urls`: 媒体URL列表（JSONB，存储图片/视频/GIF链接）
- `has_media`: 是否包含媒体（BOOLEAN，便于筛选）
- `created_at`: 创建时间（UTC）
- `updated_at`: 更新时间（UTC）

### watched_users 表
监听用户表，字段包括：
- `id`: 主键
- `username`: 用户名（唯一）
- `display_name`: 展示名称
- `priority`: 优先级（1-10）
- `is_active`: 是否激活
- `last_crawled_at`: 最后采集时间（UTC）
- `notes`: 备注
- `created_at`: 创建时间（UTC）
- `updated_at`: 更新时间（UTC）

## 注意事项

- 所有时间字段使用 `TIMESTAMP WITH TIME ZONE`（UTC）
- 数据库连接使用连接池，避免频繁创建连接
- Redis 客户端使用单例模式
- 所有操作都有错误处理和日志记录
