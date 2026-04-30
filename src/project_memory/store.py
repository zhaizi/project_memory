"""zvec 向量存储层 - 基于 zvec Collection API"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import zvec

from .config import get_config, get_project_index_dir, get_metadata_file
from .embedding import embed_text, get_embedding_dim
from .types import MemoryItem, MemoryType, SearchResult

logger = logging.getLogger(__name__)


def _build_collection_schema() -> zvec.CollectionSchema:
    """构建 Collection Schema"""
    dim = get_embedding_dim()
    return zvec.CollectionSchema(
        name="project_memory",
        fields=[
            zvec.FieldSchema("content", zvec.DataType.STRING),
            zvec.FieldSchema("memory_type", zvec.DataType.STRING),
            zvec.FieldSchema("tags", zvec.DataType.ARRAY_STRING),
            zvec.FieldSchema("importance", zvec.DataType.INT32),
            zvec.FieldSchema("created_at", zvec.DataType.DOUBLE),
            zvec.FieldSchema("updated_at", zvec.DataType.DOUBLE),
            zvec.FieldSchema("access_count", zvec.DataType.INT32),
            zvec.FieldSchema("last_accessed_at", zvec.DataType.DOUBLE),
        ],
        vectors=[
            zvec.VectorSchema(
                "embedding",
                zvec.DataType.VECTOR_FP32,
                dimension=dim,
                index_param=zvec.HnswIndexParam(
                    metric_type=zvec.MetricType.COSINE,
                    m=32,
                    ef_construction=200,
                ),
            ),
        ],
    )


class MemoryStore:
    """基于 zvec Collection 的向量记忆存储"""

    def __init__(self, project_path: str) -> None:
        self.project_path = project_path
        self._index_dir = get_project_index_dir(project_path)
        self._metadata_file = get_metadata_file(project_path)
        self._metadata: dict[int, dict] = self._load_metadata()
        self._next_id = self._compute_next_id()
        self._collection: Optional[zvec.Collection] = None

    @property
    def collection(self) -> zvec.Collection:
        """获取或创建 zvec Collection"""
        if self._collection is None:
            coll_path = str(self._index_dir / "memory_collection")
            if os.path.exists(coll_path):
                self._collection = zvec.open(coll_path)
                logger.info("Opened existing collection: %s", coll_path)
            else:
                schema = _build_collection_schema()
                self._collection = zvec.create_and_open(coll_path, schema)
                logger.info("Created new collection: %s (dim=%d)", coll_path, get_embedding_dim())
        return self._collection

    def save(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.PROJECT_CONTEXT,
        tags: Optional[list[str]] = None,
        importance: int = 5,
    ) -> MemoryItem:
        """保存一条记忆"""
        memory_id = self._next_id
        self._next_id += 1

        vector = embed_text(content)

        now = time.time()
        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            project_path=self.project_path,
            importance=importance,
            created_at=now,
            updated_at=now,
        )

        doc = zvec.Doc(
            id=str(memory_id),
            vectors={"embedding": vector},
            fields={
                "content": content,
                "memory_type": memory_type.value,
                "tags": tags or [],
                "importance": importance,
                "created_at": now,
                "updated_at": now,
                "access_count": 0,
                "last_accessed_at": 0.0,
            },
        )
        self.collection.insert(doc)
        self.collection.flush()

        self._metadata[memory_id] = memory.model_dump()
        self._save_metadata()

        logger.info("Saved memory #%d: %s", memory_id, content[:50])
        return memory

    def recall(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        """语义搜索记忆"""
        if not self._metadata:
            return []

        query_vector = embed_text(query)

        search_k = min(limit * 3, max(len(self._metadata), 1))
        vq = zvec.VectorQuery(field_name="embedding", vector=query_vector)
        results = self.collection.query(vectors=vq, topk=search_k)

        search_results = []
        for doc in results:
            memory_id = int(doc.id)
            meta = self._metadata.get(memory_id)
            if meta is None:
                meta = self._doc_fields_to_meta(memory_id, doc)

            memory = MemoryItem(**meta)

            if memory_type and memory.memory_type != memory_type:
                continue

            if tags and not any(t in memory.tags for t in tags):
                continue

            memory.access_count += 1
            memory.last_accessed_at = time.time()
            self._metadata[memory_id] = memory.model_dump()

            score = doc.score if doc.score is not None else 0.0
            search_results.append(SearchResult(memory=memory, score=score))

            if len(search_results) >= limit:
                break

        self._save_metadata()
        return search_results

    def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50,
    ) -> list[MemoryItem]:
        """列出所有记忆"""
        memories = []
        for meta in self._metadata.values():
            memory = MemoryItem(**meta)
            if memory_type and memory.memory_type != memory_type:
                continue
            memories.append(memory)

        memories.sort(key=lambda m: m.updated_at, reverse=True)
        return memories[:limit]

    def delete(self, memory_id: int) -> bool:
        """删除一条记忆"""
        if memory_id not in self._metadata:
            return False

        try:
            self.collection.delete(str(memory_id))
            self.collection.flush()
        except Exception:
            logger.warning("Failed to delete vector %d from collection", memory_id)

        del self._metadata[memory_id]
        self._save_metadata()
        logger.info("Deleted memory #%d", memory_id)
        return True

    def clean(self, days: int = 90) -> int:
        """清理过期记忆，返回清理数量"""
        cutoff = time.time() - (days * 86400)
        to_delete = []

        for memory_id, meta in self._metadata.items():
            last_access = (
                meta.get("last_accessed_at")
                or meta.get("updated_at")
                or meta.get("created_at", 0)
            )
            if last_access < cutoff and meta.get("importance", 5) < 8:
                to_delete.append(memory_id)

        for memory_id in to_delete:
            self.delete(memory_id)

        logger.info("Cleaned %d expired memories", len(to_delete))
        return len(to_delete)

    def get_context(
        self,
        current_task: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """获取当前项目上下文记忆（自动加载）"""
        context_memories = []
        for meta in self._metadata.values():
            memory = MemoryItem(**meta)
            context_memories.append(memory)

        if current_task:
            search_results = self.recall(current_task, limit=limit // 2)
            search_ids = {r.memory.id for r in search_results}

            importance_memories = sorted(
                [m for m in context_memories if m.id not in search_ids],
                key=lambda m: (m.importance, m.updated_at),
                reverse=True,
            )
            result = [r.memory for r in search_results]
            result.extend(importance_memories[: limit - len(result)])
        else:
            context_memories.sort(
                key=lambda m: (m.importance, m.updated_at),
                reverse=True,
            )
            result = context_memories[:limit]

        return result

    @staticmethod
    def _doc_fields_to_meta(memory_id: int, doc: zvec.Doc) -> dict:
        """将 zvec Doc 的 fields 转换为元数据字典"""
        fields = doc.fields or {}
        return {
            "id": memory_id,
            "content": fields.get("content", ""),
            "memory_type": fields.get("memory_type", "project_context"),
            "tags": fields.get("tags", []),
            "project_path": "",
            "importance": fields.get("importance", 5),
            "created_at": fields.get("created_at", 0.0),
            "updated_at": fields.get("updated_at", 0.0),
            "access_count": fields.get("access_count", 0),
            "last_accessed_at": fields.get("last_accessed_at", 0.0),
        }

    def _load_metadata(self) -> dict[int, dict]:
        """从 JSON 文件加载元数据"""
        if not self._metadata_file.exists():
            return {}
        try:
            data = json.loads(self._metadata_file.read_text(encoding="utf-8"))
            return {int(k): v for k, v in data.items()}
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load metadata: %s", e)
            return {}

    def _save_metadata(self) -> None:
        """保存元数据到 JSON 文件"""
        try:
            self._metadata_file.parent.mkdir(parents=True, exist_ok=True)
            self._metadata_file.write_text(
                json.dumps(self._metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("Failed to save metadata: %s", e)

    def _compute_next_id(self) -> int:
        """计算下一个可用 ID"""
        if not self._metadata:
            return 1
        return max(self._metadata.keys()) + 1
