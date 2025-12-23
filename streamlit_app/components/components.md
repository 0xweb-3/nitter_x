# components 目录

## 目录作用

存放可复用的 Streamlit UI 组件。

## 说明

本目录用于存放跨页面使用的通用 UI 组件，提高代码复用性。

## 组件设计建议

### 1. 用户列表表格 (user_table.py)
```python
def render_user_table(users_df):
    """
    渲染用户列表表格

    Args:
        users_df: 用户数据 DataFrame

    Returns:
        选中的用户列表
    """
    # 使用 streamlit-aggrid 渲染表格
    pass
```

### 2. 推文卡片 (tweet_card.py)
```python
def render_tweet_card(tweet):
    """
    渲染单个推文卡片

    Args:
        tweet: 推文数据字典
    """
    # 展示推文内容、作者、时间等
    pass
```

### 3. 统计卡片 (stats_card.py)
```python
def render_stats_card(title, value, delta=None):
    """
    渲染统计数据卡片

    Args:
        title: 卡片标题
        value: 主要数值
        delta: 变化量（可选）
    """
    # 展示统计指标
    pass
```

### 4. 筛选器组件 (filters.py)
```python
def render_time_filter():
    """
    渲染时间范围筛选器

    Returns:
        (start_date, end_date) 元组
    """
    pass

def render_user_filter(users):
    """
    渲染用户筛选器

    Args:
        users: 用户列表

    Returns:
        选中的用户名
    """
    pass
```

## 使用示例

```python
# 在页面中使用组件
from streamlit_app.components.user_table import render_user_table
from streamlit_app.components.stats_card import render_stats_card

# 渲染统计卡片
render_stats_card("总推文数", 1234, delta="+56")

# 渲染用户表格
selected_users = render_user_table(users_df)
```

## 组件设计原则

1. **单一职责**：每个组件只负责一个功能
2. **参数化**：通过参数控制组件行为
3. **无状态**：避免组件内部维护状态
4. **可复用**：设计通用接口，适用于多个场景
5. **文档完善**：提供清晰的文档字符串

## 当前状态

该目录预留用于未来开发，当前组件代码直接嵌入在页面文件中。

建议在以下情况创建组件：
- 同一 UI 元素在多个页面中使用
- 代码复杂度较高，需要封装
- 需要统一样式和交互逻辑
