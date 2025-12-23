"""
LLM 提示词管理

统一管理所有 LLM 调用的提示词，便于后续调优
"""

from typing import Dict


class TweetProcessingPrompts:
    """推文处理相关提示词"""

    # 系统消息
    SYSTEM_GRADE = "你是一个专业的加密货币内容分析专家，擅长判断内容与加密货币的相关性。"
    SYSTEM_PROCESS = "你是一个专业的内容分析助手，擅长翻译、摘要和关键词提取。"

    # 分级定义
    GRADE_DEFINITIONS = """A - 和 crypto 强相关（直接讨论加密货币、区块链技术、DeFi、NFT等）
B - 和 crypto 相关（涉及加密货币相关的人物、公司、政策）
C - 对 crypto 有影响（宏观经济、金融政策、科技趋势、钱包转账等）
D - 对 crypto 间接影响（一般性经济新闻、科技新闻）
E - 某些投资讨论（投资理念、资产配置，但不特指加密货币）
F - 没有关系可舍弃（娱乐、体育、生活等与加密货币无关的内容）"""

    # 分级提示词模板
    GRADE_TEMPLATE = """请对以下推文内容进行分级，判断其与 cryptocurrency（加密货币）的相关性。

分级标准：
{grade_definitions}

推文内容：
{content}

请仔细分析后，只返回一个字母（A/B/C/D/E/F），不要有任何其他解释。"""

    # 详细处理提示词模板
    PROCESS_TEMPLATE = """请对以下推文内容进行分析和处理。

推文内容：
{content}

请按以下格式输出（严格使用 JSON 格式）：
{{
    "is_chinese": true/false,  // 原文是否为中文
    "translated_content": "中文翻译内容",  // 如果原文非中文，提供翻译；如果是中文，此字段为 null
    "summary_cn": "30字以内的中文摘要",  // 提炼核心观点
    "keywords": ["关键词1", "关键词2", "关键词3"]  // 3-5个关键词
}}

注意：
1. 如果原文是中文，translated_content 字段设为 null
2. 摘要必须严格控制在 30 个中文字符以内
3. 关键词应该提取与加密货币相关的核心概念
4. 必须返回有效的 JSON 格式"""

    @classmethod
    def get_grade_prompt(cls, content: str) -> str:
        """
        获取分级提示词

        Args:
            content: 推文内容

        Returns:
            格式化后的提示词
        """
        return cls.GRADE_TEMPLATE.format(
            grade_definitions=cls.GRADE_DEFINITIONS, content=content
        )

    @classmethod
    def get_process_prompt(cls, content: str) -> str:
        """
        获取详细处理提示词

        Args:
            content: 推文内容

        Returns:
            格式化后的提示词
        """
        return cls.PROCESS_TEMPLATE.format(content=content)


# 导出常用提示词类
__all__ = ["TweetProcessingPrompts"]
