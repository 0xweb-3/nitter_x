# Nitter X - 推文信息收集系统

基于 Nitter 的 X (Twitter) 推文采集与智能分析系统，支持指定用户推文采集、LLM 智能分级、内容摘要和可视化展示。

## ✨ 核心功能

- 🐦 **智能采集** - 基于 Nitter 代理，低封禁风险，支持多实例自动切换
- 🤖 **LLM 分析** - P0-P6 价格影响分级，自动翻译、摘要、关键词提取
- 📲 **实时推送** - iOS Bark 推送，P0/P1/P2 高优先级消息自动通知
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

# 推文处理配置
ENABLE_24H_EXPIRATION=true            # 启用推文过期判断（默认启用）
TWEET_EXPIRATION_HOURS=24             # 推文过期时间阈值（小时）

# Bark 推送配置
BARK_PUSH_ENABLED=true                # 启用 Bark 推送（默认启用）
BARK_PUSH_GRADES=P0,P1,P2             # 推送级别（逗号分隔）
BARK_PUSH_ICON=https://...            # 推送图标 URL
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

### Bark 推送配置

```bash
# 测试推送功能
python test_bark_push.py

# 预览不同图标效果（会发送多条测试推送）
python test_bark_icons.py

# 测试启用/禁用功能
python test_bark_enable_disable.py
```

**通过 Web 界面配置**：
1. 访问 **http://localhost:8501**
2. 进入 **"⚙️ 系统设置"** 页面
3. 在 **"🔑 Bark Keys 管理"** Tab：
   - 添加 Bark key（支持完整 URL 或仅 key）
   - 测试推送（验证配置）
   - 启用/禁用特定设备
   - 查看推送统计
4. 在 **"📲 推送配置"** Tab：
   - 全局推送开关
   - 选择推送级别（默认 P0/P1/P2）
   - 自定义推送图标

**推送消息格式**：
- 标题：`🔴 P0 级推文 - @username`
- 内容：摘要 + 关键词
- 点击跳转：原文链接
- 图标：可自定义（默认 💰 钱袋）
- 分组：Nitter-X-P0/P1/P2

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
| `bark_keys` | Bark 推送密钥 | key_name, bark_url, is_active, push_count |
| `push_settings` | 推送配置 | push_enabled, push_grades, push_icon |
| `push_history` | 推送历史 | tweet_id, push_status, pushed_at |

---

## 🤖 智能处理

### 分级系统（P0-P6，价格影响导向）

**重要前提**：所有分级必须与加密货币直接或间接相关，与加密货币无关的内容直接归为 P6。

| 级别 | 说明 | 影响 | 处理 |
|------|------|------|------|
| 🔴 **P0** | 加密货币价格驱动事件 | 已发生，必然触发资金行为 | ✅ 全量 |
| 🟠 **P1** | 触发加密货币价格的强信号 | 极可能发生，提前交易 | ✅ 全量 |
| 🟡 **P2** | 影响加密货币的结构性因素 | 改变价格中枢 | ✅ 全量 |
| 🟢 **P3** | 对加密货币整体估值的宏观政策 | 影响风险资产定价 | ✅ 全量 |
| 🔵 **P4** | 加密货币行业叙事情绪 | 资金反应不稳定 | ✅ 全量 |
| ⚪ **P5** | 加密货币信息噪音 | 不改变资金决策 | ✅ 全量 |
| ⚫ **P6** | 与加密货币无关或可舍弃 | 无价格影响 | ✅ 全量 |

**全量处理**包括：语言检测、翻译、100字摘要、关键词提取（3-5个）、向量化（384维）

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
3. 推文过期判断（可配置）：
   - 如果启用，超过配置时间阈值的推文自动标记为 P6（无需调用 LLM）
   - 通过 `ENABLE_24H_EXPIRATION` 和 `TWEET_EXPIRATION_HOURS` 配置
4. 对未过期推文进行全量 LLM 处理（P0-P6）
5. 更新处理状态和结果

---

## 🌐 Web 界面

访问 **http://localhost:8501**

### 主要页面

- **首页** - 系统概览、统计数据、快速操作
- **处理结果** - P0-P6 分级展示、摘要、关键词、媒体资源、处理进度监控
  - 实时显示剩余待处理推文数量
  - 显示上一轮单条处理耗时（秒）
  - 支持自动刷新和手动刷新统计
- **推文展示** - 卡片式展示、筛选、导出、媒体播放
- **用户管理** - 添加/编辑/删除监听用户
- **系统设置** - Bark 推送配置、推送级别管理、密钥管理
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

### 5. Bark 推送不工作

```bash
# 1. 检查推送配置
python test_bark_push.py

# 2. 检查数据库配置
docker-compose exec postgres psql -U nitter_user -d nitter_x -c "SELECT * FROM push_settings"

# 3. 查看推送历史
docker-compose exec postgres psql -U nitter_user -d nitter_x -c "SELECT * FROM push_history ORDER BY pushed_at DESC LIMIT 10"

# 4. 检查 Bark key 状态
docker-compose exec postgres psql -U nitter_user -d nitter_x -c "SELECT * FROM bark_keys"
```

**常见问题**：
- 确保全局推送开关已启用
- 检查 Bark key 是否正确配置
- 验证推送级别设置包含当前推文级别
- 查看 process_worker.log 日志中的推送相关信息

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
│   ├── notification/            # 推送模块（Bark）
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

### v4.0.0 (2024-12-24) - iOS Bark 推送通知 ✅

**新增功能**
- 📲 **iOS Bark 推送集成** - P0/P1/P2 高优先级推文自动推送到 iOS 设备
- 🔑 **多设备支持** - 支持配置多个 Bark keys，所有设备同时推送
- ⚙️ **系统设置页面** - Streamlit 新增配置页面，管理推送开关、级别、密钥
- 📊 **推送历史记录** - 完整的推送成功/失败记录和统计
- 💬 **消息格式化** - 级别 emoji + 摘要 + 关键词 + 原文链接
- 🎨 **自定义图标** - 支持配置推送图标（默认：💰 钱袋）

**技术实现**
- 新增 `src/notification/` 模块（Bark API 客户端 + 推送服务）
- 新增数据库表：`bark_keys`、`push_settings`、`push_history`
- 集成到 `process_worker.py`，推送失败不影响主流程
- 修复 numpy 类型兼容问题（int64/bool 转换）

**使用方式**
```bash
# 访问系统设置页面
http://localhost:8501 → 系统设置

# 添加 Bark key
# 配置推送级别（默认 P0/P1/P2）
# 启用/禁用推送开关

# 测试推送
python test_bark_push.py
python test_bark_icons.py  # 预览不同图标效果
```

---

### 未来规划
- **v5.0.0** - 具备上下文的信息关联汇总后再处理
- **v4.1.0** - 分析总结出新的热 MEME，新的叙事

### 历史版本
- **v3.0.0** - P0-P6 价格影响分级系统、LLM 集成、向量化、一键部署✅
- **v2.6.0** - 媒体资源采集、实例缓存优化、动态锁超时✅
- **v2.5.0** - Streamlit Web 界面、用户管理、系统监控✅
- **v2.0.0** - Nitter 采集、实例发现、Redis 缓存✅
- **v1.0.0** - 基础环境、数据库设计✅

---

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交 Issue。
