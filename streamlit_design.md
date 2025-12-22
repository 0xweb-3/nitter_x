# Streamlit Web UI 设计方案

## 目录结构

```
nitter_x/
├── src/                          # 原有后端代码
├── streamlit_app/                # Streamlit 前端应用（新增）
│   ├── app.py                    # 主入口（首页）
│   ├── pages/                    # 多页面目录
│   │   ├── 1_👥_用户管理.py      # 用户管理页面
│   │   ├── 2_📝_推文展示.py      # 推文展示页面
│   │   └── 3_⚙️_系统监控.py      # 系统监控页面
│   ├── components/               # 可复用组件
│   │   ├── __init__.py
│   │   ├── user_table.py         # 用户列表表格
│   │   ├── tweet_card.py         # 推文卡片
│   │   ├── stats_display.py      # 统计数据显示
│   │   └── filters.py            # 筛选器组件
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── db_helper.py          # 数据库查询辅助
│       └── format_helper.py      # 格式化辅助
├── requirements-streamlit.txt    # Streamlit 依赖
└── README_STREAMLIT.md           # Streamlit 使用文档
```

## 页面设计

### 1. 首页 (app.py)
- **功能**: 系统概览
- **内容**:
  - 欢迎信息
  - 关键指标卡片（监听用户数、采集推文总数、今日新增推文）
  - 最近活动时间线
  - 快速操作按钮

### 2. 用户管理页面 (pages/1_👥_用户管理.py)
- **功能**: 管理监听的 Twitter 用户
- **内容**:
  - 用户列表（表格展示）
    - 用户名、优先级、状态、最后采集时间、推文总数
    - 操作按钮：编辑、启用/禁用、删除
  - 添加用户表单
    - 输入用户名、设置优先级、备注
  - 批量导入功能
  - 搜索和筛选

### 3. 推文展示页面 (pages/2_📝_推文展示.py)
- **功能**: 浏览和搜索已采集的推文
- **内容**:
  - 筛选器（按用户、时间范围、关键词）
  - 推文列表（卡片式展示）
    - 作者信息
    - 推文内容
    - 发布时间
    - 是否置顶标记
    - 操作按钮（查看详情、导出）
  - 分页功能
  - 导出功能（CSV/JSON）

### 4. 系统监控页面 (pages/3_⚙️_系统监控.py)
- **功能**: 监控系统运行状态
- **内容**:
  - 爬虫运行状态（运行中/停止）
  - Redis 连接状态
  - PostgreSQL 连接状态
  - 可用 Nitter 实例列表
  - 采集统计图表（时间序列）
  - 队列状态（待处理任务数）
  - 日志查看器（最近 100 条）

## 技术特性

### 路由设计
- Streamlit 使用基于文件的路由
- `pages/` 目录下的文件自动成为页面
- 文件名格式：`序号_emoji_页面名.py`
- 自动生成侧边栏导航

### 数据刷新策略
- 使用 `st.cache_data` 缓存数据库查询
- 设置 TTL（Time To Live）避免过期数据
- 提供手动刷新按钮

### 响应式设计
- 使用 Streamlit 布局组件（columns, expander, tabs）
- 适配不同屏幕尺寸
- 使用 Streamlit 主题系统

### 安全性
- 环境变量管理数据库连接
- 复用现有的配置系统（settings.py）
- 不暴露敏感信息

## 依赖包
```
streamlit>=1.29.0
pandas>=2.0.0
plotly>=5.18.0
streamlit-aggrid>=0.3.4  # 高级表格
streamlit-autorefresh>=0.0.1  # 自动刷新
```

## 启动命令
```bash
# 启动 Streamlit 应用
streamlit run streamlit_app/app.py --server.port 8501

# 后台启动爬虫
python main.py &
```

## 开发计划
1. ✅ 设计目录结构和页面布局
2. ⏳ 创建基础框架和主入口
3. ⏳ 实现用户管理页面
4. ⏳ 实现推文展示页面
5. ⏳ 实现系统监控页面
6. ⏳ 优化 UI/UX 和添加图表
7. ⏳ 编写使用文档
