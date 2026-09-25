# Individual contribution report

## Thông tin

- Họ và tên: Trần Văn Điền
- Mã học viên: HV03
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository/branch: `awun0105/K4-L3B-RAG-Pipeline` (branch `VanDien`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Semantic Search (Task 5) | Triển khai truy vấn cosine similarity từ ChromaDB và chuẩn hóa kết quả đầu ra theo schema `SearchResult` | `src/task5_semantic_search.py`, commit `3ccef3b` | Done |
| Lexical Search BM25 (Task 6) | Cài đặt thuật toán BM25Okapi trên tập chunk chung với vector store, xử lý tokenizer tiếng Việt đơn giản | `src/task6_lexical_search.py`, PR #2 | Done |
| Reciprocal Rank Fusion (Task 7) | Lập trình thuật toán RRF kết hợp thứ tự xếp hạng từ dense và lexical search với hệ số điều hòa $k=60$ | `src/task7_reranking.py`, PR #2 | Done |
| PageIndex Fallback (Task 8) | Tích hợp connector tìm kiếm văn bản phi vector (PageIndex vectorless) cho các tài liệu dài hoặc mục lục phức tạp | `src/task8_pageindex_vectorless.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng thuật toán Reciprocal Rank Fusion (RRF) thay vì cộng điểm trực tiếp (linear score combination).  
   **Lý do/evidence:** Điểm cosine similarity của dense retrieval (dao động từ 0 đến 1) và điểm BM25 (dương, không bị chặn trên) nằm trên hai thang đo hoàn toàn khác nhau. Cộng trực tiếp sẽ bị thiên lệch nặng về BM25. RRF chỉ dựa vào thứ bậc ($1 / (k + rank)$), loại bỏ hoàn toàn sự chênh lệch thang điểm.  
   **Trade-off:** RRF không giữ lại độ chênh lệch tuyệt đối về khoảng cách ngữ nghĩa giữa top 1 và top 2, nhưng tạo ra tính ổn định cao nhất cho hệ thống hybrid.

2. **Quyết định:** Nạp corpus cho BM25 trực tiếp từ collection ChromaDB đã index ở Task 4 thay vì đọc lại từ file disk.  
   **Lý do/evidence:** Đảm bảo tính nhất quán tuyệt đối về ID và nội dung giữa hai nguồn tìm kiếm: mọi chunk được BM25 chấm điểm đều có ID tương ứng 1:1 với chunk trong ChromaDB.  
   **Trade-off:** Cần ChromaDB được khởi tạo trước khi gọi `lexical_search()`, nhưng tránh được hoàn toàn nguy cơ lệch ID giữa 2 bảng xếp hạng.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `test_lexical_search_returns_bm25_contract`, `test_rrf_uses_rank_deduplicates_and_marks_hybrid`.
- Kết quả trước/sau nếu có: Cả hai bài kiểm tra contract đều đạt 100% kết quả mong đợi; các kết quả trùng lặp được loại bỏ và đánh dấu đúng `retrieval_method="hybrid"`.
- Lỗi đã phát hiện và cách xử lý: Khử trùng lặp ID khi một văn bản xuất hiện ở cả danh sách dense và sparse bằng cách gom nhóm dictionary theo chunk ID.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Tokenizer của BM25 hiện tại sử dụng biểu thức chính quy tách từ đơn, chưa sử dụng thư viện tách từ tiếng Việt chuyên dụng như `pyvi` hay `underthesea`.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Tích hợp thư viện tách từ tiếng Việt ghép (compound words) cho BM25 để cải thiện độ chuẩn xác khi tìm kiếm các thuật ngữ hành chính như "khen thưởng", "kỷ luật", "học vụ".

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Trần Văn Điền
