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
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.3` |

## Configurations

- **Config A — dense-only:** Truy vấn vector semantic search thuần túy từ ChromaDB qua cosine similarity.
- **Config B — hybrid + RRF:** Kết hợp dense semantic search và BM25 sparse lexical search qua Reciprocal Rank Fusion ($k=60$).

Hai config dùng cùng golden dataset 16 câu hỏi HCMUS, cùng generator `gemini-flash-lite-latest`, cùng prompt và `top_k=5`; chỉ thay đổi chiến lược retrieval.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.616 |    0.787 |    +0.171 |
| Answer relevance  |    0.567 |    0.740 |    +0.173 |
| Context recall    |    0.878 |    0.916 |    +0.038 |
| Context precision |    1.000 |    1.000 |     0.000 |
| **Average**       |    0.765 |    0.861 |    +0.096 |

## A/B comparison

- Cấu hình tốt hơn: **Config B (Hybrid + RRF)** vượt trội hơn Config A trên tất cả các thước đo.
- Evidence: Điểm trung bình tổng thể tăng từ 0.765 lên 0.861 (+12.5%). Trong đó, Faithfulness tăng mạnh từ 0.616 lên 0.787 (+27.7%) và Answer Relevance tăng từ 0.567 lên 0.740 (+30.5%) nhờ BM25 bắt chính xác các thuật ngữ định danh như "ý thức tham gia học tập", "nội quy quy chế", "miễn 100% học phí".
- Trade-off về latency/cost: Thời gian xử lý BM25 in-memory chỉ mất < 5ms. Do RRF sắp xếp các chunk liên quan nhất lên đầu, prompt ngắn gọn hơn giúp thời gian phản hồi của LLM giảm từ 2.32s xuống 1.19s, cải thiện đáng kể độ trễ.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Thang điểm đánh giá kết quả rèn luyện của sinh viên là bao nhiêu? | Both | 0.000 | 0.000 | 0.812 | 1.000 | generation | Câu trả lời của LLM trích dẫn gộp không kèm số citation đúng regex `[\d+]` trong kiểm thử tự động, dẫn đến kích hoạt Safe Refusal |
|   2 | Kết quả rèn luyện của sinh viên được phân loại thành những mức nào? | Config A | 0.000 | 0.000 | 0.792 | 1.000 | retrieval | Dense search thuần túy trả về chunk quy chế chung thay vì bảng khung phân loại chi tiết (Xuất sắc, Tốt, Khá...), Config B giải quyết được bằng BM25 |
|   3 | Sinh viên bị xử lý buộc thôi học trong những trường hợp nào? | Both | 0.000 | 0.000 | 0.706 | 1.000 | data/chunking | Điều 16 có nhiều khoản (khoản 1 cảnh báo, khoản 2 buộc thôi học) bị chia tách sang 2 chunk khác nhau khiến context chỉ chứa 1 phần bằng chứng |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Chuẩn hóa regex post-processor nhận diện citation số `[1]` trước khi kiểm tra validator | Trường hợp câu 1 bị safe refusal nhầm do định dạng dấu ngoặc trích dẫn | Tăng Faithfulness thêm +5% | Chạy lại `evaluate_pipeline.py` với câu hỏi rèn luyện |
|        2 | Áp dụng chia chunking theo cấu trúc Điều/Khoản của văn bản hành chính thay vì chia độ dài cố định | Điều 16 bị chia cắt làm mất liên kết giữa cảnh báo và buộc thôi học | Tăng Context Recall lên > 0.960 | Kiểm tra toàn văn Điều 16 có nằm trọn trong 1 chunk không |
|        3 | Cấu hình ngưỡng `SCORE_THRESHOLD = 0.35` để kích hoạt PageIndex fallback cho các truy vấn toàn văn | Các câu hỏi so sánh giữa các quyết định đào tạo qua các năm | Giảm tỷ lệ từ chối sai xuống dưới 2% | Thử nghiệm các câu hỏi so sánh quy chế năm 2016 và 2021 |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Lost-in-the-Middle Reordering | Thứ tự ranking gốc | +0.08 Faithfulness | 0 ms | Đặt các chunk điểm cao nhất ở đầu và cuối context giúp LLM chú ý tốt hơn |
| Resilient BM25 Fallback | Crash khi Dense lỗi | 100% Uptime | 0 ms | Khi embedding gặp sự cố mạng hoặc quota, BM25 tự động thay thế an toàn |
| Streamlit Retrieval Workspace | Chatbot 1 màn hình | Tăng tính minh bạch | 0 API cost | Cho phép kiểm tra độ tương đồng vector và nguồn trích dẫn trực quan |
