"""
用户管理页面
管理监听的 Twitter 用户
"""
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.utils.db_helper import get_db_helper
from streamlit_app.utils.format_helper import (
    format_datetime,
    format_priority,
    format_status,
    format_number,
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="用户管理 - Nitter X",
    page_icon="👥",
    layout="wide",
)

# ==================== 数据加载 ====================


@st.cache_data(ttl=30)
def load_users():
    """加载用户列表（缓存 30 秒）"""
    db = get_db_helper()
    return db.get_all_users()


# ==================== 主页面 ====================

st.title("👥 用户管理")
st.markdown("管理监听的 Twitter 用户，控制采集行为")

st.markdown("---")

# 操作区域
col_action1, col_action2, col_action3 = st.columns([2, 2, 6])

with col_action1:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_action2:
    if st.button("➕ 添加用户", use_container_width=True, type="primary"):
        st.session_state.show_add_form = True

st.markdown("---")

# 添加用户表单（折叠式）
if st.session_state.get("show_add_form", False):
    with st.expander("➕ 添加新用户", expanded=True):
        with st.form("add_user_form"):
            col_form1, col_form2, col_form3 = st.columns([3, 2, 2])

            with col_form1:
                new_username = st.text_input(
                    "用户名",
                    placeholder="输入 Twitter 用户名（不含 @）",
                    help="例如：elonmusk",
                )

            with col_form2:
                new_priority = st.slider(
                    "优先级",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="优先级越高，采集频率越高",
                )

            with col_form3:
                new_notes = st.text_input("备注", placeholder="可选")

            col_btn1, col_btn2 = st.columns([1, 5])

            with col_btn1:
                submit_add = st.form_submit_button("✅ 添加", use_container_width=True)

            with col_btn2:
                cancel_add = st.form_submit_button("❌ 取消", use_container_width=True)

            if submit_add:
                if not new_username:
                    st.error("❌ 用户名不能为空")
                else:
                    db = get_db_helper()
                    success = db.add_user(new_username, new_priority, new_notes)

                    if success:
                        st.success(f"✅ 成功添加用户: {new_username}")
                        st.cache_data.clear()
                        st.session_state.show_add_form = False
                        st.rerun()
                    else:
                        st.error(f"❌ 添加失败（用户可能已存在）: {new_username}")

            if cancel_add:
                st.session_state.show_add_form = False
                st.rerun()

# 用户列表
st.markdown("### 📋 用户列表")

