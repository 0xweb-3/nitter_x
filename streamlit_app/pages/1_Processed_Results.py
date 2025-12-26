"""
推文处理结果页面

展示经过 LLM 处理后的推文分级、摘要、关键词等信息
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

from src.storage.postgres_client import get_postgres_client
from streamlit_app.utils.format_helper import (
    format_datetime,
    format_relative_time,
    format_number,
)

# 页面配置
st.set_page_config(
    page_title="推文处理结果",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 推文处理结果")
st.markdown("查看经过 LLM 智能处理后的推文分级和摘要信息")

# 分级定义（价格影响导向）
GRADE_INFO = {
    "P0": {"label": "🔴 P0 - 价格驱动事件", "color": "#ff0000", "desc": "已发生或即将确定发生，必然触发资金行为"},
    "P1": {"label": "🟠 P1 - 强信号事件", "color": "#ff6600", "desc": "尚未完全落地，但市场共识认为极可能发生"},
    "P2": {"label": "🟡 P2 - 结构性影响", "color": "#ffcc00", "desc": "不会立刻拉盘/砸盘，但会改变价格中枢"},
    "P3": {"label": "🟢 P3 - 宏观政策", "color": "#66cc00", "desc": "不直接针对crypto，但影响风险资产定价"},
    "P4": {"label": "🔵 P4 - 叙事情绪", "color": "#3399ff", "desc": "会影响市场讲什么故事，但资金反应不稳定"},
    "P5": {"label": "⚪ P5 - 信息噪音", "color": "#999999", "desc": "和crypto有关，但几乎不改变任何资金决策"},
    "P6": {"label": "⚫ P6 - 可舍弃", "color": "#333333", "desc": "无价格影响的内容"},
}

# 侧边栏 - 筛选器
st.sidebar.header("📊 筛选与设置")

# 分级筛选
selected_grades = st.sidebar.multiselect(
    "按分级筛选",
    options=list(GRADE_INFO.keys()),
    default=["P0", "P1", "P2"],
    format_func=lambda x: GRADE_INFO[x]["label"],
)

# 每页显示数量
page_size = st.sidebar.selectbox(
    "每页显示数量",
    options=[10, 20, 50, 100],
    index=1,
)

# 自动刷新（checkbox）
auto_refresh = st.sidebar.checkbox("自动刷新（20秒）", value=False)

# 初始化分页状态
if "processed_page" not in st.session_state:
    st.session_state.processed_page = 0

# 获取数据
@st.cache_data(ttl=60)
def load_processed_data(grades, limit, offset):
    """加载处理结果数据"""
    pg = get_postgres_client()

    if not grades:
        return []

    # 如果选择了多个分级，需要修改查询
    if len(grades) == 1:
        return pg.get_processed_tweets(grade=grades[0], limit=limit, offset=offset)
    else:
        # 多分级查询
        placeholders = ','.join(['%s'] * len(grades))
        query = f"""
        SELECT
            p.id,
            p.tweet_id,
            t.author,
            t.content,
            t.tweet_url,
            t.media_urls,
            t.has_media,
            p.grade,
            p.summary_cn,
            p.keywords,
            p.translated_content,
            p.processing_time_ms,
            p.processed_at,
            t.published_at
        FROM processed_tweets p
        JOIN tweets t ON p.tweet_id = t.tweet_id
        WHERE p.grade IN ({placeholders})
        ORDER BY t.published_at DESC
        LIMIT %s OFFSET %s
        """
        params = tuple(grades) + (limit, offset)
        result = pg.execute_query(query, params)
        return result if result else []

@st.cache_data(ttl=60)
def get_stats():
    """获取统计数据"""
    pg = get_postgres_client()

    query = """
    SELECT
        grade,
        COUNT(*) as count
    FROM processed_tweets
    GROUP BY grade
    ORDER BY grade
    """

    result = pg.execute_query(query)
    return result if result else []

@st.cache_data(ttl=60)
def get_pending_count():
    """获取待处理推文数量"""
    pg = get_postgres_client()

    query = """
    SELECT COUNT(*) as pending_count
    FROM tweets
    WHERE processing_status = 'pending'
    """

    result = pg.execute_query(query)
    if result and len(result) > 0:
        return result[0]['pending_count']
    return 0

@st.cache_data(ttl=60)
def get_last_processing_time():
    """获取最近一次处理的耗时"""
    pg = get_postgres_client()

    query = """
    SELECT processing_time_ms
    FROM processed_tweets
    ORDER BY processed_at DESC
    LIMIT 1
    """

    result = pg.execute_query(query)
    if result and len(result) > 0:
        return result[0]['processing_time_ms']
    return None

# 加载数据
if selected_grades:
    offset = st.session_state.processed_page * page_size
    processed_tweets = load_processed_data(selected_grades, page_size, offset)

    if processed_tweets:
        # 顶部分页控制
        col_info, col_nav = st.columns([3, 9])

        with col_info:
            st.write(f"📄 第 {st.session_state.processed_page + 1} 页 | 每页 {page_size} 条")

        with col_nav:
            nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 2, 1])

            with nav_col1:
                if st.button("⬅️ 上一页", disabled=st.session_state.processed_page == 0):
                    st.session_state.processed_page -= 1
                    st.rerun()

            with nav_col2:
                if st.button("➡️ 下一页", disabled=len(processed_tweets) < page_size):
                    st.session_state.processed_page += 1
                    st.rerun()

            with nav_col3:
                jump_page = st.number_input(
                    "跳转到页码",
                    min_value=1,
                    value=st.session_state.processed_page + 1,
                    step=1,
                    label_visibility="collapsed"
                )

            with nav_col4:
                if st.button("跳转"):
                    st.session_state.processed_page = jump_page - 1
                    st.rerun()

        st.divider()

        # 显示推文卡片
        for tweet in processed_tweets:
            grade = tweet['grade']
            grade_info = GRADE_INFO[grade]

            with st.container():
                # 卡片头部
                col_header1, col_header2 = st.columns([6, 6])

                with col_header1:
                    st.markdown(f"### {grade_info['label']}")

                with col_header2:
                    st.caption(f"⏱️ 处理于 {format_relative_time(tweet['processed_at'])} | 耗时 {tweet['processing_time_ms']}ms")

                # 作者和发布时间
                col_meta1, col_meta2 = st.columns([6, 6])

                with col_meta1:
                    st.markdown(f"**作者**: @{tweet['author']} | **发布于**: {format_datetime(tweet['published_at'])}")

                with col_meta2:
                    # 源推文链接
                    if tweet.get('tweet_url'):
                        st.markdown(f"**🔗 原文链接**: [{tweet['tweet_url']}]({tweet['tweet_url']})")

                # 处理结果
                if grade in ['P0', 'P1', 'P2']:
                    # 主要展示：摘要和关键词
                    # 摘要
                    if tweet.get('summary_cn'):
                        st.markdown(f"**📝 摘要**: {tweet['summary_cn']}")

                    # 关键词
                    if tweet.get('keywords'):
                        try:
                            keywords = json.loads(tweet['keywords']) if isinstance(tweet['keywords'], str) else tweet['keywords']
                            if keywords:
                                keyword_tags = " ".join([f"`{kw}`" for kw in keywords])
                                st.markdown(f"**🏷️ 关键词**: {keyword_tags}")
                        except:
                            pass

                    # 次要展示：原文和翻译（折叠）
                    translated = tweet.get('translated_content')
                    original = tweet.get('content', '')

                    # 检查是否有有效的翻译内容
                    has_valid_translation = (
                        translated and
                        translated.strip() != '' and
                        translated != original and
                        len(translated) > 10
                    )

                    # 原文展示（始终折叠）
                    with st.expander("📄 查看原文", expanded=False):
                        st.write(original)

                    # 如果有翻译，也折叠展示
                    if has_valid_translation:
                        with st.expander("🌐 查看中文翻译", expanded=False):
                            st.write(translated)

                    # 媒体资源
                    if tweet.get('has_media') and tweet.get('media_urls'):
                        try:
                            media_urls = json.loads(tweet['media_urls']) if isinstance(tweet['media_urls'], str) else tweet['media_urls']
                            if media_urls:
                                st.markdown("**📷 媒体资源:**")
                                for i, media_url in enumerate(media_urls):
                                    with st.expander(f"🖼️ 媒体 {i+1}", expanded=False):
                                        if media_url.endswith(('.mp4', '.webm', '.mov')):
                                            st.video(media_url)
                                        else:
                                            st.image(media_url, use_container_width=True)
                        except Exception as e:
                            st.caption(f"⚠️ 媒体加载失败: {str(e)}")

                else:
                    # P3/P4/P5/P6 级推文，展示原文
                    with st.expander("📄 查看原文", expanded=False):
                        st.write(tweet['content'])
                    st.caption(f"ℹ️ {grade_info['desc']}")

                st.divider()

        # 底部分页控制
        col_nav_bottom = st.columns([1, 1, 8])

        with col_nav_bottom[0]:
            if st.button("⬅️ 上一页 ", key="prev_bottom", disabled=st.session_state.processed_page == 0):
                st.session_state.processed_page -= 1
                st.rerun()

        with col_nav_bottom[1]:
            if st.button("➡️ 下一页 ", key="next_bottom", disabled=len(processed_tweets) < page_size):
                st.session_state.processed_page += 1
                st.rerun()

    else:
        st.info(f"暂无 {', '.join([GRADE_INFO[g]['label'] for g in selected_grades])} 的处理结果")

else:
    st.warning("⚠️ 请至少选择一个分级进行筛选")

# 统计概览（放在底部）
st.divider()

# 添加刷新按钮
col_title, col_refresh = st.columns([10, 2])
with col_title:
    st.subheader("📈 统计概览（所有级别）")
with col_refresh:
    if st.button("🔄 刷新统计", key="refresh_stats"):
        st.cache_data.clear()
        st.rerun()

# 获取待处理数量和最近处理耗时
pending_count = get_pending_count()
last_processing_time = get_last_processing_time()

# 显示处理状态信息
col_status1, col_status2 = st.columns(2)
with col_status1:
    st.metric(
        label="⏳ 剩余待处理",
        value=format_number(pending_count),
        help="当前 processing_status = 'pending' 的推文数量"
    )
with col_status2:
    if last_processing_time is not None:
        # 将毫秒转换为秒
        processing_time_sec = last_processing_time / 1000.0
        st.metric(
            label="⚡ 上一轮单条耗时",
            value=f"{processing_time_sec:.2f}s",
            help="最近一条处理记录的耗时"
        )
    else:
        st.metric(
            label="⚡ 上一轮单条耗时",
            value="暂无数据",
            help="尚未有处理记录"
        )

stats_data = get_stats()
if stats_data:
    # 创建统计字典
    stats_dict = {row['grade']: row['count'] for row in stats_data}

    # 显示总计
    total_count = sum(stats_dict.values())
    st.caption(f"总处理数: {format_number(total_count)} 条")

    # 分级统计
    cols = st.columns(len(GRADE_INFO))

    for idx, (grade, info) in enumerate(GRADE_INFO.items()):
        count = stats_dict.get(grade, 0)
        with cols[idx]:
            st.metric(
                label=info["label"],
                value=format_number(count),
                help=info["desc"]
            )
else:
    st.info("暂无处理结果数据")

# 页脚信息
st.divider()
st.caption("💡 提示：运行 `python process_worker.py` 启动处理 Worker 来处理待处理推文")

# 自动刷新逻辑（在页面渲染完成后执行）
if auto_refresh:
    import time
    time.sleep(20)
    st.rerun()
