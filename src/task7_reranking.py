"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    if not ranked_lists or top_k <= 0:
        return []

    effective_k = max(1, k)
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        if not ranked_list:
            continue
        for rank, item in enumerate(ranked_list, 1):
            if not isinstance(item, dict) or "id" not in item:
                continue
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1 / (effective_k + rank)
            # Cùng một id thì content/metadata giống nhau, chỉ khác score và
            # retrieval_method; giữ bản ghi gặp đầu tiên để kết quả ổn định.
            items.setdefault(item_id, item)

    # sorted ổn định: hai id cùng điểm giữ nguyên thứ tự xuất hiện đầu tiên.
    ranked_ids = sorted(scores, key=lambda item_id: scores[item_id], reverse=True)

    results = []
    for item_id in ranked_ids[:top_k]:
        result = dict(items[item_id])
        result["score"] = float(scores[item_id])
        result["retrieval_method"] = "hybrid"
        results.append(result)
    return results


if __name__ == "__main__":
    print("Implement rerank_rrf, then run contract tests.")
