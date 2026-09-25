"""Read-only corpus and retrieval inspection views for the Streamlit UI."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import streamlit as st

from src.task4_chunking_indexing import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKING_METHOD,
    chunk_documents,
    load_documents,
)


@st.cache_data(show_spinner=False)
def corpus_snapshot() -> tuple[list[dict], list[dict]]:
    """Load real standardized documents and their local chunks for inspection."""
    documents = load_documents()
    return documents, chunk_documents(documents)


def render_corpus_view() -> None:
    """Show the standardized source documents without changing the corpus."""
    try:
        documents, chunks = corpus_snapshot()
    except Exception as error:
        st.error(f"Không thể đọc kho tài liệu: {error}")
        return

    legal_count = sum(item["metadata"]["doc_type"] == "legal" for item in documents)
    news_count = len(documents) - legal_count
    a, b, c = st.columns(3)
    a.metric("Tài liệu chuẩn hóa", len(documents))
    b.metric("Quy định / chính sách", legal_count)
    c.metric("Thông báo", news_count)
    st.caption(f"Kho hiện có tạo ra {len(chunks)} chunks để phục vụ retrieval.")

    labels = {
        item["id"]: f"{item['metadata']['title']} · {item['metadata']['doc_type']}"
        for item in documents
    }
    selected_id = st.selectbox("Chọn tài liệu để xem", list(labels), format_func=labels.get)
    document = next(item for item in documents if item["id"] == selected_id)
    metadata = document["metadata"]
    st.markdown("<div class='document-sheet'>", unsafe_allow_html=True)
    st.subheader(metadata["title"])
    st.caption(f"Nguồn: {metadata['source']} · Loại: {metadata['doc_type']}")
    if metadata.get("url"):
        st.link_button("Mở nguồn gốc", metadata["url"], use_container_width=False)
    with st.expander("Xem nội dung Markdown chuẩn hóa", expanded=True):
        st.markdown(document["content"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_retrieval_view() -> None:
    """Explain and preview the retrieval-ready chunks using real local data."""
    try:
        documents, chunks = corpus_snapshot()
    except Exception as error:
        st.error(f"Không thể đọc chunks: {error}")
        return

    st.markdown("### Retrieval workspace")
    st.caption("Các thông số và chunks dưới đây được đọc trực tiếp từ corpus hiện tại.")
    a, b, c, d = st.columns(4)
    a.metric("Documents", len(documents))
    b.metric("Chunks", len(chunks))
    c.metric("Chunk size", CHUNK_SIZE)
    d.metric("Overlap", CHUNK_OVERLAP)
    st.markdown(f"<div class='retrieval-note'>Strategy: <b>{CHUNKING_METHOD}</b> · Dense search + BM25 → RRF · PageIndex là fallback tùy chọn.</div>", unsafe_allow_html=True)

    counts = Counter(item["metadata"]["doc_type"] for item in chunks)
    st.caption("Phân bố chunk: " + " · ".join(f"{kind}: {count}" for kind, count in sorted(counts.items())))
    doc_ids = [item["id"] for item in documents]
    selected_id = st.selectbox("Lọc chunks theo tài liệu", doc_ids, format_func=lambda item_id: next(item["metadata"]["title"] for item in documents if item["id"] == item_id), key="chunk-document")
    document_chunks = [item for item in chunks if item["id"].startswith(f"{selected_id}::")]
    st.caption(f"{len(document_chunks)} chunks từ tài liệu đã chọn")
    for chunk in document_chunks:
        index = chunk["metadata"]["chunk_index"]
        with st.expander(f"Chunk {index + 1} · {len(chunk['content'])} ký tự"):
            st.write(chunk["content"])

    index_state = "Chưa thấy thư mục index"
    if CHROMA_DIR.exists():
        try:
            from src.task4_chunking_indexing import get_collection
            index_state = f"ChromaDB đã index {get_collection().count()} chunks"
        except Exception as error:
            index_state = f"Index tồn tại nhưng chưa đọc được: {error}"
    st.info(index_state, icon="🔎")
