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
│   ├── processor/               # 处理与分析层
│   │   ├── llm_client.py       # LLM 客户端封装
│   │   ├── prompts.py          # 提示词统一管理
│   │   ├── tweet_processor.py  # 推文处理器
│   │   └── embedder.py         # 文本向量化模块
│   ├── web/                     # 展示层（预留）
│   └── utils/                   # 工具函数
│       └── logger.py           # 日志配置
│
├── streamlit_app/               # Streamlit Web UI
│   ├── app.py                   # 主入口（首页）
│   ├── pages/                   # 多页面目录
│   │   ├── 1_用户管理.py
│   │   ├── 2_推文展示.py
│   │   ├── 3_系统监控.py
│   │   └── 4_处理结果.py       # 推文处理结果展示
│   ├── components/              # 可复用组件
│   └── utils/                   # 工具函数
│       ├── db_helper.py        # 数据库查询辅助
│       └── format_helper.py    # 格式化辅助
│
├── migrations/                  # 数据库迁移脚本
├── tests/                       # 测试目录
├── logs/                        # 日志目录
├── data/                        # 数据目录
│   └── models/                  # 向量模型缓存
│
├── main.py                      # 推文采集主程序
├── process_worker.py            # 推文处理 Worker
├── manage_users.py              # 用户管理工具
├── discover_instances.py        # Nitter 实例发现工具
├── test_system.py               # 系统测试脚本
├── test_llm.py                  # LLM 配置测试
├── test_tweet_processing.py     # 推文处理流程测试
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
- **推文列表**：卡片式展示推文内容
- **作者信息**：显示格式为 `@username (展示名)`
- **媒体展示**：
  - 支持图片、视频、GIF 展示
  - 使用可折叠面板，第一个媒体默认展开
  - 图片自适应宽度，视频嵌入播放器
- **原文链接**：显示 x.com 原始链接，便于溯源
- **筛选功能**：按用户、时间范围、关键词筛选（折叠在底部）
- **分页浏览**：自定义每页显示数量（10/20/50/100）
- **数据导出**：导出为 CSV 格式（当前页/全部）
- **内容优先**：打开即显示推文，筛选后置

#### 4. 系统监控
- 服务状态：PostgreSQL、Redis、爬虫运行状态
- 系统指标：监听用户数、推文总数、今日新增
- 采集趋势：最近 30 天推文采集趋势图
- Nitter 实例：显示可用实例列表和响应时间
- 自动刷新：每 10 秒自动刷新数据

#### 5. 处理结果
- **分级统计**：显示各分级（P0-P6）推文数量
- **筛选功能**：多选分级筛选（默认显示 P0/P1/P2 级）
- **推文卡片**：
  - 分级标签（带颜色区分，价格影响导向）
  - 处理耗时显示
  - 原文内容（可折叠）
  - 中文摘要（仅 P0/P1/P2 级，≤30字）
  - 关键词标签（仅 P0/P1/P2 级）
  - 翻译内容（如果有，可折叠）
  - 媒体资源（图片/视频，可折叠展示）
- **分页浏览**：支持 10/20/50/100 条/页
- **自动刷新**：可选 60 秒自动刷新
- **分级标准说明**：完整的价格影响分级标准和图例

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
- ✅ Redis 缓存（5 分钟有效期，快速适应实例可用性变化）
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
1. 从数据库读取所有活跃的关注用户（距上次采集超过指定时间）
2. 根据用户数动态计算锁超时时间
3. 获取分布式锁（防止并发采集冲突）
4. 按优先级顺序遍历每个用户
5. 从 Nitter 实例获取用户最新推文
6. 与数据库中最新推文 ID 对比，只采集新推文
7. 去重后存入 PostgreSQL，媒体信息（图片/视频）保存为 URL 列表
8. 更新用户的最后采集时间
9. 释放分布式锁，等待下一轮采集

### 推文处理流程

系统使用 LLM 对采集到的推文进行智能分级、翻译、摘要和向量化处理。

