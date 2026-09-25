"""Reusable Streamlit components; no RAG business logic is implemented here."""
from __future__ import annotations
import html, os, re
from pathlib import Path
import streamlit as st
from src.retrieval_adapter import get_retriever
from src.task10_generation import SAFE_REFUSAL

SUGGESTIONS=[
    ("💳 Học phí", "Học phí học kỳ 2 năm học 2025–2026 được thông báo như thế nào?"),
    ("🎓 Học bổng", "Điều kiện xét cấp học bổng khuyến khích học tập là gì?"),
    ("🏠 Ký túc xá", "Sinh viên cần làm gì để đăng ký vào ký túc xá?"),
    ("📋 Tốt nghiệp", "Hồ sơ xét tốt nghiệp đại học hệ chính quy cần nộp khi nào?"),
]

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def corpus_document_count() -> int:
    """Count the real standardized documents currently available to retrieval."""
    return len(list(STANDARDIZED_DIR.rglob("*.md"))) if STANDARDIZED_DIR.is_dir() else 0

def get_system_status() -> dict[str,str]:
    """Derive visible status from environment/config only, without API calls."""
    mode=os.getenv("RAG_RETRIEVAL_MODE","auto").strip().lower() or "auto"
    provider=os.getenv("LLM_PROVIDER","").strip().lower()
    key={"openai":"OPENAI_API_KEY","gemini":"GEMINI_API_KEY","anthropic":"ANTHROPIC_API_KEY"}.get(provider)
    configured=bool(key and os.getenv(key))
    try: get_retriever(); retriever="Available"
    except ValueError: retriever="Unavailable"
    if mode not in {"auto","mock","real"}: level,label="limited","Configuration required"
    elif mode=="mock": level,label="limited","Development / mock"
    elif configured: level,label="ready","Configured (not verified)"
    else: level,label="limited","LLM not configured"
    return {"level":level,"label":label,"retrieval":mode.title(),"provider":provider.title() if provider else "Unknown","api":"Configured" if configured else "Missing","retriever":retriever}

def render_sidebar() -> int:
    status=get_system_status(); sources=sum(len(m.get("sources",[])) for m in st.session_state.messages if m.get("role")=="assistant")
    document_count = corpus_document_count()
    with st.sidebar:
        st.markdown("<div class='product-mark'>HCMUS · STUDENT INFORMATION</div><div class='side-title'>UniGuide</div><div class='side-copy'>Tra cứu quy định và thông báo sinh viên từ tài liệu HCMUS đã chuẩn hóa.</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='status'><span class='{status['level']}'>● {status['label']}</span><br><b>Retrieval mode</b> · {html.escape(status['retrieval'])}<br><b>Provider</b> · {html.escape(status['provider'])}<br><b>API</b> · {html.escape(status['api'])}<br><b>Adapter</b> · {html.escape(status['retriever'])}</div>",unsafe_allow_html=True)
        st.markdown("<div class='top-k-panel'><div class='top-k-title'>Độ sâu tra cứu</div><div class='top-k-copy'>Số đoạn tài liệu dùng để tạo câu trả lời.</div></div>", unsafe_allow_html=True)
        top_k=st.slider("Top K", min_value=1, max_value=10, value=5, key="top_k")
        st.toggle("Giao diện tối", key="dark_mode")
        st.markdown(f"<div class='side-facts'>Corpus hiện có · {document_count} tài liệu<br>Phiên hiện tại · {len(st.session_state.messages)} tin nhắn<br>Nguồn đã dùng · {sources}</div>",unsafe_allow_html=True)
        if st.button("Bắt đầu cuộc trò chuyện mới",use_container_width=True): st.session_state.confirm_new_chat=True
        if st.session_state.get("confirm_new_chat"):
            st.warning("Xóa toàn bộ lịch sử cuộc trò chuyện này?")
            yes,no=st.columns(2)
            with yes:
                if st.button("Xóa",key="confirm-delete",use_container_width=True):
                    st.session_state.messages=[];st.session_state.confirm_new_chat=False;st.rerun()
            with no:
                if st.button("Giữ lại",key="cancel-delete",use_container_width=True): st.session_state.confirm_new_chat=False;st.rerun()
    return top_k

def render_header() -> None:
    count = corpus_document_count()
    st.markdown(f"<header class='app-header'><div><h1>🎓 UniGuide AI</h1><p>Quy định và thông báo sinh viên HCMUS.</p></div><div class='header-status'>{count} tài liệu đã chuẩn hóa</div></header>",unsafe_allow_html=True)

