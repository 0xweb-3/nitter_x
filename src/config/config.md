# config 目录

## 目录作用

系统配置管理模块。

## 文件说明

### settings.py
系统配置管理类，负责：
- 从 `.env` 文件读取环境变量
- 提供统一的配置访问接口
- 管理数据库连接参数
- 管理爬虫配置参数
- 管理日志配置参数

## 配置项

### 数据库配置
- `POSTGRES_HOST`: PostgreSQL 主机地址
- `POSTGRES_PORT`: PostgreSQL 端口
- `POSTGRES_DB`: 数据库名称
- `POSTGRES_USER`: 数据库用户
- `POSTGRES_PASSWORD`: 数据库密码

### Redis 配置
- `REDIS_HOST`: Redis 主机地址
- `REDIS_PORT`: Redis 端口
- `REDIS_PASSWORD`: Redis 密码

### 采集配置
- `CRAWL_INTERVAL`: 采集循环间隔（秒）
- `CRAWL_USER_INTERVAL`: 用户采集间隔（秒）
- `ESTIMATED_TIME_PER_USER`: 单个用户预估采集时间（秒），用于动态计算锁超时时间
- `CRAWLER_TIMEOUT`: 请求超时（秒）
- `CRAWLER_DELAY`: 每个用户采集间隔（秒）

**锁超时机制**：
- 采集任务使用分布式锁防止并发冲突
- 锁超时时间动态计算：`user_count × ESTIMATED_TIME_PER_USER + CRAWL_INTERVAL`
- 最小超时时间为 `2 × CRAWL_INTERVAL`
- 根据待采集用户数自动调整，避免超时过长或过短

### LLM 配置
- `LLM_API_KEY`: LLM API 密钥（必需，用于调用 LLM 服务）
- `LLM_API_URL`: LLM API 端点 URL（默认：https://api.openai.com/v1）
- `LLM_MODEL`: LLM 模型名称（默认：gpt-3.5-turbo）

**说明**：
- 支持兼容 OpenAI API 格式的第三方服务（如 yibuapi.com）
- 基于 LangChain 框架，统一调用接口
- 用于推文内容分析、标签生成等功能

### 推文处理配置
- `ENABLE_24H_EXPIRATION`: 启用推文过期判断（默认：true）
  - 设置为 `true`/`1`/`yes` 启用
  - 设置为 `false`/`0`/`no` 禁用
  - 启用后，超过指定时间阈值的推文将自动标记为 P6（已过期），无需调用 LLM
- `TWEET_EXPIRATION_HOURS`: 推文过期时间阈值（默认：24 小时）
  - 单位：小时
  - 示例：设置为 1 表示 1 小时后过期，设置为 48 表示 48 小时后过期
  - 用于判断推文是否过期，过期推文直接标记为 P6，节省 LLM API 调用成本

**推文过期判断说明**：
- 过期判断基于推文的发布时间（`published_at`）与当前时间（UTC）的时间差
- 过期推文会被自动标记为 P6（可舍弃），跳过 LLM 处理，直接保存到 `processed_tweets` 表
- 适用于加密货币新闻等时效性强的内容，避免对旧内容浪费 API 调用
- 可根据实际需求调整过期时间：
  - 1-6 小时：适合超短期交易信号
  - 24 小时：适合一般新闻资讯（默认）
  - 48-72 小时：适合中长期分析内容
  - 设置为 `false` 禁用：所有推文都进行完整 LLM 处理

### 日志配置
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `LOG_FILE`: 日志文件路径

### 时区配置
- `TZ`: 系统时区（默认 Asia/Shanghai，但所有时间存储使用 UTC）

## 使用方式

```python
from src.config.settings import settings

# 访问配置
db_host = settings.POSTGRES_HOST
redis_host = settings.REDIS_HOST
```

## 注意事项

- 不要将 `.env` 文件提交到版本控制
- 使用 `.env.example` 作为模板
- 生产环境必须修改默认密码
