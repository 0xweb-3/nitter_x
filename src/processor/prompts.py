"""
LLM 提示词管理

统一管理所有 LLM 调用的提示词，便于后续调优
"""

from typing import Dict


class TweetProcessingPrompts:
    """推文处理相关提示词"""

    # 系统消息
    SYSTEM_GRADE = "你是一个专业的加密货币价格分析专家，擅长判断信息对加密货币价格的影响程度。"
    SYSTEM_PROCESS = "你是一个专业的内容分析助手，擅长翻译、摘要和关键词提取。"

    # 分级定义
    GRADE_DEFINITIONS = """P0 - 直接、可验证、已发生的价格驱动事件（最高优先级）
    - 已经发生或即将确定发生，必然触发资金行为
    - 例如：ETF批准/否决、交易所上线/下架、协议被盗、巨鲸转账、稳定币脱锚
    - 价格影响：强烈、短期立刻反应（分钟级~小时级波动）

P1 - 高概率触发价格的"强信号事件"
    - 尚未完全落地，但市场共识认为"极可能发生"
    - 例如：ETF审批最终阶段、主网上线官宣、代币解锁/回购计划、大额融资披露
    - 价格影响：提前交易（buy the rumor），波动可持续数天

P2 - 结构性、长期价格影响因素（慢变量）
    - 不会立刻拉盘/砸盘，但会改变价格中枢
    - 例如：代币经济模型调整、L2成本下降、BTC减半、ETH升级
    - 价格影响：慢热、趋势型，适合中长期配置判断

P3 - 宏观 & 政策级，对crypto整体估值有影响
    - 不直接针对crypto，但影响风险资产定价
    - 例如：美联储加息/降息、CPI/非农/PCE、美元流动性变化、全球金融危机
    - 价格影响：全市场联动，对BTC/ETH权重更高

P4 - 行业、叙事、情绪层面的信息
    - 会影响市场"讲什么故事"，但资金反应不稳定
    - 例如：AI+Crypto叙事、RWA/DePIN/Restaking热度、大佬喊单、VC报告
    - 价格影响：高度依赖情绪，容易过期

P5 - 信息噪音（相关但基本不影响价格）
    - 和crypto有关，但几乎不改变任何资金决策
    - 例如：项目PR合作、普通AMA/采访、社区治理投票、已消化的旧消息
    - 价格影响：极低

P6 - 可直接舍弃（无价格影响）
    - 例如：娱乐化meme、无链上/资金/政策影响的内容、单纯观点输出"""

    # 分级提示词模板
    GRADE_TEMPLATE = """请对以下推文内容进行分级，判断其对加密货币价格的影响程度。

分级标准（价格影响导向）：
{grade_definitions}

推文内容：
{content}

请基于以下三个核心问题进行判断：
1. 是否会改变市场对未来的预期？
2. 是否会触发真实资金的买卖行为？
3. 影响范围是单币/赛道/全市场？

请仔细分析后，只返回等级代码（P0/P1/P2/P3/P4/P5/P6），不要有任何其他解释。"""

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
