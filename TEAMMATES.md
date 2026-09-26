# Danh Sách Thành Viên & Phân Công Nhiệm Vụ — Nhóm K4-L3B

**Dự án:** UniGuide AI — Hệ thống RAG tra cứu quy chế và công tác sinh viên Trường ĐH Khoa học Tự nhiên, ĐHQG-HCM  
**Repository:** `awun0105/K4-L3B-RAG-Pipeline`

---

## 1. Bảng Tổng Quan Thành Viên (3 Thành Viên)

| STT | Mã Học Viên | Họ và Tên | Vai trò | Nhánh Git | Phần việc chính |
| :---: | :---: | :--- | :--- | :---: | :--- |
| 1 | `2A202602467` | **Lâm Quang Anh Quân** | **Team Lead / Data & Ingestion / Release & Bonus Architecture** | `Quan` | - Quản lý phiên bản Git, điều phối PR & tích hợp nhánh vào `develop`<br>- Lập trình trọn bộ script thu thập & chuẩn hóa dữ liệu HCMUS (Task 1–3)<br>- Audit chất lượng code, refactor & enhance toàn diện Tasks 4–10 lúc cuối<br>- Xây dựng trọn bộ 4 tính năng Bonus (+10 điểm Rubric)<br>- Thiết kế Golden Dataset 16 cases & framework đánh giá A/B benchmark |
| 2 | `2A202602615` | **Nguyễn Văn Diện** | **Retrieval & Search Specialist** | `VanDien` | - Phân đoạn văn bản & Indexing Vector vào ChromaDB (Task 4)<br>- Tìm kiếm ngữ nghĩa Semantic Search (Task 5)<br>- Tìm kiếm từ khóa BM25Okapi (Task 6)<br>- Tái xếp hạng Reciprocal Rank Fusion RRF (Task 7)<br>- Tìm kiếm phi vector PageIndex Fallback (Task 8)<br>- Tích hợp Hybrid Retrieval Pipeline (Task 9) |
| 3 | `2A202602688` | **Bùi Văn Quang** | **Generation & UI / Integration Engineer** | `Quang` | - Xây dựng module sinh câu trả lời Grounded Generation (Task 10)<br>- Citation mapping & xử lý từ chối an toàn Safe Refusal<br>- Phát triển và tinh chỉnh giao diện Streamlit Chatbot (`app.py`, `ui/`)<br>- Tích hợp và kiểm thử pipeline End-to-End |

---

## 2. Chi Tiết Đóng Góp Của Từng Thành Viên

