"""
系统设置页面
管理 Bark 推送配置
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
from src.notification.bark_client import get_bark_client

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="系统设置 - Nitter X",
    page_icon="⚙️",
    layout="wide",
)

# ==================== 数据加载 ====================

@st.cache_data(ttl=30)
def load_bark_keys():
    """加载 Bark keys 列表"""
    db = get_db_helper()
    query = """
    SELECT
        id,
        key_name,
        bark_url,
        is_active,
        priority,
        last_push_at,
        push_count,
        notes,
        created_at
    FROM bark_keys
    ORDER BY priority DESC, created_at DESC
    """
    results = db.pg_client.execute_query(query)
    return pd.DataFrame(results) if results else pd.DataFrame()


@st.cache_data(ttl=30)
def load_push_settings():
    """加载推送配置"""
    db = get_db_helper()
    query = "SELECT setting_key, setting_value, description FROM push_settings"
    results = db.pg_client.execute_query(query)
    return {row['setting_key']: row for row in results}


def save_push_setting(key: str, value: str) -> bool:
    """保存推送配置"""
    db = get_db_helper()
    query = """
    UPDATE push_settings
    SET setting_value = %s, updated_at = NOW()
    WHERE setting_key = %s
    """
    return db.pg_client.execute_update(query, (value, key)) > 0


# ==================== 主页面 ====================

st.title("⚙️ 系统设置")
st.markdown("管理 Bark 推送配置和系统参数")

st.markdown("---")

# ==================== Tab 布局 ====================
tab_push, tab_bark_keys = st.tabs(["📲 推送配置", "🔑 Bark Keys 管理"])

# ==================== Tab 1: 推送配置 ====================
with tab_push:
    st.subheader("📲 推送配置")

    # 加载当前配置
    settings = load_push_settings()

    # 全局推送开关
    current_enabled = settings.get('push_enabled', {}).get('setting_value', 'false') == 'true'
    push_enabled = st.toggle(
        "启用 Bark 推送",
        value=current_enabled,
        help="开启后，符合条件的推文会自动推送到配置的 Bark keys"
    )

    if push_enabled != current_enabled:
        if save_push_setting('push_enabled', 'true' if push_enabled else 'false'):
            st.success("✅ 推送开关已更新")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("❌ 更新失败")

    st.markdown("---")

    # 推送级别配置
    st.markdown("#### 推送级别")
    current_grades = settings.get('push_grades', {}).get('setting_value', 'P0,P1,P2')
    default_grades = [g.strip() for g in current_grades.split(',')]

    selected_grades = st.multiselect(
        "选择需要推送的级别",
        options=['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
        default=default_grades,
        help="只有选中级别的推文会触发推送"
    )

    if st.button("💾 保存级别配置", type="primary"):
        new_grades = ','.join(selected_grades)
        if save_push_setting('push_grades', new_grades):
            st.success(f"✅ 推送级别已更新为: {new_grades}")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("❌ 更新失败")

    st.markdown("---")

    # 推送图标配置
    st.markdown("#### 推送图标")
    current_icon = settings.get('push_icon', {}).get('setting_value', '')

    new_icon = st.text_input(
        "推送图标 URL",
        value=current_icon,
        help="推送消息显示的图标（建议使用加密货币相关图标）"
    )

    if new_icon != current_icon:
        if st.button("💾 保存图标配置"):
            if save_push_setting('push_icon', new_icon):
                st.success("✅ 推送图标已更新")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("❌ 更新失败")

    # 预览图标
    if new_icon:
        try:
            st.image(new_icon, width=64, caption="图标预览")
        except:
            st.warning("⚠️ 图标加载失败，请检查 URL")

# ==================== Tab 2: Bark Keys 管理 ====================
with tab_bark_keys:
    st.subheader("🔑 Bark Keys 管理")

    # 操作按钮
    col_action1, col_action2, col_action3 = st.columns([2, 2, 6])

    with col_action1:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with col_action2:
        if st.button("➕ 添加 Bark Key", use_container_width=True, type="primary"):
            st.session_state.show_add_bark_form = True

    st.markdown("---")

    # 添加 Bark Key 表单
    if st.session_state.get("show_add_bark_form", False):
        with st.expander("➕ 添加新的 Bark Key", expanded=True):
            with st.form("add_bark_form"):
                col_form1, col_form2 = st.columns([3, 3])

                with col_form1:
                    new_key_name = st.text_input(
                        "Key 名称 *",
                        placeholder="例如：我的iPhone",
                        help="用于识别这个 Bark key（必填）"
                    )

                with col_form2:
                    new_bark_url = st.text_input(
                        "Bark URL 或 Key *",
                        placeholder="https://api.day.app/xxx/ 或 xxx",
                        help="完整的 Bark URL 或仅 key 部分（必填）"
                    )

                col_form3, col_form4 = st.columns([3, 3])

                with col_form3:
                    new_priority = st.slider(
                        "优先级",
                        min_value=0,
                        max_value=10,
                        value=0,
                        help="优先级（预留字段）"
                    )

                with col_form4:
                    new_notes = st.text_input("备注", placeholder="可选")

                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])

                with col_btn1:
                    submit_add = st.form_submit_button("✅ 添加", use_container_width=True)

                with col_btn2:
                    cancel_add = st.form_submit_button("❌ 取消", use_container_width=True)

                with col_btn3:
                    test_before_add = st.form_submit_button("🧪 测试后添加", use_container_width=True)

                if submit_add or test_before_add:
                    if not new_key_name or not new_bark_url:
                        st.error("❌ Key 名称和 Bark URL 不能为空")
                    else:
                        # 如果是测试后添加，先测试
                        if test_before_add:
                            with st.spinner("正在测试 Bark 推送..."):
                                bark_client = get_bark_client()
                                test_result = bark_client.test_notification(new_bark_url)

                                if not test_result['success']:
                                    st.error(f"❌ 测试失败: {test_result['message']}")
                                    st.stop()
                                else:
                                    st.success("✅ 测试成功！正在添加...")

                        # 添加到数据库
                        db = get_db_helper()
                        query = """
                        INSERT INTO bark_keys (key_name, bark_url, priority, notes, is_active)
                        VALUES (%s, %s, %s, %s, TRUE)
                        ON CONFLICT (bark_url) DO NOTHING
                        """
                        rows = db.pg_client.execute_update(
                            query,
                            (new_key_name, new_bark_url, new_priority, new_notes)
                        )

                        if rows > 0:
                            st.success(f"✅ 成功添加 Bark Key: {new_key_name}")
                            st.cache_data.clear()
                            st.session_state.show_add_bark_form = False
                            st.rerun()
                        else:
                            st.error(f"❌ 添加失败（Key 可能已存在）")

                if cancel_add:
                    st.session_state.show_add_bark_form = False
                    st.rerun()

    # Bark Keys 列表
    st.markdown("### 📋 Bark Keys 列表")

    try:
        df = load_bark_keys()

        if df.empty:
            st.info("📭 暂无 Bark Key，请先添加")
        else:
            # 统计
            total_keys = len(df)
            active_keys = len(df[df["is_active"] == True])
            total_pushes = df["push_count"].sum()

            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("总 Keys", total_keys)
            with col_stat2:
                st.metric("启用 Keys", active_keys)
            with col_stat3:
                st.metric("总推送次数", int(total_pushes))

            st.markdown("---")

            # 格式化展示
            display_df = df.copy()
            display_df["状态"] = display_df["is_active"].apply(
                lambda x: "✅ 启用" if x else "❌ 禁用"
            )
            display_df["最后推送"] = display_df["last_push_at"].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "从未"
            )
            display_df["创建时间"] = display_df["created_at"].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "未知"
            )

            # 选择显示列
            display_df = display_df[
                ["key_name", "bark_url", "状态", "push_count", "最后推送", "创建时间", "notes"]
            ]
            display_df.columns = ["名称", "Bark URL", "状态", "推送次数", "最后推送", "创建时间", "备注"]

            # 使用 AgGrid 展示
            gb = GridOptionsBuilder.from_dataframe(display_df)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_default_column(resizable=True, filterable=True, sortable=True)
            gb.configure_selection(selection_mode="single", use_checkbox=True)
            gb.configure_column("名称", pinned="left", width=150)
            gb.configure_column("Bark URL", width=300)
            gb.configure_column("状态", width=100)
            gb.configure_column("推送次数", width=100)
            gb.configure_column("最后推送", width=180)
            gb.configure_column("创建时间", width=180)

            gridOptions = gb.build()

            grid_response = AgGrid(
                display_df,
                gridOptions=gridOptions,
                update_on=["selectionChanged"],
                height=400,
                theme="streamlit",
            )

            # 选中行操作
            selected_rows = grid_response["selected_rows"]

            st.markdown("---")

            if selected_rows is not None and len(selected_rows) > 0:
                selected_name = selected_rows.iloc[0]["名称"]
                original_row = df[df["key_name"] == selected_name].iloc[0]

                st.markdown(f"### ⚙️ 操作 Key: **{selected_name}**")

                col_op1, col_op2, col_op3, col_op4 = st.columns([2, 2, 2, 4])

                with col_op1:
                    # 启用/禁用
                    current_status = original_row["is_active"]
                    if current_status:
                        if st.button("❌ 禁用", use_container_width=True):
                            db = get_db_helper()
                            query = "UPDATE bark_keys SET is_active = FALSE WHERE id = %s"
                            # 转换 numpy.int64 为 Python int
                            if db.pg_client.execute_update(query, (int(original_row['id']),)):
                                st.success(f"✅ 已禁用: {selected_name}")
                                st.cache_data.clear()
                                st.rerun()
                    else:
                        if st.button("✅ 启用", use_container_width=True, type="primary"):
                            db = get_db_helper()
                            query = "UPDATE bark_keys SET is_active = TRUE WHERE id = %s"
                            # 转换 numpy.int64 为 Python int
                            if db.pg_client.execute_update(query, (int(original_row['id']),)):
                                st.success(f"✅ 已启用: {selected_name}")
                                st.cache_data.clear()
                                st.rerun()

                with col_op2:
                    if st.button("🧪 测试推送", use_container_width=True):
                        with st.spinner("正在测试..."):
                            bark_client = get_bark_client()
                            result = bark_client.test_notification(original_row['bark_url'])

                            if result['success']:
                                st.success("✅ 测试推送成功！请检查你的设备")
                            else:
                                st.error(f"❌ 测试失败: {result['message']}")

                with col_op3:
                    if st.button("🗑️ 删除", use_container_width=True):
                        # 转换 numpy.int64 为 Python int
                        st.session_state.confirm_delete_bark = int(original_row['id'])

                # 确认删除
                # 转换 numpy.int64 为 Python int 进行比较
                if st.session_state.get("confirm_delete_bark") == int(original_row['id']):
                    st.warning(f"⚠️ 确认删除 Bark Key **{selected_name}** 吗？")
                    col_confirm1, col_confirm2 = st.columns([1, 5])

                    with col_confirm1:
                        if st.button("✅ 确认删除"):
                            db = get_db_helper()
                            query = "DELETE FROM bark_keys WHERE id = %s"
                            # 转换 numpy.int64 为 Python int
                            if db.pg_client.execute_update(query, (int(original_row['id']),)):
                                st.success(f"✅ 已删除: {selected_name}")
                                st.session_state.confirm_delete_bark = None
                                st.cache_data.clear()
                                st.rerun()

                    with col_confirm2:
                        if st.button("❌ 取消"):
                            st.session_state.confirm_delete_bark = None
                            st.rerun()

            else:
                st.markdown("### ⚙️ Key 操作")
                st.info("👆 请在上方表格中勾选一个 Key，然后在此处进行操作")

    except Exception as e:
        st.error(f"❌ 加载失败: {str(e)}")
