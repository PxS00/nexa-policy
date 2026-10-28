from __future__ import annotations

from pathlib import Path

import chromadb

from src.models import SearchResult, TextChunk


class VectorStore:
    """Persistent Chroma collection configured for cosine similarity."""

    def __init__(self, path: Path, collection_name: str, *, persistent: bool = True) -> None:
        self._client = (chromadb.PersistentClient(path=str(path))
                        if persistent else chromadb.EphemeralClient())
        self._collection_name = collection_name
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self._collection.count()

    def replace_all(self, chunks: list[TextChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("A quantidade de chunks e embeddings deve ser igual.")

        # A failed deletion must surface rather than mixing old and new content.
        self._client.delete_collection(self._collection_name)

        self._collection = self._get_or_create_collection()
        if not chunks:
            return

        batch_size = 100
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            batch_embeddings = embeddings[start:start + batch_size]
            self._collection.upsert(
                ids=[chunk.id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                metadatas=[chunk.metadata for chunk in batch],
                embeddings=batch_embeddings,
            )

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        if self.count() == 0:
            return []

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count()),
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