### 2.1. Lâm Quang Anh Quân (Mã học viên: `2A202602467` — Nhánh `Quan`)
- **Vai trò:** Trưởng nhóm, phụ trách Quản trị phiên bản Git & Release, Lập trình pipeline dữ liệu, Audit & Nâng cấp chất lượng code cuối kỳ, Đánh giá chất lượng RAG và Bộ tính năng điểm thưởng Bonus (+10 điểm).
- **Phần việc cụ thể:**
  - **Quản lý phiên bản Git & Release Management:** Khởi tạo và quản lý cấu trúc nhánh (`develop`, `Quan`, `VanDien`, `Quang`), thiết lập quy trình Pull Request và gating kiểm thử tự động, trực tiếp xử lý merge conflict khi tích hợp các nhánh độc lập (PR #1, PR #2, PR #3, PR #5) bảo đảm branch `develop` luôn ổn định và passing 100% tests.
  - **Lập trình Script Thu thập & Chuẩn hóa Dữ liệu (Task 1–3):**
    - *Task 1 (`src/task1_collect_legal_docs.py`):* Viết script tự động nạp văn bản pháp quy từ manifest CSV hoặc nguồn công khai HCMUS vào `data/landing/legal/`.
    - *Task 2 (`src/task2_crawl_news.py`):* Viết script cào tin tức thông báo công tác sinh viên bằng custom TextExtractor / HTML-to-Markdown parser vào `data/landing/news/`.
    - *Task 3 (`src/task3_convert_markdown.py`):* Viết script tự động chuyển đổi PDF/DOCX sang Markdown chuẩn hóa có metadata YAML, xử lý bóc tách text layer từ `STSV2025_ONLINE.pdf` để thay thế PDF scan mộc đỏ mờ, đảm bảo dữ liệu sạch 100% cho bước indexing.
  - **Audit, Kiểm định Chất lượng & Tinh chỉnh Code Toàn diện (Tasks 4–10):**
    - Rà soát toàn bộ code của nhóm trước khi nộp, bổ sung chunk deduplication & hashing (Task 4), sửa lỗi crash mock signature `input_type` và kẹp khoảng chuẩn hóa $[0, 1]$ (Task 5), tối ưu regex tokenizer tiếng Việt BM25 (Task 6), bảo toàn deduplication RRF (Task 7), nâng cấp PageIndex hierarchy heading `#`, `##` (Task 8), tinh chỉnh routing fallback threshold `SCORE_THRESHOLD = 0.60` (Task 9).
    - Tại Task 10: Xây dựng bộ lọc và chuẩn hóa trích dẫn `_normalize_citations` (chuyển đổi `[1, 2]` thành `[1][2]`), bổ sung exponential backoff retry cho Gemini API khi gặp lỗi rate limit 429 quota. Nhờ đó nâng điểm benchmark trung bình từ 0.736 lên 0.889.
  - **Bonus Suite (+10 điểm Rubric):**
    - *HyDE & Domain Query Expansion (+3 điểm):* Module `src/query_expansion.py` tự động nhận diện từ viết tắt trường (`ĐRL`, `HBKK`, `KTX`, `CTĐT`, `GDQP-AN`, `thang điểm 100`, `Điều 16`). Tăng Context Recall từ 0.916 lên 0.940.
    - *Cross-Encoder Reranker (+3 điểm):* Module `src/task7_reranking.py` dùng `cross-encoder/ms-marco-MiniLM-L-6-v2` chấm điểm tương tác sâu giữa câu hỏi và ứng viên RRF. Giữ vững Context Precision = 1.000 ($MRR=1.0$).
    - *Conversation Memory (+2 điểm):* Module `src/conversation_memory.py` ghi nhớ lịch sử nhiều lượt, viết lại câu hỏi nối tiếp (follow-up) thành standalone query trong `app.py`.
    - *Interactive UI Source Highlighting (+2 điểm):* CSS `:target` animation phát sáng viền và cuộn mượt mà (`smooth scroll`) tới thẻ nguồn khi người dùng click citation badge `[1]`.
  - **UI Interaction:** Xây dựng cấu trúc đa tab (Hỏi đáp, Kho tài liệu, Retrieval workspace), dark mode toggle, hiển thị thẻ bằng chứng context và hiệu ứng highlight nguồn trích dẫn.
  - **Evaluation & Benchmark:** Thiết kế `golden_dataset.json` (16 test cases grounded thực tế), viết script `evaluate_pipeline.py` tự động đo 4 chỉ số và lập báo cáo `RESULT.md`.

---

### 2.2. Nguyễn Văn Diện (Mã học viên: `2A202602615` — Nhánh `VanDien`)
- **Vai trò:** Kỹ sư Retrieval, phụ trách thiết kế và hiện thực toàn bộ hạ tầng tìm kiếm Hybrid từ Task 4 đến Task 9.
- **Phần việc cụ thể:**
  - **Task 4 (Chunking & Indexing):** Cài đặt chiến lược chia đoạn đệ quy (`RecursiveCharacterTextSplitter`) với kích thước 500 ký tự, overlap 50 ký tự; tạo chunk ID tất định (`{doc_id}-chunk-{index}`) và lập chỉ mục 1.206 chunks vào ChromaDB với embedding cục bộ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
  - **Task 5 (Semantic Search):** Xây dựng hàm tìm kiếm vector ngữ nghĩa qua ChromaDB, chuyển đổi khoảng cách cosine thành điểm tương đồng chuẩn hóa $[0, 1]$ và đóng gói kết quả theo contract `SearchResult` (`retrieval_method="dense"`).
  - **Task 6 (Lexical Search):** Cài đặt tìm kiếm từ khóa BM25Okapi trên cùng tập 1.206 chunks, viết regex tokenizer tiếng Việt, gán `retrieval_method="sparse"`.
  - **Task 7 (Reranking RRF):** Lập trình thuật toán Reciprocal Rank Fusion ($k=60$) dung hòa thứ hạng hai nguồn dense và sparse, xử lý khử trùng lặp (deduplication) ổn định.
  - **Task 8 (PageIndex Fallback):** Xây dựng tìm kiếm theo cấu trúc phân cấp mục lục (`#`, `##`) không dùng vector dành cho các tài liệu pháp quy dài.
  - **Task 9 (Retrieval Pipeline):** Tích hợp luồng Hybrid retrieval hoàn chỉnh, điều phối semantic search, lexical search, RRF và cơ chế fallback an toàn qua ngưỡng `SCORE_THRESHOLD`.

---

### 2.3. Bùi Văn Quang (Mã học viên: `2A202602688` — Nhánh `Quang`)
- **Vai trò:** Kỹ sư Tích hợp & Giao diện, phụ trách module sinh câu trả lời và trải nghiệm người dùng Streamlit.
- **Phần việc cụ thể:**
  - **Task 10 (Grounded Generation):** Thiết kế System Prompt định hướng câu trả lời hoàn toàn dựa vào retrieved context, triệt tiêu hallucination; xây dựng hàm định dạng context và kỹ thuật sắp xếp vị trí tài liệu *Lost-in-the-Middle* (`reorder_for_llm`).
  - **Citation & Safe Refusal:** Xây dựng logic từ chối an toàn `SAFE_REFUSAL` ("Thông tin trong nguồn hiện có chưa đủ để xác minh câu hỏi này") khi điểm similarity thấp hoặc câu hỏi ngoài phạm vi; trích xuất số nguồn từ citation brackets.
  - **Giao diện Streamlit:** Hoàn thiện luồng nhập liệu `st.chat_input`, hiển thị avatar trợ lý UniGuide, trình bày các câu hỏi gợi ý nhanh và các khối hiển thị đoạn trích dẫn nguồn có thể mở rộng (`st.expander`).
  - **End-to-End Integration:** Kết nối module Generation với Retrieval Adapter, kiểm thử hỏi đáp trên các tình huống quy chế thực tế của trường.

---

## 3. Ma Trận Phân Công Module Kỹ Thuật

| Hạng mục / Module | File mã nguồn / Tài liệu chính | Thành viên phụ trách chính | Thành viên phối hợp / Review |
| :--- | :--- | :---: | :---: |
| **Quản lý phiên bản Git & Release PRs** | `.git/`, Git branches & PR workflow | **Lâm Quang Anh Quân** | Nguyễn Văn Diện, Bùi Văn Quang |
| **Kiến trúc, Hợp đồng & Test suites** | `src/contracts.py`, `tests/` | **Lâm Quang Anh Quân** | Nguyễn Văn Diện, Bùi Văn Quang |
| **Script Thu thập & Chuẩn hóa dữ liệu (Task 1–3)** | `src/task1_*.py`, `src/task2_*.py`, `src/task3_*.py`, `data/` | **Lâm Quang Anh Quân** | Nguyễn Văn Diện |
| **Chunking & Vector Indexing (Task 4)** | `src/task4_chunking_indexing.py` | **Nguyễn Văn Diện** | Lâm Quang Anh Quân |
| **Semantic Search (Task 5)** | `src/task5_semantic_search.py` | **Nguyễn Văn Diện** | Lâm Quang Anh Quân |
| **Lexical Search BM25 (Task 6)** | `src/task6_lexical_search.py` | **Nguyễn Văn Diện** | Bùi Văn Quang |
| **Reciprocal Rank Fusion RRF (Task 7)** | `src/task7_reranking.py` | **Nguyễn Văn Diện** | Lâm Quang Anh Quân |
| **PageIndex Fallback (Task 8)** | `src/task8_pageindex_vectorless.py` | **Nguyễn Văn Diện** | Bùi Văn Quang |
| **Retrieval Pipeline (Task 9)** | `src/task9_retrieval_pipeline.py` | **Nguyễn Văn Diện** | Lâm Quang Anh Quân |
| **Generation & Citations (Task 10)** | `src/task10_generation.py` | **Bùi Văn Quang** | Lâm Quang Anh Quân |
| **Audit & Nâng cấp Code toàn diện (Tasks 4–10)** | `src/` (toàn bộ pipeline) | **Lâm Quang Anh Quân** | Nguyễn Văn Diện, Bùi Văn Quang |
| **Chatbot UI Streamlit** | `app.py`, `ui/` | **Bùi Văn Quang** | Lâm Quang Anh Quân |
| **Đánh giá Golden Dataset & A/B Benchmark** | `group_project/evaluation/`, `reports/RESULT.md` | **Lâm Quang Anh Quân** | Bùi Văn Quang |
| **Bộ 4 Tính Năng Điểm Thưởng (+10 Bonus)** | `src/query_expansion.py`, `src/conversation_memory.py` | **Lâm Quang Anh Quân** | Nguyễn Văn Diện |
