"""记忆管理核心逻辑 - 高级业务层"""

import logging
import os
from typing import Optional

from .config import get_config
from .store import MemoryStore
from .types import (
    AutoContextRequest,
    MemoryItem,
    MemoryType,
    RecallRequest,
    SaveRequest,
    SearchResult,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆管理器 - 提供高级记忆操作接口"""

    def __init__(self, project_path: Optional[str] = None) -> None:
        self.project_path = project_path or os.getcwd()
        self._stores: dict[str, MemoryStore] = {}

    def _get_store(self, project_path: Optional[str] = None) -> MemoryStore:
        """获取项目的存储实例"""
        path = project_path or self.project_path
        if path not in self._stores:
            self._stores[path] = MemoryStore(path)
        return self._stores[path]

    def save(self, request: SaveRequest) -> MemoryItem:
        """保存一条记忆"""
        store = self._get_store(request.project_path)
        return store.save(
            content=request.content,
            memory_type=request.memory_type,
            tags=request.tags,
            importance=request.importance,
        )

    def recall(self, request: RecallRequest) -> list[SearchResult]:
        """语义搜索记忆"""
        store = self._get_store(request.project_path)
        return store.recall(
            query=request.query,
            memory_type=request.memory_type,
            tags=request.tags,
            limit=request.limit,
        )

    def list_memories(
        self,
        project_path: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50,
    ) -> list[MemoryItem]:
        """列出项目记忆"""
        store = self._get_store(project_path)
        return store.list_memories(memory_type=memory_type, limit=limit)

    def delete(self, memory_id: int, project_path: Optional[str] = None) -> bool:
        """删除一条记忆"""
        store = self._get_store(project_path)
        return store.delete(memory_id)

    def clean(self, project_path: Optional[str] = None, days: Optional[int] = None) -> int:
        """清理过期记忆"""
        config = get_config()
        expiration_days = days or config["expiration_days"]
        store = self._get_store(project_path)
        return store.clean(days=expiration_days)

    def get_context(self, request: AutoContextRequest) -> list[MemoryItem]:
        """获取项目上下文（自动加载）"""
        store = self._get_store(request.project_path)
        return store.get_context(
            current_task=request.current_task,
            limit=request.limit,
        )

    def auto_save(self, content: str, project_path: Optional[str] = None) -> Optional[MemoryItem]:
        """智能判断并保存记忆

        根据内容特征自动判断记忆类型和重要性。
        """
        path = project_path or self.project_path
        store = self._get_store(path)

        # 检查是否已有相似记忆
        existing = store.recall(query=content, limit=3)
        for result in existing:
            if result.score > 0.95:
                logger.info("Similar memory already exists (#%d), skipping", result.memory.id)
                return None

        # 自动推断记忆类型
        memory_type = self._infer_memory_type(content)
        importance = self._infer_importance(content)

        return store.save(
            content=content,
            memory_type=memory_type,
            importance=importance,
        )

    @staticmethod
    def _infer_memory_type(content: str) -> MemoryType:
        """根据内容特征推断记忆类型"""
        content_lower = content.lower()

        bug_keywords = ["bug", "fix", "error", "issue", "crash", "故障", "修复", "错误", "异常"]
        if any(kw in content_lower for kw in bug_keywords):
            return MemoryType.BUG_FIX

        decision_keywords = ["决定", "决策", "选择", "decided", "chose", "方案", "approach"]
        if any(kw in content_lower for kw in decision_keywords):
            return MemoryType.DECISION

        preference_keywords = ["偏好", "习惯", "喜欢", "prefer", "like", "style", "风格"]
        if any(kw in content_lower for kw in preference_keywords):
            return MemoryType.USER_PREFERENCE

        task_keywords = ["todo", "进行中", "待办", "wip", "in progress", "任务"]
        if any(kw in content_lower for kw in task_keywords):
            return MemoryType.TASK_STATUS

        code_keywords = ["function", "class", "pattern", "util", "函数", "类", "模式"]
        if any(kw in content_lower for kw in code_keywords):
            return MemoryType.CODE_PATTERN

        return MemoryType.PROJECT_CONTEXT

    @staticmethod
    def _infer_importance(content: str) -> int:
        """根据内容特征推断重要性"""
        importance = 5

        high_importance_keywords = [
            "架构", "architecture", "核心", "critical",
            "安全", "security", "决定", "decision",
            "生产", "production", "线上", "online",
        ]
        if any(kw in content.lower() for kw in high_importance_keywords):
            importance += 2

        medium_importance_keywords = [
            "重要", "important", "注意", "attention",
            "优化", "optimize", "重构", "refactor",
        ]
        if any(kw in content.lower() for kw in medium_importance_keywords):
            importance += 1

        return min(importance, 10)
