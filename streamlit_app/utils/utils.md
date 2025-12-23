# utils 目录

## 目录作用

存放 Streamlit 应用的工具函数模块。

## 文件说明

### db_helper.py
数据库查询辅助函数，提供：
- 获取推文列表（支持分页、筛选）
- 用户管理（获取、添加、修改、删除）
- 获取系统统计数据
- 获取推文趋势数据
- 用户推文统计

**主要函数**：
```python
# 推文相关
def get_tweets(limit, offset, username=None, start_date=None, end_date=None, keyword=None):
    """
    获取推文列表（支持分页和筛选）

    返回字段：
    - tweet_id: 推文ID
    - author: 用户名
    - display_name: 展示名称（关联 watched_users 表）
    - content: 推文内容
    - published_at: 发布时间（UTC）
    - tweet_url: x.com 原始链接
    - created_at: 采集时间（UTC）
    - media_urls: 媒体URL列表（JSONB）
    - has_media: 是否包含媒体
    """
    pass

def get_tweet_count(username=None, start_date=None, end_date=None, keyword=None):
    """获取推文总数（支持筛选）"""
    pass

# 用户管理
def get_all_users():
    """获取所有监听用户（包含推文统计）"""
    pass

def add_user(username, priority=1, notes="", display_name=""):
    """添加监听用户"""
    pass

def update_user(username, priority=None, notes=None, display_name=None, is_active=None):
    """更新用户信息（支持部分更新）"""
    pass

def delete_user(username):
    """删除监听用户"""
    pass

# 统计数据
def get_system_stats():
    """获取系统统计数据"""
    pass

def get_daily_tweet_stats(days=7):
    """获取每日推文统计（最近 N 天）"""
    pass

def get_user_tweet_stats(limit=10):
    """获取用户推文统计（Top N 活跃用户）"""
    pass
```

**特点**：
- 封装数据库查询逻辑
- 返回 Pandas DataFrame 或字典
- 处理异常并返回友好错误信息
- 使用 Streamlit 缓存优化性能
- 调用 PostgresClient 的底层方法，保持代码一致性

### format_helper.py
格式化辅助函数，提供：
- 时间格式化（绝对时间、相对时间）
- 数字格式化（千位分隔符）
- 文本截断
- 优先级标签
- 状态标签

**主要函数**：
```python
def format_datetime(dt, show_time=True, show_timezone=False):
    """格式化日期时间"""
    # 返回：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM:SS UTC
    pass

def format_relative_time(dt):
    """格式化为相对时间（如 "2 小时前"）"""
    pass

def format_number(num):
    """格式化数字（添加千位分隔符）"""
    # 返回：1,234,567
    pass

def format_tweet_content(content, max_length=200):
    """格式化推文内容（截断）"""
    pass

def format_priority(priority):
    """格式化优先级"""
    # 返回：⭐ 高 / 📌 中 / 📋 低
    pass

def format_status(is_active):
    """格式化状态"""
    # 返回：✅ 启用 / ❌ 禁用
    pass

def truncate_string(text, length=50):
    """截断字符串"""
    pass
```

**特点**：
- UTC 时间处理（自动转换为 UTC）
- 支持时区显示
- 友好的相对时间显示
- 多语言支持（中文）

## 使用示例

### db_helper.py
```python
from streamlit_app.utils.db_helper import get_tweets, get_stats

# 获取推文列表
tweets_df = get_tweets(
    limit=20,
    offset=0,
    username="elonmusk",
    start_date=datetime(2025, 12, 1),
    end_date=datetime(2025, 12, 23),
    keyword="AI"
)

# 获取系统统计
stats = get_stats()
st.metric("总推文数", stats["total_tweets"])
```

### format_helper.py
```python
from streamlit_app.utils.format_helper import (
    format_datetime,
    format_relative_time,
    format_number
)

# 格式化时间
formatted = format_datetime(tweet.published_at, show_timezone=True)
# 输出：2025-12-23 10:30:45 UTC

# 相对时间
relative = format_relative_time(tweet.published_at)
# 输出：2 小时前

# 格式化数字
formatted_num = format_number(1234567)
# 输出：1,234,567
```

## 时间处理规范

### UTC 时间标准
- 所有时间存储使用 UTC
- 数据库时间字段带有时区信息
- Python datetime 对象使用 `timezone.utc`

### 时间显示
- 默认显示 UTC 时间
- 可选显示时区标识（UTC）
- 使用相对时间提升用户体验

### 示例
```python
from datetime import datetime, timezone

# 生成 UTC 时间
now = datetime.now(timezone.utc)

# 格式化显示
format_datetime(now)  # "2025-12-23 10:30:45"
format_datetime(now, show_timezone=True)  # "2025-12-23 10:30:45 UTC"
format_relative_time(now)  # "刚刚"
```

## 扩展建议

可以添加其他工具函数：

### 数据验证
```python
def validate_username(username):
    """验证用户名格式"""
    pass

def validate_priority(priority):
    """验证优先级范围（1-10）"""
    pass
```

### 数据转换
```python
def df_to_csv(df):
    """DataFrame 转 CSV"""
    return df.to_csv(index=False).encode('utf-8-sig')

def df_to_json(df):
    """DataFrame 转 JSON"""
    return df.to_json(orient='records', force_ascii=False)
```

## 注意事项

- 工具函数应该是纯函数，无副作用
- 添加充分的文档字符串和类型注解
- 错误处理应该返回友好的错误信息
- 使用 Streamlit 缓存优化性能
- 遵循 UTC 时间处理规范
