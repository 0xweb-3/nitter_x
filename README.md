# Nitter X - 推文信息收集系统

基于 Nitter 的 X (Twitter) 推文采集与智能分析系统，支持指定用户推文采集、LLM 智能分级、内容摘要和可视化展示。

## ✨ 核心功能

- 🐦 **智能采集** - 基于 Nitter 代理，低封禁风险，支持多实例自动切换
- 🤖 **LLM 分析** - P0-P6 价格影响分级，自动翻译、摘要、关键词提取
- 📊 **可视化管理** - Streamlit Web 界面，支持用户管理、推文展示、系统监控
- 💾 **完整存储** - PostgreSQL 主存储 + Redis 缓存，支持媒体资源保存
- 🚀 **一键部署** - 自动环境检查、数据库初始化、服务启动

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **数据库**: PostgreSQL 16 + Redis 7
- **容器化**: Docker + Docker Compose
- **前端**: Streamlit
- **AI**: LangChain + OpenAI API (兼容)
- **向量**: sentence-transformers (384维)

---

## 🚀 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+

### 2. 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd nitter_x

# 配置环境变量
cp .env.example .env
nano .env  # 修改密码和 LLM API 配置

# 启动 Docker 服务
docker-compose up -d

# 安装 Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt requirements-streamlit.txt

# 验证部署（可选）
python verify_deployment.py

# 添加监听用户
python manage_users.py add elonmusk --name "Elon Musk" --priority 10

# 一键启动所有服务
./start.sh
```

访问 **http://localhost:8501** 查看 Web 界面

### 3. 环境变量配置

编辑 `.env` 文件，配置以下必需参数：

```bash
# 数据库密码
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password

# LLM API（用于推文处理）
LLM_API_KEY=your-api-key              # 必需
LLM_API_URL=https://yibuapi.com/v1    # 可选
LLM_MODEL=gpt-3.5-turbo               # 可选
```

---

## 📖 使用指南

### 服务管理

```bash
# 一键启动所有服务（采集、处理、Web界面）
./start.sh

# 查看服务状态
./status.sh

# 停止所有服务
./stop.sh

# 查看日志
tail -f logs/crawler.log        # 采集日志
tail -f logs/process_worker.log # 处理日志
tail -f logs/streamlit.log      # Web 日志
```

### 用户管理

```bash
# 添加监听用户
python manage_users.py add <username> --name "显示名" --priority 10

# 查看用户列表
python manage_users.py list

# 启用/禁用用户
python manage_users.py enable <username>
python manage_users.py disable <username>
```

### Nitter 实例管理

```bash
# 查看可用实例
python discover_instances.py

# 强制刷新实例列表
python discover_instances.py --force-refresh
```

### 数据库操作

```bash
# 连接数据库
docker-compose exec postgres psql -U nitter_user -d nitter_x

# 备份数据
docker-compose exec postgres pg_dump -U nitter_user nitter_x > backup.sql

# 恢复数据
cat backup.sql | docker-compose exec -T postgres psql -U nitter_user nitter_x
```

---

## 📊 系统架构

### 数据流程

```
采集层 (Nitter) → 存储层 (PostgreSQL) → 处理层 (LLM) → 展示层 (Streamlit)
                           ↓
                    缓存层 (Redis)
