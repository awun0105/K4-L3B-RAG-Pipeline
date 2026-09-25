"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re

from .task4_chunking_indexing import get_collection


CORPUS: list[dict] = []
_CACHED_BM25 = None
_CACHED_CORPUS_ID = None

# Tokenize dùng chung cho corpus và query để BM25 so khớp nhất quán.
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Tách token chữ/số, bỏ dấu câu và ký hiệu markdown."""
    return _TOKEN_PATTERN.findall(text.lower())


def load_corpus() -> list[dict]:
    """Nạp đúng các chunk đã index trong ChromaDB (cùng corpus với Task 5)."""
    response = get_collection().get(include=["documents", "metadatas"])
    return [
        {"id": item_id, "content": content, "metadata": metadata}
        for item_id, content, metadata in zip(
            response.get("ids") or [],
            response.get("documents") or [],
            response.get("metadatas") or [],
        )
    ]


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    tokenized = [_tokenize(item["content"]) for item in corpus]
    return BM25Okapi(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    global CORPUS, _CACHED_BM25, _CACHED_CORPUS_ID

    if top_k <= 0:
        return []

    # CORPUS có thể do người dùng gán trước; nếu còn rỗng thì nạp một lần từ
    # ChromaDB để BM25 chạy trên đúng corpus chunks mà Task 5 đang query.
    if not CORPUS:
        CORPUS = load_corpus()
    if not CORPUS:
        return []

    corpus_id = id(CORPUS), len(CORPUS)
    if _CACHED_BM25 is None or _CACHED_CORPUS_ID != corpus_id:
        _CACHED_BM25 = build_bm25_index(CORPUS)
        _CACHED_CORPUS_ID = corpus_id

    scores = _CACHED_BM25.get_scores(_tokenize(query))


    # sorted ổn định nên các score bằng nhau giữ nguyên thứ tự corpus.
    order = sorted(range(len(CORPUS)), key=lambda index: -float(scores[index]))

    # BM25 có thể cho mọi điểm bằng 0 (corpus nhỏ làm idf = 0, hoặc không token
    # nào khớp). Khi đã có chunk điểm dương thì bỏ các chunk điểm 0 cho sạch kết
    # quả; nếu tất cả bằng 0 thì vẫn trả thứ hạng ổn định thay vì list rỗng.
    positive = [index for index in order if scores[index] > 0]
    ranked = positive or order

    results = []
    for index in ranked[:top_k]:
        item = CORPUS[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": float(scores[index]),
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
