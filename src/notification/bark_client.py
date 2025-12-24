"""
Bark 推送客户端

提供 iOS Bark 推送功能
"""

import logging
import requests
from typing import List, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class BarkClient:
    """Bark 推送客户端"""

    def __init__(self, timeout: int = 10):
        """
        初始化 Bark 客户端

        Args:
            timeout: HTTP 请求超时时间（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Nitter-X/1.0 Bark Client'
        })

    def _normalize_url(self, bark_url: str) -> str:
        """
        规范化 Bark URL

        Args:
            bark_url: Bark URL或key

        Returns:
            完整的 Bark API URL（不含消息部分）
        """
        bark_url = bark_url.strip()

        # 如果是完整URL
        if bark_url.startswith('http'):
            # 确保以 / 结尾
            return bark_url if bark_url.endswith('/') else bark_url + '/'
        else:
            # 如果只是key，构建完整URL
            return f"https://api.day.app/{bark_url}/"

    def _build_push_url(
        self,
        bark_url: str,
        title: str,
        content: str,
        url: str = None,
        icon: str = None,
        sound: str = None,
        group: str = None
    ) -> str:
        """
        构建 Bark 推送 URL

        Args:
            bark_url: Bark基础URL
            title: 标题
            content: 内容
            url: 点击跳转链接
            icon: 推送图标URL
            sound: 推送声音
            group: 分组名称

        Returns:
            完整的推送URL
        """
        base_url = self._normalize_url(bark_url)

        # URL编码
        encoded_title = quote(title)
        encoded_content = quote(content)

        # 构建基础URL
        push_url = f"{base_url}{encoded_title}/{encoded_content}"

        # 添加可选参数
        params = []
        if url:
            params.append(f"url={quote(url)}")
        if icon:
            params.append(f"icon={quote(icon)}")
        if sound:
            params.append(f"sound={sound}")
        if group:
            params.append(f"group={quote(group)}")

        if params:
            push_url += "?" + "&".join(params)

        return push_url

    def send_notification(
        self,
        bark_url: str,
        title: str,
        content: str,
        url: str = None,
        icon: str = None,
        sound: str = "default",
        group: str = "Nitter-X"
    ) -> Dict:
        """
        发送 Bark 推送

        Args:
            bark_url: Bark URL或key
            title: 推送标题
            content: 推送内容
            url: 点击跳转链接
            icon: 推送图标URL
            sound: 推送声音（默认：default）
            group: 推送分组（默认：Nitter-X）

        Returns:
            推送结果字典：
            {
                "success": bool,
                "message": str,
                "response": dict/None
            }
        """
        try:
            # 构建推送URL
            push_url = self._build_push_url(
                bark_url=bark_url,
                title=title,
                content=content,
                url=url,
                icon=icon,
                sound=sound,
                group=group
            )

            logger.debug(f"发送 Bark 推送: {push_url[:100]}...")

            # 发送GET请求
            response = self.session.get(push_url, timeout=self.timeout)

            # 检查响应
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    # Bark API 返回格式：{"code": 200, "message": "success", "timestamp": ...}
                    if response_data.get("code") == 200:
                        logger.info(f"Bark 推送成功: {title}")
                        return {
                            "success": True,
                            "message": "推送成功",
                            "response": response_data
                        }
                    else:
                        error_msg = response_data.get("message", "未知错误")
                        logger.error(f"Bark API 返回错误: {error_msg}")
                        return {
                            "success": False,
                            "message": f"Bark API 错误: {error_msg}",
                            "response": response_data
                        }
                except Exception as e:
                    logger.error(f"解析 Bark 响应失败: {e}")
                    return {
                        "success": False,
                        "message": f"解析响应失败: {str(e)}",
                        "response": None
                    }
            else:
                logger.error(f"Bark HTTP 请求失败: {response.status_code}")
                return {
                    "success": False,
                    "message": f"HTTP 错误: {response.status_code}",
                    "response": None
                }

        except requests.exceptions.Timeout:
            logger.error(f"Bark 推送超时: {bark_url}")
            return {
                "success": False,
                "message": "请求超时",
                "response": None
            }
        except Exception as e:
            logger.error(f"Bark 推送异常: {e}")
            return {
                "success": False,
                "message": f"推送异常: {str(e)}",
                "response": None
            }

    def test_notification(self, bark_url: str) -> Dict:
        """
        测试 Bark 推送配置

        Args:
            bark_url: Bark URL或key

        Returns:
            测试结果字典
        """
        return self.send_notification(
            bark_url=bark_url,
            title="Nitter-X 测试推送",
            content="如果你收到这条消息，说明 Bark 配置正确！",
            icon="https://em-content.zobj.net/source/apple/391/check-mark-button_2705.png",
            sound="bell"
        )

    def close(self):
        """关闭会话"""
        self.session.close()


# 全局单例
_bark_client = None


def get_bark_client() -> BarkClient:
    """获取 Bark 客户端单例"""
    global _bark_client
    if _bark_client is None:
        _bark_client = BarkClient()
    return _bark_client
