from dataclasses import replace
from contextlib import nullcontext

import pytest

from src.indexing import index_fingerprint, rebuild_index
from src.config import Settings


def test_embedding_count_mismatch_preserves_existing_index(tmp_path):
    (tmp_path / "policy.md").write_text("Política de férias", encoding="utf-8")

    class IncompleteEmbeddings:
        def embed_documents(self, texts):
            return []

    class UntouchedStore:
        def rebuild_lock(self):
            return nullcontext()

        def replace_all(self, chunks, embeddings):
            pytest.fail("Invalid embeddings must not replace the existing index")

    with pytest.raises(RuntimeError, match="quantidade de embeddings"):
        rebuild_index(replace(Settings.from_env(), documents_path=tmp_path), IncompleteEmbeddings(), UntouchedStore())


def test_fingerprint_detects_corpus_and_embedding_changes(tmp_path):
    path = tmp_path / "policy.md"
    path.write_text("Primeira versão", encoding="utf-8")
    settings = replace(Settings.from_env(), documents_path=tmp_path, embedding_provider="gemini")
    original = index_fingerprint(settings)
    assert original == index_fingerprint(settings)
    assert original != index_fingerprint(replace(settings, embedding_model="another-model"))
    assert original != index_fingerprint(replace(settings, embedding_provider="ollama"))
    path.write_text("Segunda versão", encoding="utf-8")
    assert original != index_fingerprint(settings)


def test_groq_with_ollama_does_not_require_gemini_key():
    settings = replace(Settings.from_env(), gemini_api_key="", llm_provider="groq", embedding_provider="ollama", groq_api_key="test")
    settings.validate()
    settings.require_api_key()
    settings.require_generation_key()


def test_documents_changed_during_embedding_do_not_replace_active_index(tmp_path):
    path = tmp_path / "policy.md"
    path.write_text("Primeira versão", encoding="utf-8")
    settings = replace(Settings.from_env(), documents_path=tmp_path)

    class ChangingClient:
        def embed_documents(self, texts):
            path.write_text("Nova versão", encoding="utf-8")
            return [[1.0, 0.0] for _ in texts]

    class UntouchedStore:
        def rebuild_lock(self):
            return nullcontext()

        def replace_all(self, *args, **kwargs):
            pytest.fail("O índice antigo deve ser preservado")

    with pytest.raises(RuntimeError, match="mudaram durante"):
        rebuild_index(settings, ChangingClient(), UntouchedStore())


def test_rebuild_removes_deleted_document_from_active_index(tmp_path):
    from src.vector_store import VectorStore
    from uuid import uuid4
    docs = tmp_path / "docs"
    docs.mkdir()
    a = docs / "a.md"
    a.write_text("Versão antiga", encoding="utf-8")
    (docs / "b.md").write_text("Documento removível", encoding="utf-8")
    settings = replace(Settings.from_env(), documents_path=docs)

    class Client:
        def embed_documents(self, texts):
            return [[1, 0] for _ in texts]

    store = VectorStore(tmp_path / "index", "test-" + uuid4().hex, persistent=False)
    rebuild_index(settings, Client(), store)
    assert store.count() == 2
    (docs / "b.md").unlink()
    a.write_text("Versão nova", encoding="utf-8")
    rebuild_index(settings, Client(), store)
    assert store.count() == 1
    assert store.search([1, 0], 4)[0].text == "Versão nova"
