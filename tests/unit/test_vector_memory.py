from app.vector_memory.store import (
    MemoryVector,
    SearchResult,
    VectorMemoryConfig,
    VectorMemoryStore,
)


class TestMemoryVector:
    def test_to_dict(self):
        mv = MemoryVector(
            event_type="test_event",
            payload={"key": "value"},
            source="test_source",
        )
        d = mv.to_dict()
        assert d["event_type"] == "test_event"
        assert d["payload"] == {"key": "value"}
        assert d["source"] == "test_source"

    def test_default_vector_id(self):
        mv = MemoryVector()
        assert len(mv.vector_id) > 0


class TestSearchResult:
    def test_to_dict(self):
        mv = MemoryVector(event_type="test")
        sr = SearchResult(vector=mv, score=0.95)
        d = sr.to_dict()
        assert d["score"] == 0.95
        assert d["vector"]["event_type"] == "test"


class TestVectorMemoryStore:
    def test_initial_state(self):
        store = VectorMemoryStore()
        assert store.count() == 0
        assert store.total_stored() == 0

    def test_store_and_retrieve(self):
        store = VectorMemoryStore()
        vid = store.store("test_event", {"msg": "hello"}, source="worker1")
        assert len(vid) > 0
        assert store.count() == 1
        assert store.total_stored() == 1

    def test_get_existing(self):
        store = VectorMemoryStore()
        vid = store.store("test_event", {"msg": "hello"})
        retrieved = store.get(vid)
        assert retrieved is not None
        assert retrieved.event_type == "test_event"

    def test_get_nonexistent(self):
        store = VectorMemoryStore()
        assert store.get("nonexistent-id") is None

    def test_default_embedder_returns_128_dims(self):
        vec = VectorMemoryStore._default_embedder("hello world")
        assert len(vec) == 32
        assert all(isinstance(v, float) for v in vec)

    def test_cosine_similarity_identical(self):
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        sim = VectorMemoryStore._cosine_similarity(a, b)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        sim = VectorMemoryStore._cosine_similarity(a, b)
        assert abs(sim) < 1e-6

    def test_cosine_similarity_empty(self):
        assert VectorMemoryStore._cosine_similarity([], []) == 0.0

    def test_search_returns_top_k(self):
        store = VectorMemoryStore()
        store.store("event_a", {"x": 1})
        store.store("event_b", {"x": 2})
        store.store("event_c", {"x": 3})
        results = store.search("test query", top_k=2)
        assert len(results) == 2

    def test_search_empty_store(self):
        store = VectorMemoryStore()
        results = store.search("anything")
        assert results == []

    def test_search_by_event_type(self):
        store = VectorMemoryStore()
        store.store("type_a", {"k": "v1"})
        store.store("type_b", {"k": "v2"})
        store.store("type_a", {"k": "v3"})
        results = store.search_by_event_type("type_a")
        assert len(results) == 2
        results = store.search_by_event_type("type_b")
        assert len(results) == 1

    def test_search_by_event_type_empty(self):
        store = VectorMemoryStore()
        assert store.search_by_event_type("nonexistent") == []

    def test_clear(self):
        store = VectorMemoryStore()
        store.store("test", {"k": "v"})
        store.store("test", {"k": "v"})
        assert store.count() == 2
        cleared = store.clear()
        assert cleared == 2
        assert store.count() == 0

    def test_eviction_when_full(self):
        config = VectorMemoryConfig(max_vectors=3)
        store = VectorMemoryStore(config=config)
        store.store("a", {"n": 1})
        store.store("b", {"n": 2})
        store.store("c", {"n": 3})
        assert store.count() == 3
        store.store("d", {"n": 4})
        assert store.count() == 3

    def test_total_stored_tracks_all(self):
        config = VectorMemoryConfig(max_vectors=3)
        store = VectorMemoryStore(config=config)
        store.store("a", {"n": 1})
        store.store("b", {"n": 2})
        store.store("c", {"n": 3})
        store.store("d", {"n": 4})
        assert store.total_stored() == 4

    def test_config_property(self):
        config = VectorMemoryConfig(dimension=64, max_vectors=500)
        store = VectorMemoryStore(config=config)
        assert store.config.dimension == 64
        assert store.config.max_vectors == 500

    def test_custom_embedder(self):
        def custom_embedder(text: str) -> list[float]:
            return [1.0, 0.0]

        store = VectorMemoryStore(embedder=custom_embedder)
        vid = store.store("test", {"k": "v"})
        vec = store.get(vid)
        assert vec is not None
        assert vec.embedding == [1.0, 0.0]

    def test_search_with_event_type_filter(self):
        store = VectorMemoryStore()
        store.store("login", {"user": "a"}, source="src1")
        store.store("purchase", {"item": "b"}, source="src2")
        store.store("login", {"user": "c"}, source="src3")
        results = store.search("user", event_type_filter="login")
        assert len(results) == 2
        for r in results:
            assert r.vector.event_type == "login"

    def test_cosine_similarity_zero_norm(self):
        assert VectorMemoryStore._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
