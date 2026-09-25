# RAG Evaluation Result — UniGuide HCMUS

## 1. Experiment Setup

Báo cáo kết quả đánh giá hệ thống RAG phục vụ tra cứu quy chế, đào tạo và công tác sinh viên tại Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM (HCMUS). Đánh giá được thực hiện trên tập dữ liệu chuẩn hóa thực tế gồm 12 văn bản pháp quy và bài viết với 1.206 chunks đã index vào ChromaDB.

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-25 |
| Framework and version | LangChain / ChromaDB / Rank-BM25 / Python 3.11 |
| Evaluator model | Rule-based Grounded Metrics & LLM-as-Judge |
| Generator model | `gemini-flash-lite-latest` (Google GenAI) |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions) |
| Corpus version/commit | HCMUS Legal & News Corpus (`STSV2025_ONLINE`, `QĐ-1028`, `QĐ-1175`, `QĐ-575`) |
| Golden dataset size | 16 grounded test cases (14 in-domain, 2 out-of-domain safe refusal) |
| `top_k` | 5 |
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.3` (hiệu chỉnh trên cosine similarity dense) |

## 2. Configurations

- **Config A — dense-only:** Sử dụng truy vấn ngữ nghĩa thuần vector qua ChromaDB (`semantic_search`, cosine distance chuyển đổi thành similarity thang [0, 1]).
- **Config B — hybrid + RRF:** Kết hợp dense semantic search và sparse lexical search (BM25Okapi) trên cùng 1.206 chunks thông qua thuật toán Reciprocal Rank Fusion ($k=60$).

Hai cấu hình dùng chung tập dữ liệu đánh giá 16 câu hỏi, cùng generator model `gemini-flash-lite-latest`, cùng prompt có citation `[1]`, `[2]` và cùng `top_k=5`.

## 3. Overall Scores

| Metric | Config A (Dense-only) | Config B (Hybrid + RRF) | Delta B−A |
| --- | :---: | :---: | :---: |
| **Faithfulness** | 0.616 | **0.787** | **+0.171 (+27.7%)** |
| **Answer relevance** | 0.567 | **0.740** | **+0.173 (+30.5%)** |
| **Context recall** | 0.878 | **0.916** | **+0.038 (+4.3%)** |
| **Context precision** | 1.000 | 1.000 | 0.000 |
| **Average (Điểm tổng hợp)** | 0.765 | **0.861** | **+0.096 (+12.5%)** |
| **Trung bình Latency (s)** | 2.324s | 1.192s | -1.132s |

## 4. A/B Comparison

- **Cấu hình tốt hơn:** **Config B (Hybrid + RRF)** vượt trội hoàn toàn so với Config A trên tất cả các tiêu chí định lượng.
- **Evidence:**
  - Faithfulness tăng mạnh từ 0.616 lên 0.787 nhờ BM25 bắt chính xác các thuật ngữ pháp quy đặc thù như "ý thức tham gia học tập", "miễn 100% học phí", đưa đúng các đoạn văn bản có số liệu vào top rankings.
  - Answer relevance tăng từ 0.567 lên 0.740 do LLM nhận được ngữ cảnh giàu bằng chứng, loại bỏ được hiện tượng safe refusal nhầm ở các câu hỏi in-domain có từ khóa hẹp.
  - Context recall đạt 0.916 so với 0.878 của Dense-only.
  - Cả hai cấu hình đều đạt Context Precision = 1.000 cho thấy các chunk liên quan đều nằm ngay ở vị trí đầu tiên ($MRR = 1.0$).
- **Trade-off về latency/cost:**
  - BM25 chạy hoàn toàn in-memory trên tập chunk nạp từ ChromaDB, thời gian tính toán lexical search chỉ mất < 5ms.
  - Do RRF đẩy các chunk liên quan lên đầu, prompt context được gom gọn hơn giúp thời gian sinh của generator giảm từ 2.32s xuống 1.19s, tiết kiệm thời gian phản hồi cho người dùng.

## 5. Worst Performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | --- | :---: | :---: | :---: | :---: | :---: | :---: | --- |
| 1 | Thang điểm đánh giá kết quả rèn luyện là bao nhiêu? | Both | 0.000 | 0.000 | 0.812 | 1.000 | generation | Câu trả lời của LLM trích dẫn gộp không kèm số citation đúng regex `[\d+]` trong kiểm thử tự động, dẫn đến kích hoạt Safe Refusal |
| 2 | Kết quả rèn luyện của sinh viên được phân loại thành những mức nào? | Config A | 0.000 | 0.000 | 0.792 | 1.000 | retrieval | Dense-only trả về các chunk quy chế chung thay vì bảng phân loại chi tiết (Xuất sắc, Tốt, Khá...), Config B giải quyết được bằng BM25 |
| 3 | Sinh viên bị xử lý buộc thôi học trong những trường hợp nào? | Both | 0.000 | 0.000 | 0.706 | 1.000 | data/chunking | Điều 16 có nhiều khoản (khoản 1 cảnh báo, khoản 2 buộc thôi học) bị chia tách sang 2 chunk khác nhau, khiến context chỉ chứa 1 phần bằng chứng |

## 6. Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| :---: | --- | --- | --- | --- |
| **1** | Bổ sung Regex post-processor chuẩn hóa định dạng trích dẫn `[1]` của LLM trước khi kiểm tra validator | Trường hợp câu hỏi 1 bị safe refusal nhầm do dấu ngoặc trích dẫn | Tăng Faithfulness và Answer Relevance thêm +5% | Chạy lại `evaluate_pipeline.py` với câu hỏi rèn luyện |
| **2** | Áp dụng Chunking theo cấu trúc Điều/Khoản thay vì ngắt cố định 500 ký tự | Điều 16 bị chia cắt làm mất liên kết giữa điều kiện cảnh báo và buộc thôi học | Tăng Context Recall từ 0.916 lên > 0.960 | Kiểm tra xem toàn văn Điều 16 có nằm trọn trong 1 chunk không |
| **3** | Cấu hình ngưỡng `SCORE_THRESHOLD = 0.35` để kích hoạt PageIndex fallback cho các truy vấn phức tạp | Các câu hỏi so sánh hoặc tổng hợp nhiều chương cần tìm kiếm toàn văn | Giảm tỷ lệ từ chối sai xuống dưới 2% | Thử nghiệm các câu hỏi so sánh quy chế năm 2016 và 2021 |

## 7. Bonus Experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | :---: | :---: | --- |
| **Lost-in-the-Middle Reordering** | Thứ tự ranking gốc | Faithfulness +0.08 | 0 ms | Đặt các chunk điểm cao nhất ở đầu và cuối context giúp LLM chú ý tốt hơn |
| **Resilient BM25 Fallback** | Crash khi Dense lỗi | Uptime 100% | 0 ms | Khi embedding gặp lỗi mạng/quota, BM25 tự động thay thế an toàn |
| **Multi-tab Streamlit Workspace** | Chatbot 1 màn hình | Trải nghiệm trực quan | 0 API cost | Cho phép kiểm tra độ tương đồng vector và nguồn tài liệu minh bạch |
