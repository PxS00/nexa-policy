from pathlib import Path
from uuid import uuid4

import pytest

from src.models import TextChunk
from src.vector_store import VectorStore


def test_real_chroma_search_and_replacement():
    store = VectorStore(Path("unused"), "test-" + uuid4().hex, persistent=False)
    assert store.search([1.0, 0.0], 4) == []
    store.replace_all([TextChunk("a", "Férias", {"source_path": "rh/a.md"}),
                       TextChunk("b", "Cursos", {"source_path": "rh/b.md"})],
                      [[1.0, 0.0], [0.0, 1.0]])
    results = store.search([1.0, 0.0], 10)
    assert len(results) == 2
    assert results[0].text == "Férias"
    assert results[0].distance == pytest.approx(0.0)
    assert results[0].metadata["source_path"] == "rh/a.md"
    store.replace_all([TextChunk("c", "Nova política", {"source_path": "rh/c.md"})], [[1.0, 0.0]])
    assert store.count() == 1
    assert store.search([1.0, 0.0], 4)[0].text == "Nova política"
    with pytest.raises(ValueError):
        store.replace_all([], [[1.0, 0.0]])
    assert store.count() == 1


def test_persistent_index_can_be_reopened(tmp_path):
    path = tmp_path / "chroma"
    name = "test-" + uuid4().hex
    store = VectorStore(path, name)
    store.replace_all([TextChunk("a", "Política de férias", {"source_path": "rh/ferias.md"})], [[1.0, 0.0]])

    reopened = VectorStore(path, name)
    results = reopened.search([1.0, 0.0], 1)
    assert reopened.count() == 1
    assert results[0].text == "Política de férias"
    assert results[0].metadata["source_path"] == "rh/ferias.md"
