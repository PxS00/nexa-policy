from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from src.ai_client import GeminiClient
from src.config import Settings
from src.document_loader import DocumentLoader, SUPPORTED_EXTENSIONS
from src.text_processing import chunk_sections
from src.vector_store import VectorStore


@dataclass(frozen=True, slots=True)
class IndexingResult:
    documents: int
    chunks: int


def index_fingerprint(settings: Settings) -> str:
    """Fingerprint source bytes and settings that determine the index."""
    root = settings.documents_path
    if not root.is_dir():
        raise FileNotFoundError(f"Diretório de documentos não encontrado: {root}")
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    data = {"files": files, "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "chunk_size": settings.chunk_size, "chunk_overlap": settings.chunk_overlap}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def rebuild_index(
    settings: Settings,
    ai_client: GeminiClient,
    vector_store: VectorStore,
) -> IndexingResult:
    """Rebuild the vector index from the curated document directory."""
    with vector_store.rebuild_lock():
        return _rebuild_index(settings, ai_client, vector_store)


def _rebuild_index(settings: Settings, ai_client: GeminiClient, vector_store: VectorStore) -> IndexingResult:
    before = index_fingerprint(settings)
    loader = DocumentLoader(settings.documents_path)
    sections = loader.load_directory()
    chunks = chunk_sections(sections, settings.chunk_size, settings.chunk_overlap)

    if not chunks:
        raise RuntimeError("Nenhum conteúdo válido foi encontrado para indexação.")

    embeddings: list[list[float]] = []
    batch_size = 50
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        embeddings.extend(ai_client.embed_documents([chunk.text for chunk in batch]))

    if len(embeddings) != len(chunks):
        raise RuntimeError("A quantidade de embeddings retornada não corresponde aos chunks gerados.")

    if index_fingerprint(settings) != before:
        raise RuntimeError("Os documentos mudaram durante a indexação; tente novamente.")
    vector_store.replace_all(chunks, embeddings, fingerprint=before)
    source_paths = {str(section.metadata.get("source_path", "")) for section in sections}
    return IndexingResult(documents=len(source_paths), chunks=len(chunks))
