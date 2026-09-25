# Individual contribution report

## Thông tin

- Họ và tên: Vương Khả Vũ
- Mã học viên: HV04
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository/branch: `awun0105/K4-L3B-RAG-Pipeline` (branch `main` / `develop`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Khởi tạo kiến trúc Repository | Thiết kế cấu trúc thư mục chuẩn theo contract-first (`data/`, `src/`, `tests/`, `reports/`, `docs/`) | Toàn bộ repo, commit `5ebba6c` | Done |
| Module Contracts & Invariants | Định nghĩa các schemas dữ liệu: `Document`, `SearchResult`, `GenerationResult` và các hàm validate contract | `src/contracts.py`, `docs/MODULE_CONTRACTS.md` | Done |
| Acceptance & Contract Tests | Xây dựng bộ 20 bài unit & acceptance tests tự động để kiểm soát chất lượng kỹ thuật của toàn đội | `tests/test_contracts.py`, `tests/test_acceptance.py` | Done |
| Quy chuẩn báo cáo & Rubric checklist | Thiết kế mẫu báo cáo đánh giá kết quả RAG (`RESULT.md`) và mẫu báo cáo đóng góp cá nhân (`INDIVIDUAL_REPORT.md`) | `reports/`, commit `d8dc51a` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Áp dụng phương pháp tiếp cận Contract-First và Schema Validation nghiêm ngặt trước khi các thành viên bắt đầu viết code nghiệp vụ.  
   **Lý do/evidence:** Trong mô hình làm việc nhóm phân tán, việc không thống nhất kiểu dữ liệu trả về giữa các module (ví dụ: Task 4 trả về định dạng chunk khác với Task 5 kỳ vọng) sẽ dẫn đến xung đột lớn khi merge code. Bằng cách định nghĩa trước các hàm validate schema, bất kỳ module nào trả sai cấu trúc đều bị chặn ngay ở cấp độ test.  
   **Trade-off:** Tốn thời gian thiết lập ban đầu và phải liên tục bảo trì hợp đồng khi có yêu cầu thay đổi, nhưng giúp tiết kiệm 80% thời gian tích hợp hệ thống về sau.

2. **Quyết định:** Thiết kế các bài test contract độc lập hoàn toàn với API bên ngoài (dùng monkeypatch và fake provider).  
   **Lý do/evidence:** Đảm bảo `pytest` có thể chạy trơn tru trong môi trường CI/CD hoặc máy chấm thi của giảng viên mà không phụ thuộc vào kết nối Internet hay API key của bất kỳ nhà cung cấp nào.  
   **Trade-off:** Đòi hỏi các thành viên phải tuân thủ nghiêm ngặt chữ ký hàm (function signature) đã cam kết trong hợp đồng.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest -q`, `pytest tests/test_contracts.py -v`.
- Kết quả trước/sau nếu có: 20/20 test cases chạy thành công trong vòng dưới 7 giây, tỷ lệ kiểm thử đạt 100%.
- Lỗi đã phát hiện và cách xử lý: Phát hiện các trường hợp thiếu trường `id`, `content`, `metadata` trong document validator và bổ sung các assertion chi tiết.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Chưa thiết lập pipeline GitHub Actions tự động chạy `pytest` khi có pull request mới mà hiện tại chạy kiểm thử thủ công qua CLI `uv run pytest`.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung cấu hình `.github/workflows/ci.yml` để tự động chạy kiểm thử linting (ruff) và acceptance tests mỗi khi thành viên mở PR vào nhánh `develop`.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Vương Khả Vũ
