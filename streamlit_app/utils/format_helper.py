"""
格式化辅助函数
提供各种数据格式化功能
"""
from datetime import datetime, timezone
from typing import Any


def format_datetime(dt: datetime, show_time: bool = True, show_timezone: bool = False) -> str:
    """
    格式化日期时间

    Args:
        dt: datetime 对象（应该是UTC时区）
        show_time: 是否显示时间
        show_timezone: 是否显示时区标识（UTC）

    Returns:
        格式化后的字符串
    """
    if dt is None:
        return "从未"

    # 如果datetime带有时区信息且不是UTC，转换为UTC
    if dt.tzinfo is not None and dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    if show_time:
        formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        if show_timezone:
            formatted += " UTC"
        return formatted
    else:
        return dt.strftime("%Y-%m-%d")


def format_relative_time(dt: datetime) -> str:
    """
    格式化为相对时间（如 "2 小时前"）

    Args:
        dt: datetime 对象

    Returns:
        相对时间字符串
    """
    if dt is None:
        return "从未"

    # 如果 dt 有时区信息，使用带时区的 now；否则使用不带时区的 now
    if dt.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()

    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} 年前"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} 个月前"
    elif diff.days > 0:
        return f"{diff.days} 天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} 小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} 分钟前"
    else:
        return "刚刚"


def format_number(num: int) -> str:
    """
    格式化数字（添加千位分隔符）

    Args:
        num: 数字

    Returns:
        格式化后的字符串
    """
    return f"{num:,}"


def format_tweet_content(content: str, max_length: int = 200) -> str:
    """
    格式化推文内容（截断）

    Args:
        content: 推文内容
        max_length: 最大长度

    Returns:
        格式化后的内容
    """
    if len(content) <= max_length:
        return content

    return content[:max_length] + "..."


def format_priority(priority: int) -> str:
    """
    格式化优先级

    Args:
        priority: 优先级数字 (1-10)

    Returns:
        优先级标签
    """
    if priority >= 8:
        return "⭐ 高"
    elif priority >= 5:
        return "📌 中"
    else:
        return "📋 低"


def format_status(is_active: bool) -> str:
    """
    格式化状态

    Args:
        is_active: 是否激活

    Returns:
        状态标签
    """
    return "✅ 启用" if is_active else "❌ 禁用"


def truncate_string(text: str, length: int = 50) -> str:
    """
    截断字符串

    Args:
        text: 原始文本
        length: 最大长度

    Returns:
        截断后的文本
    """
    if text is None:
        return ""

    if len(text) <= length:
        return text

    return text[:length] + "..."
