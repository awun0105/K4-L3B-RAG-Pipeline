"""UniGuide AI UI orchestration. RAG backend contracts remain unchanged."""
from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from src.task10_generation import generate_with_citation
from ui.components import render_empty_state, render_header, render_message, render_sidebar
from ui.data_views import render_corpus_view, render_retrieval_view
from ui.styles import APP_CSS, DARK_OVERRIDE


load_dotenv()
st.set_page_config(
    page_title="UniGuide AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


def handle_query(query: str, top_k: int) -> None:
    """Single UI entry point for both chat input and suggestion cards."""
    if not query.strip():
        return
    st.session_state.messages.append({"role": "user", "content": query})
    with st.spinner("Đang tìm nguồn phù hợp…"):
        result = generate_with_citation(query, top_k)
    st.session_state.messages.append({"role": "assistant", **result})
    st.rerun()


st.markdown(
    APP_CSS + (DARK_OVERRIDE if st.session_state.dark_mode else ""),
    unsafe_allow_html=True,
)
top_k = render_sidebar()
render_header()

chat_tab, corpus_tab, retrieval_tab = st.tabs(
    ["💬 Hỏi đáp", "📚 Kho tài liệu", "🔎 Retrieval workspace"]
)

with chat_tab:
    if not st.session_state.messages:
        suggestion = render_empty_state()
        if suggestion:
            handle_query(suggestion, top_k)
    for message in st.session_state.messages:
        render_message(message, top_k)
    query = st.chat_input("Hỏi về học phí, học bổng, ký túc xá, tốt nghiệp…")
    if query:
        handle_query(query, top_k)

with corpus_tab:
    render_corpus_view()

with retrieval_tab:
    render_retrieval_view()
