"""
用户管理工具 - 添加/管理关注用户
"""

import argparse
import logging

from src.utils.logger import setup_logger
from src.storage.postgres_client import get_postgres_client

logger = setup_logger("manage_users", log_file="logs/manage.log")


def list_users():
    """列出所有关注用户"""
    pg_client = get_postgres_client()

    try:
        users = pg_client.execute_query(
            "SELECT * FROM watched_users ORDER BY priority DESC, username"
        )

        if not users:
            print("没有关注用户")
            return

        print(f"\n共有 {len(users)} 个关注用户:\n")
        print(f"{'ID':<5} {'用户名':<20} {'显示名称':<30} {'优先级':<8} {'状态':<8} {'最后采集时间'}")
        print("-" * 100)

        for user in users:
            status = "活跃" if user["is_active"] else "禁用"
            last_crawled = user["last_crawled_at"] or "从未"

            print(
                f"{user['id']:<5} {user['username']:<20} {user['display_name'] or '':<30} "
                f"{user['priority']:<8} {status:<8} {last_crawled}"
            )

    finally:
        pg_client.close()


def add_user(username: str, display_name: str = "", priority: int = 0):
    """添加关注用户"""
    pg_client = get_postgres_client()

    try:
        success = pg_client.add_watched_user(username, display_name, priority)

        if success:
            print(f"✓ 成功添加用户: {username}")
        else:
            print(f"✗ 用户已存在: {username}")

    finally:
        pg_client.close()


def remove_user(username: str):
    """移除关注用户"""
    pg_client = get_postgres_client()

    try:
        rows = pg_client.execute_update(
            "DELETE FROM watched_users WHERE username = %s", (username,)
        )

        if rows > 0:
            print(f"✓ 成功移除用户: {username}")
        else:
            print(f"✗ 用户不存在: {username}")

    finally:
        pg_client.close()


def toggle_user(username: str, active: bool):
    """启用/禁用用户"""
    pg_client = get_postgres_client()

    try:
        rows = pg_client.execute_update(
            "UPDATE watched_users SET is_active = %s WHERE username = %s",
            (active, username),
        )

        if rows > 0:
            status = "启用" if active else "禁用"
            print(f"✓ 成功{status}用户: {username}")
        else:
            print(f"✗ 用户不存在: {username}")

    finally:
        pg_client.close()


def main():
    parser = argparse.ArgumentParser(description="用户管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list 命令
    subparsers.add_parser("list", help="列出所有关注用户")

    # add 命令
    add_parser = subparsers.add_parser("add", help="添加关注用户")
    add_parser.add_argument("username", help="用户名")
    add_parser.add_argument("--name", default="", help="显示名称")
    add_parser.add_argument("--priority", type=int, default=0, help="优先级")

    # remove 命令
    remove_parser = subparsers.add_parser("remove", help="移除关注用户")
    remove_parser.add_argument("username", help="用户名")

    # enable 命令
    enable_parser = subparsers.add_parser("enable", help="启用用户")
    enable_parser.add_argument("username", help="用户名")

    # disable 命令
    disable_parser = subparsers.add_parser("disable", help="禁用用户")
    disable_parser.add_argument("username", help="用户名")

    args = parser.parse_args()

    if args.command == "list":
        list_users()
    elif args.command == "add":
        add_user(args.username, args.name, args.priority)
    elif args.command == "remove":
        remove_user(args.username)
    elif args.command == "enable":
        toggle_user(args.username, True)
    elif args.command == "disable":
        toggle_user(args.username, False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
