"""Thin retrieval boundary for Generation and Streamlit.

Replace only Task 9's implementation (or set ``RAG_RETRIEVAL_MODE=real``)
after the retrieval branch is merged.  No search algorithm lives here.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable

from .task9_retrieval_pipeline import retrieve as retrieve_real


MOCK_LABEL = "DEVELOPMENT / MOCK DATA — not a real university source"


def _mock_result(
    item_id: str, title: str, source: str, content: str, score: float
) -> dict:
    return {
        "id": item_id,
        "content": content,
        "score": score,
        "metadata": {
            "source": source,
            "title": title,
            "doc_type": "legal",
            "url": None,
            "chunk_index": 0,
            "data_status": MOCK_LABEL,
        },
        "retrieval_method": "hybrid",
    }


MOCK_CORPUS: list[dict] = [
    _mock_result("admission_alpha_methods_2026", "Đề án tuyển sinh Đại học Alpha năm 2026", "mock_alpha_admission_2026.pdf", "DEVELOPMENT / MOCK DATA. Đại học Alpha sử dụng ba phương thức: xét điểm thi tốt nghiệp THPT, xét học bạ và xét tuyển thẳng.", 0.95),
    _mock_result("admission_alpha_quota_2026", "Chỉ tiêu tuyển sinh Đại học Alpha năm 2026", "mock_alpha_quota_2026.pdf", "DEVELOPMENT / MOCK DATA. Tổng chỉ tiêu tuyển sinh dự kiến của Đại học Alpha là 5.000 sinh viên.", 0.92),
    _mock_result("admission_alpha_tuition_2026", "Thông báo học phí Đại học Alpha", "mock_alpha_tuition_2026.pdf", "DEVELOPMENT / MOCK DATA. Học phí chương trình chuẩn của Đại học Alpha dao động từ 25 đến 35 triệu đồng mỗi năm tùy ngành.", 0.90),
    _mock_result("admission_alpha_cutoff_2025", "Điểm chuẩn Đại học Alpha năm 2025", "mock_alpha_cutoff_2025.pdf", "DEVELOPMENT / MOCK DATA. Điểm chuẩn ngành Công nghệ thông tin năm 2025 theo điểm thi tốt nghiệp THPT là 26,5 điểm.", 0.88),
    _mock_result("admission_alpha_programs_2026", "Ngành đào tạo Đại học Alpha", "mock_alpha_programs_2026.pdf", "DEVELOPMENT / MOCK DATA. Đại học Alpha công bố các ngành Công nghệ thông tin, Quản trị kinh doanh và Ngôn ngữ Anh; nguồn mock không đề cập ngành Y khoa.", 0.84),
    _mock_result("admission_beta_methods_2026", "Đề án tuyển sinh Đại học Beta năm 2026", "mock_beta_admission_2026.pdf", "DEVELOPMENT / MOCK DATA. Đại học Beta xét điểm thi tốt nghiệp THPT và xét học bạ.", 0.93),
    _mock_result("admission_beta_quota_2026", "Chỉ tiêu tuyển sinh Đại học Beta năm 2026", "mock_beta_quota_2026.pdf", "DEVELOPMENT / MOCK DATA. Tổng chỉ tiêu dự kiến của Đại học Beta là 3.200 sinh viên.", 0.89),
    _mock_result("admission_beta_tuition_2026", "Thông báo học phí Đại học Beta", "mock_beta_tuition_2026.pdf", "DEVELOPMENT / MOCK DATA. Học phí chương trình chuẩn của Đại học Beta từ 22 đến 30 triệu đồng mỗi năm tùy ngành.", 0.87),
    _mock_result("admission_beta_cutoff_2025", "Điểm chuẩn Đại học Beta năm 2025", "mock_beta_cutoff_2025.pdf", "DEVELOPMENT / MOCK DATA. Điểm chuẩn ngành Công nghệ thông tin năm 2025 theo điểm thi tốt nghiệp THPT là 24,0 điểm.", 0.85),
    _mock_result("admission_gamma_tuition_2026", "Thông báo học phí Đại học Gamma", "mock_gamma_tuition_2026.pdf", "DEVELOPMENT / MOCK DATA. Học phí chương trình chuẩn của Đại học Gamma là 28 triệu đồng mỗi năm.", 0.82),
]

STOPWORDS = {"có", "của", "đại", "học", "là", "bao", "nhiêu", "năm", "trường", "và", "theo", "cho", "về", "so", "sánh"}


def mock_retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Keyword mock for UI development only; it is intentionally easy to delete."""
    tokens = set(re.findall(r"[\wÀ-ỹ]+", query.lower())) - STOPWORDS
    domain = {"tuyển", "sinh", "đại", "học", "trường", "alpha", "beta", "gamma", "học phí", "họcphí", "phí", "điểm", "chuẩn", "chỉ tiêu", "ngành", "xét", "cntt", "công", "nghệ", "thông", "tin", "phương thức", "phương", "thức"}
    if not tokens.intersection(domain):
        return []
    if "y" in tokens and "khoa" in tokens:
        return []
    scored: list[dict] = []
    for item in MOCK_CORPUS:
        haystack = f"{item['metadata']['title']} {item['content']}".lower()
        overlap = sum(token in haystack for token in tokens)
        if overlap:
            copy = {**item, "metadata": dict(item["metadata"])}
            # Development ranking only: lexical overlap makes the mock useful
            # for focused UI demonstrations without pretending to be real RRF.
            copy["score"] = round(float(item["score"]) + overlap / 10, 4)
            scored.append(copy)
    return sorted(scored, key=lambda item: (-item["score"], item["id"]))[:top_k]


def get_retriever() -> Callable[[str, int], list[dict]]:
    """Return mock, real, or automatic retrieval without leaking it into UI."""
    # Production/default path uses the indexed HCMUS corpus. Mock data is only
    # selected explicitly for UI development.
    mode = os.getenv("RAG_RETRIEVAL_MODE", "real").strip().lower()
    if mode == "mock":
        return mock_retrieve
    if mode == "real":
        return lambda query, top_k: retrieve_real(query, top_k=top_k)
    if mode == "auto":
        def automatic(query: str, top_k: int) -> list[dict]:
            try:
                results = retrieve_real(query, top_k=top_k)
                return results or mock_retrieve(query, top_k)
            except (NotImplementedError, FileNotFoundError, RuntimeError):
                return mock_retrieve(query, top_k)
        return automatic
    raise ValueError("RAG_RETRIEVAL_MODE must be auto, mock, or real")
