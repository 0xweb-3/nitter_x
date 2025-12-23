"""
数据库迁移：将分级从 A-F 改为 P0-P6

将 processed_tweets 表的 grade 字段从单字母改为价格影响等级
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.storage.postgres_client import get_postgres_client
from src.utils.logger import setup_logger

logger = setup_logger("migration", log_file="logs/migration.log")


def migrate():
    """执行迁移"""
    pg = get_postgres_client()

    logger.info("开始数据库迁移：更新分级从 A-F 到 P0-P6")

    try:
        # 1. 删除旧的检查约束
        logger.info("1. 删除旧的 grade 检查约束")
        query1 = """
        ALTER TABLE processed_tweets
        DROP CONSTRAINT IF EXISTS processed_tweets_grade_check
        """
        pg.execute_update(query1)
        logger.info("  ✓ 旧检查约束已删除")

        # 2. 修改 grade 字段类型
        logger.info("2. 修改 grade 字段类型")
        query2 = """
        ALTER TABLE processed_tweets
        ALTER COLUMN grade TYPE VARCHAR(2)
        """
        pg.execute_update(query2)
        logger.info("  ✓ grade 字段类型已更新为 VARCHAR(2)")

        # 3. 添加新的检查约束
        logger.info("3. 添加新的 grade 检查约束（P0-P6）")
        query3 = """
        ALTER TABLE processed_tweets
        ADD CONSTRAINT processed_tweets_grade_check
        CHECK (grade IN ('P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6'))
        """
        pg.execute_update(query3)
        logger.info("  ✓ 新检查约束已添加")

        # 4. 更新注释说明
        logger.info("4. 更新表注释")
        query4 = """
        COMMENT ON COLUMN processed_tweets.grade IS
        '价格影响等级：P0(最高)/P1(强信号)/P2(结构性)/P3(宏观)/P4(叙事)/P5(噪音)/P6(舍弃)'
        """
        pg.execute_update(query4)
        logger.info("  ✓ 表注释已更新")

        logger.info("✅ 数据库迁移完成：分级体系已从 A-F 更新为 P0-P6")
        logger.info("⚠️ 注意：已有数据的分级值需要手动转换或重新处理")

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        raise


def rollback():
    """回滚迁移"""
    pg = get_postgres_client()

    logger.info("开始回滚：恢复 A-F 分级体系")

    try:
        # 删除新约束
        logger.info("1. 删除 P0-P6 检查约束")
        query1 = """
        ALTER TABLE processed_tweets
        DROP CONSTRAINT IF EXISTS processed_tweets_grade_check
        """
        pg.execute_update(query1)

        # 恢复字段类型
        logger.info("2. 恢复 grade 字段类型")
        query2 = """
        ALTER TABLE processed_tweets
        ALTER COLUMN grade TYPE CHAR(1)
        """
        pg.execute_update(query2)

        # 添加旧约束
        logger.info("3. 恢复 A-F 检查约束")
        query3 = """
        ALTER TABLE processed_tweets
        ADD CONSTRAINT processed_tweets_grade_check
        CHECK (grade IN ('A', 'B', 'C', 'D', 'E', 'F'))
        """
        pg.execute_update(query3)

        logger.info("✅ 回滚完成：已恢复 A-F 分级体系")

    except Exception as e:
        logger.error(f"❌ 回滚失败: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移：更新分级体系")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
