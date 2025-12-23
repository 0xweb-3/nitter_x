# Nitter X - 推文信息收集系统

## 项目说明

构建一个**稳定、可扩展、低封禁风险**的 X（Twitter）推文信息收集与处理系统，实现：

- 面向**指定用户列表**的持续推文采集
- 推文内容的**清洗、结构化、标签化、权重评分**（开发中）
- 基于 **Streamlit** 的可视化管理界面
- 面向第三方用户的**筛选展示与推送能力**（计划中）

系统遵循 **"采集 → 解耦 → 处理 → 排序 → 展示"** 的流水线架构，最大化降低各模块耦合度。

## 技术栈

- **后端**: Python 3.10+
- **数据库**: PostgreSQL (主存储) + Redis (缓存/队列)
- **容器化**: Docker + Docker Compose
- **前端**: Streamlit (Web UI)
- **数据采集**: Nitter (Twitter 代理)

---

## 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，修改密码等配置
nano .env
```

### 3. 启动服务

```bash
# 启动 PostgreSQL 和 Redis
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 安装 Python 依赖

```bash
# 创建虚拟环境（可选）
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Streamlit 依赖
pip install -r requirements-streamlit.txt
```

### 5. 添加监听用户

```bash
# 添加用户到监听列表
python manage_users.py add elonmusk --name "Elon Musk" --priority 10
python manage_users.py add VitalikButerin --name "Vitalik Buterin" --priority 9

# 查看用户列表
python manage_users.py list
```

### 6. 启动应用

```bash
# 启动 Streamlit Web UI
./start_streamlit.sh
# 或手动启动
streamlit run streamlit_app/app.py

# 在另一个终端启动推文采集
python main.py
```

访问 **http://localhost:8501** 查看 Web 界面。

---

## 项目结构

```
nitter_x/
├── docker/                      # Docker 相关配置
│   └── postgres/
│       └── init/
│           └── 01-init.sql     # 数据库初始化脚本
│
├── src/                         # 源代码目录
│   ├── config/                  # 配置模块
│   │   └── settings.py         # 系统配置
│   ├── crawler/                 # 数据采集层
│   │   ├── nitter_crawler.py   # Nitter 爬虫
│   │   ├── constants.py        # 内置实例列表
│   │   ├── instance_sources.py # 实例来源管理
│   │   └── instance_discovery.py # 实例健康检测
│   ├── storage/                 # 数据存储层
│   │   ├── postgres_client.py  # PostgreSQL 客户端
│   │   └── redis_client.py     # Redis 客户端
│   ├── processor/               # 处理与分析层（预留）
│   ├── web/                     # 展示层（预留）
│   └── utils/                   # 工具函数
│       └── logger.py           # 日志配置
│
├── streamlit_app/               # Streamlit Web UI
│   ├── app.py                   # 主入口（首页）
│   ├── pages/                   # 多页面目录
│   │   ├── 1_用户管理.py
│   │   ├── 2_推文展示.py
│   │   └── 3_系统监控.py
│   ├── components/              # 可复用组件
│   └── utils/                   # 工具函数
│       ├── db_helper.py        # 数据库查询辅助
│       └── format_helper.py    # 格式化辅助
│
├── migrations/                  # 数据库迁移脚本
├── tests/                       # 测试目录
├── logs/                        # 日志目录
├── data/                        # 数据目录
│
├── main.py                      # 推文采集主程序
├── manage_users.py              # 用户管理工具
├── discover_instances.py        # Nitter 实例发现工具
├── test_system.py               # 系统测试脚本
├── start_streamlit.sh           # Streamlit 启动脚本
│
├── .env                         # 环境变量配置（不提交）
├── .env.example                 # 环境变量示例
├── docker-compose.yml           # Docker Compose 配置
├── requirements.txt             # Python 依赖
├── requirements-streamlit.txt   # Streamlit 依赖
│
└── README.md                    # 项目说明（本文件）
```

---

## 功能特性

### 📊 Streamlit Web UI

#### 1. 首页
- 系统概览：监听用户数、推文总数、今日新增
- 数据可视化：每日推文趋势图、Top 10 活跃用户
- 快速操作：一键跳转到各功能页面

#### 2. 用户管理
- 用户列表：表格展示所有监听用户
- 添加用户：输入用户名、设置优先级、添加备注
- 编辑用户：修改优先级和备注
- 启用/禁用：控制是否采集该用户
- 删除用户：删除监听用户（推文数据保留）

