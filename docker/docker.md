# docker 目录

## 目录作用

存放 Docker 相关配置文件和数据库初始化脚本。

## 目录结构

```
docker/
└── postgres/
    └── init/
        └── 01-init.sql    # PostgreSQL 初始化脚本
```

## 子目录说明

### postgres/
PostgreSQL 数据库相关配置：
- `init/`: 数据库初始化脚本目录
- 该目录下的 `.sql` 文件会在容器首次启动时自动执行
- 文件按字母顺序执行

### postgres/init/
数据库初始化脚本，包含：
- `01-init.sql`: 主初始化脚本

## init/01-init.sql 内容

### 1. 表结构创建
- `tweets`: 推文主表
- `watched_users`: 关注用户列表
- `tag_definitions`: 标签定义表
- `processing_logs`: 处理日志表

### 2. 索引创建
- 推文 ID 索引
- 作者索引
- 发布时间索引（降序）
- 用户名索引
- 优先级索引

### 3. 触发器函数
- `update_updated_at_column()`: 自动更新 `updated_at` 字段

### 4. 视图创建
- `processed_tweets`: 已处理完成的推文视图

### 5. 默认数据插入
- 标签定义默认数据（主题、情绪、类型）

## 使用说明

### 首次启动
```bash
# 启动 Docker Compose
docker-compose up -d

# 数据库会自动执行 init/ 目录下的 SQL 脚本
# 查看日志确认初始化完成
docker-compose logs postgres
```

### 修改初始化脚本
如果需要修改数据库结构：
1. 修改 `01-init.sql` 文件
2. 删除现有数据库卷：`docker-compose down -v`
3. 重新启动：`docker-compose up -d`

### 添加新的初始化脚本
- 创建新的 `.sql` 文件，命名如 `02-add-feature.sql`
- 文件会按字母顺序执行
- 确保幂等性（可重复执行）

## 注意事项

- ⚠️ **初始化脚本只在首次创建数据库时执行**
- ⚠️ **修改脚本后需要删除数据卷才能重新执行**
- ⚠️ **删除数据卷会丢失所有数据，请先备份**
- ✅ 所有时间字段使用 `TIMESTAMP WITH TIME ZONE`
- ✅ 默认时区设置为 UTC

## 数据持久化

数据库数据存储在 Docker 卷中：
- 卷名：`postgres_data`
- 挂载路径：`/var/lib/postgresql/data`

## 扩展建议

可以添加其他服务的 Docker 配置：
```
docker/
├── postgres/       # PostgreSQL 配置
├── redis/          # Redis 配置（可选）
└── nginx/          # Nginx 配置（可选）
```
