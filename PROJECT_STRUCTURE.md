# Nitter X 项目结构

```
nitter_x/
├── docker/                      # Docker 相关配置
│   └── postgres/
│       └── init/
│           └── 01-init.sql     # 数据库初始化脚本
│
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── config/                  # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py         # 系统配置
│   │
│   ├── crawler/                 # 数据采集层
│   │   ├── __init__.py
│   │   └── nitter_crawler.py   # Nitter 爬虫
│   │
│   ├── storage/                 # 数据存储层
│   │   ├── __init__.py
│   │   ├── postgres_client.py  # PostgreSQL 客户端
│   │   └── redis_client.py     # Redis 客户端
│   │
│   ├── processor/               # 处理与分析层（预留）
│   │   └── __init__.py
│   │
│   ├── web/                     # 展示层（预留）
│   │   └── __init__.py
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       └── logger.py           # 日志配置
│
├── tests/                       # 测试目录
├── logs/                        # 日志目录
├── data/                        # 数据目录
│
├── .env                         # 环境变量配置（不提交到 git）
├── .env.example                 # 环境变量示例
├── docker-compose.yml           # Docker Compose 配置
├── requirements.txt             # Python 依赖
│
├── main.py                      # 主程序入口
├── manage_users.py              # 用户管理工具
├── test_system.py               # 系统测试脚本
│
├── DEPLOYMENT.md                # 部署文档
└── README.md                    # 项目说明
```

## 模块说明

### src/config
- `settings.py`: 系统配置管理，从 .env 读取配置

### src/crawler
- `nitter_crawler.py`: Nitter 推文爬虫，负责从 Nitter 实例获取推文

### src/storage
- `postgres_client.py`: PostgreSQL 数据库客户端，管理推文和用户数据
- `redis_client.py`: Redis 客户端，管理队列和缓存

### src/processor（预留 v3.0.0）
- 文本清洗
- LLM 标签系统
- 权重与等级计算

### src/web（预留 v4.0.0）
- Streamlit 展示界面

### src/utils
- `logger.py`: 日志配置工具

## 核心文件

### main.py
主程序入口，执行推文采集任务：
1. 从数据库读取关注用户列表
2. 遍历每个用户，调用爬虫获取推文
3. 去重后存入数据库
4. 推送到 Redis 处理队列

### manage_users.py
用户管理工具，支持：
- `list`: 列出所有关注用户
- `add`: 添加关注用户
- `remove`: 移除关注用户
- `enable/disable`: 启用/禁用用户

### test_system.py
系统测试脚本，验证：
- PostgreSQL 连接
- Redis 连接
- Nitter 爬虫功能
