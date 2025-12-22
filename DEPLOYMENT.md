# 部署指南

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+

## 快速启动

### 1. 配置环境变量

复制环境变量示例文件并修改配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改以下配置项:
- `POSTGRES_PASSWORD`: 设置 PostgreSQL 数据库密码
- `REDIS_PASSWORD`: 设置 Redis 密码

### 2. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 验证服务

#### 验证 PostgreSQL

```bash
# 连接到 PostgreSQL
docker-compose exec postgres psql -U nitter_user -d nitter_x

# 查看表结构
\dt

# 查看表数据
SELECT * FROM watched_users;
SELECT * FROM tag_definitions;

# 退出
\q
```

#### 验证 Redis

```bash
# 连接到 Redis
docker-compose exec redis redis-cli -a your_redis_password_here

# 测试连接
ping

# 退出
exit
```

### 4. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止服务并删除数据卷（谨慎使用）
docker-compose down -v
```

## 服务端口

- PostgreSQL: `5432`
- Redis: `6379`

## 数据持久化

数据卷存储位置:
- PostgreSQL 数据: `postgres_data`
- Redis 数据: `redis_data`

## 数据库结构

### 主要表说明

1. **tweets**: 推文主表
   - 存储原始推文内容
   - 存储清洗后的内容
   - 存储标签、权重、等级等处理结果

2. **watched_users**: 关注用户列表
   - 管理需要采集的用户列表
   - 支持优先级设置

3. **tag_definitions**: 标签定义表
   - 定义可用的标签类别和名称
   - 设置标签权重

4. **processing_logs**: 处理日志表
   - 记录推文处理过程
   - 用于调试和监控

### 视图

- **processed_tweets**: 已处理完成的推文视图

## 连接信息

### Python 连接示例

```python
import psycopg2
import redis
from dotenv import load_dotenv
import os

load_dotenv()

# PostgreSQL 连接
pg_conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

# Redis 连接
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)
```

## 故障排除

### PostgreSQL 无法启动

1. 检查端口是否被占用: `lsof -i :5432`
2. 检查数据卷权限
3. 查看日志: `docker-compose logs postgres`

### Redis 无法连接

1. 检查端口是否被占用: `lsof -i :6379`
2. 验证密码配置
3. 查看日志: `docker-compose logs redis`

### 数据初始化失败

1. 删除数据卷重新初始化:
```bash
docker-compose down -v
docker-compose up -d
```

2. 检查初始化脚本: `docker/postgres/init/01-init.sql`

## 备份与恢复

### PostgreSQL 备份

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U nitter_user nitter_x > backup.sql

# 恢复数据库
cat backup.sql | docker-compose exec -T postgres psql -U nitter_user nitter_x
```

### Redis 备份

```bash
# Redis 使用 AOF 持久化，数据自动保存在 redis_data 卷中
# 手动触发保存
docker-compose exec redis redis-cli -a your_redis_password_here SAVE
```

## 安全建议

1. 修改默认密码，使用强密码
2. 不要将 `.env` 文件提交到版本控制
3. 定期备份数据
4. 生产环境建议使用外部数据库服务

## 下一步

v1.0.0 基础环境已构建完成。后续版本开发:
- v2.0.0: 实现推文获取功能
- v3.0.0: 实现内容管理功能
- v4.0.0: 实现内容展示功能
