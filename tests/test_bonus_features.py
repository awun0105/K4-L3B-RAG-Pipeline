"""Unit tests for Bonus Features: Query Expansion and Cross-Encoder Reranking."""

import pytest
from src.query_expansion import expand_query, DOMAIN_ACRONYMS
from src.task7_reranking import rerank_cross_encoder
from src.task9_retrieval_pipeline import retrieve_advanced


def test_query_expansion_acronyms():
    query = "Sinh viên cần bao nhiêu ĐRL để đạt loại Xuất sắc?"
    expanded = expand_query(query)
    assert "điểm rèn luyện" in expanded
    assert "ĐRL" in expanded


def test_query_expansion_topical_keywords():
    query = "Thang điểm đánh giá kết quả rèn luyện là bao nhiêu?"
    expanded = expand_query(query)
    assert "thang điểm 100" in expanded
    assert "được đánh giá bằng thang điểm 100" in expanded


def test_query_expansion_untouched():
    query = "Hôm nay thời tiết thế nào?"
    expanded = expand_query(query)
    assert expanded == query


def test_cross_encoder_rerank_contract(monkeypatch):
    candidates = [
        {
            "id": "chunk-1",
            "content": "Ký túc xá Đại học Quốc gia cơ sở Thủ Đức.",
            "metadata": {"source": "ktx.md"},
            "score": 0.03,
            "retrieval_method": "hybrid",
        },
        {
            "id": "chunk-2",
            "content": "Điểm rèn luyện sinh viên đánh giá theo thang điểm 100.",
            "metadata": {"source": "drl.md"},
            "score": 0.02,
            "retrieval_method": "hybrid",
        },
    ]

    class FakeModel:
        def predict(self, pairs):
            # Give higher score to chunk-2 for drl query
            return [-5.0, 5.0]

    import src.task7_reranking as rk
    monkeypatch.setattr(rk, "get_cross_encoder", lambda model_name: FakeModel())

    reranked = rerank_cross_encoder("thang điểm rèn luyện", candidates, top_k=2)
    assert len(reranked) == 2
    assert reranked[0]["id"] == "chunk-2"
    assert reranked[0]["retrieval_method"] == "cross-encoder"
    assert reranked[0]["score"] == 5.0


def test_conversation_memory_empty_history():
    from src.conversation_memory import reformulate_query

    query = "Điều kiện tốt nghiệp là gì?"
    assert reformulate_query(query, []) == query
    assert reformulate_query(query, None) == query


def test_conversation_memory_reformulation_with_mock_llm(monkeypatch):
    import src.task10_generation as gen
    from src.conversation_memory import reformulate_query

    history = [
        {"role": "user", "content": "Điều kiện xét học bổng khuyến khích là gì?"},
        {"role": "assistant", "answer": "Sinh viên cần điểm học tập khá và ĐRL tốt."},
    ]
    monkeypatch.setattr(
        gen,
        "call_llm",
        lambda sys_prompt, user_msg: "Điều kiện xét học bổng khuyến khích loại Xuất sắc là gì?",
    )

    result = reformulate_query("Thế còn loại Xuất sắc thì sao?", history)
    assert "học bổng khuyến khích loại Xuất sắc" in result