```

### 核心模块

- **采集层** (`src/crawler/`) - Nitter 爬虫，实例发现与健康检测
- **存储层** (`src/storage/`) - PostgreSQL + Redis 客户端
- **处理层** (`src/processor/`) - LLM 分级、翻译、摘要、向量化
- **展示层** (`streamlit_app/`) - Web 界面，用户管理、推文展示、系统监控

### 数据库表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `tweets` | 推文主表 | tweet_id, author, content, media_urls, processing_status |
| `processed_tweets` | 处理结果表 | grade (P0-P6), summary_cn, keywords, embedding |
| `watched_users` | 监听用户 | username, priority, is_active, notes |

---

## 🤖 智能处理

### 分级系统（P0-P6，价格影响导向）

| 级别 | 说明 | 影响 | 处理 |
|------|------|------|------|
| 🔴 **P0** | 价格驱动事件 | 已发生，必然触发资金行为 | ✅ 全量 |
| 🟠 **P1** | 强信号事件 | 极可能发生，提前交易 | ✅ 全量 |
| 🟡 **P2** | 结构性影响 | 改变价格中枢 | ✅ 全量 |
| 🟢 **P3** | 宏观政策 | 影响风险资产定价 | ❌ 仅分级 |
| 🔵 **P4** | 叙事情绪 | 资金反应不稳定 | ❌ 仅分级 |
| ⚪ **P5** | 信息噪音 | 不改变资金决策 | ❌ 仅分级 |
| ⚫ **P6** | 可舍弃 | 无价格影响 | ❌ 仅分级 |

**全量处理**包括：语言检测、翻译、30字摘要、关键词提取（3-5个）、向量化（384维）

### 处理流程

```bash
# 测试 LLM 配置
python test_llm.py

# 测试处理流程
python test_tweet_processing.py

# 启动处理 Worker（持续后台运行）
python process_worker.py
```

Worker 自动：
1. 每 5 秒检查待处理推文
2. 批量处理（10条/批）
3. 对 P0/P1/P2 级推文进行全量处理
4. 更新处理状态和结果

---

## 🌐 Web 界面

访问 **http://localhost:8501**

### 主要页面

- **首页** - 系统概览、统计数据、快速操作
- **处理结果** - P0-P6 分级展示、摘要、关键词、媒体资源
- **推文展示** - 卡片式展示、筛选、导出、媒体播放
- **用户管理** - 添加/编辑/删除监听用户
- **系统监控** - 服务状态、采集趋势、实例列表

---

## 🔧 常见问题

### 1. 数据库连接失败

```bash
# 检查 Docker 服务
docker-compose ps

# 查看日志
docker-compose logs postgres redis
```

### 2. Nitter 实例不可用

```bash
# 刷新实例列表
python discover_instances.py --force-refresh

# 或清除 Redis 缓存
docker-compose exec redis redis-cli -a <password> DEL nitter:instances:available
```

### 3. LLM 处理失败

检查 `.env` 中的 `LLM_API_KEY` 配置，运行测试：
```bash
python test_llm.py
```

### 4. 重置数据库

```bash
# 备份数据（可选）
docker-compose exec postgres pg_dump -U nitter_user nitter_x > backup.sql

# 停止并删除数据卷
docker-compose down -v

# 重新启动（自动初始化）
docker-compose up -d
```

---

## 📁 项目结构

```
nitter_x/
├── docker/                      # Docker 配置
│   └── postgres/init/           # 数据库初始化脚本
├── src/                         # 源代码
│   ├── crawler/                 # 采集模块
│   ├── processor/               # 处理模块（LLM、向量化）
│   ├── storage/                 # 存储模块（PostgreSQL、Redis）
│   ├── config/                  # 配置管理
│   └── utils/                   # 工具函数
├── streamlit_app/               # Web 界面
│   ├── pages/                   # 多页面
│   └── utils/                   # 辅助函数
├── migrations/                  # 数据库迁移脚本
├── logs/                        # 日志目录
├── data/models/                 # 向量模型缓存
├── main.py                      # 采集主程序
├── process_worker.py            # 处理 Worker
├── manage_users.py              # 用户管理工具
├── start.sh                     # 一键启动脚本
├── stop.sh                      # 停止脚本
├── status.sh                    # 状态查看脚本
└── verify_deployment.py         # 部署验证脚本
```

---

## 🔄 版本历史

- **v4.0.0** - 分析总结出新的热MEME，新的叙事
- **v3.0.0** - P0-P6 价格影响分级系统、LLM 集成、向量化、一键部署
- **v2.6.0** - 媒体资源采集、实例缓存优化、动态锁超时
- **v2.5.0** - Streamlit Web 界面、用户管理、系统监控
- **v2.0.0** - Nitter 采集、实例发现、Redis 缓存
- **v1.0.0** - 基础环境、数据库设计

---

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交 Issue。
