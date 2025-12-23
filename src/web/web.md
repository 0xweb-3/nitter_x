# web 目录

## 目录作用

Web 展示层（预留 v4.0.0）。

## 说明

本目录预留用于实现 Web 服务和 API 接口。

**注意**：当前项目使用 Streamlit 作为 Web UI（位于 `streamlit_app/` 目录），本目录预留用于未来可能的 FastAPI/Flask 等后端服务。

## 规划功能

### 1. RESTful API
- 推文查询接口
- 用户管理接口
- 系统状态接口
- 认证和鉴权

### 2. Webhook 推送
- 高权重推文实时推送
- 支持多种推送方式（HTTP、Webhook、WebSocket）
- 推送规则配置

### 3. 第三方集成
- Telegram Bot
- Email 通知
- Discord/Slack 集成

## 技术选型（待定）

### 可选框架
- **FastAPI**: 现代、高性能、支持异步
- **Flask**: 轻量级、灵活
- **Django REST Framework**: 功能完整、生态丰富

### API 设计示例
```python
# 预期的 API 结构
GET  /api/tweets          # 获取推文列表
GET  /api/tweets/{id}     # 获取推文详情
POST /api/users           # 添加监听用户
GET  /api/stats           # 获取系统统计
POST /api/webhooks        # 配置 Webhook
```

## 当前状态

该模块尚未实现，预计在 v4.0.0 版本开发。

目前使用 Streamlit 提供 Web 界面（见 `streamlit_app/` 目录）。
