"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    query_vector = embed_texts([query], input_type="query")[0]
    response = get_collection().query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma trả về một list con cho mỗi query; collection rỗng thì list con rỗng.
    ids = response.get("ids") or [[]]
    if not ids[0]:
        return []

    documents = (response.get("documents") or [[]])[0]
    metadatas = (response.get("metadatas") or [[]])[0]
    distances = (response.get("distances") or [[]])[0]

    results = []
    for item_id, content, metadata, distance in zip(
        ids[0], documents, metadatas, distances
    ):
        results.append(
            {
                "id": item_id,
                "content": content,
                # cosine distance -> similarity. Kẹp về 0 để threshold của Task 9
                # luôn so trên cùng một thang [0, 1].
                "score": max(0.0, 1.0 - float(distance)),
                "metadata": metadata,
                "retrieval_method": "dense",
            }
        )

    # sorted ổn định nên các score bằng nhau giữ nguyên thứ tự Chroma trả về.
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
