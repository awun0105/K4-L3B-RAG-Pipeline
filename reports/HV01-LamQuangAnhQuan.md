# Individual contribution report

## Thông tin

- Họ và tên: Lâm Quang Anh Quân
- Mã học viên: HV01
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository/branch: `awun0105/K4-L3B-RAG-Pipeline` (branch `Quan`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập & Chuẩn hóa dữ liệu (Task 1-3) | Thu thập các văn bản quy chế đào tạo, điểm rèn luyện, học bổng HCMUS; chuyển đổi và trích xuất toàn bộ điều khoản từ PDF gốc sang Markdown có YAML metadata đầy đủ | `data/landing/`, `data/standardized/`, commit `fa929e3` | Done |
| Pipeline bugfix & Contract compliance (Task 5) | Khắc phục lỗi chữ ký monkeypatch `input_type` trong `semantic_search` giúp bộ test đạt 20/20 test pass 100% | `src/task5_semantic_search.py`, commit `75634b3` | Done |
| Generation & Citation (Task 10) | Hoàn thiện citation mapping `[1]`, `[2]` tương ứng với nguồn trích dẫn, lost-in-the-middle context formatting và safe refusal | `src/task10_generation.py`, PR #1 | Done |
| Chatbot Streamlit App | Xây dựng giao diện Streamlit đa tab (Hỏi đáp, Kho tài liệu, Retrieval workspace) hiển thị điểm similarity và source trích dẫn | `app.py`, `ui/`, commit `b613165` | Done |
| Golden Dataset & Evaluation | Xây dựng bộ 16 câu hỏi HCMUS grounded thực tế và báo cáo đánh giá 4 metrics | `group_project/evaluation/`, `reports/RESULT.md` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng tài liệu Sổ tay sinh viên số hóa chính thức (`STSV2025_ONLINE.pdf`) để trích xuất nguyên vẹn văn bản quy chế thay vì dùng OCR cục bộ trên file scan hình ảnh mờ.  
   **Lý do/evidence:** Bản scan quyết định gốc QĐ 1028 và QĐ 1175 là ảnh chụp, OCR cục bộ dễ sinh lỗi chính tả tiếng Việt nghiêm trọng ở các con số và điều khoản pháp quy, gây hallucination cho RAG. Sổ tay sinh viên chứa đúng toàn văn nghị quyết với text layer sạch 100%.  
   **Trade-off:** Mất thời gian tiền xử lý phân tách từng chương/mục thành các file markdown chuyên biệt, nhưng đem lại độ chính xác gần như tuyệt đối cho quá trình chunking và retrieval.

2. **Quyết định:** Bọc lệnh gọi embedding trong `semantic_search` bằng cơ chế try-except linh hoạt đối với tham số `input_type`.  
   **Lý do/evidence:** Hỗ trợ tương thích tối đa với cả model yêu cầu prefix (như E5, Nemotron) lẫn các hàm mock/lambda trong unit test không khai báo keyword arguments.  
   **Trade-off:** Thêm 4 dòng mã phòng thủ nhưng bảo toàn hoàn toàn tính bất biến (invariant) của hợp đồng module và giúp 100% test case kiểm thử tự động pass.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest -v`, query kiểm tra: *"Điều kiện để sinh viên được xét và công nhận tốt nghiệp đại học tại HCMUS là gì?"*, *"Thang điểm rèn luyện là bao nhiêu?"*.
- Kết quả trước/sau nếu có: Trước đây test contract `test_semantic_search_uses_shared_embedding_and_contract` bị TypeError, sau khi tối ưu đạt 20/20 PASSED. Khi test câu hỏi in-domain, chatbot trích dẫn chính xác Điều 17 QĐ 1175 và Điều 3 QĐ 1028 kèm citation `[1]`.
- Lỗi đã phát hiện và cách xử lý: Lỗi quota API free tier được phòng thủ bằng cơ chế fallback BM25 và cấu hình provider Gemini ổn định.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Tốc độ xử lý của mô hình trích xuất bảng biểu phức tạp trong quy chế điểm rèn luyện vẫn cần tinh chỉnh để giữ nguyên cấu trúc Markdown table chi tiết nhất.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Triển khai thêm mô hình reranker BGE-reranker-large chạy trên GPU để tối ưu hóa thứ tự văn bản pháp luật trước khi đưa vào context LLM.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Lâm Quang Anh Quân
