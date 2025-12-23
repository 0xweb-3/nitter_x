"""
文本向量化模块

使用本地 sentence-transformers 模型生成文本嵌入向量
"""

import logging
import os
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# 延迟导入，避免启动时加载大型模型
_model = None
_model_name = "paraphrase-multilingual-MiniLM-L12-v2"  # 多语言模型，支持中文


def get_embedder():
    """
    获取向量化模型（单例）

    Returns:
        SentenceTransformer 模型实例
    """
    global _model

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"正在加载向量化模型: {_model_name}")

            # 设置模型缓存目录
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "models")
            os.makedirs(cache_dir, exist_ok=True)

            # 加载模型（首次会下载，后续使用缓存）
            _model = SentenceTransformer(_model_name, cache_folder=cache_dir)

            logger.info(f"向量化模型加载成功，向量维度: {_model.get_sentence_embedding_dimension()}")

        except Exception as e:
            logger.error(f"向量化模型加载失败: {e}")
            raise

    return _model


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    生成文本的嵌入向量

    Args:
        text: 输入文本

    Returns:
        嵌入向量（列表形式），失败返回 None
    """
    try:
        if not text or not text.strip():
            logger.warning("输入文本为空，无法生成向量")
            return None

        model = get_embedder()

        # 生成嵌入向量
        embedding = model.encode(text, convert_to_numpy=True)

        # 转换为 Python list（便于 JSON 序列化）
        embedding_list = embedding.tolist()

        logger.debug(f"文本向量生成成功，维度: {len(embedding_list)}")
        return embedding_list

    except Exception as e:
        logger.error(f"向量生成失败: {e}")
        return None


def generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """
    批量生成文本嵌入向量

    Args:
        texts: 文本列表

    Returns:
        嵌入向量列表
    """
    try:
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [t if t and t.strip() else "" for t in texts]

        model = get_embedder()

        # 批量编码（效率更高）
        embeddings = model.encode(valid_texts, convert_to_numpy=True, batch_size=32)

        # 转换为列表
        result = []
        for i, embedding in enumerate(embeddings):
            if valid_texts[i]:
                result.append(embedding.tolist())
            else:
                result.append(None)

        logger.info(f"批量向量生成成功，处理 {len(texts)} 条文本")
        return result

    except Exception as e:
        logger.error(f"批量向量生成失败: {e}")
        return [None] * len(texts)


def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    计算两个向量的余弦相似度

    Args:
        embedding1: 向量1
        embedding2: 向量2

    Returns:
        余弦相似度（0-1之间）
    """
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # 余弦相似度
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

        return float(similarity)

    except Exception as e:
        logger.error(f"相似度计算失败: {e}")
        return 0.0


# 便捷函数
def vectorize(text: str) -> Optional[List[float]]:
    """
    便捷函数：生成文本向量

    Args:
        text: 输入文本

    Returns:
        嵌入向量
    """
    return generate_embedding(text)


def vectorize_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """
    便捷函数：批量生成文本向量

    Args:
        texts: 文本列表

    Returns:
        嵌入向量列表
    """
    return generate_embeddings_batch(texts)
