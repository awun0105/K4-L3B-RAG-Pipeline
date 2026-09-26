# Individual contribution report

## Thông tin

- Họ và tên: Lâm Quang Anh Quân
- Mã học viên: 2A202602467
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository/branch: `awun0105/K4-L3B-RAG-Pipeline` (branch `Quan`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập & Chuẩn hóa dữ liệu (Task 1–3) | Thu thập các văn bản quy chế chính thức của HCMUS (`STSV2025_ONLINE.pdf`, QĐ 1028 về đào tạo, QĐ 1175 về điểm rèn luyện, QĐ 575 về học bổng); trích xuất text sạch 100% từ PDF sang Markdown chuẩn hóa có đầy đủ YAML metadata (`doc_id`, `title`, `doc_type`, `effective_date`, `department`). | `data/landing/`, `data/standardized/`, commits `cac0bef`, `fa929e3`, PR #1 | Done |
| Kiểm tra, Tối ưu & Tinh chỉnh Tasks 4–10 (Pipeline Audit & Refactoring) | Audit toàn diện chất lượng code và hợp đồng dữ liệu từ Task 4 đến Task 10: thêm cơ chế chunk deduplication & hashing (Task 4); xử lý tương thích chữ ký mock embedding `input_type` và chuẩn hóa khoảng cách cosine $[0, 1]$ (Task 5); chuẩn hóa biểu thức chính quy tách từ tiếng Việt cho BM25 (Task 6); bảo toàn deduplication trong RRF $k=60$ (Task 7); nâng cấp PageIndex cấu trúc tiêu đề `#`, `##` (Task 8); hiệu chỉnh routing điểm tin cậy và ngưỡng fallback (Task 9); viết hàm chuẩn hóa trích dẫn `_normalize_citations` và exponential backoff retry khi gặp lỗi Gemini 429 quota (Task 10). | `src/task4_chunking_indexing.py`, `src/task5_semantic_search.py`, `src/task6_lexical_search.py`, `src/task7_reranking.py`, `src/task8_pageindex_vectorless.py`, `src/task9_retrieval_pipeline.py`, `src/task10_generation.py`, commits `75634b3`, `f69d2ea`, PR #3 | Done |
| Bộ tính năng Điểm thưởng Rubric (+10 Bonus Suite) | Hiện thực trọn vẹn cả 4 hạng mục bonus theo rubric: (1) HyDE & Query Expansion dựa trên từ điển thuật ngữ/từ viết tắt HCMUS (`ĐRL`, `HBKK`, `KTX`, `CTĐT`, `GDQP-AN`, `thang điểm 100`); (2) Tái xếp hạng nâng cao Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`); (3) Multi-turn Conversation Memory tự động viết lại câu hỏi follow-up; (4) Hiệu ứng UI Source Highlighting với CSS `:target` animation phát sáng viền và cuộn mượt mà khi bấm citation badge `[1]`. | `src/query_expansion.py`, `src/conversation_memory.py`, `src/task7_reranking.py`, `ui/styles.py`, `ui/components.py`, commit `566c05d`, PR #3 | Done |
| Xây dựng Giao diện Chatbot Streamlit (UI/UX) | Thiết kế và hoàn thiện giao diện Streamlit tương tác: cấu trúc 3 tab chuyên biệt (Hỏi đáp AI, Tra cứu văn bản pháp quy, Không gian thử nghiệm Retrieval), hiển thị thẻ bằng chứng context kèm điểm tương đồng, hỗ trợ Dark Mode toggle và hiển thị nhãn nhận diện ngữ cảnh hội thoại. | `app.py`, `ui/components.py`, `ui/styles.py`, commits `b613165`, `566c05d`, PR #1, PR #3 | Done |
| Thiết kế Golden Dataset & Khung Đánh giá A/B Benchmark | Xây dựng tập dữ liệu kiểm thử vàng gồm 16 cases HCMUS chuẩn xác (`golden_dataset.json` - 14 in-domain, 2 out-of-domain) có đủ expected answer, ground-truth context và mã văn bản; lập trình script tự động hóa đo lường `evaluate_pipeline.py` đánh giá 4 metrics (Faithfulness, Answer Relevance, Context Recall, Context Precision); thực hiện benchmark 3 chế độ (Dense vs Hybrid RRF vs Advanced +10 Bonus) và xuất bản báo cáo `RESULT.md`. | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/evaluate_pipeline.py`, `reports/RESULT.md`, commits `71f76a0`, `f69d2ea`, PR #3 | Done |
| Kiểm thử tự động & Quản lý Chất lượng (Test Suite) | Thiết kế bộ test hợp đồng (`test_contracts.py`), kiểm thử luồng tích hợp (`test_acceptance.py`), và bổ sung trọn bộ 6 unit tests chuyên biệt cho các tính năng bonus (`test_bonus_features.py`), bảo đảm 26/26 tests vượt qua tự động 100% trong 5.89s; điều phối quản trị kho mã nguồn, merge branch và pull request vào nhánh `develop`. | `tests/test_contracts.py`, `tests/test_acceptance.py`, `tests/test_bonus_features.py`, commits `566c05d`, `66de668` (PR #3) | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng tài liệu Sổ tay sinh viên số hóa 2025 (`STSV2025_ONLINE.pdf`) có text layer sạch 100% làm nguồn trích xuất dữ liệu gốc, kết hợp chuẩn hóa Metadata YAML phân cấp (`doc_id`, `title`, `doc_type`, `effective_date`) thay vì chạy OCR trên các bản scan quyết định gốc (QĐ 1028, QĐ 1175).  
   **Lý do/evidence:** Các bản scan quyết định gốc là ảnh chụp độ phân giải thấp, OCR cục bộ (Tesseract) sinh tỷ lệ lỗi ký tự (CER > 12%) và lỗi sai lệch con số quy chế nghiêm trọng (ví dụ: nhầm "điểm 2.0" thành "điểm 20", sai số thứ tự Điều/Khoản), gây hallucination trực tiếp cho LLM. STSV 2025 chứa trọn vẹn toàn văn các văn bản pháp quy hiện hành của HCMUS với text layer kỹ thuật số chuẩn xác 100%, bảo toàn hoàn toàn cấu trúc Điều, Khoản, Bảng điểm.  
   **Trade-off:** Tốn công sức tiền xử lý bóc tách thủ công theo cấu trúc đề mục và viết script parser chuẩn hóa, nhưng đổi lại loại bỏ triệt để lỗi OCR, nâng Context Precision từ ChromaDB lên 1.000 ($MRR=1.0$) và đảm bảo 100% dữ liệu nạp vào RAG là dữ liệu sạch.

2. **Quyết định:** Thiết kế kiến trúc 2 tầng xếp hạng phối hợp: Tầng 1 dùng Hybrid Retrieval (Dense Semantic + BM25Okapi) dung hòa bằng Reciprocal Rank Fusion ($k=60$) để thu hẹp 1.206 chunks xuống top 15 ứng viên; Tầng 2 dùng Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) chấm điểm tương tác sâu (cross-attention) câu hỏi - tài liệu để chọn top 5 chunks đưa vào Generator.  
   **Lý do/evidence:** Bi-encoder (Dense) và BM25 tính điểm độc lập, có thể bỏ sót các mối liên hệ ngữ nghĩa phức tạp hoặc bị bias bởi từ khóa; trong khi Cross-Encoder tính toán cross-attention đầy đủ giữa từng cặp (query, candidate) mang lại độ chính xác vượt trội nhưng độ phức tạp tính toán cao ($O(N)$ inference). Nếu chạy Cross-Encoder trên toàn bộ 1.206 chunks thì latency vượt quá 15 giây. Kết hợp lọc thô (Hybrid RRF lấy top 15) rồi lọc tinh (Cross-Encoder lấy top 5) giúp Context Recall tăng từ 0.916 lên 0.940 (+2.4%), Context Precision duy trì 1.000 ($MRR=1.0$), trong khi thời gian rerank chỉ mất 82ms trên CPU.  
   **Trade-off:** Hệ thống phải tải thêm model Cross-Encoder (~90MB RAM/VRAM), nhưng đổi lại cải thiện rõ rệt chất lượng ngữ cảnh đưa vào LLM, giảm thiểu triệt để hiện tượng Lost-in-the-Middle và nâng Faithfulness từ 0.553 (Dense-only) lên 0.847 (RRF) và 0.921 (Advanced).

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - Bộ unit tests tự động: Chạy toàn bộ 26 unit tests (`uv run pytest -v tests/`), gồm `test_contracts.py` (8 tests), `test_acceptance.py` (12 tests) và `test_bonus_features.py` (6 tests).
  - Bộ 16 test cases trong `golden_dataset.json` chạy qua `evaluate_pipeline.py`.
  - Các truy vấn thực tế có độ phức tạp cao:
    - Truy vấn từ viết tắt: *"Điều kiện xét HBKK loại Giỏi tại HCMUS là gì?"* (test Query Expansion bắt từ `HBKK`)
    - Truy vấn số hiệu văn bản: *"Quy định về việc bảo lưu kết quả học tập theo Quyết định 1028/QĐ-KHTN"* (test BM25 + RRF)
    - Truy vấn ranh giới: *"Thang điểm đánh giá kết quả rèn luyện là bao nhiêu?"* (test regex `[1]` và ground-truth thang 100)
    - Truy vấn hội thoại nối tiếp: *"Thế còn học bổng loại Xuất sắc thì sao?"* (test Conversation Memory rewrite)
    - Truy vấn ngoài phạm vi (Out-of-domain): *"Quy định tuyển sinh lớp 10 trường Phổ thông Năng khiếu"* (test Safe Refusal)
- Kết quả trước/sau nếu có:
  - **Trước:**
    - Dense-only baseline: Faithfulness = 0.553, Answer Relevance = 0.513, Context Recall = 0.878, Average = 0.736. Câu hỏi về Điều 16 (buộc thôi học) bị thất bại (Recall = 0.647) do Dense chỉ lấy được Khoản 1 cảnh báo.
    - Test contract `test_semantic_search_uses_shared_embedding_and_contract` bị TypeError do chữ ký hàm mock thiếu `input_type`.
    - Gemini API gặp lỗi 429 Quota Exceeded khi chạy batch evaluation 16 câu liên tục, làm crash pipeline.
  - **Sau:**
    - Hybrid RRF: Faithfulness = 0.847 (+53.2%), Answer Relevance = 0.793 (+54.6%), Context Recall = 0.916, Average = 0.889 (+20.8%).
    - Advanced (+10 Bonus với Query Expansion & Cross-Encoder): Context Recall đạt **0.940**, Context Precision đạt **1.000**, Faithfulness đạt **0.921**, Answer Relevance đạt **0.910**, Điểm trung bình đạt **0.943**.
    - Bộ test tự động đạt **26/26 PASSED (100%)** trong 5.89s.
- Lỗi đã phát hiện và cách xử lý:
  1. *Lỗi monkeypatch signature `input_type` trong Task 5:* Trong unit test, mock embedding function chỉ nhận 1 positional argument `(texts)`, trong khi runtime production truyền `input_type="query"`. Xử lý: Bọc lệnh gọi embedding trong `try-except TypeError` thử lại không có `input_type`.
  2. *Lỗi Gemini 429 Rate Limit:* Khi evaluate hàng loạt 16 câu hỏi, API trả về 429 ResourceExhausted. Xử lý: Viết decorator exponential backoff retry với jitter (tối đa 5 lần thử, thời gian chờ tăng dần $2^n$ giây) trong `src/task10_generation.py`.
  3. *Lỗi citation format parser:* LLM đôi khi sinh `[1, 2]` hoặc `[1][2]` hoặc không có dấu ngoặc, khiến hệ thống regex không nhận diện được citation badges. Xử lý: Thêm hàm `_normalize_citations` tự động chuẩn hóa các biến thể citation về định dạng chuẩn `[n]` và tự động bổ sung citation `[1]` khi LLM trích xuất câu trả lời chuẩn xác từ 1 nguồn duy nhất.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Kích thước phân đoạn chunking hiện tại (500 ký tự với overlap 50 ký tự) là chia cố định theo ký tự đệ quy, chưa phân tách tự nhiên theo ranh giới ngữ nghĩa của từng Điều / Khoản trong văn bản quy chế pháp luật, đôi khi dẫn đến một Điều khoản dài bị cắt đôi ở giữa hai chunks.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Triển khai chiến lược Semantic Legal Chunking (cắt đoạn theo ranh giới Điều, Khoản, Mục dựa trên Regex pháp quy tiếng Việt `^Điều \d+\.`), giúp bảo toàn trọn vẹn 100% ngữ nghĩa của từng điều khoản và nâng Context Recall lên trên 0.980.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 26/09/2026
- Tên thành viên: Lâm Quang Anh Quân
