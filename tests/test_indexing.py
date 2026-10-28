from dataclasses import replace

import pytest

from src.indexing import rebuild_index
from src.config import Settings


def test_embedding_count_mismatch_preserves_existing_index(tmp_path):
    (tmp_path / "policy.md").write_text("Política de férias", encoding="utf-8")

    class IncompleteEmbeddings:
        def embed_documents(self, texts):
            return []

    class UntouchedStore:
        def replace_all(self, chunks, embeddings):
            pytest.fail("Invalid embeddings must not replace the existing index")

    with pytest.raises(RuntimeError, match="quantidade de embeddings"):
        rebuild_index(replace(Settings.from_env(), documents_path=tmp_path), IncompleteEmbeddings(), UntouchedStore())
