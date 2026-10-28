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
    settings = replace(Settings.from_env(), documents_path=tmp_path)
    original = index_fingerprint(settings)
    assert original == index_fingerprint(settings)
    assert original != index_fingerprint(replace(settings, embedding_model="another-model"))
    path.write_text("Segunda versão", encoding="utf-8")
    assert original != index_fingerprint(settings)


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
