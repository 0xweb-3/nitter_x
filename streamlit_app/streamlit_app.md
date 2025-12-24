# streamlit_app 目录

## 目录作用

Streamlit Web UI 应用，提供可视化的推文采集系统管理界面。

## 目录结构

```
streamlit_app/
├── app.py                # 主入口（首页）
├── pages/                # 多页面目录
│   ├── 1_用户管理.py
│   ├── 2_Tweets.py      # 推文展示
│   └── 3_Monitor.py     # 系统监控
├── components/           # 可复用组件（预留）
│   └── __init__.py
└── utils/                # 工具函数
    ├── __init__.py
    ├── db_helper.py      # 数据库查询辅助
    └── format_helper.py  # 格式化辅助
```

## 文件说明

### app.py
Streamlit 应用主入口（首页），展示：
- 系统概览：监听用户数、推文总数、今日新增
- 数据可视化：每日推文趋势图、Top 10 活跃用户
- 快速操作：一键跳转到各功能页面

### pages/
多页面目录，每个文件对应一个页面：
- `1_用户管理.py`: 用户管理页面
- `2_Tweets.py`: 推文展示页面
- `3_Monitor.py`: 系统监控页面

**命名规范**：
- `序号_页面名.py`
- Streamlit 会自动识别并生成侧边栏导航
- 序号决定页面顺序

### components/
可复用 UI 组件（预留）

可以创建通用组件，例如：
- `user_table.py`: 用户列表表格
- `tweet_card.py`: 推文卡片
- `stats_display.py`: 统计数据显示

### utils/
工具函数模块，提供：
- `db_helper.py`: 数据库查询辅助函数
- `format_helper.py`: 格式化辅助函数（时间、数字、文本）

## 功能特性

### 1. 首页 (app.py)
- 系统概览卡片
- 每日推文趋势图（最近 14 天）
- Top 10 活跃用户统计
- 快速操作按钮

### 2. 处理结果页面 (1_Processed_Results.py)
- 推文处理结果展示（P0-P6 分级）
- 按分级筛选展示
- 显示摘要、关键词、翻译内容
- 媒体资源展示（图片、视频）
- 处理进度监控：
  - 实时显示剩余待处理推文数量
  - 显示上一轮单条处理耗时（秒）
  - 支持自动刷新（20秒）和手动刷新统计
- 分页浏览（10/20/50/100 条/页）
- 统计概览（各分级推文数量）

### 3. 用户管理页面
- 用户列表（表格展示）
- 添加用户（表单）
- 编辑用户（优先级、备注）
- 启用/禁用用户
- 删除用户（二次确认）

### 4. 推文展示页面
- 推文列表（卡片式）
- 筛选功能（用户、时间范围、关键词）
- 分页浏览
- 数据导出（CSV）

### 5. 系统监控页面
- 服务状态（PostgreSQL、Redis、爬虫）
- 系统指标（用户数、推文数、今日新增）
- 采集趋势图（最近 30 天）
- Nitter 实例列表
- 自动刷新（10 秒）

## 启动方式

```bash
# 直接启动
streamlit run streamlit_app/app.py

# 使用启动脚本
./start_streamlit.sh

# 指定端口
streamlit run streamlit_app/app.py --server.port 8502

# 后台启动
nohup streamlit run streamlit_app/app.py > logs/streamlit.log 2>&1 &
```

## 技术栈

- **框架**: Streamlit 1.29+
- **数据可视化**: Plotly 5.18+
- **表格组件**: streamlit-aggrid 0.3.4+
- **数据处理**: Pandas 2.0+
- **后端**: PostgreSQL + Redis

## 配置

### .streamlit/config.toml（可选）
```toml
[server]
port = 8501
headless = true
enableCORS = false

[theme]
primaryColor = "#1DA1F2"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## 开发建议

### 添加新页面
1. 在 `pages/` 目录创建新文件
2. 文件命名：`序号_页面名.py`
3. 使用 `st.set_page_config()` 配置页面
4. 页面会自动出现在侧边栏

### 添加新组件
1. 在 `components/` 目录创建组件文件
2. 定义可复用的函数
3. 在页面中导入使用

### 性能优化
- 使用 `@st.cache_data` 缓存数据库查询
- 设置合理的 TTL（Time To Live）
- 避免频繁的数据库查询
- 使用分页减少数据加载

## 注意事项

- Streamlit 会在代码修改后自动重新加载
- 使用 `st.session_state` 管理会话状态
- 大数据量查询建议分页
- 长时间运行的操作使用 `st.spinner()`
- 错误处理使用 `try-except` + `st.error()`