#### 1. 配置 LLM API

在 `.env` 文件中配置 LLM API 参数：

```bash
# LLM API 配置
LLM_API_KEY=your-api-key              # API 密钥（必需）
LLM_API_URL=https://yibuapi.com/v1   # API 端点 URL
LLM_MODEL=gpt-3.5-turbo               # 模型名称
```

#### 2. 运行数据库迁移

首次使用前需要运行迁移脚本创建处理结果表：

```bash
# 创建 processed_tweets 表和相关索引
python migrations/add_processed_tweets.py
```

#### 3. 测试处理流程

测试单条推文的处理流程：

```bash
# 测试 LLM 配置
python test_llm.py

# 测试完整处理流程
python test_tweet_processing.py
```

#### 4. 启动处理 Worker

启动后台 Worker 持续处理待处理推文：

```bash
# 启动处理 Worker（推荐在后台运行）
python process_worker.py

# 或使用 nohup 在后台运行
nohup python process_worker.py > logs/process_worker.log 2>&1 &

# 查看处理日志
tail -f logs/process_worker.log
```

**Worker 工作流程**：
1. 每 5 秒检查一次待处理推文（`processing_status = 'pending'`）
2. 每批处理 10 条推文
3. 对每条推文进行分级（P0-P6，价格影响导向）
4. 对 P0/P1/P2 级推文进行详细处理：
   - 检测语言，非中文自动翻译为中文
   - 生成 30 字以内的中文摘要
   - 提取 3-5 个关键词
   - 生成摘要的向量表示（384 维）
5. 保存处理结果到 `processed_tweets` 表
6. 更新推文状态为 `completed` 或 `skipped`
7. 推文间延迟 1 秒，避免 API 限流

#### 5. 查看处理结果

在 Streamlit Web UI 中查看处理结果：

```bash
# 启动 Streamlit（如果还未启动）
streamlit run streamlit_app/app.py
```

访问 **http://localhost:8501/处理结果** 页面，可以：
- 📊 查看各分级（P0-P6）统计
- 🔍 按分级筛选推文（默认显示 P0/P1/P2 级）
- 📝 查看中文摘要和关键词
- 🌐 查看翻译内容（非中文推文）
- 📷 查看媒体资源（图片/视频）
- 📄 分页浏览结果（10/20/50/100 条/页）
- 🔄 可选自动刷新（60 秒）

#### 6. 分级标准（价格影响导向）

系统根据推文对加密货币价格的影响程度进行分级：

| 分级 | 说明 | 价格影响 | 详细处理 |
|------|------|----------|----------|
| 🔴 **P0级** | 价格驱动事件 | 已发生或即将确定发生，必然触发资金行为。如：ETF批准/否决、交易所上线/下架、协议被盗、巨鲸转账、稳定币脱锚。影响：强烈、短期立刻反应（分钟级~小时级波动） | ✅ 翻译、摘要、关键词、向量 |
| 🟠 **P1级** | 强信号事件 | 尚未完全落地，但市场共识认为"极可能发生"。如：ETF审批最终阶段、主网上线官宣、代币解锁/回购计划、大额融资披露。影响：提前交易（buy the rumor），波动可持续数天 | ✅ 翻译、摘要、关键词、向量 |
| 🟡 **P2级** | 结构性影响 | 不会立刻拉盘/砸盘，但会改变价格中枢。如：代币经济模型调整、L2成本下降、BTC减半、ETH升级。影响：慢热、趋势型，适合中长期配置判断 | ✅ 翻译、摘要、关键词、向量 |
| 🟢 **P3级** | 宏观政策 | 不直接针对crypto，但影响风险资产定价。如：美联储加息/降息、CPI/非农/PCE、美元流动性变化、全球金融危机。影响：全市场联动，对BTC/ETH权重更高 | ❌ 仅分级 |
| 🔵 **P4级** | 叙事情绪 | 会影响市场"讲什么故事"，但资金反应不稳定。如：AI+Crypto叙事、RWA/DePIN/Restaking热度、大佬喊单、VC报告。影响：高度依赖情绪，容易过期 | ❌ 仅分级 |
| ⚪ **P5级** | 信息噪音 | 和crypto有关，但几乎不改变任何资金决策。如：项目PR合作、普通AMA/采访、社区治理投票、已消化的旧消息。影响：极低 | ❌ 仅分级 |
| ⚫ **P6级** | 可舍弃 | 无价格影响的内容。如：娱乐化meme、无链上/资金/政策影响的内容、单纯观点输出 | ❌ 仅分级 |

