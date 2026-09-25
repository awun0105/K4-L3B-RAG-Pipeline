# RAG Evaluation Result

## 1. Experiment Setup

**STATUS: MOCK DRY RUN.** The real university-admission corpus, indexing and retrieval modules have not yet been merged. The Alpha/Beta/Gamma data and `golden_dataset_mock.json` are development-only, not official university information or official metrics.

| Field | Value |
| --- | --- |
| Topic | Tuyển sinh đại học Việt Nam |
| Corpus version | Development mock corpus only |
| Date | 2026-09-25 |
| Golden cases | 16 mock dry-run cases |
| LLM provider/model | Configured through environment; offline mock fallback during development |
| Top-K | 5 |
| Threshold | Pending calibration on merged corpus |
| Config A | Dense-only |
| Config B | Hybrid + RRF |

## 2. Overall Scores

No official faithfulness, answer relevance, context recall, or context precision score is reported. Run the agreed evaluator against real grounded data before publishing metrics.

| Metric | Dense-only | Hybrid + RRF | Delta B-A |
| --- | --- | --- | --- |
| Faithfulness | Not measured | Not measured | Not measured |
| Answer relevance | Not measured | Not measured | Not measured |
| Context recall | Not measured | Not measured | Not measured |
| Context precision | Not measured | Not measured | Not measured |

## 3. Latency

The dry-run runner records per-question latency. Compare latency only after both configurations use the same real corpus and model.

## 4. A/B Comparison

Run the same corpus, prompt, evaluator, LLM and `top_k` for dense-only and hybrid + RRF. Only retrieval changes. Save outputs as `results_dense.json` and `results_hybrid.json`; no conclusion is made from mock data.

## 5. Worst Performers

| Question | Config | Observed behavior | Failure stage | Root cause | Verification method |
| --- | --- | --- | --- | --- | --- |
| Alpha có ngành Y khoa không? | Mock | Safe refusal expected | data | No evidence in mock corpus | Confirm no citation/source is rendered |
| So sánh học phí Alpha và Beta | Mock | Requires two tuition sources | retrieval | Multi-source ranking needs real validation | Inspect both cited source IDs |
| Thời tiết Hà Nội hôm nay thế nào? | Mock | Safe refusal expected | retrieval | Out-of-domain query | Confirm `sources=[]` and `retrieval_source=none` |

## 6. Recommendations

1. Merge verified admission documents and source URLs before declaring answers or metrics production-ready.
2. Complete real dense/BM25/RRF modules, then set `RAG_RETRIEVAL_MODE=real`.
3. Replace mock cases with source-grounded cases and inspect the three worst cases before tuning prompts.

## 7. Reproduction

```powershell
$env:RAG_RETRIEVAL_MODE = "mock"
python group_project/evaluation/evaluation_runner.py

$env:RAG_RETRIEVAL_MODE = "real"
python group_project/evaluation/evaluation_runner.py --dataset group_project/evaluation/golden_dataset.json --output group_project/evaluation/results_hybrid.json
```
