"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


load_dotenv()

DEFAULT_TOP_K = 5
DEFAULT_SCORE_THRESHOLD = 0.3


def _load_score_threshold(default: float = DEFAULT_SCORE_THRESHOLD) -> float:
    """Đọc SCORE_THRESHOLD đã hiệu chỉnh từ .env; trống/sai định dạng thì mặc định."""
    try:
        return float(os.getenv("SCORE_THRESHOLD", "").strip())
    except ValueError:
        return default


SCORE_THRESHOLD = _load_score_threshold()


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    # Lấy rộng hơn top_k để RRF có đủ ứng viên từ cả hai nguồn.
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    if use_reranking:
        # RRF chỉ chạy một lần và chỉ gộp theo thứ hạng.
        hybrid = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        hybrid = dense[:top_k]

    # Fallback quyết định bằng cosine score gốc của dense retrieval,
    # không dùng RRF score vì hai thang đo khác nhau.
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
        except Exception:
            # Provider lỗi thì giữ hybrid, không làm UI crash.
            fallback = []
        if fallback:
            return fallback

    return hybrid[:top_k]


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)
