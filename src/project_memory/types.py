"""数据类型定义"""

import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """记忆类型枚举"""

    PROJECT_CONTEXT = "project_context"  # 项目上下文：架构决策、技术栈
    USER_PREFERENCE = "user_preference"  # 用户偏好：编码风格、工具偏好
    BUG_FIX = "bug_fix"  # 问题记录：Bug 修复经验
    CODE_PATTERN = "code_pattern"  # 代码片段：常用模式、工具函数
    DECISION = "decision"  # 会议/讨论：关键决策
    TASK_STATUS = "task_status"  # 任务状态：进行中的工作


class MemoryItem(BaseModel):
    """单条记忆"""

    id: int = Field(description="记忆唯一 ID（zvec 向量 ID）")
    content: str = Field(description="记忆内容")
    memory_type: MemoryType = Field(description="记忆类型")
    tags: list[str] = Field(default_factory=list, description="标签")
    project_path: str = Field(description="项目路径")
    importance: int = Field(default=5, ge=1, le=10, description="重要性评分 1-10")
    created_at: float = Field(default_factory=time.time, description="创建时间戳")
    updated_at: float = Field(default_factory=time.time, description="更新时间戳")
    access_count: int = Field(default=0, description="访问次数")
    last_accessed_at: Optional[float] = Field(default=None, description="最后访问时间")


class SearchResult(BaseModel):
    """搜索结果"""

    memory: MemoryItem
    score: float = Field(description="相似度分数")


class SaveRequest(BaseModel):
    """保存请求"""

    content: str = Field(description="记忆内容")
    memory_type: MemoryType = Field(default=MemoryType.PROJECT_CONTEXT)
    tags: list[str] = Field(default_factory=list)
    project_path: str = Field(description="项目路径")
    importance: int = Field(default=5, ge=1, le=10)


class RecallRequest(BaseModel):
    """检索请求"""

    query: str = Field(description="搜索查询")
    project_path: str = Field(description="项目路径")
    memory_type: Optional[MemoryType] = Field(default=None)
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=50)


class AutoContextRequest(BaseModel):
    """自动上下文加载请求"""

    project_path: str = Field(description="项目路径")
    current_task: Optional[str] = Field(default=None, description="当前任务描述")
    limit: int = Field(default=10, ge=1, le=50)
