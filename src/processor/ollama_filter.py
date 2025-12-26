"""
Ollama 本地筛选器

使用本地 Ollama 模型快速筛选推文，过滤不相关内容以降低远程 LLM 成本
"""

import logging
from typing import Optional, Dict

from src.config.settings import settings
from src.processor.prompts import TweetProcessingPrompts

logger = logging.getLogger(__name__)


class OllamaFilter:
    """Ollama 本地筛选器，用于快速过滤不相关推文"""

    def __init__(self):
        """初始化 Ollama 筛选器"""
        self.enabled = False
        self.client = None
        self.stats = {
            "total_filtered": 0,      # 总筛选次数
            "relevant_count": 0,       # 判定为相关的次数
            "irrelevant_count": 0,     # 判定为不相关的次数
            "error_count": 0,          # 错误次数
            "total_time_ms": 0,        # 总耗时
            "avg_time_ms": 0,          # 平均耗时
        }

        # 如果配置未启用，直接返回
        if not settings.OLLAMA_ENABLED:
            logger.info("Ollama 筛选器未启用（OLLAMA_ENABLED=false）")
            return

        try:
            logger.info("正在初始化 Ollama 筛选器...")

            # 使用原生 ollama 库
            import ollama
            self.ollama_client = ollama

            # 检测可用性
            if self._check_availability():
                self.enabled = True
                logger.info("✓ Ollama 筛选器初始化成功并可用")
            else:
                logger.warning("✗ Ollama 筛选器初始化失败，已禁用本地筛选")

        except Exception as e:
            logger.error(f"✗ Ollama 筛选器初始化异常: {e}")
            logger.warning("已禁用本地筛选，将使用远程 LLM 处理所有推文")
            self.enabled = False

    def _check_availability(self) -> bool:
        """
        检测 Ollama 服务和模型是否可用

        Returns:
            bool: 是否可用
        """
        try:
            # 首先检查 Ollama 服务是否运行
            import requests
            try:
                response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
                if response.status_code != 200:
                    raise Exception(f"服务响应异常: HTTP {response.status_code}")

                # 检查模型是否已安装
                data = response.json()
                models = data.get('models', [])
                model_exists = any(
                    settings.OLLAMA_MODEL in model.get('name', '')
                    for model in models
                )

                if not model_exists:
                    raise Exception(f"模型 {settings.OLLAMA_MODEL} 未安装")

            except requests.exceptions.ConnectionError:
                raise Exception("无法连接到 Ollama 服务")

            logger.info(f"✓ Ollama 服务可用: {settings.OLLAMA_BASE_URL}")

            # 尝试调用一个简单的测试请求来预热模型
            logger.info(f"正在预热模型 {settings.OLLAMA_MODEL}...")

            # 使用原生 ollama 库进行测试
            response = self.ollama_client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': 'hi'}]
            )

            if response and response.get('message', {}).get('content'):
                logger.info(f"✓ 模型可用: {settings.OLLAMA_MODEL}")
                return True
            else:
                raise ValueError("响应为空")

        except Exception as e:
            logger.error(f"✗ Ollama 不可用: {e}")
            logger.error(f"  - 服务地址: {settings.OLLAMA_BASE_URL}")
            logger.error(f"  - 模型: {settings.OLLAMA_MODEL}")
            logger.error(f"  - 请检查:")
            logger.error(f"    1. Ollama 服务是否启动: ollama serve")
            logger.error(f"    2. 模型是否已下载: ollama pull {settings.OLLAMA_MODEL}")
            logger.error(f"    3. 模型是否正常加载（可能需要等待几秒）")
            return False

    def is_relevant(self, content: str) -> bool:
        """
        判断推文是否与 crypto/投资/经济相关

        Args:
            content: 推文内容

        Returns:
            bool: True=相关（继续处理），False=不相关（标记P6）
        """
        if not self.enabled:
            # 未启用时默认相关，继续使用远程 LLM
            return True

        try:
            # 使用统一的提示词管理
            system_msg = TweetProcessingPrompts.SYSTEM_OLLAMA_FILTER
            user_msg = TweetProcessingPrompts.get_ollama_filter_prompt(content)

            # 使用原生 ollama 库调用
            response = self.ollama_client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': user_msg}
                ]
            )

            result = response.get('message', {}).get('content', '').strip().upper()

            # 解析结果（宽松判断：只要包含 YES 就认为相关）
            is_relevant = "YES" in result

            logger.debug(f"Ollama 筛选结果: {result} -> {'相关' if is_relevant else '不相关'}")

            return is_relevant

        except Exception as e:
            # 筛选失败时，默认相关，继续使用远程 LLM（降级）
            logger.warning(f"Ollama 筛选调用失败: {e}，默认判定为相关")
            self.stats["error_count"] += 1
            return True

    def record_filter(self, is_relevant: bool, time_ms: int):
        """
        记录筛选统计

        Args:
            is_relevant: 是否相关
            time_ms: 耗时（毫秒）
        """
        self.stats["total_filtered"] += 1

        if is_relevant:
            self.stats["relevant_count"] += 1
        else:
            self.stats["irrelevant_count"] += 1

        self.stats["total_time_ms"] += time_ms

        # 计算平均耗时
        if self.stats["total_filtered"] > 0:
            self.stats["avg_time_ms"] = self.stats["total_time_ms"] // self.stats["total_filtered"]

    def get_filter_rate(self) -> float:
        """
        获取过滤率（被过滤掉的比例）

        Returns:
            float: 过滤率（0.0-1.0）
        """
        if self.stats["total_filtered"] == 0:
            return 0.0
        return self.stats["irrelevant_count"] / self.stats["total_filtered"]

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计信息字典
        """
        stats = self.stats.copy()
        stats["filter_rate"] = self.get_filter_rate()
        return stats


# 全局单例
_ollama_filter: Optional[OllamaFilter] = None


def get_ollama_filter() -> Optional[OllamaFilter]:
    """
    获取 Ollama 筛选器单例

    Returns:
        OllamaFilter 实例（如果未启用则为 None）
    """
    global _ollama_filter
    if _ollama_filter is None:
        _ollama_filter = OllamaFilter()
    return _ollama_filter
