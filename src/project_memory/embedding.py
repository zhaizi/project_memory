"""Embedding 生成模块 - 支持本地/在线双模式"""

import logging
import os
from typing import Optional

import httpx

from .config import get_config, get_embedding_mode, get_online_api_key

logger = logging.getLogger(__name__)

# 本地模型单例
_local_model_instance = None

# 维度缓存
_dim_cache: Optional[int] = None


def _get_local_model():
    """获取或初始化本地 embedding 模型（单例模式）"""
    global _local_model_instance
    if _local_model_instance is None:
        import zvec

        logger.info("Loading zvec DefaultLocalDenseEmbedding (all-MiniLM-L6-v2)")
        _local_model_instance = zvec.DefaultLocalDenseEmbedding()
        logger.info("Local embedding model loaded successfully")
    return _local_model_instance


def _embed_online(text: str) -> list[float]:
    """使用在线 API 生成 embedding 向量"""
    config = get_config()
    online_cfg = config.get("online_embedding", {})
    api_url = online_cfg.get("api_url", "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal")
    model = online_cfg.get("model", "doubao-embedding-vision-251215")
    timeout = online_cfg.get("timeout", 30)

    api_key = get_online_api_key()
    if not api_key:
        raise ValueError(
            "在线嵌入 API Key 未配置。"
            "请在 config.json 的 online_embedding.api_key 中设置，"
            "或设置环境变量 ARK_API_KEY"
        )

    payload = {
        "model": model,
        "input": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    # 解析响应：data.embedding (dict 格式)
    resp_data = data.get("data")
    if not resp_data or "embedding" not in resp_data:
        raise ValueError(f"在线嵌入 API 返回格式异常: {data}")

    return resp_data["embedding"]


def _embed_online_batch(texts: list[str]) -> list[list[float]]:
    """批量使用在线 API 生成 embedding 向量（逐个调用，因为 API 只返回单个 embedding）"""
    results = []
    for text in texts:
        embedding = _embed_online(text)
        results.append(embedding)
    return results


def embed_text(text: str) -> list[float]:
    """将文本转换为向量（根据配置自动选择本地/在线模式）"""
    mode = get_embedding_mode()

    if mode == "online":
        logger.debug("Using online embedding (doubao)")
        return _embed_online(text)

    # 本地模式
    model = _get_local_model()
    return model.embed(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量将文本转换为向量"""
    if not texts:
        return []

    mode = get_embedding_mode()

    if mode == "online":
        logger.debug("Using online embedding batch (doubao), count=%d", len(texts))
        return _embed_online_batch(texts)

    # 本地模式
    model = _get_local_model()
    return [model.embed(text) for text in texts]


def get_embedding_dim() -> int:
    """根据当前模式获取 embedding 维度"""
    from .config import get_embedding_dim as _get_dim

    return _get_dim()
