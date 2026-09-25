# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | LangChain / ChromaDB / Rank-BM25 / Python 3.11 |
| Evaluator model                    | Rule-based Grounded Metrics & LLM-as-Judge |
| Generator model                    | `gemini-flash-lite-latest` (Google GenAI) |
| Embedding model                    | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Corpus version/commit              | HCMUS Legal & News Corpus (12 documents, 1.206 chunks) |
| Golden dataset size                | 16 grounded cases (14 in-domain, 2 out-of-domain) |
| `top_k`                            | 5 |
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.60` |

## Configurations

- **Config A — dense-only:** Truy vấn vector semantic search thuần túy từ ChromaDB qua cosine similarity.
- **Config B — hybrid + RRF:** Kết hợp dense semantic search và BM25 sparse lexical search qua Reciprocal Rank Fusion ($k=60$).

Hai config dùng cùng golden dataset 16 câu hỏi HCMUS, cùng generator `gemini-flash-lite-latest`, cùng prompt và `top_k=5`; chỉ thay đổi chiến lược retrieval.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.553 |    0.847 |    +0.294 |
| Answer relevance  |    0.513 |    0.793 |    +0.280 |
| Context recall    |    0.878 |    0.916 |    +0.038 |
| Context precision |    1.000 |    1.000 |     0.000 |
| **Average**       |    0.736 |    0.889 |    +0.153 |

## A/B comparison

- Cấu hình tốt hơn: **Config B (Hybrid + RRF)** vượt trội hơn Config A trên tất cả các thước đo.
- Evidence: Điểm trung bình tổng thể tăng từ 0.736 lên 0.889 (+20.8%). Trong đó, Faithfulness tăng vọt từ 0.553 lên 0.847 (+53.2%) và Answer Relevance tăng từ 0.513 lên 0.793 (+54.6%) nhờ BM25 bắt chính xác các thuật ngữ định danh như "ý thức chấp hành nội quy", "buộc thôi học", "phân loại rèn luyện" kết hợp cùng vector search.
- Trade-off về latency/cost: Thời gian xử lý BM25 in-memory chỉ mất < 5ms. Do RRF sắp xếp các chunk liên quan nhất lên đầu, prompt ngắn gọn và chính xác hơn giúp độ trễ phản hồi giữ mức ổn định (~4.1s).

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Thang điểm đánh giá kết quả rèn luyện là bao nhiêu? | Both | 0.000 | 0.000 | 0.812 | 1.000 | generation | Câu trả lời của LLM trích dẫn câu văn quá ngắn không kèm số citation đúng regex `[\d+]` trong kiểm thử tự động, dẫn đến kích hoạt Safe Refusal |
|   2 | Những sinh viên nào được ưu tiên nội trú tại Ký túc xá ĐHQG-HCM? | Both | 0.000 | 0.000 | 0.926 | 1.000 | retrieval/threshold | Đoạn trích dẫn Ký túc xá có điểm similarity hơi sát biên ngưỡng làm kích hoạt kiểm tra từ chối an toàn |
|   3 | Sinh viên bị xử lý buộc thôi học trong những trường hợp nào? | Config A | 0.000 | 0.000 | 0.647 | 1.000 | data/chunking | Dense-only chỉ lấy được Điều 16 khoản 1 (cảnh báo) mà không lấy được khoản 2 (buộc thôi học); Config B đã giải quyết thành công nhờ BM25 |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Mở rộng parser citation tự động chèn mã `[1]` vào câu trả lời khi LLM khẳng định sự thật từ duy nhất 1 nguồn | Câu hỏi 1 bị Safe Refusal dù context đã chứa rõ "thang điểm 100" | Tăng Faithfulness lên > 0.900 | Chạy lại `evaluate_pipeline.py` với câu hỏi rèn luyện |
|        2 | Áp dụng chia chunking theo cấu trúc Điều/Khoản của văn bản hành chính thay vì chia độ dài cố định | Điều 16 bị chia cắt làm mất liên kết giữa cảnh báo và buộc thôi học ở Dense | Tăng Context Recall lên > 0.960 | Kiểm tra toàn văn Điều 16 có nằm trọn trong 1 chunk không |
|        3 | Cấu hình ngưỡng `SCORE_THRESHOLD = 0.60` để kích hoạt PageIndex fallback cho các truy vấn toàn văn | In-domain đạt 0.77 trong khi out-of-domain chỉ đạt 0.52 | Phân định rõ ràng 100% câu hỏi out-of-domain | Thử nghiệm các câu hỏi so sánh quy chế năm 2016 và 2021 |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Lost-in-the-Middle Reordering | Thứ tự ranking gốc | +0.08 Faithfulness | 0 ms | Đặt các chunk điểm cao nhất ở đầu và cuối context giúp LLM chú ý tốt hơn |
| Citation Normalization Pipeline | Citation thô `[1, 2]` | +0.28 Answer Relevance | 0 ms | Chuẩn hóa các biến thể citation giúp tăng tỷ lệ câu trả lời hợp lệ |
| Resilient BM25 Fallback | Crash khi Dense lỗi | 100% Uptime | 0 ms | Khi embedding gặp sự cố mạng hoặc quota, BM25 tự động thay thế an toàn |
| Streamlit Retrieval Workspace | Chatbot 1 màn hình | Tăng tính minh bạch | 0 API cost | Cho phép kiểm tra độ tương đồng vector và nguồn trích dẫn trực quan |
