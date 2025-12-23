# crawler 目录

## 目录作用

数据采集层，负责从 Nitter 实例获取推文数据。

## 文件说明

### nitter_crawler.py
Nitter 爬虫主类，功能：
- 从 Nitter 实例获取用户推文
- 解析 HTML 提取推文数据
- 支持增量采集
- 自动从 Redis 获取可用实例
- 加权随机选择实例（更快的实例优先）

### constants.py
常量定义，包括：
- `KNOWN_INSTANCES`: 内置的 40+ 个已验证 Nitter 实例列表
- 其他爬虫相关常量

### instance_sources.py
Nitter 实例来源管理，支持：
- `InstanceSource`: 实例来源基类
- `StatusPageSource`: 从 status.d420.de 获取实例
- `BuiltinSource`: 使用内置实例列表
- `InstanceSourceManager`: 多来源管理器

### instance_discovery.py
Nitter 实例健康检测工具：
- `NitterInstanceChecker`: 实例健康检测器
- `NitterInstanceDiscovery`: 整合来源获取和健康检测
- 并发检测所有实例的可用性和响应时间
- 将结果缓存到 Redis（3 小时 TTL）

### README_SOURCES.md
实例来源扩展文档，说明如何添加自定义实例来源。

## 工作流程

1. **实例发现**：从多个来源获取实例列表
2. **健康检测**：并发检测所有实例的可用性和响应时间
3. **Redis 缓存**：将可用实例列表缓存到 Redis（3 小时）
4. **爬虫使用**：从 Redis 读取实例，按响应时间加权随机选择
5. **自动刷新**：缓存过期后自动重新检测

## 使用示例

```python
from src.crawler.nitter_crawler import NitterCrawler

# 初始化爬虫（默认从 Redis 获取实例）
crawler = NitterCrawler(use_redis_instances=True)

# 获取推文
tweets = crawler.fetch_user_timeline("elonmusk", max_tweets=20)
```

## 设计原则

- 永不直连 x.com
- Redis 缓存优先，减少实例检测频率
- 支持多实例负载均衡
- 容错机制：实例失败自动切换
