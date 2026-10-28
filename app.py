from __future__ import annotations

from dataclasses import asdict

import streamlit as st

from src.ai_client import GeminiClient
from src.config import Settings
from src.indexing import rebuild_index
from src.rag import RagAgent
from src.vector_store import VectorStore

st.set_page_config(
    page_title="NexaPolicy",
    page_icon="🤖",
    layout="centered",
)


@st.cache_resource
def build_services():
    settings = Settings.from_env()
    settings.require_api_key()
    ai_client = GeminiClient(
        api_key=settings.gemini_api_key,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        embedding_dimensions=settings.embedding_dimensions,
        llm_fallback_model=settings.llm_fallback_model,
    )
    vector_store = VectorStore(settings.chroma_path, settings.chroma_collection)
    agent = RagAgent(settings, ai_client, vector_store)
    return settings, ai_client, vector_store, agent


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander("Fontes consultadas"):
        for source in sources:
            source_name = source.get("source") or "Documento sem nome"
            category = source.get("category") or "geral"
            location = source.get("location") or "documento"

            st.write(f"[FONTE {source.get('citation_id', 1)}] {source.get('source_path') or source_name}")
            st.caption(f"Categoria: {category} · Localização: {location}")
            st.text(source.get("excerpt", ""))
            if "distance" in source:
                st.caption(f"Distância de cosseno: {source['distance']:.3f} (menor = mais próximo; não é probabilidade)")


st.title("NexaPolicy")
st.caption("Consulte políticas de férias, reembolsos e onboarding da empresa fictícia NexaCorp com evidências documentais.")
st.caption("Demonstração de portfólio com dados fictícios. Confira os trechos recuperados antes de tomar decisões.")

try:
    settings, ai_client, vector_store, agent = build_services()
except Exception as exc:
    st.error(str(exc))
    st.info("Configure a variável GEMINI_API_KEY antes de iniciar a aplicação.")
    st.stop()

with st.sidebar:
    st.header("Base de conhecimento")
    st.metric("Chunks indexados", vector_store.count())

    if st.button("Reindexar documentos", use_container_width=True):
        try:
            with st.spinner("Processando documentos e atualizando embeddings..."):
                result = rebuild_index(settings, ai_client, vector_store)
            st.success(f"{result.documents} documentos e {result.chunks} chunks indexados.")
            st.rerun()
        except Exception as exc:
            st.error(f"Falha ao reindexar: {exc}")

    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if vector_store.count() == 0:
    try:
        with st.spinner("Preparando a base de conhecimento pela primeira vez..."):
            result = rebuild_index(settings, ai_client, vector_store)
        st.success(f"Base pronta: {result.documents} documentos e {result.chunks} chunks indexados.")
    except Exception as exc:
        st.error(f"Não foi possível preparar a base: {exc}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        render_sources(message.get("sources", []))

question = st.chat_input("Pergunte sobre férias, reembolsos, onboarding, conduta ou benefícios...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando documentos..."):
                response = agent.ask(question)

            st.markdown(response.answer)
            sources = [asdict(source) for source in response.sources]
            render_sources(sources)
            st.session_state.messages.append(
                {"role": "assistant", "content": response.answer, "sources": sources}
            )
        except Exception as exc:
            message = f"Não foi possível processar a pergunta: {exc}"
            st.error(message)
            st.session_state.messages.append({"role": "assistant", "content": message})
