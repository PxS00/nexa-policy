from __future__ import annotations

from pathlib import Path
from contextlib import nullcontext
import hashlib
from uuid import uuid4

import chromadb
from filelock import FileLock

from src.models import SearchResult, TextChunk
from src.embedding_validation import validate_embeddings


class VectorStore:
    """Persistent Chroma collection configured for cosine similarity."""

    def __init__(self, path: Path, collection_name: str, *, persistent: bool = True) -> None:
        self._client = (chromadb.PersistentClient(path=str(path))
                        if persistent else chromadb.EphemeralClient())
        self._collection_name = collection_name
        self._collection = self._get_or_create_collection()
        lock_id = hashlib.sha256(collection_name.encode()).hexdigest()[:24]
        self._lock_path = path / f".rebuild-{lock_id}.lock" if persistent else None

    def rebuild_lock(self):
        """Serialize rebuilds of the same persistent collection across local processes."""
        return FileLock(str(self._lock_path), timeout=0) if self._lock_path else nullcontext()

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self._active_collection().count()

    def _active_collection(self):
        anchor = self._client.get_collection(self._collection_name)
        active = (anchor.metadata or {}).get("active_collection")
        return self._client.get_collection(active) if active else anchor

    def fingerprint(self) -> str | None:
        anchor = self._client.get_collection(self._collection_name)
        return (anchor.metadata or {}).get("index_fingerprint")

    def replace_all(self, chunks: list[TextChunk], embeddings: list[list[float]], *, fingerprint: str | None = None) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("A quantidade de chunks e embeddings deve ser igual.")
        validate_embeddings(embeddings, len(chunks))
        if len({chunk.id for chunk in chunks}) != len(chunks):
            raise ValueError("IDs de chunks duplicados.")

        # Stage a complete collection before changing the active pointer.
        stage_name = "stage-" + uuid4().hex
        stage = self._client.create_collection(name=stage_name, metadata={"hnsw:space": "cosine"})

        try:
            batch_size = 100
            for start in range(0, len(chunks), batch_size):
                batch = chunks[start:start + batch_size]
                batch_embeddings = embeddings[start:start + batch_size]
                stage.upsert(
                    ids=[chunk.id for chunk in batch],
                    documents=[chunk.text for chunk in batch],
                    metadatas=[chunk.metadata for chunk in batch],
                    embeddings=batch_embeddings,
                )
            if stage.count() != len(chunks):
                raise RuntimeError("A coleção temporária está incompleta; o índice anterior foi preservado.")
        except Exception:
            # Only delete before promotion; a failed pointer update can be ambiguous.
            try:
                self._client.delete_collection(stage_name)
            except Exception:
                pass
            raise
        anchor = self._client.get_collection(self._collection_name)
        metadata = {**(anchor.metadata or {}), "active_collection": stage_name}
        metadata.pop("hnsw:space", None)  # Chroma rejects this key in modify metadata.
        if fingerprint is not None:
            metadata["index_fingerprint"] = fingerprint
        else:
            metadata.pop("index_fingerprint", None)
        anchor.modify(metadata=metadata)

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k deve ser maior que zero.")
        validate_embeddings([query_embedding], 1)
        if self.count() == 0:
            return []

        collection = self._active_collection()
        count = collection.count()
        if not count:
            return []
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        return [
            SearchResult(text=document, metadata=metadata or {}, distance=float(distance))
            for document, metadata, distance in zip(documents, metadatas, distances, strict=True)
            if document
        ]
