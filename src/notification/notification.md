# notification 模块说明

## 模块作用

本模块提供 iOS Bark 推送通知功能，用于将高优先级推文（P0/P1/P2）自动推送到用户的 iOS 设备。

## 主要功能

1. **Bark 推送客户端** (`bark_client.py`)
   - 封装 Bark API 调用
   - 支持完整 URL 或仅 key 的配置方式
   - 提供测试推送功能
   - 完整的错误处理和重试机制

2. **推送业务服务** (`push_service.py`)
   - 推送条件判断（全局开关、级别筛选）
   - 批量推送到多个 Bark keys
   - 推送消息格式化（级别emoji、摘要、关键词）
   - 推送历史记录和统计

## 数据库表

### bark_keys
存储 Bark 推送密钥配置
- `key_name`: Key 名称（用于识别）
- `bark_url`: Bark URL 或 key
- `is_active`: 是否启用
- `push_count`: 推送次数统计
- `last_push_at`: 最后推送时间

### push_settings
存储推送功能配置
- `push_enabled`: 全局推送开关
- `push_grades`: 推送的级别（逗号分隔）
- `push_icon`: 推送图标 URL

### push_history
记录推送历史
- `tweet_id`: 推文 ID
- `bark_key_id`: 使用的 Bark key
- `push_status`: 推送状态（success/failed）
- `error_message`: 错误信息
- `response_data`: Bark API 响应

## 使用方式

### 在 process_worker.py 中集成

```python
from src.notification.push_service import get_push_service

# 初始化
push_service = get_push_service()

# 推送推文
push_result = push_service.push_tweet(
    tweet_id=tweet_id,
    grade=grade,
    summary=summary,
    keywords=keywords,
    tweet_url=tweet_url,
    author=author
)
```

### 在 Streamlit 页面中管理

访问 `streamlit_app/pages/5_Settings.py` 进行配置：
- 开启/关闭全局推送开关
- 选择需要推送的级别
- 添加/删除/测试 Bark keys
- 配置推送图标

## 推送消息格式

**标题**：`{emoji} {grade} 级推文 - @{author}`
- P0: 🔴, P1: 🟠, P2: 🟡

**内容**：
```
📝 {摘要}

🏷️ #{关键词1}, #{关键词2}, #{关键词3}
```

**点击跳转**：原文链接
**图标**：加密货币 icon（可配置）
**分组**：`Nitter-X-{grade}`

## 配置项

### 环境变量（.env）

```bash
BARK_PUSH_ENABLED=true
BARK_PUSH_GRADES=P0,P1,P2
BARK_PUSH_ICON=https://em-content.zobj.net/source/apple/391/coin_1fa99.png
```

### Settings 类

```python
settings.BARK_PUSH_ENABLED  # 推送开关
settings.BARK_PUSH_GRADES   # 推送级别
settings.BARK_PUSH_ICON     # 推送图标
```

**注意**：环境变量仅作为默认值，实际配置以数据库 `push_settings` 表为准。

## Bark API 说明

### API 格式
```
GET https://api.day.app/{key}/{title}/{content}?url={url}&icon={icon}&sound={sound}&group={group}
```

### 参数说明
- `key`: Bark 密钥
- `title`: 推送标题（需 URL 编码）
- `content`: 推送内容（需 URL 编码）
- `url`: 点击跳转链接（可选）
- `icon`: 推送图标 URL（可选）
- `sound`: 推送声音（可选，默认 default）
- `group`: 推送分组（可选，默认 Nitter-X）

### 响应格式
```json
{
  "code": 200,
  "message": "success",
  "timestamp": 1640000000000
}
```

## 错误处理

1. **推送失败不阻塞主流程**：所有推送异常都会被捕获，不影响推文处理
2. **详细的错误记录**：失败的推送会记录到 `push_history` 表
3. **重试机制**：网络超时会自动重试（requests 库默认行为）

## 扩展性

本模块设计支持后续扩展：
- 添加其他推送渠道（Telegram、Email、Webhook等）
- 支持自定义推送模板
- 支持推送频率限制
- 支持推送优先级排序

## 依赖

- `requests`: HTTP 请求库
- `psycopg2`: PostgreSQL 客户端
- `streamlit`: Web 界面框架
- `st_aggrid`: 高级表格组件
