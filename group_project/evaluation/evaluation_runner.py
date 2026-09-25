"""Reproducible evaluation scaffold; metrics run only against real corpus data."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from src.task10_generation import generate_with_citation


ROOT = Path(__file__).parent


def run(dataset_path: Path, top_k: int = 5) -> list[dict]:
    """Capture required raw fields; evaluator scores are added by the real-data run."""
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for item in dataset:
        started = time.perf_counter()
        generated = generate_with_citation(item["question"], top_k)
        rows.append({
            "question": item["question"], "expected_answer": item["expected_answer"],
            "expected_context": item["expected_context"],
            "retrieved_context": [source["content"] for source in generated["sources"]],
            "generated_answer": generated["answer"], "sources": generated["sources"],
            "retrieval_method": generated["retrieval_source"],
            "latency": round(time.perf_counter() - started, 4),
            "faithfulness": None, "answer_relevance": None,
            "context_recall": None, "context_precision": None,
        })
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "golden_dataset_mock.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results_mock.json")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    args.output.write_text(json.dumps(run(args.dataset, args.top_k), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved raw evaluation records to {args.output}")
