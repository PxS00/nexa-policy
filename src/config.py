from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    gemini_api_key: str
    llm_model: str
    embedding_model: str
    embedding_dimensions: int
    chroma_path: Path
    chroma_collection: str
    documents_path: Path
    chunk_size: int
    chunk_overlap: int
    top_k: int
    max_cosine_distance: float
    llm_fallback_model: str = "gemini-3.5-flash-lite"
    llm_provider: str = "gemini"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    embedding_provider: str = "gemini"
    ollama_model: str = "embeddinggemma"
    ollama_base_url: str = "http://127.0.0.1:11434"

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            llm_model=os.getenv("LLM_MODEL", "gemini-3.5-flash").strip(),
            embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip(),
            embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "768")),
            chroma_path=Path(os.getenv("CHROMA_PATH", ".chroma")),
            chroma_collection=os.getenv("CHROMA_COLLECTION", "corporate_documents").strip(),
            documents_path=Path(os.getenv("DOCUMENTS_PATH", "documents")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            top_k=int(os.getenv("TOP_K", "2")),
            max_cosine_distance=float(os.getenv("MAX_COSINE_DISTANCE", "0.65")),
            llm_fallback_model=os.getenv(
                "LLM_FALLBACK_MODEL", "gemini-3.5-flash-lite"
            ).strip(),
            llm_provider=os.getenv("LLM_PROVIDER", "gemini").strip().lower(),
            groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
            groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip(),
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", "gemini").strip().lower(),
            ollama_model=os.getenv("OLLAMA_MODEL", "embeddinggemma").strip(),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.llm_provider not in {"gemini", "groq"}:
            raise ValueError("LLM_PROVIDER deve ser gemini ou groq.")
        if self.embedding_provider not in {"gemini", "ollama"}:
            raise ValueError("EMBEDDING_PROVIDER deve ser gemini ou ollama.")
        if self.embedding_provider == "ollama" and (not self.ollama_model or not self.ollama_base_url):
            raise ValueError("OLLAMA_MODEL e OLLAMA_BASE_URL são obrigatórios.")
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE deve ser maior que zero.")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP deve ser >= 0 e menor que CHUNK_SIZE.")
        if self.top_k <= 0:
            raise ValueError("TOP_K deve ser maior que zero.")
        if self.embedding_dimensions <= 0:
            raise ValueError("EMBEDDING_DIMENSIONS deve ser maior que zero.")
        if not 0 <= self.max_cosine_distance <= 2:
            raise ValueError("MAX_COSINE_DISTANCE deve estar entre 0 e 2.")

    def require_api_key(self) -> None:
        if (self.embedding_provider == "gemini" or self.llm_provider == "gemini") and not self.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Copie .env.example para .env e informe a chave."
            )

    def require_generation_key(self) -> None:
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY não configurada no arquivo .env.")
