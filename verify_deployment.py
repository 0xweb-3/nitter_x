#!/usr/bin/env python3
"""
部署验证脚本

用于验证 Nitter X 项目在新环境中的部署状态
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.storage.postgres_client import get_postgres_client
from src.storage.redis_client import get_redis_client
from src.utils.logger import setup_logger

logger = setup_logger("deployment_check", log_file="logs/deployment_check.log")


def check_database():
    """检查数据库连接和表结构"""
    print("\n📊 检查 PostgreSQL 数据库...")

    try:
        pg = get_postgres_client()

        # 检查连接
        result = pg.execute_query("SELECT version()")
        if result:
            print("  ✅ PostgreSQL 连接成功")
            print(f"     版本: {result[0]['version'].split(',')[0]}")

        # 检查必需的表
        tables = {
            "tweets": [
                "tweet_id", "author", "content", "published_at",
                "tweet_url", "media_urls", "has_media", "processing_status"
            ],
            "watched_users": ["username", "display_name", "priority", "is_active", "notes"],
            "processed_tweets": [
                "tweet_id", "grade", "summary_cn", "keywords",
                "translated_content", "embedding", "processing_time_ms"
            ],
            "tag_definitions": ["category", "name", "weight"],
            "processing_logs": ["tweet_id", "stage", "status"]
        }

        for table_name, expected_columns in tables.items():
            # 检查表是否存在
            query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """
            columns = pg.execute_query(query, (table_name,))

            if not columns:
                print(f"  ❌ 表 '{table_name}' 不存在")
                continue

            column_names = [col['column_name'] for col in columns]
            print(f"  ✅ 表 '{table_name}' 存在 ({len(column_names)} 个字段)")

            # 检查关键字段
            missing_columns = [col for col in expected_columns if col not in column_names]
            if missing_columns:
                print(f"     ⚠️  缺少字段: {', '.join(missing_columns)}")
            else:
                print(f"     ✅ 所有关键字段存在")

        # 检查 processing_status 枚举类型
        enum_query = """
        SELECT enumlabel
        FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname = 'processing_status_enum'
        ORDER BY enumsortorder
        """
        enum_values = pg.execute_query(enum_query)

        if enum_values:
            values = [row['enumlabel'] for row in enum_values]
            print(f"  ✅ 枚举类型 'processing_status_enum' 存在")
            print(f"     值: {', '.join(values)}")
        else:
            print(f"  ❌ 枚举类型 'processing_status_enum' 不存在")

        # 检查 processed_tweets 表的 grade 字段约束
        constraint_query = """
        SELECT conname, pg_get_constraintdef(oid) as condef
        FROM pg_constraint
        WHERE conrelid = 'processed_tweets'::regclass
        AND contype = 'c'
        """
        constraints = pg.execute_query(constraint_query)

        if constraints:
            for constraint in constraints:
                if 'grade' in constraint['condef']:
                    print(f"  ✅ grade 字段约束存在")
                    if 'P0' in constraint['condef'] and 'P6' in constraint['condef']:
                        print(f"     ✅ 使用 P0-P6 分级系统")
                    else:
                        print(f"     ⚠️  可能使用旧的 A-F 分级系统")

        return True

    except Exception as e:
        print(f"  ❌ PostgreSQL 检查失败: {e}")
        return False


def check_redis():
    """检查 Redis 连接"""
    print("\n📦 检查 Redis 缓存...")

    try:
        redis = get_redis_client()

        # 测试连接
        redis.set_cache("deployment_check", "ok", expire=10)
        value = redis.get_cache("deployment_check")

        if value == "ok":
            print("  ✅ Redis 连接成功")

            # 检查实例缓存
            instances_key = "nitter:instances:available"
            instances = redis.get_cache(instances_key)

            if instances:
                import json
                instances_data = json.loads(instances)
                print(f"  ✅ Nitter 实例缓存存在 ({len(instances_data)} 个实例)")
            else:
                print(f"  ⚠️  Nitter 实例缓存为空（首次运行正常）")

            return True
        else:
            print("  ❌ Redis 读写测试失败")
            return False

    except Exception as e:
        print(f"  ❌ Redis 检查失败: {e}")
        return False


def check_llm_config():
    """检查 LLM 配置"""
    print("\n🤖 检查 LLM 配置...")

    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("LLM_API_KEY")
        api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1")
        model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

        if api_key and api_key != "your-api-key":
            print(f"  ✅ LLM_API_KEY 已配置")
        else:
            print(f"  ⚠️  LLM_API_KEY 未配置（推文处理功能不可用）")
            print(f"     请在 .env 文件中设置 LLM_API_KEY")
            return False

        print(f"  ℹ️  LLM_API_URL: {api_url}")
        print(f"  ℹ️  LLM_MODEL: {model}")

        # 尝试测试 LLM 客户端初始化（不实际调用 API）
        try:
            from src.processor.llm_client import get_llm_client
            client = get_llm_client()
            print(f"  ✅ LLM 客户端初始化成功")
            return True
        except Exception as e:
            print(f"  ⚠️  LLM 客户端初始化失败: {e}")
            print(f"     如需使用推文处理功能，请检查 LLM 配置")
            return False

    except Exception as e:
        print(f"  ⚠️  LLM 配置检查失败: {e}")
        print(f"     如需使用推文处理功能，请配置 .env 文件中的 LLM 参数")
        return False


def check_directories():
    """检查必要的目录"""
    print("\n📁 检查目录结构...")

    required_dirs = [
        "logs",
        "data",
        "data/models",
        "migrations",
        "src",
        "src/crawler",
        "src/processor",
        "src/storage",
        "streamlit_app",
        "streamlit_app/pages"
    ]

    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ (不存在)")
            all_exist = False

    return all_exist


def main():
    print("=" * 60)
    print("🚀 Nitter X 部署验证")
    print("=" * 60)

    results = {
        "数据库": check_database(),
        "Redis": check_redis(),
        "LLM配置": check_llm_config(),
        "目录结构": check_directories(),
    }

    print("\n" + "=" * 60)
    print("📋 验证结果汇总")
    print("=" * 60)

    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 所有检查通过！部署成功！")
        print("\n下一步:")
        print("  1. 添加监听用户: python manage_users.py add <username>")
        print("  2. 启动 Streamlit: streamlit run streamlit_app/app.py")
        print("  3. 启动采集: python main.py")
        print("  4. 启动处理: python process_worker.py")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请根据上述提示进行修复。")
        print("\n常见问题:")
        print("  - 数据库连接失败: 检查 docker-compose 服务是否运行")
        print("  - 表不存在: 确认 Docker 容器首次启动时运行了初始化脚本")
        print("  - LLM 配置错误: 检查 .env 文件中的 LLM_API_KEY 配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
