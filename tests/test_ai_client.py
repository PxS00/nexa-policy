from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import types

from src.ai_client import GeminiClient


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
