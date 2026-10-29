from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import types

from src.ai_client import GeminiClient, GroqGenerationClient


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