> **注意**：只有 P0/P1/P2 级推文会进行翻译、摘要、关键词提取和向量化处理，P3/P4/P5/P6 级仅保留分级结果。

#### 7. 向量模型

系统使用 **sentence-transformers** 生成文本向量：
- 模型：`paraphrase-multilingual-MiniLM-L12-v2`
- 支持多语言（包括中文）
- 向量维度：384
- 模型自动下载并缓存到 `data/models/` 目录
- 用于后续相似度检索和推荐

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
- `tweets`: 推文主表
  - 推文基础信息：`tweet_id`, `author`, `content`, `published_at`
  - x.com 原文链接：`tweet_url`（便于溯源）
  - 媒体信息：`media_urls`（JSONB 数组，存储图片/视频/GIF URL）
  - 媒体标志：`has_media`（布尔值，便于筛选含媒体推文）
  - 处理状态：`processing_status`（枚举类型：pending/processing/completed/failed/skipped）
  - 标签与权重：`tags`, `weight`（预留）
- `processed_tweets`: 推文处理结果表
  - 基础信息：`tweet_id`（外键关联 tweets 表）
  - 分级结果：`grade`（P0/P1/P2/P3/P4/P5/P6，价格影响导向）
  - 中文摘要：`summary_cn`（≤30 字，仅 P0/P1/P2 级）
  - 关键词：`keywords`（JSONB 数组，仅 P0/P1/P2 级）
  - 向量表示：`embedding`（JSONB，384 维，仅 P0/P1/P2 级）
  - 翻译内容：`translated_content`（非中文推文的翻译）
  - 处理耗时：`processing_time_ms`（毫秒）
  - 处理时间：`processed_at`（UTC）
- `watched_users`: 关注用户列表
  - 用户信息：`username`, `display_name`, `priority`
  - 采集控制：`is_active`, `last_crawled_at`
  - 备注：`notes`
- `tag_definitions`: 标签定义表（预留）
- `processing_logs`: 处理日志表（预留）

**时间管理**：
- 所有时间字段使用 `TIMESTAMP WITH TIME ZONE`（UTC）
- 数据库连接默认时区为 UTC
- 确保跨时区数据一致性

#### Redis（中间态与队列）

- **实例缓存**：可用 Nitter 实例列表（5 分钟 TTL，快速适应实例可用性变化）
- **采集队列**：新推文 ID / URL
- **处理队列**：等待 LLM 处理的推文（预留）
- **去重缓存**：短期 tweet_id / hash（24 小时 TTL）

> Redis 只保存"短生命周期状态"，PostgreSQL 才是事实源（Source of Truth）。

### 3. 处理与分析层（Worker）

#### 3.1 推文智能处理（✅ 已实现）

系统使用 LLM 对推文进行智能分级和内容处理：

**LLM 客户端**：
- 基于 LangChain 框架
- 支持自定义 API 端点（兼容 OpenAI API 格式）
- 单例模式，避免重复初始化
- 多种调用方式：简单聊天、模板聊天、批量调用
- 统一的提示词管理（`src/processor/prompts.py`）

**推文处理器**：
- 分级系统（P0-P6，价格影响导向）：根据对加密货币价格的影响程度分级
- P0/P1/P2 级推文详细处理：
  - 语言检测
  - 非中文自动翻译为中文
  - 生成 30 字以内中文摘要
  - 提取 3-5 个关键词
  - 生成摘要的向量表示（384 维）