def render_empty_state() -> str|None:
    st.markdown("<section class='welcome'><div class='welcome-label'>HCMUS STUDENT INFORMATION</div><h2>Tra cứu quy định.<br>Hiểu đúng thông báo.</h2><p>Hỏi về học phí, học bổng, ký túc xá, bảo hiểm y tế, rèn luyện hoặc thủ tục tốt nghiệp. Mỗi câu trả lời đều đi kèm đoạn nguồn liên quan.</p></section><div class='section-label'>Tra cứu nhanh</div>",unsafe_allow_html=True)
    selected=None
    for row in (SUGGESTIONS[:2],SUGGESTIONS[2:]):
        cols=st.columns(2,gap="small")
        for col,(title,question) in zip(cols,row):
            with col:
                st.markdown("<div class='suggestion-button'>",unsafe_allow_html=True)
                if st.button(f"{title}\n\n{question}",key=f"suggestion-{question}",use_container_width=True): selected=question
                st.markdown("</div>",unsafe_allow_html=True)
    return selected

def _answer_html(answer:str,count:int)->str:
    """Escape answer and retain only citations that map to a source."""
    valid=set(range(1,count+1));parts=[];last=0
    for match in re.finditer(r"\[(\d+)\]",answer):
        parts.append(html.escape(answer[last:match.start()]));number=int(match.group(1))
        if number in valid: parts.append(f"<a class='citation' href='#source-{number}' aria-label='Đi tới nguồn {number}'>[{number}]</a>")
        last=match.end()
    parts.append(html.escape(answer[last:]));return "".join(parts).replace("\n","<br>")

def _snippet(content: str, limit: int = 260) -> str:
    """Trim at a natural sentence/word boundary for compact evidence cards."""
    if len(content) <= limit: return content
    candidates=[content.rfind(mark, 0, limit) for mark in (". ", ".", ";", " ")]
    cut=max(candidates)
    return content[:cut if cut > limit // 2 else limit].rstrip() + "…"

def render_source_card(index:int,source:dict)->None:
    meta=source["metadata"];content=str(source["content"]);snippet=_snippet(content)
    mock="<span class='mock'>MOCK</span>" if meta.get("data_status") else ""
    st.markdown(f"<article class='source-card' id='source-{index}'><div class='source-no'>[{index}]</div><div><div class='source-kicker'>SOURCE {index} {mock}</div><div class='source-title'>{html.escape(str(meta['title']))}</div><div class='source-file'>{html.escape(str(meta['source']))}</div><p class='snippet'>{html.escape(snippet.replace('DEVELOPMENT / MOCK DATA. ',''))}</p><div class='source-meta'>{html.escape(str(source['retrieval_method']))} · match score {float(source['score']):.2f}</div></div></article>",unsafe_allow_html=True)
    if len(content)>260:
        with st.expander("Xem đoạn nguồn"): st.write(content)

def render_message(message:dict,top_k:int)->None:
    if message["role"]=="user":
        st.markdown(f"<div class='user-row'><div class='user-bubble'>{html.escape(message['content'])}</div></div>",unsafe_allow_html=True);return
    sources=message.get("sources",[])
    st.markdown("<div class='assistant-turn'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<div class='assistant-label'><i>✦</i> UNIGUIDE</div>",unsafe_allow_html=True)
        if message.get("reformulated_query"):
            st.markdown(f"<div class='reformulated-badge'><i>✦ Ngữ cảnh hội thoại:</i> {html.escape(str(message['reformulated_query']))}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='answer-copy'>{_answer_html(message['answer'],len(sources))}</div>",unsafe_allow_html=True)
        if message["answer"]==SAFE_REFUSAL:
            status=get_system_status()
            if status["api"]=="Missing" and status["retrieval"]!="Mock":
                st.markdown("<div class='refusal'>Chưa thể tạo câu trả lời vì nhà cung cấp AI chưa được cấu hình. Hãy kiểm tra biến môi trường API.</div>",unsafe_allow_html=True)
            else:
                st.markdown("<div class='refusal'>Thông tin này chưa có bằng chứng phù hợp trong nguồn hiện tại.</div>",unsafe_allow_html=True)
        if sources:
            st.markdown(f"<div class='evidence'><b>Evidence</b><small>Grounded retrieval · {html.escape(message.get('retrieval_source','none'))} · {len(sources)} sources / top {top_k}</small></div>",unsafe_allow_html=True)
            for index,source in enumerate(sources[:3],1): render_source_card(index,source)
            if len(sources)>3:
                with st.expander(f"Xem thêm {len(sources)-3} nguồn"):
                    for index,source in enumerate(sources[3:],4): render_source_card(index,source)
    st.markdown("</div>",unsafe_allow_html=True)
