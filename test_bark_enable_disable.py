"""
测试 Bark key 的启用/禁用功能
验证 numpy.int64 类型转换是否正确
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.storage.postgres_client import get_postgres_client
import pandas as pd
import numpy as np


def test_numpy_int64_conversion():
    """测试 numpy.int64 到 Python int 的转换"""
    print("=" * 80)
    print("测试 numpy.int64 类型转换")
    print("=" * 80)

    pg_client = get_postgres_client()

    # 查询所有 Bark keys
    query = "SELECT id, key_name, is_active FROM bark_keys ORDER BY id"
    results = pg_client.execute_query(query)

    if not results:
        print("❌ 没有找到 Bark keys，请先添加")
        return False

    # 转换为 DataFrame（模拟 Streamlit AgGrid 的行为）
    df = pd.DataFrame(results)
    print(f"\n找到 {len(df)} 个 Bark keys")
    print(df)

    # 获取第一行（模拟选中操作）
    if len(df) > 0:
        first_row = df.iloc[0]
        print(f"\n选中第一行:")
        print(f"  ID: {first_row['id']} (类型: {type(first_row['id'])})")
        print(f"  名称: {first_row['key_name']}")
        print(f"  状态: {first_row['is_active']}")

        # 测试类型转换
        bark_id = first_row['id']

        # 检查是否是 numpy.int64
        if isinstance(bark_id, np.int64):
            print(f"\n✓ 确认是 numpy.int64 类型")

            # 转换为 Python int
            python_int = int(bark_id)
            print(f"✓ 转换后类型: {type(python_int)}")

            # 测试数据库更新（切换状态）
            current_status = first_row['is_active']
            new_status = not current_status

            print(f"\n测试数据库更新:")
            print(f"  当前状态: {current_status}")
            print(f"  目标状态: {new_status}")

            update_query = "UPDATE bark_keys SET is_active = %s WHERE id = %s"

            try:
                # 使用转换后的 Python int 和 bool
                rows = pg_client.execute_update(update_query, (bool(new_status), python_int))
                print(f"✅ 更新成功！影响 {rows} 行")

                # 验证更新
                verify_query = "SELECT is_active FROM bark_keys WHERE id = %s"
                result = pg_client.execute_query(verify_query, (python_int,))
                if result and result[0]['is_active'] == new_status:
                    print(f"✅ 验证成功：状态已更改为 {new_status}")

                    # 恢复原状态（也需要转换 bool 类型）
                    pg_client.execute_update(update_query, (bool(current_status), python_int))
                    print(f"✅ 已恢复原状态")
                    return True
                else:
                    print(f"❌ 验证失败")
                    return False

            except Exception as e:
                print(f"❌ 更新失败: {e}")
                return False
        else:
            print(f"⚠️  不是 numpy.int64 类型: {type(bark_id)}")
            return False

    return False


def main():
    print("\n" + "=" * 80)
    print("Bark Key 启用/禁用功能测试")
    print("=" * 80 + "\n")

    success = test_numpy_int64_conversion()

    print("\n" + "=" * 80)
    if success:
        print("✅ 测试通过！numpy.int64 类型转换正常工作")
    else:
        print("❌ 测试失败")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
