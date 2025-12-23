# postgres 目录

## 目录作用

PostgreSQL 数据库相关配置和初始化脚本。

## 目录结构

```
postgres/
└── init/
    └── 01-init.sql    # 数据库初始化脚本
```

## init 子目录

### 作用
存放数据库初始化 SQL 脚本，在 PostgreSQL 容器首次启动时自动执行。

### 执行规则
- Docker Compose 将 `init/` 目录挂载到容器的 `/docker-entrypoint-initdb.d/`
- 容器首次创建时，会按字母顺序执行该目录下的所有 `.sql` 和 `.sh` 文件
- **只在首次创建数据库时执行一次**

### 文件说明

#### 01-init.sql
主初始化脚本，创建：

1. **表结构**
   - `tweets`: 推文主表
   - `watched_users`: 关注用户列表
   - `tag_definitions`: 标签定义表
   - `processing_logs`: 处理日志表

2. **索引**
   - 优化查询性能
   - 支持按时间、作者、状态等字段快速检索

3. **触发器**
   - 自动更新 `updated_at` 字段

4. **视图**
   - `processed_tweets`: 已处理完成的推文视图

5. **默认数据**
   - 标签定义（主题、情绪、类型）

## 数据库设计要点

### 时间字段
所有时间字段使用 `TIMESTAMP WITH TIME ZONE`，确保：
- 跨时区数据一致性
- 自动存储时区信息
- 应用层传入带时区的 datetime 对象

### 索引策略
- 频繁查询的字段创建索引
- 时间字段使用降序索引（`DESC`）
- 避免过多索引影响写入性能

### 触发器
- `update_updated_at_column()`: 在 UPDATE 操作前自动设置 `updated_at = CURRENT_TIMESTAMP`
- 应用于 `tweets` 和 `watched_users` 表

## 使用示例

### 查看表结构
```bash
docker-compose exec postgres psql -U nitter_user -d nitter_x

\dt                        # 列出所有表
\d tweets                  # 查看 tweets 表结构
\di                        # 列出所有索引
```

### 手动执行 SQL
```bash
# 执行自定义 SQL
docker-compose exec postgres psql -U nitter_user -d nitter_x -c "SELECT COUNT(*) FROM tweets;"

# 执行 SQL 文件
cat custom.sql | docker-compose exec -T postgres psql -U nitter_user -d nitter_x
```

## 注意事项

- 修改初始化脚本后，需要删除数据卷才能重新执行
- 删除数据卷会丢失所有数据，务必先备份
- 生产环境建议使用数据库迁移工具（如 Alembic）
- 保持 SQL 脚本幂等性（使用 `IF NOT EXISTS`、`ON CONFLICT` 等）
