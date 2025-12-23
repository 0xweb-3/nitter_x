"""
Redis Keys 管理
集中管理所有 Redis 键名
"""

# Nitter 实例相关
REDIS_KEY_AVAILABLE_INSTANCES = "nitter:instances:available"  # 可用实例列表（缓存）
REDIS_KEY_INSTANCE_PREFIX = "nitter:instance:"  # 单个实例信息前缀

# 队列相关（已有的队列）
REDIS_QUEUE_CRAWL = "queue:crawl"  # 采集队列
REDIS_QUEUE_PROCESS = "queue:process"  # 处理队列
REDIS_SET_DEDUP = "set:dedup"  # 去重集合

# 缓存过期时间（秒）
CACHE_EXPIRE_INSTANCES = 3 * 60 * 60  # 3小时（预留，未使用）
CACHE_EXPIRE_INSTANCE_DISCOVERY = 5 * 60  # 5分钟（实例发现缓存）
CACHE_EXPIRE_DEDUP = 24 * 60 * 60  # 24小时
