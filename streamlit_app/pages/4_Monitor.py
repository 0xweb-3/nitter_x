"""
系统监控页面
监控系统运行状态和统计信息
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.utils.db_helper import get_db_helper
from streamlit_app.utils.format_helper import (
    format_datetime,
    format_number,
    format_relative_time,
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="系统监控 - Nitter X",
    page_icon="⚙️",
    layout="wide",
)

# ==================== 自动刷新 ====================
# 每 10 秒自动刷新一次
st_autorefresh(interval=10 * 1000, key="system_monitor_refresh")

# ==================== 数据加载 ====================


@st.cache_data(ttl=10)
def load_system_stats():
    """加载系统统计（缓存 10 秒）"""
    db = get_db_helper()
    return db.get_system_stats()


@st.cache_data(ttl=30)
def load_daily_stats(days=30):
    """加载每日统计（缓存 30 秒）"""
    db = get_db_helper()
    return db.get_daily_tweet_stats(days=days)


@st.cache_data(ttl=60)
def check_connections():
    """检查服务连接状态（缓存 60 秒）"""
    db = get_db_helper()
    redis_ok = db.check_redis_connection()

    # 检查 PostgreSQL（尝试简单查询）
    try:
        db.pg_client.execute_query("SELECT 1")
        postgres_ok = True
    except Exception:
        postgres_ok = False

    return {"redis": redis_ok, "postgres": postgres_ok}


@st.cache_data(ttl=300)
def load_nitter_instances():
    """加载 Nitter 实例列表（缓存 5 分钟）"""
    db = get_db_helper()
    return db.get_nitter_instances()


# ==================== 主页面 ====================

st.title("⚙️ 系统监控")
st.markdown("实时监控系统运行状态")

st.markdown("---")

# 服务状态检查
st.markdown("### 🔌 服务状态")

connections = check_connections()

col_status1, col_status2, col_status3, col_status4 = st.columns(4)

with col_status1:
    if connections["postgres"]:
        st.success("✅ PostgreSQL 连接正常")
    else:
        st.error("❌ PostgreSQL 连接失败")

with col_status2:
    if connections["redis"]:
        st.success("✅ Redis 连接正常")
    else:
        st.error("❌ Redis 连接失败")

with col_status3:
    # 简单判断爬虫是否在运行（根据最近采集时间）
    stats = load_system_stats()
    if stats["last_crawl_time"]:
        from datetime import timedelta

        # 使用带时区的 datetime
        time_diff = datetime.now(timezone.utc) - stats["last_crawl_time"]
        if time_diff < timedelta(minutes=10):
            st.success("✅ 爬虫运行中")
        else:
            st.warning(f"⚠️ 爬虫可能已停止\n\n最后采集: {format_relative_time(stats['last_crawl_time'])}")
    else:
        st.info("ℹ️ 爬虫未运行")

with col_status4:
    # 检查处理 Worker 状态（根据待处理推文数量）
    stats = load_system_stats()
    if stats["pending_count"] == 0:
        st.success("✅ 处理队列为空")
    elif stats["pending_count"] < 100:
        st.info(f"ℹ️ 处理中\n\n待处理: {stats['pending_count']} 条")
    else:
        st.warning(f"⚠️ 队列积压\n\n待处理: {stats['pending_count']} 条")

st.markdown("---")

# 系统指标
st.markdown("### 📊 系统指标")

try:
    stats = load_system_stats()

    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)

    with col_metric1:
        st.metric(
            label="👥 监听用户数",
            value=format_number(stats["user_count"]),
        )

    with col_metric2:
        st.metric(
            label="📝 推文总数",
            value=format_number(stats["tweet_count"]),
        )

    with col_metric3:
        st.metric(
            label="🆕 今日新增",
            value=format_number(stats["today_count"]),
        )

    with col_metric4:
        st.metric(
            label="📥 待处理推文",
            value=format_number(stats["pending_count"]),
        )

    st.markdown("---")

    # 采集趋势图表
    st.markdown("### 📈 采集趋势")

    daily_stats = load_daily_stats(days=30)

    if not daily_stats.empty:
        # 使用 Plotly 绘制折线图
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=daily_stats["date"],
                y=daily_stats["count"],
                mode="lines+markers",
                name="推文数",
                line=dict(color="#1DA1F2", width=2),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor="rgba(29, 161, 242, 0.1)",
            )
        )

        fig.update_layout(
            title="最近 30 天推文采集趋势",
            xaxis_title="日期",
            yaxis_title="推文数",
            height=400,
            hovermode="x unified",
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无统计数据")

    st.markdown("---")

    # Nitter 实例状态
    st.markdown("### 🌐 可用 Nitter 实例")

    instances = load_nitter_instances()

    if instances:
        st.success(f"✅ 共有 **{len(instances)}** 个可用实例")

        # 展示前 10 个实例
        display_instances = instances[:10]

        for idx, instance in enumerate(display_instances, 1):
            col_inst1, col_inst2, col_inst3 = st.columns([1, 6, 2])

            with col_inst1:
                st.markdown(f"**#{idx}**")

            with col_inst2:
                st.markdown(f"[{instance['url']}]({instance['url']})")

            with col_inst3:
                response_time = instance.get("response_time", 0)
                if response_time > 0:
                    st.caption(f"⚡ {response_time:.0f}ms")
                else:
                    st.caption("⚡ N/A")

        if len(instances) > 10:
            st.info(f"显示前 10 个实例，共 {len(instances)} 个")
    else:
        st.warning("⚠️ 暂无可用实例，请检查实例发现服务")

    st.markdown("---")

    # 最近采集活动
    st.markdown("### 📝 最近采集活动")

    if stats["last_crawl_time"]:
        col_activity1, col_activity2 = st.columns(2)

        with col_activity1:
            st.info(
                f"""
                **⏰ 最后采集时间**

                {format_datetime(stats["last_crawl_time"])}

                ({format_relative_time(stats["last_crawl_time"])})
                """
            )

        with col_activity2:
            st.success(
                f"""
                **🆕 今日采集**

                共采集 **{format_number(stats["today_count"])}** 条推文

                还有 **{format_number(stats["pending_count"])}** 条待处理
                """
            )
    else:
        st.info("暂无采集记录")

    st.markdown("---")

    # 系统配置信息
    st.markdown("### 🛠️ 系统配置")

    from src.config.settings import settings

    col_config1, col_config2 = st.columns(2)

    with col_config1:
        st.markdown(
            f"""
            **⏱️ 采集配置**
            - 采集循环间隔: `{settings.CRAWL_INTERVAL}` 秒
            - 用户采集间隔: `{settings.CRAWL_USER_INTERVAL}` 秒
            - 单用户预估时间: `{settings.ESTIMATED_TIME_PER_USER}` 秒
            """
        )

    with col_config2:
        st.markdown(
            f"""
            **🌐 网络配置**
            - 请求超时: `{settings.CRAWLER_TIMEOUT}` 秒
            - 重试次数: `{settings.HTTP_RETRY_COUNT}` 次
            - 重试延迟: `{settings.HTTP_RETRY_DELAY}` 秒
            - 请求延迟: `{settings.CRAWLER_DELAY}` 秒
            """
        )

except Exception as e:
    st.error(f"❌ 加载系统信息失败: {str(e)}")
    st.info("💡 请确保数据库和 Redis 服务正常运行")

# 操作按钮
st.markdown("---")
st.markdown("### 🎛️ 系统操作")

col_op1, col_op2, col_op3 = st.columns([2, 2, 6])

with col_op1:
    if st.button("🔄 刷新数据", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

with col_op2:
    if st.button("📊 查看日志", use_container_width=True):
        st.info("💡 日志查看功能开发中...")

# 页脚说明
st.markdown("---")
st.caption("ℹ️ 页面每 10 秒自动刷新一次")
