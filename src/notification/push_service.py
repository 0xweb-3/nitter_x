"""
推送服务

统一管理推文的 Bark 推送逻辑
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.notification.bark_client import get_bark_client
from src.storage.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)


class PushService:
    """推送服务类"""

    def __init__(self):
        self.bark_client = get_bark_client()
        self.pg_client = get_postgres_client()

    def _get_push_settings(self) -> Dict:
        """
        获取推送配置

        Returns:
            配置字典
        """
        query = "SELECT setting_key, setting_value FROM push_settings"
        results = self.pg_client.execute_query(query)

        settings = {}
        for row in results:
            key = row['setting_key']
            value = row['setting_value']

            # 转换布尔值
            if value.lower() in ('true', 'false'):
                settings[key] = value.lower() == 'true'
            else:
                settings[key] = value

        return settings

    def _get_active_bark_keys(self) -> List[Dict]:
        """
        获取所有启用的 Bark keys

        Returns:
            Bark key 列表
        """
        query = """
        SELECT id, key_name, bark_url
        FROM bark_keys
        WHERE is_active = TRUE
        ORDER BY priority DESC, id
        """
        return self.pg_client.execute_query(query)

    def _update_bark_key_stats(self, bark_key_id: int):
        """
        更新 Bark key 推送统计

        Args:
            bark_key_id: Bark key ID
        """
        query = """
        UPDATE bark_keys
        SET last_push_at = NOW(), push_count = push_count + 1
        WHERE id = %s
        """
        self.pg_client.execute_update(query, (bark_key_id,))

    def _record_push_history(
        self,
        tweet_id: str,
        bark_key_id: int,
        grade: str,
        push_status: str,
        error_message: str = None,
        response_data: dict = None
    ):
        """
        记录推送历史

        Args:
            tweet_id: 推文ID
            bark_key_id: Bark key ID
            grade: 推文级别
            push_status: 推送状态
            error_message: 错误信息
            response_data: 响应数据
        """
        import json

        query = """
        INSERT INTO push_history (
            tweet_id, bark_key_id, grade, push_status,
            error_message, response_data
        ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """
        params = (
            tweet_id,
            bark_key_id,
            grade,
            push_status,
            error_message,
            json.dumps(response_data) if response_data else None
        )
        self.pg_client.execute_update(query, params)

    def _format_push_message(
        self,
        grade: str,
        summary: str,
        keywords: List[str],
        tweet_url: str,
        author: str
    ) -> tuple:
        """
        格式化推送消息

        Args:
            grade: 推文级别
            summary: 摘要
            keywords: 关键词列表
            tweet_url: 原文链接
            author: 作者

        Returns:
            (title, content) 元组
        """
        # 级别emoji映射
        grade_emoji = {
            'P0': '🔴',
            'P1': '🟠',
            'P2': '🟡',
            'P3': '🟢',
            'P4': '🔵',
            'P5': '⚪',
            'P6': '⚫'
        }

        emoji = grade_emoji.get(grade, '📌')
        title = f"{emoji} {grade} 级推文 - @{author}"

        # 构建内容
        content_parts = []

        # 摘要
        if summary:
            content_parts.append(f"📝 {summary}")

        # 关键词
        if keywords:
            keywords_str = ", ".join([f"#{kw}" for kw in keywords])
            content_parts.append(f"🏷️ {keywords_str}")

        content = "\n\n".join(content_parts)

        return title, content

    def should_push(self, grade: str) -> bool:
        """
        判断是否应该推送

        Args:
            grade: 推文级别

        Returns:
            是否应该推送
        """
        settings = self._get_push_settings()

        # 检查全局开关
        if not settings.get('push_enabled', False):
            logger.debug("推送功能已禁用")
            return False

        # 检查级别是否在推送范围内
        push_grades = settings.get('push_grades', 'P0,P1,P2').split(',')
        push_grades = [g.strip() for g in push_grades]

        if grade not in push_grades:
            logger.debug(f"级别 {grade} 不在推送范围内: {push_grades}")
            return False

        return True

    def push_tweet(
        self,
        tweet_id: str,
        grade: str,
        summary: str,
        keywords: List[str],
        tweet_url: str,
        author: str
    ) -> Dict:
        """
        推送推文通知

        Args:
            tweet_id: 推文ID
            grade: 推文级别
            summary: 摘要
            keywords: 关键词列表
            tweet_url: 原文链接
            author: 作者

        Returns:
            推送结果统计
        """
        # 检查是否应该推送
        if not self.should_push(grade):
            return {
                "pushed": False,
                "reason": "不满足推送条件",
                "success_count": 0,
                "failed_count": 0
            }

        # 获取启用的 Bark keys
        bark_keys = self._get_active_bark_keys()

        if not bark_keys:
            logger.warning("没有启用的 Bark key，跳过推送")
            return {
                "pushed": False,
                "reason": "没有启用的 Bark key",
                "success_count": 0,
                "failed_count": 0
            }

        # 格式化推送消息
        title, content = self._format_push_message(
            grade=grade,
            summary=summary,
            keywords=keywords,
            tweet_url=tweet_url,
            author=author
        )

        # 获取推送图标
        settings = self._get_push_settings()
        icon = settings.get('push_icon', 'https://em-content.zobj.net/source/apple/391/coin_1fa99.png')

        # 批量推送
        success_count = 0
        failed_count = 0

        logger.info(f"开始向 {len(bark_keys)} 个 Bark key 推送推文: {tweet_id}")

        for bark_key in bark_keys:
            bark_key_id = bark_key['id']
            bark_url = bark_key['bark_url']
            key_name = bark_key['key_name']

            try:
                # 发送推送
                result = self.bark_client.send_notification(
                    bark_url=bark_url,
                    title=title,
                    content=content,
                    url=tweet_url,
                    icon=icon,
                    sound="default",
                    group=f"Nitter-X-{grade}"
                )

                if result['success']:
                    logger.info(f"✓ 推送成功: {key_name}")
                    success_count += 1

                    # 更新统计
                    self._update_bark_key_stats(bark_key_id)

                    # 记录历史
                    self._record_push_history(
                        tweet_id=tweet_id,
                        bark_key_id=bark_key_id,
                        grade=grade,
                        push_status='success',
                        response_data=result.get('response')
                    )
                else:
                    logger.error(f"✗ 推送失败: {key_name}, 原因: {result['message']}")
                    failed_count += 1

                    # 记录失败历史
                    self._record_push_history(
                        tweet_id=tweet_id,
                        bark_key_id=bark_key_id,
                        grade=grade,
                        push_status='failed',
                        error_message=result['message'],
                        response_data=result.get('response')
                    )

            except Exception as e:
                logger.error(f"✗ 推送异常: {key_name}, 错误: {e}")
                failed_count += 1

                # 记录异常历史
                self._record_push_history(
                    tweet_id=tweet_id,
                    bark_key_id=bark_key_id,
                    grade=grade,
                    push_status='failed',
                    error_message=str(e)
                )

        logger.info(
            f"推文 {tweet_id} 推送完成: 成功 {success_count}/{len(bark_keys)}, "
            f"失败 {failed_count}/{len(bark_keys)}"
        )

        return {
            "pushed": True,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_keys": len(bark_keys)
        }


# 全局单例
_push_service = None


def get_push_service() -> PushService:
    """获取推送服务单例"""
    global _push_service
    if _push_service is None:
        _push_service = PushService()
    return _push_service
