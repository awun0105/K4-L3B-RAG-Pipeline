# Individual contribution report

## Thông tin

- Họ và tên: Bùi Văn Quang
- Mã học viên: HV02
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository/branch: `awun0105/K4-L3B-RAG-Pipeline` (branch `Quang`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Chunking & Indexing (Task 4) | Cấu hình chunking recursive (chunk_size=500, overlap=50), quản lý collection ChromaDB và cơ chế upsert chống trùng lặp dữ liệu | `src/task4_chunking_indexing.py`, commit `c4deda0` | Done |
| Multi-provider Embedding | Tích hợp đa dạng provider (SentenceTransformers local, OpenRouter, Gemini), cơ chế caching model và chuẩn hóa vector embedding | `src/task4_chunking_indexing.py` | Done |
| Resilient Retrieval Fallback (Task 9) | Xây dựng cơ chế fallback an toàn: khi Dense retrieval gặp lỗi quota/driver/mạng, tự động chuyển hướng qua BM25 và PageIndex | `src/task9_retrieval_pipeline.py`, commit `c4deda0` | Done |
| Retrieval Workspace UI | Thiết kế tab trực quan hóa quá trình truy vấn (Retrieval Workspace) trong Streamlit để kiểm tra các chunk được dense & BM25 thu thập | `ui/data_views.py`, commit `b613165` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Thiết kế cơ chế phòng vệ lỗi truy xuất (graceful degradation) trong `retrieve()` thay vì trả về crash hoặc lập tức safe refusal.  
   **Lý do/evidence:** Trong môi trường sản phẩm thực tế, dịch vụ embedding vector hoặc API bên thứ ba có thể bị nghẽn mạng hoặc vượt ngưỡng quota. BM25 chạy hoàn toàn offline từ index ChromaDB sẵn có nên có thể gánh tải truy vấn từ khóa ngay lập tức.  
   **Trade-off:** Khi fallback sang sparse-only, độ bao quát ngữ nghĩa (semantic breadth) giảm đi đôi chút so với hybrid đầy đủ, nhưng hệ thống vẫn phản hồi đúng nội dung thay vì từ chối người dùng.

2. **Quyết định:** Chuẩn hóa kích thước chunk 500 ký tự với overlap 50 ký tự theo chiến lược phân đoạn đệ quy.  
   **Lý do/evidence:** Văn bản pháp quy và điều lệ trường đại học thường có cấu trúc Điều, Khoản gồm 2–4 câu súc tích. Kích thước 500 ký tự đảm bảo một chunk chứa trọn vẹn 1 điều khoản hoặc 1 bảng biểu nhỏ mà không bị xé vụn.  
   **Trade-off:** Tạo ra tổng cộng 1.206 chunks, đòi hỏi nhiều request embedding hơn, nhưng được bù đắp bằng tốc độ index batch 32–64 chunks/request.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `test_chunk_documents_preserves_identity_and_metadata`, `test_retrieve_survives_fallback_provider_error`.
- Kết quả trước/sau nếu có: Toàn bộ các test contract về chunking và fallback pipeline đều đạt PASSED trong 0.2s.
- Lỗi đã phát hiện và cách xử lý: Xử lý triệt để lỗi ép kiểu metadata rỗng của ChromaDB (`None` được chuẩn hóa thành chuỗi rỗng `""` theo đúng invariant).

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Hiện tại chưa tích hợp cơ chế semantic chunking tự động theo tiêu đề Điều/Khoản của văn bản hành chính mà dùng recursive character splitter.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Triển khai bộ phân đoạn dựa trên regex nhận diện tiêu đề "Điều ...", "Khoản ..." để tăng thêm độ gắn kết ngữ cảnh cho từng chunk.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Bùi Văn Quang
