"""FastAPI REST API - 为前端提供 HTTP 接口"""

import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .memory import MemoryManager
from .types import MemoryType

app = FastAPI(title="Project Memory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_manager: Optional[MemoryManager] = None


def _get_manager() -> MemoryManager:
    global _manager
    if _manager is None:
        _manager = MemoryManager()
    return _manager


# --- Request/Response Models ---


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1)
    memory_type: str = Field(default="project_context")
    tags: list[str] = Field(default_factory=list)
    importance: int = Field(default=5, ge=1, le=10)
    project_path: str


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    memory_type: Optional[str] = None
    tags: Optional[list[str]] = None
    importance: Optional[int] = Field(default=None, ge=1, le=10)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    project: str
    limit: int = Field(default=10, ge=1, le=50)


class MemoryResponse(BaseModel):
    id: int
    content: str
    memory_type: str
    tags: list[str]
    project_path: str
    importance: int
    created_at: float
    updated_at: float
    access_count: int
    last_accessed_at: Optional[float] = None


class SearchResult(BaseModel):
    memory: MemoryResponse
    score: float


class StatsResponse(BaseModel):
    total: int
    by_type: dict[str, int]
    project: str


class ProjectInfo(BaseModel):
    path: str
    name: str
    memory_count: int


# --- API Endpoints ---


@app.get("/api/projects", response_model=list[ProjectInfo])
def list_projects():
    """列出所有有记忆数据的项目"""
    from .config import DATA_DIR

    manager = _get_manager()
    projects = []

    metadata_dir = DATA_DIR / "metadata"
    if metadata_dir.exists():
        for item in metadata_dir.iterdir():
            if item.is_dir():
                for mode_dir in item.iterdir():
                    if mode_dir.is_dir():
                        meta_file = mode_dir / "memories.json"
                        if meta_file.exists():
                            try:
                                import json
                                data = json.loads(meta_file.read_text(encoding="utf-8"))
                                if data:
                                    first = list(data.values())[0]
                                    project_path = first.get("project_path", "")
                                    projects.append(ProjectInfo(
                                        path=project_path,
                                        name=os.path.basename(project_path) or project_path,
                                        memory_count=len(data),
                                    ))
                            except (json.JSONDecodeError, OSError):
                                pass

    return projects


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(project: str = Query(...)):
    """获取项目记忆统计"""
    manager = _get_manager()
    memories = manager.list_memories(
        project_path=os.path.abspath(project),
        limit=10000,
    )

    type_counts: dict[str, int] = {}
    for m in memories:
        t = m.memory_type.value
        type_counts[t] = type_counts.get(t, 0) + 1

    return StatsResponse(
        total=len(memories),
        by_type=type_counts,
        project=os.path.abspath(project),
    )


@app.get("/api/memories", response_model=list[MemoryResponse])
def list_memories(
    project: str = Query(...),
    type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """列出项目记忆（分页）"""
    manager = _get_manager()
    memory_type = MemoryType(type) if type else None

    memories = manager.list_memories(
        project_path=os.path.abspath(project),
        memory_type=memory_type,
        limit=limit + offset,
    )

    result = memories[offset : offset + limit]
    return [_to_response(m) for m in result]


@app.post("/api/memories", response_model=MemoryResponse, status_code=201)
def create_memory(req: MemoryCreate):
    """创建记忆"""
    from .types import SaveRequest

    manager = _get_manager()
    try:
        memory_type = MemoryType(req.memory_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid memory type: {req.memory_type}. "
            f"Valid types: {[t.value for t in MemoryType]}",
        )

    save_req = SaveRequest(
        content=req.content,
        memory_type=memory_type,
        tags=req.tags,
        project_path=os.path.abspath(req.project_path),
        importance=req.importance,
    )

    result = manager.save(save_req)
    return _to_response(result)


@app.get("/api/memories/{memory_id}", response_model=MemoryResponse)
def get_memory(memory_id: int, project: str = Query(...)):
    """获取单条记忆"""
    manager = _get_manager()
    memories = manager.list_memories(
        project_path=os.path.abspath(project),
        limit=10000,
    )

    for m in memories:
        if m.id == memory_id:
            return _to_response(m)

    raise HTTPException(status_code=404, detail=f"Memory #{memory_id} not found")


@app.put("/api/memories/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: int, project: str = Query(...), req: MemoryUpdate = None):
    """更新记忆（删除后重建）"""
    manager = _get_manager()
    abs_path = os.path.abspath(project)

    memories = manager.list_memories(project_path=abs_path, limit=10000)
    target = None
    for m in memories:
        if m.id == memory_id:
            target = m
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"Memory #{memory_id} not found")

    # 删除旧的，创建新的（保持原有时间戳）
    manager.delete(memory_id, project_path=abs_path)

    new_content = req.content if req.content is not None else target.content
    new_type = MemoryType(req.memory_type) if req.memory_type else target.memory_type
    new_tags = req.tags if req.tags is not None else target.tags
    new_importance = req.importance if req.importance is not None else target.importance

    from .types import SaveRequest

    save_req = SaveRequest(
        content=new_content,
        memory_type=new_type,
        tags=new_tags,
        project_path=abs_path,
        importance=new_importance,
    )

    result = manager.save(save_req)
    return _to_response(result)


@app.delete("/api/memories/{memory_id}")
def delete_memory(memory_id: int, project: str = Query(...)):
    """删除记忆"""
    manager = _get_manager()
    success = manager.delete(memory_id, project_path=os.path.abspath(project))

    if not success:
        raise HTTPException(status_code=404, detail=f"Memory #{memory_id} not found")

    return {"success": True, "deleted_id": memory_id}


@app.post("/api/memories/search", response_model=list[SearchResult])
def search_memories(req: SearchRequest):
    """语义搜索记忆"""
    from .types import RecallRequest

    manager = _get_manager()
    recall_req = RecallRequest(
        query=req.query,
        project_path=os.path.abspath(req.project),
        limit=req.limit,
    )

    results = manager.recall(recall_req)
    return [
        SearchResult(memory=_to_response(r.memory), score=r.score)
        for r in results
    ]


def _to_response(m) -> MemoryResponse:
    """将 MemoryItem 转为 API 响应"""
    return MemoryResponse(
        id=m.id,
        content=m.content,
        memory_type=m.memory_type.value,
        tags=m.tags,
        project_path=m.project_path,
        importance=m.importance,
        created_at=m.created_at,
        updated_at=m.updated_at,
        access_count=m.access_count,
        last_accessed_at=m.last_accessed_at,
    )
