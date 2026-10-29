from __future__ import annotations

from dataclasses import asdict

import streamlit as st

from src.ai_client import GeminiClient, GroqGenerationClient, OllamaGroqClient
from src.config import Settings
from src.indexing import index_fingerprint, rebuild_index
from src.rag import RagAgent
from src.vector_store import VectorStore

st.set_page_config(
    page_title="NexaPolicy",
    page_icon="N",
    layout="centered",
)


st.markdown("""
<style>
:root { --ink:#172b3a; --muted:#5c6e79; --paper:#f5f7f6; --line:#dbe4e2; --teal:#087f75; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width:900px; padding-top:2.2rem; padding-bottom:3rem; }
[data-testid="stHeader"] { background:transparent; }
.hero { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.5rem 1.7rem; margin:0 0 1.4rem; box-shadow:0 8px 28px #193b3510; }
.brand { color:var(--teal); font-size:.76rem; font-weight:750; letter-spacing:.14em; text-transform:uppercase; }
.hero h1 { color:var(--ink); font-size:2rem; letter-spacing:-.04em; margin:.35rem 0 .35rem; }
.hero p { color:var(--muted); margin:0; font-size:1rem; }
[data-testid="stChatMessage"] { border:1px solid var(--line); border-radius:15px; padding:.8rem 1rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) { background:#fff; }
[data-testid="stChatInput"] { border-color:#bdcfcb; border-radius:14px; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:12px; background:#fff; }
[data-testid="stSidebar"] { background:#edf2f0; border-right:1px solid var(--line); }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stMetricLabel"],
[data-testid="stSidebar"] [data-testid="stMetricValue"] { color:var(--ink) !important; }
.stButton > button { border-radius:10px; border-color:#cbdad6; color:var(--ink); }
.stButton > button:hover { border-color:var(--teal); color:var(--teal); }
.stChatInput textarea { color:var(--ink); }
.suggestions { margin-top:5rem; text-align:center; }
.suggestions h3 { color:var(--ink); font-size:1.1rem; }
.suggestions p { color:var(--muted); font-size:.9rem; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:12px; padding:.7rem; }
.stCaption { color:var(--muted); }
</style>
<div class="hero"><div class="brand">NexaPolicy · Base fictícia NexaCorp</div><h1>Encontre a política. Confira a fonte.</h1><p>Respostas documentais com trechos para você verificar. O assistente não aprova solicitações.</p></div>
""", unsafe_allow_html=True)


@st.cache_resource
def build_services():
    settings = Settings.from_env()
    settings.require_api_key()
    settings.require_generation_key()
    if settings.embedding_provider == "ollama":
        if settings.llm_provider != "groq":
            raise ValueError("Embeddings Ollama atualmente exigem LLM_PROVIDER=groq.")
        ai_client = OllamaGroqClient(settings.ollama_base_url, settings.ollama_model,
                                     settings.embedding_dimensions, settings.groq_api_key, settings.groq_model)
    else:
        client_class = GroqGenerationClient if settings.llm_provider == "groq" else GeminiClient
        extra = {"groq_api_key": settings.groq_api_key, "groq_model": settings.groq_model} if settings.llm_provider == "groq" else {}
        ai_client = client_class(
            api_key=settings.gemini_api_key,
            llm_model=settings.llm_model,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
            llm_fallback_model=settings.llm_fallback_model,
            **extra,
        )
    vector_store = VectorStore(settings.chroma_path, settings.chroma_collection)
    agent = RagAgent(settings, ai_client, vector_store)
    return settings, ai_client, vector_store, agent


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    cited = [source for source in sources if source.get("cited", False)]
    other = [source for source in sources if not source.get("cited", False)]
    for label, group in (("Fontes citadas", cited), ("Outros trechos consultados", other)):
        if not group:
            continue
        with st.expander(label):
            for source in group:
                source_name = source.get("source") or "Documento sem nome"
                category = source.get("category") or "geral"
                location = source.get("location") or "documento"

                st.write(f"[FONTE {source.get('citation_id', 1)}] {source.get('source_path') or source_name}")
                st.caption(f"Categoria: {category} · Localização: {location}")
                st.text(source.get("excerpt", ""))
                if "distance" in source:
                    st.caption(f"Distância de cosseno: {source['distance']:.3f} (menor = mais próximo; não é probabilidade)")


st.caption("Políticas de pessoas, reembolsos, conduta e onboarding")

try:
    settings, ai_client, vector_store, agent = build_services()
except Exception as exc:
    st.error(str(exc))
    st.info("Confira as chaves e o provedor no arquivo .env.")
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

try:
    saved_fingerprint = vector_store.fingerprint()
    if not saved_fingerprint or saved_fingerprint != index_fingerprint(settings):
        st.warning("A base ou a configuração de embeddings mudou (ou o índice é antigo). Reindexe para continuar.")
        st.stop()
except (OSError, ValueError) as exc:
    st.warning(f"Não foi possível verificar a versão da base: {exc}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        render_sources(message.get("sources", []))

if not st.session_state.messages:
    st.markdown('<div class="suggestions"><h3>Comece com uma destas perguntas</h3><p>Consulte os documentos fictícios e confira as fontes da resposta.</p></div>', unsafe_allow_html=True)
    suggestions = [
        "Qual a duração mínima dos períodos quando as férias são divididas?",
        "Quem solicita meus acessos internos e onde abro chamados de TI?",
        "Qual o valor do auxílio creche?",
    ]
    columns = st.columns(3)
    for column, suggestion in zip(columns, suggestions):
        with column:
            if st.button(suggestion, key=f"suggest-{suggestion}", use_container_width=True):
                st.session_state.pending_question = suggestion

question = st.chat_input("Pergunte sobre férias, reembolsos, onboarding, conduta ou benefícios...")
if not question:
    question = st.session_state.pop("pending_question", None)

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
