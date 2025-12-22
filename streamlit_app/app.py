"""
Nitter X 推文采集系统 - Streamlit Web UI
主入口页面（首页）
"""
import sys
from pathlib import Path

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.utils.db_helper import get_db_helper
from streamlit_app.utils.format_helper import (
    format_datetime,
    format_number,
    format_relative_time,
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Nitter X 推文采集系统",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 样式设置 ====================
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1DA1F2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1DA1F2;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.image("https://abs.twimg.com/icons/apple-touch-icon-192x192.png", width=100)
    st.title("🐦 Nitter X")
    st.markdown("---")

    # 手动刷新按钮
    if st.button("🔄 手动刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        ### 📖 使用指南
        - **用户管理**: 添加/管理监听的 Twitter 用户
        - **推文展示**: 浏览和搜索已采集的推文
        - **系统监控**: 查看系统运行状态和统计
        """
    )

# ==================== 数据加载 ====================


@st.cache_data(ttl=60)
def load_system_stats():
    """加载系统统计数据（缓存 60 秒）"""
    db = get_db_helper()
    return db.get_system_stats()


@st.cache_data(ttl=300)
def load_daily_stats(days=7):
    """加载每日统计数据（缓存 5 分钟）"""
    db = get_db_helper()
    return db.get_daily_tweet_stats(days=days)


@st.cache_data(ttl=300)
def load_user_stats(limit=10):
    """加载用户统计数据（缓存 5 分钟）"""
    db = get_db_helper()
    return db.get_user_tweet_stats(limit=limit)


# ==================== 主页面 ====================

# 标题
st.markdown('<div class="main-header">🐦 Nitter X 推文采集系统</div>', unsafe_allow_html=True)

st.markdown("### 📊 系统概览")

# 加载统计数据
try:
    stats = load_system_stats()

    # 指标卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="👥 监听用户",
            value=format_number(stats["user_count"]),
            delta=None,
        )

    with col2:
        st.metric(
            label="📝 推文总数",
            value=format_number(stats["tweet_count"]),
            delta=None,
        )

    with col3:
        st.metric(
            label="🆕 今日新增",
            value=format_number(stats["today_count"]),
            delta=f"+{stats['today_count']}",
        )

    with col4:
        st.metric(
            label="⏰ 最近采集",
            value=format_relative_time(stats["last_crawl_time"]),
            delta=None,
        )

    st.markdown("---")

    # 图表区域
    col_left, col_right = st.columns(2)

    # 左侧：每日推文统计
    with col_left:
        st.markdown("### 📈 每日推文趋势")

        daily_stats = load_daily_stats(days=14)

        if not daily_stats.empty:
            fig = px.bar(
                daily_stats,
                x="date",
                y="count",
                title="最近 14 天推文采集量",
                labels={"date": "日期", "count": "推文数"},
                color="count",
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                xaxis_title="日期",
                yaxis_title="推文数",
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无统计数据")

    # 右侧：Top 用户统计
    with col_right:
        st.markdown("### 🏆 Top 活跃用户")

        user_stats = load_user_stats(limit=10)

        if not user_stats.empty:
            fig = px.bar(
                user_stats,
                x="tweet_count",
                y="author",
                orientation="h",
                title="推文数量 Top 10",
                labels={"author": "用户", "tweet_count": "推文数"},
                color="tweet_count",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(
                xaxis_title="推文数",
                yaxis_title="用户",
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无统计数据")

    st.markdown("---")

    # 快速操作区域
    st.markdown("### ⚡ 快速操作")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("➕ 添加用户", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Users.py")

    with col_b:
        if st.button("📝 查看推文", use_container_width=True):
            st.switch_page("pages/2_Tweets.py")

    with col_c:
        if st.button("⚙️ 系统监控", use_container_width=True):
            st.switch_page("pages/3_Monitor.py")

    # 系统信息
    st.markdown("---")
    st.markdown("### ℹ️ 系统信息")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.info(f"📊 **数据库**: PostgreSQL\n\n💾 **缓存**: Redis\n\n🔄 **队列任务**: {stats['queue_length']} 个待处理")

    with info_col2:
        if stats["last_crawl_time"]:
            last_time_str = format_datetime(stats["last_crawl_time"])
            st.success(
                f"✅ **爬虫状态**: 运行中\n\n⏰ **最后采集**: {last_time_str}\n\n📝 **今日采集**: {stats['today_count']} 条"
            )
        else:
            st.warning("⚠️ **爬虫状态**: 未运行\n\n💡 请先启动爬虫程序")

except Exception as e:
    st.error(f"❌ 加载数据失败: {str(e)}")
    st.info("💡 请确保数据库和 Redis 服务正常运行")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        Nitter X 推文采集系统 | Built with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