- P3/P4/P5/P6 级推文仅保留分级结果

**文本向量化**：
- 使用 sentence-transformers 本地模型
- 模型：paraphrase-multilingual-MiniLM-L12-v2
- 支持多语言（包括中文）
- 模型自动缓存到本地
- 用于后续相似度检索

**处理 Worker**：
- 持续从数据库获取待处理推文
- 批量处理（每批 10 条）
- 自动更新推文状态（pending → processing → completed/skipped）
- 完整的错误处理和重试机制
- 实时统计和日志记录

**测试工具**：
```bash
# 测试 LLM 配置
python test_llm.py

# 测试完整处理流程
python test_tweet_processing.py
```

#### 3.2 文本清理（Rule-based）- 计划中
- 去除：URL、表情符号、无效换行、RT 标记
- 统一：编码、时间格式

#### 3.3 高级标签系统 - 计划中
- 情绪标签（利好 / 利空 / 中性）
- 信息类型（新闻 / 观点 / 传言）
- 实体识别（项目名、人物、机构）

#### 3.4 权重与等级计算 - 计划中
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
ESTIMATED_TIME_PER_USER=5   # 单个用户预估采集时间（秒），用于动态计算锁超时
CRAWLER_TIMEOUT=30          # 请求超时（秒）
CRAWLER_DELAY=1.0           # 每个用户采集间隔（秒）
```

**锁超时机制**：
- 系统使用分布式锁防止并发采集冲突
- 锁超时时间根据待采集用户数动态计算：`user_count × ESTIMATED_TIME_PER_USER + CRAWL_INTERVAL`
- 最小超时时间为 `2 × CRAWL_INTERVAL`，确保即使用户数较少也不会超时过快
- 例如：采集 20 个用户时，超时为 160 秒（20×5+60）；采集 50 个用户时，超时为 310 秒（50×5+60）

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
- 用户管理页面（增删改查）
- 推文展示页面（支持媒体展示、原文链接）
- 系统监控页面
- 数据导出功能

### ✅ v2.6.0 - 优化改进（已完成）
- 实例发现缓存优化（5 分钟 TTL）
- 动态锁超时机制（基于用户数自动计算）
- 推文媒体信息采集（图片/视频/GIF）
- 推文展示 UI 优化（内容优先设计）

### ✅ v3.0.0 - 智能处理（已完成）
- **LLM 集成**：
  - LangChain 框架集成
  - 自定义 API 端点支持
  - 统一提示词管理
- **推文分级系统（价格影响导向）**：
  - P0-P6 分级（基于对加密货币价格的影响程度）
  - 三个核心判断标准：预期变化、资金行为、影响范围
  - 详细的分级标准定义和验证
- **内容处理**：
  - 语言检测和自动翻译（P0/P1/P2 级）
  - 30 字中文摘要生成（P0/P1/P2 级）
  - 关键词提取（P0/P1/P2 级）
- **文本向量化**：
  - sentence-transformers 本地模型
  - 多语言支持（384 维向量）
  - 模型自动缓存
- **处理 Worker**：
  - 批量处理机制
  - 状态管理和错误处理
  - 实时统计和日志
- **数据库支持**：
  - processed_tweets 表
  - processing_status 枚举类型
  - 索引优化
  - 分级系统迁移脚本（A-F → P0-P6）
- **UI 展示**：
  - 处理结果页面
  - 价格影响分级筛选和统计
  - 摘要和关键词展示
  - 媒体资源展示

### ⏳ v3.5.0 - 高级处理（计划中）
- 文本清洗（Rule-based）
- 情绪分析标签
- 信息类型识别
- 实体识别（项目名、人物、机构）

### ⏳ v4.0.0 - 内容展示（计划中）
- 基于向量的相似度检索
- 智能推荐系统
- 高级筛选功能
- Webhook 推送
- 邮件/Bot 通知
- API 接口

---

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。