try:
    df = load_users()

    if df.empty:
        st.info("📭 暂无监听用户，请先添加用户")
    else:
        # 数据统计
        total_users = len(df)
        active_users = len(df[df["is_active"] == True])
        total_tweets = df["tweet_count"].sum()

        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("总用户数", format_number(total_users))
        with col_stat2:
            st.metric("启用用户", format_number(active_users))
        with col_stat3:
            st.metric("总推文数", format_number(total_tweets))

        st.markdown("---")

        # 格式化数据展示
        display_df = df.copy()
        display_df["优先级"] = display_df["priority"].apply(format_priority)
        display_df["状态"] = display_df["is_active"].apply(format_status)
        display_df["最后采集"] = display_df["last_crawled_at"].apply(
            lambda x: format_datetime(x) if x else "从未"
        )
        display_df["推文数"] = display_df["tweet_count"].apply(format_number)
        display_df["创建时间"] = display_df["created_at"].apply(format_datetime)

        # 选择显示列
        display_df = display_df[
            ["username", "优先级", "状态", "最后采集", "推文数", "创建时间", "notes"]
        ]
        display_df.columns = ["用户名", "优先级", "状态", "最后采集", "推文数", "创建时间", "备注"]

        # 使用 AgGrid 展示表格
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_default_column(
            resizable=True,
            filterable=True,
            sortable=True,
            editable=False,
        )
        gb.configure_selection(selection_mode="single", use_checkbox=True)
        gb.configure_column("用户名", pinned="left", width=150)
        gb.configure_column("优先级", width=100)
        gb.configure_column("状态", width=100)
        gb.configure_column("最后采集", width=180)
        gb.configure_column("推文数", width=100)
        gb.configure_column("创建时间", width=180)
        gb.configure_column("备注", width=200)

        gridOptions = gb.build()

        grid_response = AgGrid(
            display_df,
            gridOptions=gridOptions,
            update_on=["selectionChanged"],
            height=500,
            theme="streamlit",
            allow_unsafe_jscode=True,
        )

        # 选中行操作
        selected_rows = grid_response["selected_rows"]

        if selected_rows is not None and len(selected_rows) > 0:
            selected_username = selected_rows.iloc[0]["用户名"]
            original_row = df[df["username"] == selected_username].iloc[0]

            st.markdown("---")
            st.markdown(f"### ⚙️ 操作用户: **{selected_username}**")

            col_op1, col_op2, col_op3, col_op4 = st.columns([2, 2, 2, 4])

            with col_op1:
                # 启用/禁用
                current_status = original_row["is_active"]
                if current_status:
                    if st.button("❌ 禁用用户", use_container_width=True):
                        db = get_db_helper()
                        if db.update_user(selected_username, is_active=False):
                            st.success(f"✅ 已禁用用户: {selected_username}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ 操作失败")
                else:
                    if st.button("✅ 启用用户", use_container_width=True, type="primary"):
                        db = get_db_helper()
                        if db.update_user(selected_username, is_active=True):
                            st.success(f"✅ 已启用用户: {selected_username}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ 操作失败")

            with col_op2:
                if st.button("🗑️ 删除用户", use_container_width=True):
                    st.session_state.confirm_delete = selected_username

            with col_op3:
                if st.button("✏️ 编辑信息", use_container_width=True):
                    st.session_state.edit_user = selected_username

            # 确认删除
            if st.session_state.get("confirm_delete") == selected_username:
                st.warning(f"⚠️ 确认删除用户 **{selected_username}** 吗？（推文数据不会删除）")
                col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 8])

                with col_confirm1:
                    if st.button("✅ 确认删除"):
                        db = get_db_helper()
                        if db.delete_user(selected_username):
                            st.success(f"✅ 已删除用户: {selected_username}")
                            st.session_state.confirm_delete = None
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ 删除失败")

                with col_confirm2:
                    if st.button("❌ 取消"):
                        st.session_state.confirm_delete = None
                        st.rerun()

            # 编辑信息表单
            if st.session_state.get("edit_user") == selected_username:
                with st.form("edit_user_form"):
                    st.markdown(f"#### 编辑用户: {selected_username}")

                    col_edit1, col_edit2 = st.columns(2)

                    with col_edit1:
                        edit_priority = st.slider(
                            "优先级",
                            min_value=1,
                            max_value=10,
                            value=int(original_row["priority"]),
                        )

                    with col_edit2:
                        edit_notes = st.text_input(
                            "备注",
                            value=original_row["notes"] if original_row["notes"] else "",
                        )

                    col_edit_btn1, col_edit_btn2 = st.columns([1, 5])

                    with col_edit_btn1:
                        submit_edit = st.form_submit_button("✅ 保存", use_container_width=True)

                    with col_edit_btn2:
                        cancel_edit = st.form_submit_button("❌ 取消", use_container_width=True)

                    if submit_edit:
                        db = get_db_helper()
                        if db.update_user(selected_username, edit_priority, edit_notes):
                            st.success(f"✅ 已更新用户: {selected_username}")
                            st.session_state.edit_user = None
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ 更新失败")

                    if cancel_edit:
                        st.session_state.edit_user = None
                        st.rerun()

except Exception as e:
    st.error(f"❌ 加载用户列表失败: {str(e)}")
    st.info("💡 请确保数据库服务正常运行")
