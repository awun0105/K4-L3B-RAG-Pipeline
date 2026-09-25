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

from .query_expansion import expand_query
from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_cross_encoder, rerank_rrf
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
    return retrieve_advanced(
        query=query,
        top_k=top_k,
        score_threshold=score_threshold,
        use_reranking=use_reranking,
        use_expansion=os.getenv("ENABLE_QUERY_EXPANSION", "false").lower() == "true",
        use_cross_encoder=os.getenv("ENABLE_CROSS_ENCODER", "false").lower() == "true",
    )


def retrieve_advanced(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
    use_expansion: bool = False,
    use_cross_encoder: bool = False,
) -> list[dict]:
    """Retrieval nâng cao hỗ trợ Query Expansion và Cross-Encoder Reranking."""
    if not query.strip() or top_k <= 0:
        return []

    search_query = expand_query(query) if use_expansion else query

    # Lấy rộng hơn top_k để RRF có đủ ứng viên từ cả hai nguồn.
    pool_k = top_k * 4 if (use_expansion or use_cross_encoder) else top_k * 2
    try:
        dense = semantic_search(search_query, top_k=pool_k)
    except Exception as error:
        print(f"Dense retrieval unavailable; using BM25 fallback: {error}")
        dense = []
    try:
        sparse = lexical_search(search_query, top_k=pool_k)
    except Exception as error:
        print(f"BM25 retrieval unavailable: {error}")
        sparse = []

    if not dense and not sparse:
        return []

    if use_reranking:
        # RRF chỉ chạy một lần và chỉ gộp theo thứ hạng.
        ranked_lists = [results for results in (dense, sparse) if results]
        candidates_k = pool_k if use_cross_encoder else top_k
        hybrid = rerank_rrf(ranked_lists, top_k=candidates_k)
        if use_cross_encoder and hybrid:
            hybrid = rerank_cross_encoder(query, hybrid, top_k=top_k)
    else:
        hybrid = (dense or sparse)[:top_k]

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
