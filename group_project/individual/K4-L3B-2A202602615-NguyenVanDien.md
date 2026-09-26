# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Văn Diện
- Mã học viên: 2A202602615
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository/branch: `awun0105/K4-L3B-RAG-Pipeline` (branch `VanDien`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Phân đoạn văn bản & Vector Indexing (Task 4) | Hiện thực chiến lược chunking đệ quy (recursive chunking 500 ký tự, overlap 50 ký tự), tích hợp SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`) và Gemini embedding fallback, tính toán ID chunk có tính tất định (hash-based/stable IDs), upsert vector vào ChromaDB với cosine distance | `src/task4_chunking_indexing.py`, commit `3ccef3b` | Done |
| Tìm kiếm ngữ nghĩa Semantic Search (Task 5) | Triển khai truy vấn cosine similarity từ ChromaDB dựa trên embedding của query, chuẩn hóa điểm tương đồng và định dạng danh sách kết quả theo đúng contract `SearchResult` (chứa `id`, `content`, `score`, `metadata`, `retrieval_method="dense"`) | `src/task5_semantic_search.py`, commit `3ccef3b` | Done |
| Tìm kiếm từ khóa BM25 (Task 6) | Cài đặt thuật toán BM25Okapi trên tập chunk chung với ChromaDB, xây dựng hàm tiền xử lý và tách từ tiếng Việt bằng regex, chuẩn hóa kết quả đầu ra theo schema `SearchResult` với `retrieval_method="sparse"` | `src/task6_lexical_search.py`, commit `3ccef3b` | Done |
| Tái xếp hạng Reciprocal Rank Fusion (Task 7) | Lập trình thuật toán RRF kết hợp thứ hạng từ dense search và lexical search với hằng số $k=60$, thực hiện deduplication (khử trùng lặp theo chunk ID), tính điểm fused score và gán `retrieval_method="hybrid"` | `src/task7_reranking.py`, commit `3ccef3b` | Done |
| Tìm kiếm phi vector PageIndex Fallback (Task 8) | Xây dựng cơ chế tìm kiếm cấu trúc phân cấp (mục lục / heading structure) không dùng vector cho các tài liệu dài; quét các heading `#`, `##` và nội dung tương ứng để tìm kiếm từ khóa fallback khi dense score không vượt qua ngưỡng | `src/task8_pageindex_vectorless.py`, commit `3ccef3b` | Done |
| Tích hợp Pipeline Hybrid Retrieval (Task 9) | Kết nối toàn bộ luồng tìm kiếm end-to-end: thực thi semantic search và lexical search, hòa trộn kết quả bằng RRF, kiểm tra ngưỡng tin cậy `score_threshold` trên best cosine score của dense results, kích hoạt PageIndex fallback an toàn khi độ tin cậy thấp | `src/task9_retrieval_pipeline.py`, commit `3ccef3b` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng thuật toán Reciprocal Rank Fusion (RRF) với hệ số $k=60$ để dung hòa (fuse) kết quả giữa dense semantic search và sparse BM25 search thay vì dùng phép cộng tuyến tính có trọng số (weighted linear score combination).
   **Lý do/evidence:** Điểm cosine similarity của dense retrieval (nằm trong đoạn $[0, 1]$) và điểm BM25 (dương, không có chặn trên, phụ thuộc vào tần suất xuất hiện và độ dài tài liệu) có phân phối và thang đo hoàn toàn khác nhau. Cộng tuyến tính sẽ khiến điểm BM25 lấn át hoặc đòi hỏi liên tục tinh chỉnh siêu tham số trọng số $\alpha$. RRF chỉ dựa vào thứ hạng tương đối ($1 / (k + rank)$), loại bỏ hoàn toàn sự lệch thang đo và mang lại kết quả ổn định, đặc biệt với các câu hỏi chứa số hiệu văn bản, mã quy chế của HCMUS.
   **Trade-off:** RRF làm mất đi độ lớn chênh lệch khoảng cách ngữ nghĩa tuyệt đối giữa top 1 và top 2, nhưng bù lại mang lại sự ổn định và tin cậy cao nhất cho hệ thống hybrid mà không phụ thuộc vào các kỹ thuật chuẩn hóa điểm phức tạp.

2. **Quyết định:** Quản lý ID của chunk bằng hàm băm ổn định (hash-based/deterministic chunk ID dạng `{doc_id}-chunk-{index}`) và nạp kho văn bản cho BM25 trực tiếp từ tập chunk chuẩn đã được lập chỉ mục trong ChromaDB.
   **Lý do/evidence:** Đảm bảo tính nhất quán tuyệt đối 1:1 giữa hai nguồn tìm kiếm: mọi chunk được BM25 tính điểm đều có ID và nội dung trùng khớp hoàn toàn với chunk trong ChromaDB. Tránh hiện tượng lệch dữ liệu (data drift) hoặc trùng lặp ID khi re-index, đồng thời giúp bước khử trùng lặp (deduplication) trong RRF hoạt động chính xác.
   **Trade-off:** Cần ChromaDB được khởi tạo và nạp dữ liệu trước khi chạy BM25, nhưng loại bỏ hoàn toàn nguy cơ sai lệch ánh xạ giữa dense và sparse search.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest -v`, các test contract: `test_chunk_documents_creates_valid_chunks`, `test_semantic_search_returns_dense_contract`, `test_lexical_search_returns_bm25_contract`, `test_rrf_uses_rank_deduplicates_and_marks_hybrid`, `test_retrieval_pipeline_hybrid_and_fallback`. Query kiểm tra: *"Quy định về việc hoãn thi và thi bù tại HCMUS"*, *"Mức xử lý kỷ luật khi sinh viên thi hộ hoặc nhờ người thi hộ"*, *"Quyết định 1175/QĐ-KHTN"*.
- Kết quả trước/sau nếu có: 26/26 tests kiểm thử acceptance và contract pass 100%. Cơ chế hybrid kết hợp RRF giúp tìm chính xác văn bản ngay cả khi câu hỏi dùng thuật ngữ viết tắt hoặc từ khóa chính xác mà semantic search đơn lẻ có thể xếp hạng thấp.
- Lỗi đã phát hiện và cách xử lý: Lỗi so sánh ngưỡng fallback: điểm RRF sau khi fuse nằm trong khoảng nhỏ ($< 0.033$), nếu so sánh trực tiếp với `SCORE_THRESHOLD = 0.3` sẽ luôn luôn kích hoạt PageIndex fallback ngoài ý muốn. Cách xử lý: trích xuất best cosine score ban đầu từ dense results để kiểm tra ngưỡng tin cậy trước khi quyết định kích hoạt fallback.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Bộ tiền xử lý từ khóa cho BM25 hiện tại sử dụng biểu thức chính quy tách từ cơ bản theo khoảng trắng và ký tự từ ngữ, chưa tích hợp thư viện tách từ tiếng Việt chuyên dụng (như `pyvi` hay `underthesea`) để nhận diện từ ghép đa âm tiết.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung thư viện tách từ ghép tiếng Việt cho BM25 và thử nghiệm mô hình Cross-Encoder tiếng Việt chạy cục bộ để tái xếp hạng top kết quả sau RRF nhằm nâng cao hơn nữa độ chính xác ngữ cảnh.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 26/09/2026
- Tên thành viên: Nguyễn Văn Diện
