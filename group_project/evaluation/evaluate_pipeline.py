"""Evaluation runner for RAG pipeline comparing Config A (Dense-only) and Config B (Hybrid + RRF)."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from src.task5_semantic_search import semantic_search
from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import (
    SAFE_REFUSAL,
    SYSTEM_PROMPT,
    call_llm,
    format_context,
    reorder_for_llm,
    _citation_numbers,
)

EVAL_DIR = Path(__file__).parent


def calculate_context_recall(expected_answer: str, retrieved_texts: list[str]) -> float:
    """Kiểm tra tỷ lệ từ khóa quan trọng của expected answer xuất hiện trong retrieved context."""
    if not retrieved_texts:
        return 0.0
    words = [w.lower() for w in re.findall(r"[\wÀ-ỹ]+", expected_answer) if len(w) > 2]
    if not words:
        return 1.0
    full_context = " ".join(retrieved_texts).lower()
    matches = sum(1 for w in words if w in full_context)
    return min(1.0, round(matches / len(words), 3))


def calculate_context_precision(expected_answer: str, retrieved_chunks: list[dict]) -> float:
    """Mean Reciprocal Rank (MRR) của chunk liên quan đầu tiên trong kết quả."""
    if not retrieved_chunks:
        return 0.0
    words = set(w.lower() for w in re.findall(r"[\wÀ-ỹ]+", expected_answer) if len(w) > 2)
    if not words:
        return 1.0
    for rank, chunk in enumerate(retrieved_chunks, 1):
        content = chunk["content"].lower()
        overlap = sum(1 for w in words if w in content)
        if overlap >= max(2, int(len(words) * 0.3)):
            return round(1.0 / rank, 3)
    return 0.0


def evaluate_config(
    dataset: list[dict],
    mode: str = "hybrid",
    top_k: int = 5,
) -> tuple[list[dict], dict]:
    results = []
    
    for item in dataset:
        q = item["question"]
        expected_ans = item["expected_answer"]
        expected_ctx = item["expected_context"]
        
        start_time = time.perf_counter()
        
        # 1. Retrieval
        if mode == "dense":
            chunks = semantic_search(q, top_k=top_k)
            retrieval_method = "dense"
        else:
            chunks = retrieve(q, top_k=top_k, use_reranking=True)
            retrieval_method = chunks[0]["retrieval_method"] if chunks else "none"
        
        retrieval_latency = time.perf_counter() - start_time
        
        # 2. Generation
        if not chunks:
            generated_answer = SAFE_REFUSAL
            gen_sources = []
        else:
            sources = sorted(chunks, key=lambda item: (-float(item["score"]), item["id"]))
            context = format_context(reorder_for_llm(sources))
            user_message = f"CONTEXT:\n{context}\n\nCÂU HỎI: {q}"
            try:
                ans = call_llm(SYSTEM_PROMPT, user_message)
                valid_numbers = set(range(1, len(sources) + 1))
                numbers = _citation_numbers(ans)
                if ans == SAFE_REFUSAL or not numbers or not numbers <= valid_numbers:
                    generated_answer = SAFE_REFUSAL
                    gen_sources = []
                else:
                    generated_answer = ans
                    gen_sources = sources
            except Exception:
                generated_answer = SAFE_REFUSAL
                gen_sources = []
        
        total_latency = round(time.perf_counter() - start_time, 3)
        retrieved_texts = [c["content"] for c in chunks]
        
        # 3. Metrics calculation
        is_safe_expected = "chưa đủ để xác minh" in expected_ans.lower()
        if is_safe_expected:
            # Câu hỏi out-of-domain: Safe refusal là đúng 100%
            if generated_answer == SAFE_REFUSAL:
                faithfulness = 1.0
                relevance = 1.0
                recall = 1.0
                precision = 1.0
            else:
                faithfulness = 0.0
                relevance = 0.2
                recall = 0.0
                precision = 0.0
        else:
            recall = calculate_context_recall(expected_ans, retrieved_texts)
            precision = calculate_context_precision(expected_ans, chunks)
            
            # Faithfulness: câu trả lời có được trích từ sources không
            if generated_answer == SAFE_REFUSAL:
                faithfulness = 0.0
                relevance = 0.0
            else:
                # Kiểm tra tỷ lệ từ khóa câu trả lời có trong context
                ans_words = [w.lower() for w in re.findall(r"[\wÀ-ỹ]+", generated_answer) if len(w) > 2]
                ctx_combined = " ".join(retrieved_texts).lower()
                supported = sum(1 for w in ans_words if w in ctx_combined)
                faithfulness = min(1.0, round(supported / max(1, len(ans_words)), 3))
                
                # Relevance: câu trả lời có chứa từ khóa câu hỏi không
                q_words = [w.lower() for w in re.findall(r"[\wÀ-ỹ]+", q) if len(w) > 2]
                rel_matches = sum(1 for w in q_words if w in generated_answer.lower())
                relevance = min(1.0, round(0.5 + 0.5 * (rel_matches / max(1, len(q_words))), 3))

        record = {
            "question": q,
            "expected_answer": expected_ans,
            "expected_context": expected_ctx,
            "generated_answer": generated_answer,
            "retrieval_method": retrieval_method,
            "sources": [s["id"] for s in gen_sources],
            "latency": total_latency,
            "faithfulness": faithfulness,
            "answer_relevance": relevance,
            "context_recall": recall,
            "context_precision": precision,
        }
        results.append(record)
        print(f"[{mode.upper()}] Q: {q[:35]}... -> F={faithfulness}, R={relevance}, Rec={recall}, Prec={precision}, Time={total_latency}s")

    # Aggregate
    n = len(results)
    avg_scores = {
        "faithfulness": round(sum(r["faithfulness"] for r in results) / n, 3),
        "answer_relevance": round(sum(r["answer_relevance"] for r in results) / n, 3),
        "context_recall": round(sum(r["context_recall"] for r in results) / n, 3),
        "context_precision": round(sum(r["context_precision"] for r in results) / n, 3),
        "latency": round(sum(r["latency"] for r in results) / n, 3),
    }
    avg_scores["average"] = round(
        (avg_scores["faithfulness"] + avg_scores["answer_relevance"] + avg_scores["context_recall"] + avg_scores["context_precision"]) / 4,
        3
    )
    return results, avg_scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=EVAL_DIR / "golden_dataset.json")
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    print(f"Loaded {len(dataset)} evaluation cases from {args.dataset}")

    print("\n=== EVALUATING CONFIG A (DENSE ONLY) ===")
    results_a, summary_a = evaluate_config(dataset, mode="dense", top_k=5)
    (EVAL_DIR / "results_dense.json").write_text(json.dumps(results_a, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== EVALUATING CONFIG B (HYBRID + RRF) ===")
    results_b, summary_b = evaluate_config(dataset, mode="hybrid", top_k=5)
    (EVAL_DIR / "results_hybrid.json").write_text(json.dumps(results_b, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n================== SUMMARY TABLE ==================")
    print(f"Metric             | Config A (Dense) | Config B (Hybrid) | Delta B-A")
    print(f"-------------------|------------------|-------------------|----------")
    for metric in ["faithfulness", "answer_relevance", "context_recall", "context_precision", "average", "latency"]:
        va = summary_a.get(metric, 0.0)
        vb = summary_b.get(metric, 0.0)
        delta = round(vb - va, 3)
        prefix = "+" if delta > 0 else ""
        print(f"{metric:<18} | {va:<16} | {vb:<17} | {prefix}{delta}")


if __name__ == "__main__":
    main()
