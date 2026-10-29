from dataclasses import replace
import pytest
from src.config import Settings


@pytest.mark.parametrize("change", [
    {"top_k": 0}, {"chunk_size": 0}, {"chunk_overlap": -1},
    {"chunk_overlap": 1000, "chunk_size": 1000}, {"embedding_dimensions": 0},
    {"max_cosine_distance": float("nan")}, {"llm_provider": "unknown"},
    {"embedding_provider": "unknown"},
])
def test_invalid_settings_are_rejected(change):
    with pytest.raises(ValueError):
        replace(Settings.from_env(), **change).validate()


def test_missing_groq_key_is_reported_without_showing_other_key():
    settings = replace(Settings.from_env(), llm_provider="groq", groq_api_key="", gemini_api_key="secret")
    with pytest.raises(RuntimeError) as exc:
        settings.require_generation_key()
    assert "secret" not in str(exc.value)
