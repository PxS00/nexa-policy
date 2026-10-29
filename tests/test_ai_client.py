from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import httpx
from google.genai import types

from src.ai_client import GeminiClient, GroqGenerationClient, OllamaEmbeddingClient, RETRYABLE_STATUS_CODES


def test_quota_errors_are_not_automatically_retried():
    assert 429 not in RETRYABLE_STATUS_CODES


@pytest.mark.parametrize("reason", [types.FinishReason.MAX_TOKENS, types.FinishReason.SAFETY, None])
def test_interrupted_generation_does_not_return_partial_text(reason):
    client = GeminiClient.__new__(GeminiClient)
    client._client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=SimpleNamespace(
        candidates=[SimpleNamespace(finish_reason=reason)], text="Resposta incompleta [FONTE 1]"))))
    with pytest.raises(RuntimeError, match="não terminou normalmente"):
        client._generate_with_model("model", "prompt")


def test_completed_generation_returns_text():
    client = GeminiClient.__new__(GeminiClient)
    client._client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=SimpleNamespace(
        candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)], text=" Resposta [FONTE 1] "))))
    assert client._generate_with_model("model", "prompt") == "Resposta [FONTE 1]"


def test_groq_generation_and_truncation(monkeypatch):
    client = GroqGenerationClient.__new__(GroqGenerationClient)
    client._groq_api_key = "test-secret"
    client._groq_model = "test-model"
    payload = {"choices": [{"finish_reason": "stop", "message": {"content": " Evidência [FONTE 1] "}}]}
    response = SimpleNamespace(is_error=False, json=lambda: payload)
    post = Mock(return_value=response)
    monkeypatch.setattr("src.ai_client.httpx.post", post)
    assert client.generate("Pergunta") == "Evidência [FONTE 1]"
    assert post.call_args.kwargs["json"]["model"] == "test-model"
    payload["choices"][0]["finish_reason"] = "length"
    with pytest.raises(RuntimeError, match="não terminou normalmente"):
        client.generate("Pergunta")


def test_groq_error_does_not_expose_credentials(monkeypatch):
    client = GroqGenerationClient.__new__(GroqGenerationClient)
    client._groq_api_key = "test-secret"
    client._groq_model = "test-model"
    monkeypatch.setattr("src.ai_client.httpx.post", Mock(return_value=SimpleNamespace(is_error=True, status_code=429)))
    with pytest.raises(RuntimeError, match="HTTP 429") as exc:
        client.generate("Pergunta")
    assert "test-secret" not in str(exc.value)
    assert exc.value.code == 429


def test_groq_timeout_is_sanitized(monkeypatch):
    client = GroqGenerationClient.__new__(GroqGenerationClient)
    client._groq_api_key = "secret"
    client._groq_model = "test-model"
    monkeypatch.setattr("src.ai_client.httpx.post", Mock(side_effect=httpx.ReadTimeout("secret details")))
    with pytest.raises(RuntimeError) as exc:
        client.generate("Pergunta")
    assert "secret" not in str(exc.value)


@pytest.mark.parametrize("data", [[], None, {"choices": [None]}, {"choices": [{"finish_reason": "stop", "message": None}]}])
def test_groq_malformed_response_is_rejected(monkeypatch, data):
    client = GroqGenerationClient.__new__(GroqGenerationClient)
    client._groq_api_key = "test"
    client._groq_model = "test"
    monkeypatch.setattr("src.ai_client.httpx.post", Mock(return_value=SimpleNamespace(is_error=False, json=lambda: data)))
    with pytest.raises(RuntimeError):
        client.generate("Pergunta")


def test_ollama_uses_distinct_document_and_query_prompts(monkeypatch):
    response = SimpleNamespace(raise_for_status=Mock(), json=lambda: {"embeddings": [[0.1, 0.2]]})
    post = Mock(return_value=response)
    monkeypatch.setattr("src.ai_client.httpx.post", post)
    client = OllamaEmbeddingClient("http://localhost:11434", "embeddinggemma", 2)
    assert client.embed_documents(["Férias"]) == [[0.1, 0.2]]
    assert post.call_args.kwargs["json"]["input"] == ["title: none | text: Férias"]
    assert post.call_args.kwargs["json"]["truncate"] is False
    assert client.embed_query("Férias?") == [0.1, 0.2]
    assert post.call_args.kwargs["json"]["input"] == ["task: question answering | query: Férias?"]
    assert client.embed_documents([]) == []


def test_ollama_rejects_wrong_embedding_dimensions(monkeypatch):
    response = SimpleNamespace(raise_for_status=Mock(), json=lambda: {"embeddings": [[0.1]]})
    monkeypatch.setattr("src.ai_client.httpx.post", Mock(return_value=response))
    with pytest.raises(RuntimeError, match="dimensão"):
        OllamaEmbeddingClient("http://localhost:11434", "embeddinggemma", 2).embed_query("Pergunta")
