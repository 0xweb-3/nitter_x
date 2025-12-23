# src 目录

## 目录作用

存放项目的核心源代码。

## 目录结构

```
src/
├── config/         # 配置模块
├── crawler/        # 数据采集层
├── storage/        # 数据存储层
├── processor/      # 处理与分析层（预留）
├── web/            # 展示层（预留）
└── utils/          # 工具函数
```

## 模块说明

### config
系统配置管理，从 `.env` 读取配置参数。

### crawler
Nitter 推文爬虫，负责：
- 从 Nitter 实例获取推文
- 实例健康检测和管理
- 增量采集逻辑

### storage
数据存储客户端，包括：
- PostgreSQL 客户端
- Redis 客户端

### processor（预留 v3.0.0）
推文处理模块，包括：
- 文本清洗
- LLM 标签系统
- 权重与等级计算

### web（预留 v4.0.0）
Web 服务层（Streamlit 当前在 streamlit_app/ 目录）

### utils
通用工具函数，如日志配置。

## 设计原则

- 模块之间低耦合、高内聚
- 使用依赖注入降低模块间依赖
- 遵循 Python PEP 8 编码规范
- 使用中文注释
