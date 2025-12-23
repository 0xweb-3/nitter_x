"""
推文展示页面
浏览和搜索已采集的推文
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.utils.db_helper import get_db_helper
from streamlit_app.utils.format_helper import (
    format_datetime,
    format_relative_time,
    format_tweet_content,
    format_number,
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="推文展示 - Nitter X",
    page_icon="📝",
    layout="wide",
)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### ⚙️ 页面设置")
    st.markdown("---")

    # 自动刷新选项
    auto_refresh = st.checkbox("自动刷新", value=False, key="tweets_auto_refresh")
    if auto_refresh:
        refresh_interval = st.slider(
            "刷新间隔（秒）",
            min_value=5,
            max_value=60,
            value=30,
            key="tweets_refresh_interval"
        )
        st_autorefresh(interval=refresh_interval * 1000, key="tweets_data_refresh")

    # 手动刷新按钮
    if st.button("🔄 手动刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        ### 💡 提示
        - 使用筛选器查找特定推文
        - 支持按用户、时间和关键词搜索
        - 可导出为 CSV 格式
        """
    )

# ==================== 数据加载 ====================


@st.cache_data(ttl=60)
def load_tweets(limit, offset, username, start_date, end_date, keyword):
    """加载推文列表（缓存 60 秒）"""
    db = get_db_helper()
    return db.get_tweets(limit, offset, username, start_date, end_date, keyword)


@st.cache_data(ttl=60)
def load_tweet_count(username, start_date, end_date, keyword):
    """加载推文总数（缓存 60 秒）"""
    db = get_db_helper()
    return db.get_tweet_count(username, start_date, end_date, keyword)


@st.cache_data(ttl=300)
def load_user_list():
    """加载用户列表（缓存 5 分钟）"""
    db = get_db_helper()
    users_df = db.get_all_users()
    return ["全部"] + users_df["username"].tolist()


# ==================== 主页面 ====================

# 初始化筛选器默认值（使用 session_state 保持状态）
if "filter_username" not in st.session_state:
    st.session_state.filter_username = None
if "filter_start_date" not in st.session_state:
    st.session_state.filter_start_date = None
if "filter_end_date" not in st.session_state:
    st.session_state.filter_end_date = None
if "filter_keyword" not in st.session_state:
    st.session_state.filter_keyword = None
if "page_size" not in st.session_state:
    st.session_state.page_size = 20