#### 3. 推文展示
- 推文列表：卡片式展示推文内容
- 筛选功能：按用户、时间范围、关键词筛选
- 分页浏览：自定义每页显示数量
- 数据导出：导出为 CSV 格式

#### 4. 系统监控
- 服务状态：PostgreSQL、Redis、爬虫运行状态
- 系统指标：监听用户数、推文总数、今日新增
- 采集趋势：最近 30 天推文采集趋势图
- Nitter 实例：显示可用实例列表和响应时间
- 自动刷新：每 10 秒自动刷新数据

---

## 使用指南

### Nitter 实例管理

系统使用 **Redis 缓存优先** 策略管理 Nitter 实例：

```bash
# 查看可用实例（从 Redis 缓存读取）
python discover_instances.py

# 强制刷新实例列表（重新检测并更新缓存）
python discover_instances.py --force-refresh

# 查找前 8 个最快的实例
python discover_instances.py --count 8

# 只显示响应时间小于 3 秒的实例
python discover_instances.py --max-response-time 3.0
```

**特性**：
- ✅ Redis 缓存（3 小时有效期）
- ✅ 自动健康检测
- ✅ 按响应时间排序
- ✅ 支持多种实例来源（内置、状态页面）
- ✅ 爬虫自动从缓存读取实例

### 用户管理

```bash
# 添加用户
python manage_users.py add <username> --name "显示名称" --priority <1-10>

# 示例
python manage_users.py add elonmusk --name "Elon Musk" --priority 10
python manage_users.py add VitalikButerin --name "Vitalik Buterin" --priority 9

# 查看用户列表
python manage_users.py list

# 启用/禁用用户
python manage_users.py disable elonmusk
python manage_users.py enable elonmusk

# 删除用户
python manage_users.py remove elonmusk
```

### 推文采集

```bash
# 执行一次采集
python main.py

# 查看采集日志
tail -f logs/crawler.log
```

**工作流程**：
1. 从数据库读取所有活跃的关注用户
2. 按优先级顺序遍历每个用户
3. 从 Nitter 实例获取用户最新推文
4. 与数据库中最新推文 ID 对比，只采集新推文
5. 去重后存入 PostgreSQL
6. 更新用户的最后采集时间

### 数据查询

```bash
# 连接数据库
docker-compose exec postgres psql -U nitter_user -d nitter_x
```

**常用 SQL 查询**：

```sql
-- 查看采集统计
SELECT
    author,
    COUNT(*) as tweet_count,
    MAX(published_at) as latest_tweet
FROM tweets
GROUP BY author
ORDER BY tweet_count DESC;

-- 查看最新推文
SELECT
    tweet_id,
    author,
    LEFT(content, 100) as content_preview,
    published_at
FROM tweets
ORDER BY published_at DESC
LIMIT 20;

-- 查看用户采集状态
SELECT
    username,
    priority,
    is_active,
    last_crawled_at,
    (SELECT COUNT(*) FROM tweets WHERE author = watched_users.username) as tweet_count
FROM watched_users
ORDER BY priority DESC;
```

### 数据导出

```bash
# 导出所有推文到 CSV
docker-compose exec postgres psql -U nitter_user -d nitter_x -c "\COPY (SELECT * FROM tweets ORDER BY published_at DESC) TO STDOUT CSV HEADER" > tweets.csv

# 导出某个用户的推文
docker-compose exec postgres psql -U nitter_user -d nitter_x -c "\COPY (SELECT * FROM tweets WHERE author='elonmusk' ORDER BY published_at DESC) TO STDOUT CSV HEADER" > elonmusk_tweets.csv
```

---

## 系统架构

### 1. 数据采集层（Crawler）

- **访问入口**：Nitter（xcancel.com 或自建实例）
- **职责**：
  - 获取指定用户的时间线首页（HTML）
  - 解析推文基础字段
  - 去重判断，避免重复采集

> **设计原则**：
> - 永不直连 x.com
> - 单次采集只关注「最新增量」
> - 使用 Redis 缓存的可用实例列表

### 2. 数据存储与缓冲层

#### PostgreSQL（主存储）

存储**结构化、可追溯的最终数据**：

