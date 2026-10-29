from unittest.mock import patch
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.models import AgentResponse, SourceReference


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
        assert app.title[0].value == "NexaPolicy"
        app.chat_input[0].set_value("Quantos dias?").run()
        assert not app.exception
        assert app.text[0].value == "Evidência de teste: 30 dias"
        assert [x.label for x in app.expander] == ["Fontes citadas", "Outros trechos consultados"]
        assert app.session_state.messages[-1]["sources"][0]["source_path"] == "rh/policy.md"
        app.run()
        assert app.text[0].value == "Evidência de teste: 30 dias"
