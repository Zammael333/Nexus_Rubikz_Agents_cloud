import hashlib
import json
import logging
import math
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VectorMemoryConfig:
    dimension: int = 128
    max_vectors: int = 10000
    similarity_top_k: int = 5
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "nexus-rubykz"
    use_pinecone: bool = False
    local_fallback: bool = True


@dataclass
class MemoryVector:
    vector_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector_id": self.vector_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "source": self.source,
        }


@dataclass
class SearchResult:
    vector: MemoryVector
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"vector": self.vector.to_dict(), "score": self.score}


class VectorMemoryStore:
    def __init__(
        self,
        config: VectorMemoryConfig | None = None,
        embedder: Callable[[str], list[float] | None] | None = None,
    ):
        self._config = config or VectorMemoryConfig()
        self._vectors: dict[str, MemoryVector] = {}
        self._total_stored = 0
        self._pinecone_available = False
        self._embedder = embedder or self._default_embedder
        logger.info(
            f"[VECTOR_MEMORY] Store initialized "
            f"(dim={self._config.dimension}, pinecone={self._config.use_pinecone})"
        )

    @staticmethod
    def _default_embedder(text: str) -> list[float]:
        hash_obj = hashlib.sha256(text.encode())
        digest = hash_obj.digest()
        vec = [b / 255.0 for b in digest]
        return vec[:128]

    def store(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "",
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> str:
        if len(self._vectors) >= self._config.max_vectors:
            oldest_key = min(
                self._vectors.keys(), key=lambda k: self._vectors[k].timestamp
            )
            self._vectors.pop(oldest_key, None)
            logger.debug(f"[VECTOR_MEMORY] Evicted oldest vector: {oldest_key[:8]}")
        text_repr = json.dumps(payload, sort_keys=True)
        if embedding is None:
            embedding = self._embedder(text_repr)
        vector = MemoryVector(
            event_type=event_type,
            payload=payload,
            embedding=embedding,
            metadata=metadata or {},
            source=source,
        )
        self._vectors[vector.vector_id] = vector
        self._total_stored += 1
        return vector.vector_id

    def search(
        self,
        query: str,
        top_k: int | None = None,
        event_type_filter: str | None = None,
    ) -> list[SearchResult]:
        k = top_k or self._config.similarity_top_k
        query_embedding = self._embedder(query)
        scored: list[SearchResult] = []
        for vector in self._vectors.values():
            if event_type_filter and vector.event_type != event_type_filter:
                continue
            similarity = self._cosine_similarity(query_embedding, vector.embedding)
            scored.append(SearchResult(vector=vector, score=similarity))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]

    def search_by_event_type(
        self, event_type: str, limit: int = 20
    ) -> list[MemoryVector]:
        results = [v for v in self._vectors.values() if v.event_type == event_type]
        results.sort(key=lambda v: v.timestamp, reverse=True)
        return results[:limit]

    def get(self, vector_id: str) -> MemoryVector | None:
        return self._vectors.get(vector_id)

    def count(self) -> int:
        return len(self._vectors)

    def total_stored(self) -> int:
        return self._total_stored

    def clear(self) -> int:
        count = len(self._vectors)
        self._vectors.clear()
        return count

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @property
    def config(self) -> VectorMemoryConfig:
        return self._config
