from unittest.mock import patch
from pathlib import Path
import pytest
import streamlit as st

from streamlit.testing.v1 import AppTest

from src.models import AgentResponse, SourceReference
from src.ai_client import ProviderRequestError, IncompleteGeneration
from src.rag import InvalidCitations


@pytest.fixture(autouse=True)
def isolated_service_cache():
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def test_chat_renders_evidence_and_retains_it_in_history():
    class Store:
        def __init__(self, *args):
            pass

        def count(self):
            return 5

        def fingerprint(self):
            from src.indexing import index_fingerprint
            from src.config import Settings
            return index_fingerprint(Settings.from_env())

    class Agent:
        def __init__(self, *args):
            pass

        def ask(self, question):
            return AgentResponse("São 30 dias [FONTE 1].", (SourceReference(
                "policy.md", "rh", "seção: document", 1, "rh/policy.md", "Evidência de teste: 30 dias", 0.2, True),
                SourceReference("other.md", "geral", "documento", 2, "other.md", "Outro trecho", 0.3, False)))

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key-no-network", "LLM_PROVIDER": "gemini", "EMBEDDING_PROVIDER": "gemini"}), \
         patch("src.ai_client.GeminiClient"), patch("src.vector_store.VectorStore", Store), \
         patch("src.rag.RagAgent", Agent):
        app = AppTest.from_file(Path("app.py").resolve()).run(timeout=20)
        assert not app.exception
        assert any("Encontre a política" in item.value for item in app.markdown)
        app.chat_input[0].set_value("Quantos dias?").run()
        assert not app.exception
        assert app.text[0].value == "Evidência de teste: 30 dias"
        assert [x.label for x in app.expander] == ["Fontes citadas", "Outros trechos consultados"]
        assert app.session_state.messages[-1]["sources"][0]["source_path"] == "rh/policy.md"
        app.run()
        assert app.text[0].value == "Evidência de teste: 30 dias"


@pytest.mark.parametrize("failure", [ProviderRequestError("Groq", 429), IncompleteGeneration("length"), InvalidCitations("Referência inválida")])
def test_chat_failure_is_visible_and_does_not_attach_sources(failure):
    class Store:
        def __init__(self, *args):
            pass
        def count(self):
            return 5
        def fingerprint(self):
            from src.indexing import index_fingerprint
            from src.config import Settings
            return index_fingerprint(Settings.from_env())

    class Agent:
        def __init__(self, *args):
            pass
        def ask(self, question):
            raise failure

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake", "LLM_PROVIDER": "gemini", "EMBEDDING_PROVIDER": "gemini"}), \
         patch("src.ai_client.GeminiClient"), patch("src.vector_store.VectorStore", Store), \
         patch("src.rag.RagAgent", Agent):
        app = AppTest.from_file(Path("app.py").resolve()).run(timeout=20)
        app.chat_input[0].set_value("Pergunta").run()
        assert not app.exception
        assert "Não foi possível processar" in app.error[0].value
        assert not app.session_state.messages[-1].get("sources")

