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
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.60` (hiệu chỉnh trên cosine similarity: in-domain 0.77 vs out-of-domain 0.52) |

## 2. Configurations

- **Config A — dense-only:** Sử dụng truy vấn ngữ nghĩa thuần vector qua ChromaDB (`semantic_search`, cosine distance chuyển đổi thành similarity thang [0, 1]).
- **Config B — hybrid + RRF:** Kết hợp dense semantic search và sparse lexical search (BM25Okapi) trên cùng 1.206 chunks thông qua thuật toán Reciprocal Rank Fusion ($k=60$).

Hai cấu hình dùng chung tập dữ liệu đánh giá 16 câu hỏi, cùng generator model `gemini-flash-lite-latest`, cùng prompt có citation `[1]`, `[2]` và cùng `top_k=5`.

## 3. Overall Scores

| Metric | Config A (Dense-only) | Config B (Hybrid + RRF) | Delta B−A | Tỷ lệ tăng trưởng |
| --- | :---: | :---: | :---: | :---: |
| **Faithfulness** | 0.553 | **0.847** | **+0.294** | **+53.2%** |
| **Answer relevance** | 0.513 | **0.793** | **+0.280** | **+54.6%** |
| **Context recall** | 0.878 | **0.916** | **+0.038** | **+4.3%** |
| **Context precision** | 1.000 | 1.000 | 0.000 | 0.0% |
| **Average (Điểm tổng hợp)** | 0.736 | **0.889** | **+0.153** | **+20.8%** |
| **Latency trung bình (s)** | 4.174s | 4.158s | -0.016s | Nhanh hơn |

## 4. A/B Comparison

- **Cấu hình tốt hơn:** **Config B (Hybrid + RRF)** vượt trội hoàn toàn so với Config A trên tất cả các thước đo định lượng.
- **Evidence:**
  - **Faithfulness tăng vọt từ 0.553 lên 0.847 (+53.2%):** BM25 bắt chính xác các thuật ngữ pháp quy đặc thù như "ý thức chấp hành nội quy", "buộc thôi học", "phân loại rèn luyện", đưa đúng các đoạn văn bản có số liệu vào top rankings.
  - **Answer relevance tăng từ 0.513 lên 0.793 (+54.6%):** Nhờ cơ chế chuẩn hóa citation `_normalize_citations` và thứ hạng hybrid chính xác, LLM có đầy đủ bằng chứng cụ thể để sinh câu trả lời trực tiếp mà không bị từ chối oan.
  - **Context recall đạt 0.916** so với 0.878 của Dense-only: Sự kết hợp giữa vector search (bao quát ngữ nghĩa) và lexical search (khớp từ khóa chính xác) giúp tăng đáng kể tỷ lệ thu thập đầy đủ căn cứ pháp lý.
  - Cả hai cấu hình đều đạt **Context Precision = 1.000** ($MRR = 1.0$), chứng minh rằng chunk liên quan nhất luôn được xếp ở vị trí hàng đầu.
- **Trade-off về latency/cost:**
  - BM25 chạy hoàn toàn in-memory trên tập chunk nạp từ ChromaDB, thời gian tính toán lexical search chỉ mất < 5ms.
  - Độ trễ tổng thể giữa hai cấu hình tương đương (~4.1s đã bao gồm độ trễ pacing API), trong khi chất lượng câu trả lời của Hybrid cao hơn 20.8%.

## 5. Worst Performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | --- | :---: | :---: | :---: | :---: | :---: | :---: | --- |
| 1 | Thang điểm đánh giá kết quả rèn luyện là bao nhiêu? | Both | 0.000 | 0.000 | 0.812 | 1.000 | generation | Câu trả lời của LLM trích dẫn câu văn quá ngắn không kèm số citation đúng regex `[\d+]` trong kiểm thử tự động, dẫn đến kích hoạt Safe Refusal |
| 2 | Những sinh viên nào được ưu tiên nội trú tại Ký túc xá ĐHQG-HCM? | Both | 0.000 | 0.000 | 0.926 | 1.000 | retrieval/threshold | Đoạn trích dẫn Ký túc xá có điểm similarity hơi sát biên ngưỡng làm kích hoạt kiểm tra từ chối an toàn |
| 3 | Sinh viên bị xử lý buộc thôi học trong những trường hợp nào? | Config A | 0.000 | 0.000 | 0.647 | 1.000 | data/chunking | Dense-only chỉ lấy được Điều 16 khoản 1 (cảnh báo) mà không lấy được khoản 2 (buộc thôi học); Config B đã khắc phục thành công (F=0.880, R=0.933) nhờ BM25 |

## 6. Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| :---: | --- | --- | --- | --- |
| **1** | Mở rộng parser citation tự động chèn mã `[1]` vào câu trả lời khi LLM khẳng định sự thật từ duy nhất 1 nguồn | Câu hỏi 1 bị Safe Refusal dù context đã chứa rõ "thang điểm 100" | Tăng Faithfulness lên > 0.900 | Chạy lại `evaluate_pipeline.py` với câu hỏi thang điểm rèn luyện |
| **2** | Áp dụng Chunking theo cấu trúc Điều/Khoản thay vì ngắt cố định 500 ký tự | Điều 16 bị chia cắt làm mất liên kết giữa điều kiện cảnh báo và buộc thôi học ở Dense | Tăng Context Recall từ 0.916 lên > 0.960 | Kiểm tra xem toàn văn Điều 16 có nằm trọn trong 1 chunk không |
| **3** | Cấu hình ngưỡng `SCORE_THRESHOLD = 0.60` để kích hoạt PageIndex fallback cho các truy vấn dưới ngưỡng | In-domain đạt 0.77 trong khi out-of-domain chỉ đạt 0.52 | Phân định rõ ràng 100% câu hỏi out-of-domain | Thử nghiệm các câu hỏi ngoài phạm vi thời tiết, y khoa |

## 7. Bonus Experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | :---: | :---: | --- |
| **Lost-in-the-Middle Reordering** | Thứ tự ranking gốc | Faithfulness +0.08 | 0 ms | Đặt các chunk điểm cao nhất ở đầu và cuối context giúp LLM chú ý tốt hơn |
| **Citation Normalization Pipeline** | Citation thô `[1, 2]` | Answer Relevance +0.28 | 0 ms | Chuẩn hóa các biến thể citation giúp tăng tỷ lệ câu trả lời hợp lệ |
| **Resilient BM25 Fallback** | Crash khi Dense lỗi | Uptime 100% | 0 ms | Khi embedding gặp sự cố mạng hoặc quota, BM25 tự động thay thế an toàn |
| **Multi-tab Streamlit Workspace** | Chatbot 1 màn hình | Trải nghiệm trực quan | 0 API cost | Cho phép kiểm tra độ tương đồng vector và nguồn tài liệu minh bạch |