**主要表**：
- `tweets`: 推文主表（原始推文、清洗后内容、标签、权重）
- `watched_users`: 关注用户列表
- `tag_definitions`: 标签定义表
- `processing_logs`: 处理日志表

**时间管理**：
- 所有时间字段使用 `TIMESTAMP WITH TIME ZONE`（UTC）
- 数据库连接默认时区为 UTC
- 确保跨时区数据一致性

#### Redis（中间态与队列）

- **实例缓存**：可用 Nitter 实例列表（3 小时 TTL）
- **采集队列**：新推文 ID / URL
- **处理队列**：等待 LLM 处理的推文（预留）
- **去重缓存**：短期 tweet_id / hash

> Redis 只保存"短生命周期状态"，PostgreSQL 才是事实源（Source of Truth）。

### 3. 处理与分析层（Worker）- 计划中

#### 3.1 文本清理（Rule-based）
- 去除：URL、表情符号、无效换行、RT 标记
- 统一：编码、时间格式

#### 3.2 LLM 标签系统
- 输入：清洗后的推文正文 + 元数据
- 输出：
  - 主题标签（Crypto / AI / 宏观 / 项目）
  - 情绪标签（利好 / 利空 / 中性）
  - 信息类型（新闻 / 观点 / 传言）

#### 3.3 权重与等级计算
- 多因子加权模型：作者权重、标签权重、时效性、互动指标
- 最终映射为等级：S / A / B / C

### 4. 展示与服务层（Streamlit）

- 多维筛选：用户 / 标签 / 等级 / 时间
- 排序方式：最新 / 权重优先
- 预留接口：Webhook / 邮件 / Bot 推送

---

## 常见问题

### 1. 如何查看服务状态？

```bash
# 查看 Docker 服务状态
docker-compose ps

# 查看服务日志
docker-compose logs postgres
docker-compose logs redis
```

### 2. 如何重置数据库？

```bash
# 停止服务并删除数据卷
docker-compose down -v

# 重新启动（会自动初始化数据库）
docker-compose up -d
```

### 3. 如何备份数据？

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U nitter_user nitter_x > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup_20251222.sql | docker-compose exec -T postgres psql -U nitter_user nitter_x
```

### 4. Nitter 实例不可用怎么办？

```bash
# 强制刷新实例列表
python discover_instances.py --force-refresh

# 或手动清除 Redis 缓存（下次爬虫会自动重新检测）
docker-compose exec redis redis-cli -a xin_x DEL nitter:instances:available
```

### 5. 如何调整采集频率？

修改 `.env` 文件中的参数：

```bash
CRAWL_INTERVAL=60           # 采集循环间隔（秒）
CRAWL_USER_INTERVAL=180     # 用户采集间隔（秒）
CRAWLER_TIMEOUT=30          # 请求超时（秒）
CRAWLER_DELAY=1.0           # 每个用户采集间隔（秒）
```

---

## 开发规范

项目遵循以下规范（定义在 `.claude` 文件）：

### 1. 目录说明文件
- 项目入口使用 `README.md`
- 其他目录都需要创建 `{目录名}.md` 说明文件
- 例如：`src/` 目录有 `src/src.md` 说明文件

### 2. 时间管理
- 所有时间使用 UTC 标准
- 数据库时间字段使用 `TIMESTAMP WITH TIME ZONE`
- Python datetime 对象带有 `timezone.utc` 时区信息

### 3. 代码规范
- 严格遵守 Python 命名规范（PEP 8）
- 使用中文进行代码注释

---

## 开发计划

### ✅ v1.0.0 - 基础环境（已完成）
- PostgreSQL + Redis 部署
- 数据库结构设计
- Docker 容器化

### ✅ v2.0.0 - 推文采集（已完成）
- Nitter 爬虫实现
- 增量采集逻辑
- 用户管理工具
- Nitter 实例发现与缓存
- Redis 缓存优先策略

### ✅ v2.5.0 - Web UI（已完成）
- Streamlit 管理界面
- 用户管理页面
- 推文展示页面
- 系统监控页面
- 数据导出功能

### ⏳ v3.0.0 - 内容处理（开发中）
- 文本清洗
- LLM 标签系统
- 权重与等级计算

### ⏳ v4.0.0 - 内容展示（计划中）
- 高级筛选功能
- Webhook 推送
- 邮件/Bot 通知
- API 接口

---

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。
