"""
LLM 客户端封装

提供统一的 LLM 调用接口，支持自定义 API 端点（如 yibuapi.com）
"""

import logging
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端类，封装 LangChain 调用"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥（默认从配置读取）
            api_url: API 端点 URL（默认从配置读取）
            model: 模型名称（默认从配置读取）
            temperature: 温度参数（0-1，越高越随机）
            max_tokens: 最大生成 token 数
        """
        self.api_key = api_key or settings.LLM_API_KEY
        self.api_url = api_url or settings.LLM_API_URL
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置，请在 .env 文件中设置")

        # 初始化 ChatOpenAI（兼容 OpenAI API 的服务）
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            openai_api_base=self.api_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        logger.info(f"LLM 客户端初始化成功: model={self.model}, base_url={self.api_url}")

    def chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        发送聊天消息并获取响应

        Args:
            user_message: 用户消息
            system_message: 系统消息（可选）
            **kwargs: 其他传递给 LLM 的参数（如 temperature）

        Returns:
            LLM 响应文本

        Raises:
            Exception: 当 LLM 调用失败时
        """
        try:
            messages = []

            # 添加系统消息
            if system_message:
                messages.append(SystemMessage(content=system_message))

            # 添加用户消息
            messages.append(HumanMessage(content=user_message))

            # 调用 LLM
            response = self.llm.invoke(messages, **kwargs)

            # 提取响应内容
            result = response.content

            logger.debug(f"LLM 调用成功，响应长度: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    def chat_with_template(
        self,
        template: str,
        variables: Dict[str, Any],
        system_message: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        使用模板发送消息

        Args:
            template: 消息模板（使用 {变量名} 占位符）
            variables: 模板变量字典
            system_message: 系统消息（可选）
            **kwargs: 其他传递给 LLM 的参数

        Returns:
            LLM 响应文本

        Example:
            >>> client = LLMClient()
            >>> template = "请分析这条推文的情绪：{tweet_content}"
            >>> result = client.chat_with_template(
            ...     template=template,
            ...     variables={"tweet_content": "今天天气真好！"}
            ... )
        """
        try:
            # 构建提示词
            prompt_messages = []

            if system_message:
                prompt_messages.append(("system", system_message))

            prompt_messages.append(("human", template))

            # 创建提示词模板
            prompt = ChatPromptTemplate.from_messages(prompt_messages)

            # 创建链
            chain = prompt | self.llm | StrOutputParser()

            # 执行
            result = chain.invoke(variables, **kwargs)

            logger.debug(f"模板调用成功，响应长度: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"模板调用失败: {e}")
            raise

    def batch_chat(
        self,
        messages: List[str],
        system_message: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """
        批量发送消息

        Args:
            messages: 用户消息列表
            system_message: 系统消息（可选）
            **kwargs: 其他传递给 LLM 的参数

        Returns:
            响应列表

        Note:
            批量调用会并发执行，提高效率
        """
        try:
            message_batches = []

            for msg in messages:
                batch = []
                if system_message:
                    batch.append(SystemMessage(content=system_message))
                batch.append(HumanMessage(content=msg))
                message_batches.append(batch)

            # 批量调用
            responses = self.llm.batch(message_batches, **kwargs)

            # 提取响应内容
            results = [resp.content for resp in responses]

            logger.info(f"批量调用成功，处理 {len(results)} 条消息")
            return results

        except Exception as e:
            logger.error(f"批量调用失败: {e}")
            raise


# 全局单例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    获取 LLM 客户端单例

    Returns:
        LLMClient 实例
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# 便捷函数
def chat(user_message: str, system_message: Optional[str] = None, **kwargs) -> str:
    """
    便捷函数：发送聊天消息

    Args:
        user_message: 用户消息
        system_message: 系统消息（可选）
        **kwargs: 其他参数

    Returns:
        LLM 响应文本
    """
    client = get_llm_client()
    return client.chat(user_message, system_message, **kwargs)