# 分页设置
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# 加载数据
try:
    total_count = load_tweet_count(
        st.session_state.filter_username,
        st.session_state.filter_start_date,
        st.session_state.filter_end_date,
        st.session_state.filter_keyword,
    )
    total_pages = max(1, (total_count + st.session_state.page_size - 1) // st.session_state.page_size)

    # 确保当前页不超出范围
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1

    # 顶部统计和分页控制
    col_stat, col_page_top = st.columns([3, 9])

    with col_stat:
        st.metric("📊 推文总数", format_number(total_count))

    with col_page_top:
        if total_count > 0:
            col_page1, col_page2, col_page3 = st.columns([2, 6, 2])

            with col_page1:
                if st.button("⬅️ 上一页", disabled=(st.session_state.current_page <= 1), key="top_prev"):
                    st.session_state.current_page -= 1
                    st.rerun()

            with col_page2:
                st.markdown(
                    f"<div style='text-align: center; padding-top: 0.5rem;'>"
                    f"第 <b>{st.session_state.current_page}</b> / {total_pages} 页"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_page3:
                if st.button("➡️ 下一页", disabled=(st.session_state.current_page >= total_pages), key="top_next"):
                    st.session_state.current_page += 1
                    st.rerun()

    st.markdown("---")

    if total_count == 0:
        st.info("📭 没有找到符合条件的推文，请尝试调整筛选条件（在页面底部）")
    else:
        # 加载当前页推文
        offset = (st.session_state.current_page - 1) * st.session_state.page_size
        tweets_df = load_tweets(
            st.session_state.page_size,
            offset,
            st.session_state.filter_username,
            st.session_state.filter_start_date,
            st.session_state.filter_end_date,
            st.session_state.filter_keyword,
        )

        # 展示推文（卡片式）
        for idx, tweet in tweets_df.iterrows():
            with st.container():
                # 推文卡片
                col_avatar, col_content = st.columns([1, 11])

                with col_avatar:
                    st.markdown(
                        f"""
                        <div style="text-align: center;">
                            <div style="
                                width: 48px;
                                height: 48px;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                                font-weight: bold;
                                font-size: 1.2rem;
                            ">
                                {tweet['author'][0].upper()}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_content:
                    # 作者和时间
                    col_header1, col_header2 = st.columns([10, 2])

                    with col_header1:
                        st.markdown(
                            f"**@{tweet['author']}** · "
                            f"<span style='color: #888;'>{format_relative_time(tweet['published_at'])}</span>",
                            unsafe_allow_html=True,
                        )

                    with col_header2:
                        # 查看原文链接
                        if tweet.get("tweet_url"):
                            st.markdown(
                                f'<a href="https://twitter.com{tweet["tweet_url"]}" target="_blank" '
                                f'style="text-decoration: none;">🔗 原文</a>',
                                unsafe_allow_html=True,
                            )

                    # 推文内容
                    st.markdown(f"{tweet['content']}")

                    # 元信息
                    st.caption(
                        f"📅 发布时间: {format_datetime(tweet['published_at'])} | "
                        f"💾 采集时间: {format_datetime(tweet['created_at'])} | "
                        f"🆔 ID: {tweet['tweet_id']}"
                    )

                st.markdown("---")

        # 底部分页
        col_page_bottom1, col_page_bottom2, col_page_bottom3 = st.columns([2, 6, 2])

        with col_page_bottom1:
            if st.button("⬅️ 上一页 ", key="prev_bottom", disabled=(st.session_state.current_page <= 1)):
                st.session_state.current_page -= 1
                st.rerun()

        with col_page_bottom2:
            # 页码跳转
            jump_page = st.number_input(
                "跳转到页",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.current_page,
                step=1,
                key="jump_page",
            )
            if st.button("跳转", key="jump_button"):
                st.session_state.current_page = jump_page
                st.rerun()

        with col_page_bottom3:
            if st.button("➡️ 下一页 ", key="next_bottom", disabled=(st.session_state.current_page >= total_pages)):
                st.session_state.current_page += 1
                st.rerun()

    # 筛选和设置区域（放到最后）
    st.markdown("---")
    st.markdown("---")

    with st.expander("🔍 筛选条件与设置", expanded=False):
        st.markdown("### 📝 推文筛选")
        st.markdown("配置筛选条件后，点击「应用筛选」按钮生效")

        col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 2])

        with col_filter1:
            # 用户筛选
            user_list = load_user_list()
            selected_user = st.selectbox("选择用户", user_list, index=0)
            filter_username = None if selected_user == "全部" else selected_user

        with col_filter2:
            # 时间范围筛选
            time_range = st.selectbox(
                "时间范围",
                ["全部", "今天", "最近 3 天", "最近 7 天", "最近 30 天", "自定义"],
            )

            if time_range == "今天":
                start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = None
            elif time_range == "最近 3 天":
                start_date = datetime.now(timezone.utc) - timedelta(days=3)
                end_date = None
            elif time_range == "最近 7 天":
                start_date = datetime.now(timezone.utc) - timedelta(days=7)
                end_date = None
            elif time_range == "最近 30 天":
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
                end_date = None
            elif time_range == "自定义":
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("开始日期", value=datetime.now(timezone.utc) - timedelta(days=7))
                    start_date = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                with col_date2:
                    end_date = st.date_input("结束日期", value=datetime.now(timezone.utc))
                    end_date = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
            else:
                start_date = None
                end_date = None

        with col_filter3:
            # 关键词搜索
            keyword = st.text_input("关键词搜索", placeholder="搜索推文内容...")
            filter_keyword = keyword if keyword else None

        st.markdown("---")

        # 分页大小设置
        page_size = st.selectbox("每页显示", [10, 20, 50, 100], index=1)

        st.markdown("---")

        col_filter_btn1, col_filter_btn2 = st.columns([1, 1])

        with col_filter_btn1:
            if st.button("🔍 应用筛选", use_container_width=True, type="primary"):
                # 保存筛选条件到 session_state
                st.session_state.filter_username = filter_username
                st.session_state.filter_start_date = start_date
                st.session_state.filter_end_date = end_date
                st.session_state.filter_keyword = filter_keyword
                st.session_state.page_size = page_size
                st.session_state.current_page = 1  # 重置到第一页
                st.cache_data.clear()
                st.rerun()

        with col_filter_btn2:
            if st.button("🔄 重置筛选", use_container_width=True):
                # 重置所有筛选条件
                st.session_state.filter_username = None
                st.session_state.filter_start_date = None
                st.session_state.filter_end_date = None
                st.session_state.filter_keyword = None
                st.session_state.page_size = 20
                st.session_state.current_page = 1
                st.cache_data.clear()
                st.rerun()

    # 导出功能
    st.markdown("---")

    with st.expander("📥 导出数据", expanded=False):
        st.markdown("### 💾 导出推文数据")

        col_export1, col_export2, col_export3 = st.columns([2, 2, 6])

        with col_export1:
            # 导出当前页
            if total_count > 0:
                csv_current = tweets_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="💾 导出当前页 (CSV)",
                    data=csv_current,
                    file_name=f"tweets_page_{st.session_state.current_page}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        with col_export2:
            # 导出全部（限制前 10000 条）
            if total_count > 0 and total_count <= 10000:
                all_tweets = load_tweets(
                    total_count,
                    0,
                    st.session_state.filter_username,
                    st.session_state.filter_start_date,
                    st.session_state.filter_end_date,
                    st.session_state.filter_keyword,
                )
                csv_all = all_tweets.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="💾 导出全部 (CSV)",
                    data=csv_all,
                    file_name=f"tweets_all_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            elif total_count > 10000:
                st.info(f"数据量过大（{format_number(total_count)} 条），请使用筛选后导出")

except Exception as e:
    st.error(f"❌ 加载推文失败: {str(e)}")
    st.info("💡 请确保数据库服务正常运行")
