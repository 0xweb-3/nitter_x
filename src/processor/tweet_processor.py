"""
推文处理器

使用 LLM 对推文进行分级、翻译、摘要、关键词提取
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from src.processor.llm_client import get_llm_client
from src.processor.prompts import TweetProcessingPrompts
from src.processor.embedder import generate_embedding
from src.processor.ollama_filter import get_ollama_filter
from src.config.settings import settings

logger = logging.getLogger(__name__)


class TweetProcessor:
    """推文处理器，负责分级、翻译、摘要、关键词提取"""

    def __init__(self):
        """初始化处理器"""
        self.llm_client = get_llm_client()
        self.prompts = TweetProcessingPrompts

        # 初始化 Ollama 筛选器（如果启用）
        self.ollama_filter = None
        if settings.OLLAMA_ENABLED:
            try:
                self.ollama_filter = get_ollama_filter()
                if self.ollama_filter and self.ollama_filter.enabled:
                    logger.info("✓ Ollama 筛选器初始化成功并可用")
                else:
                    logger.warning("✗ Ollama 筛选器初始化失败，已禁用本地筛选")
            except Exception as e:
                logger.warning(f"✗ Ollama 筛选器初始化异常: {e}，已禁用本地筛选")

        logger.info("推文处理器初始化成功")

    def grade_tweet(self, content: str) -> str:
        """
        对推文进行分级

        Args:
            content: 推文内容

        Returns:
            分级结果 (P0/P1/P2/P3/P4/P5/P6)
        """
        try:
            # 使用统一的提示词管理
            prompt = self.prompts.get_grade_prompt(content)

            response = self.llm_client.chat(
                user_message=prompt,
                system_message=self.prompts.SYSTEM_GRADE,
                temperature=0.1,  # 降低温度，使结果更确定
            )

            # 提取分级结果（P0-P6）
            grade = None
            response_upper = response.strip().upper()

            # 尝试匹配 P0-P6
            for level in ["P0", "P1", "P2", "P3", "P4", "P5", "P6"]:
                if level in response_upper:
                    grade = level
                    break

            if not grade:
                logger.warning(f"LLM 返回的分级结果无效: {response}，默认设为 P6")
                grade = "P6"

            logger.debug(f"推文分级成功: {grade}")
            return grade

        except Exception as e:
            logger.error(f"推文分级失败: {e}")
            # 分级失败时默认返回 P6
            return "P6"

    def process_high_grade_tweet(
        self, content: str, grade: str
    ) -> Optional[Dict[str, Any]]:
        """
        处理高等级推文（P0/P1/P2级），进行翻译、摘要、关键词提取

        Args:
            content: 推文内容
            grade: 分级结果

        Returns:
            处理结果字典，包含：
            - translated_content: 中文翻译（如果原文非中文）
            - summary_cn: 中文摘要（100字以内，由LLM总结而非截断）
            - keywords: 关键词列表
        """
        if grade not in ["P0", "P1", "P2"]:
            logger.debug(f"推文分级为 {grade}，跳过详细处理")
            return None

        try:
            # 使用统一的提示词管理
            prompt = self.prompts.get_process_prompt(content)

            response = self.llm_client.chat(
                user_message=prompt,
                system_message=self.prompts.SYSTEM_PROCESS,
                temperature=0.3,
            )

            # 解析 JSON 响应
            # 尝试提取 JSON（有时 LLM 会在 JSON 前后添加说明文字）
            response_clean = response.strip()

            # 查找 JSON 块
            json_start = response_clean.find("{")
            json_end = response_clean.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_clean[json_start:json_end]
                result = json.loads(json_str)

                # 验证必需字段
                if "summary_cn" not in result or "keywords" not in result:
                    raise ValueError("缺少必需字段")

                # 检查摘要长度（LLM应该已经控制在100字以内，这里只是兜底检查）
                summary_len = len(result["summary_cn"])
                if summary_len > 100:
                    logger.warning(
                        f"摘要长度超出限制 ({summary_len} > 100)，LLM未严格遵守提示词要求。"
                        f"原摘要: {result['summary_cn']}"
                    )
                    # 作为兜底，截断到100字（但理想情况下LLM应该自己控制）
                    result["summary_cn"] = result["summary_cn"][:100]
                    logger.info(f"已截断摘要到100字: {result['summary_cn']}")

                # 如果原文是中文，或翻译内容与原文相同，设置 translated_content 为 None
                if result.get("is_chinese"):
                    result["translated_content"] = None
                elif result.get("translated_content"):
                    # 额外检查：如果翻译内容与原文几乎相同，也设为 None
                    translated = result["translated_content"].strip()
                    original = content.strip()
                    if translated == original or len(translated) < 10:
                        result["translated_content"] = None

                logger.debug(f"高等级推文处理成功: 摘要={result['summary_cn']}")
                return result

            else:
                raise ValueError(f"无法从响应中提取 JSON: {response}")

        except Exception as e:
            logger.error(f"高等级推文处理失败: {e}")
            return None

    def process_tweet(
        self, tweet_id: str, content: str, author: str = "", published_at: str = ""
    ) -> Dict[str, Any]:
        """
        完整处理一条推文

        Args:
            tweet_id: 推文 ID
            content: 推文内容
            author: 作者用户名（可选）
            published_at: 推文发布时间（ISO格式字符串，可选）

        Returns:
            处理结果字典：
            - tweet_id: 推文 ID
            - grade: 分级结果
            - summary_cn: 中文摘要（可能为 None）
            - keywords: 关键词列表（可能为空）
            - translated_content: 翻译内容（可能为 None）
            - processing_time_ms: 处理耗时（毫秒）
            - filter_source: 筛选来源（expired/ollama_filtered/remote_llm）
        """
        start_time = time.time()

        logger.info(f"开始处理推文: {tweet_id} (作者: {author or '未知'})")

        # 默认筛选来源
        filter_source = "remote_llm"

        # 第一步：检查推文是否过期（如果启用）
        if settings.ENABLE_24H_EXPIRATION and published_at:
            try:
                # 确保 published_at 是 timezone-aware 的 datetime 对象
                if isinstance(published_at, str):
                    pub_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                else:
                    pub_dt = published_at
                    if pub_dt.tzinfo is None:
                        # 如果没有时区信息，假设为 UTC
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)

                # 计算时间差
                now = datetime.now(timezone.utc)
                time_diff = now - pub_dt

                # 如果超过配置的过期时间，直接标记为 P6
                expiration_threshold = timedelta(hours=settings.TWEET_EXPIRATION_HOURS)
                if time_diff > expiration_threshold:
                    filter_source = "expired"
                    logger.info(
                        f"推文 {tweet_id} 发布时间超过 {settings.TWEET_EXPIRATION_HOURS} 小时 "
                        f"({time_diff.total_seconds() / 3600:.1f}小时)，"
                        f"自动标记为 P6（已过期）"
                    )

                    return {
                        "tweet_id": tweet_id,
                        "grade": "P6",
                        "summary_cn": None,
                        "keywords": [],
                        "translated_content": None,
                        "embedding": None,
                        "processing_time_ms": int((time.time() - start_time) * 1000),
                        "filter_source": filter_source
                    }
            except Exception as e:
                logger.warning(f"过期检查失败: {e}，继续正常处理")

        # 第二步：Ollama 一级筛选

        if self.ollama_filter and self.ollama_filter.enabled:
            try:
                filter_start = time.time()
                is_relevant = self.ollama_filter.is_relevant(content)
                filter_time = int((time.time() - filter_start) * 1000)

                logger.info(f"Ollama 筛选: {'相关' if is_relevant else '不相关'}, 耗时: {filter_time}ms")

                # 记录统计
                self.ollama_filter.record_filter(is_relevant, filter_time)

                # 每 100 条输出一次统计信息
                if self.ollama_filter.stats["total_filtered"] % 100 == 0:
                    stats = self.ollama_filter.get_stats()
                    logger.info(
                        f"[Ollama统计] 总筛选: {stats['total_filtered']}条, "
                        f"过滤率: {stats['filter_rate']:.1%}, "
                        f"平均耗时: {stats['avg_time_ms']}ms"
                    )

                if not is_relevant:
                    filter_source = "ollama_filtered"
                    logger.info(f"推文被 Ollama 筛选为不相关，标记为 P6")

                    return {
                        "tweet_id": tweet_id,
                        "grade": "P6",
                        "summary_cn": None,
                        "keywords": [],
                        "translated_content": None,
                        "embedding": None,
                        "processing_time_ms": int((time.time() - start_time) * 1000),
                        "filter_source": filter_source
                    }
            except Exception as e:
                logger.warning(f"Ollama 筛选失败: {e}，降级到远程 LLM")
                if self.ollama_filter:
                    self.ollama_filter.stats["error_count"] += 1

        # 第三步：远程 LLM 分级
        grade = self.grade_tweet(content)
        logger.info(f"推文 {tweet_id} 分级结果: {grade}")

        # 第四步：如果是高等级推文，进行详细处理
        result = {
            "tweet_id": tweet_id,
            "grade": grade,
            "summary_cn": None,
            "keywords": [],
            "translated_content": None,
            "embedding": None,
            "processing_time_ms": 0,
            "filter_source": filter_source,  # 添加筛选来源
        }

        if grade in ["P0", "P1", "P2"]:
            detailed_result = self.process_high_grade_tweet(content, grade)
            if detailed_result:
                result["summary_cn"] = detailed_result.get("summary_cn")
                result["keywords"] = detailed_result.get("keywords", [])
                result["translated_content"] = detailed_result.get("translated_content")

                # 3. 生成摘要的向量（使用中文摘要）
                if result["summary_cn"]:
                    logger.debug(f"生成推文 {tweet_id} 的向量表示")
                    embedding = generate_embedding(result["summary_cn"])
                    if embedding:
                        result["embedding"] = embedding
                        logger.debug(f"向量生成成功，维度: {len(embedding)}")
                    else:
                        logger.warning(f"向量生成失败: {tweet_id}")

        # 计算处理耗时
        processing_time = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time

        logger.info(
            f"推文 {tweet_id} 处理完成，耗时 {processing_time}ms，"
            f"分级: {grade}，摘要: {result['summary_cn'] or '无'}"
        )

        return result


# 全局单例
_tweet_processor: Optional[TweetProcessor] = None


def get_tweet_processor() -> TweetProcessor:
    """
    获取推文处理器单例

    Returns:
        TweetProcessor 实例
    """
    global _tweet_processor
    if _tweet_processor is None:
        _tweet_processor = TweetProcessor()
    return _tweet_processor
