"""配置管理模块"""

import hashlib
import json
import os
from pathlib import Path


# 默认配置
DEFAULT_CONFIG = {
    "embedding_mode": "local",  # "local" | "online"
    "embedding_model": "BAAI/bge-small-en-v1.1",
    "embedding_dim": 384,
    "default_top_k": 5,
    "max_context_memories": 10,
    "expiration_days": 90,
    "auto_save": True,
    # 在线嵌入模型配置
    "online_embedding": {
        "api_url": "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal",
        "model": "doubao-embedding-vision-251215",
        "api_key": "",
        "dim": 2048,
        "timeout": 30,
    },
}

# 路径常量
SKILL_DIR = Path(__file__).parent.parent.parent  # project-memory/
DATA_DIR = SKILL_DIR / "data"
CONFIG_FILE = SKILL_DIR / "config.json"


def get_config() -> dict:
    """获取配置，合并默认值和用户自定义配置"""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            user_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            config.update(user_config)
        except (json.JSONDecodeError, OSError):
            pass

    # 合并 online_embedding 子配置
    if "online_embedding" in config and isinstance(config["online_embedding"], dict):
        merged_online = DEFAULT_CONFIG["online_embedding"].copy()
        merged_online.update(config["online_embedding"])
        config["online_embedding"] = merged_online

    return config


def get_embedding_mode() -> str:
    """获取当前嵌入模式"""
    config = get_config()
    mode = config.get("embedding_mode", "local")
    if mode not in ("local", "online"):
        mode = "local"
    return mode


def get_online_api_key() -> str:
    """获取在线嵌入 API Key（优先环境变量 ARK_API_KEY）"""
    env_key = os.environ.get("ARK_API_KEY", "")
    if env_key:
        return env_key
    config = get_config()
    return config.get("online_embedding", {}).get("api_key", "")


def get_embedding_dim() -> int:
    """根据当前模式获取 embedding 维度"""
    config = get_config()
    mode = get_embedding_mode()
    if mode == "online":
        return config.get("online_embedding", {}).get("dim", 2048)
    return config.get("embedding_dim", 384)


def save_config(config: dict) -> None:
    """保存用户配置"""
    CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_project_index_dir(project_path: str) -> Path:
    """获取项目对应的索引存储目录（按嵌入模式分目录）"""
    safe_name = _safe_project_name(project_path)
    mode = get_embedding_mode()
    index_dir = DATA_DIR / "indexes" / safe_name / mode
    index_dir.mkdir(parents=True, exist_ok=True)
    return index_dir


def get_metadata_dir(project_path: str) -> Path:
    """获取项目对应的元数据存储目录（按嵌入模式分目录）"""
    safe_name = _safe_project_name(project_path)
    mode = get_embedding_mode()
    meta_dir = DATA_DIR / "metadata" / safe_name / mode
    meta_dir.mkdir(parents=True, exist_ok=True)
    return meta_dir


def get_metadata_file(project_path: str) -> Path:
    """获取项目的元数据 JSON 文件路径"""
    return get_metadata_dir(project_path) / "memories.json"


def _safe_project_name(project_path: str) -> str:
    """将项目路径转换为安全的目录名（使用 hash）"""
    resolved = str(Path(project_path).resolve())
    path_hash = hashlib.md5(resolved.encode()).hexdigest()[:12]
    # 取路径最后两级目录作为可读部分
    path = Path(project_path).resolve()
    readable = path.name or "default"
    # 清理非法字符
    safe_readable = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in readable)
    return f"{safe_readable}_{path_hash}"
