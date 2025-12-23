# pages 目录

## 目录作用

存放 Streamlit 应用的多页面文件。

## 命名规范

- 文件命名格式：`序号_页面名.py`
- 序号决定页面在侧边栏的显示顺序
- Streamlit 自动识别并生成导航

## 页面说明

### 1_用户管理.py
用户管理页面，功能包括：
- 用户列表展示（表格）
- 添加新用户（表单）
- 编辑用户信息（优先级、备注）
- 启用/禁用用户
- 删除用户（带确认）
- 用户统计（推文数、最后采集时间）

**核心组件**：
- 用户列表表格
- 用户添加表单
- 用户编辑侧边栏

### 2_Tweets.py (推文展示)
推文展示页面，功能包括：
- 推文列表（卡片式展示）
- 多维筛选：
  - 按用户筛选
  - 按时间范围筛选（今天、最近3/7/30天、自定义）
  - 关键词搜索
- 分页浏览（每页 10/20/50/100 条）
- 数据导出（CSV）
- 自动刷新（可选）

**核心组件**：
- 筛选器组（用户、时间、关键词）
- 推文卡片
- 分页控制
- 导出按钮

### 3_Monitor.py (系统监控)
系统监控页面，功能包括：
- 服务状态检查：
  - PostgreSQL 连接状态
  - Redis 连接状态
  - 爬虫运行状态
- 系统指标：
  - 监听用户数
  - 推文总数
  - 今日新增
  - 待处理任务
- 数据可视化：
  - 最近 30 天推文采集趋势图
  - 每日推文数量统计
- Nitter 实例：
  - 可用实例列表
  - 响应时间
- 系统配置：
  - 采集配置参数
  - 网络配置参数
- 自动刷新（10 秒）

**核心组件**：
- 服务状态卡片
- 系统指标卡片
- 趋势图表
- 实例列表
- 配置展示

## 页面开发规范

### 1. 页面配置
每个页面文件应包含：
```python
import streamlit as st

st.set_page_config(
    page_title="页面标题",
    page_icon="📝",
    layout="wide",  # 宽布局
)
```

### 2. 数据缓存
使用缓存减少数据库查询：
```python
@st.cache_data(ttl=60)  # 缓存 60 秒
def load_data():
    # 数据库查询
    return data
```

### 3. 会话状态
使用 `st.session_state` 管理状态：
```python
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
```

### 4. 错误处理
使用 try-except 处理错误：
```python
try:
    data = load_data()
except Exception as e:
    st.error(f"❌ 加载数据失败: {str(e)}")
    st.info("💡 请确保数据库服务正常运行")
```

### 5. 加载状态
长时间操作显示加载状态：
```python
with st.spinner("正在加载数据..."):
    data = load_data()
```

## 添加新页面

1. 在 `pages/` 目录创建新文件
2. 文件命名：`序号_页面名.py`
3. 实现页面逻辑
4. 刷新 Streamlit，新页面自动出现

## 注意事项

- 页面文件名中的序号决定显示顺序
- 使用中文命名会直接显示在侧边栏
- 页面之间通过 `st.session_state` 共享状态
- 避免在页面中直接操作数据库，使用 `utils/db_helper.py`
- 使用 `utils/format_helper.py` 进行数据格式化
