# Individual contribution report

## Thông tin

- Họ và tên: Bùi Văn Quang
- Mã học viên: 2A202602688
- Nhóm: K4-L3B (UniGuide HCMUS RAG)
- Repository: `awun0105/K4-L3B-RAG-Pipeline`
- Branch: `Quang`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Generation – Sinh câu trả lời từ RAG | Xây dựng bước sinh câu trả lời cuối cùng sau khi hệ thống retrieval trả về các đoạn văn bản liên quan. Thiết kế prompt để LLM chỉ sử dụng context được truy xuất, hạn chế hallucination và ưu tiên trả lời dựa trên tài liệu của HCMUS. Chuẩn hóa đầu vào gồm câu hỏi người dùng và retrieved context trước khi gửi tới mô hình. | Module Generation / LLM của project | Done |
| Grounded Answer & Citation | Tích hợp nội dung nguồn vào câu trả lời để người dùng có thể kiểm tra thông tin được lấy từ tài liệu nào. Xử lý trường hợp context không đủ thông tin bằng cách yêu cầu hệ thống không tự suy diễn hoặc tạo thông tin ngoài dữ liệu được cung cấp. | Module Generation / Prompt | Done |
| User Interface – Streamlit UI | Xây dựng giao diện Streamlit giúp người dùng nhập câu hỏi và tương tác trực tiếp với hệ thống UniGuide. Hiển thị câu trả lời của AI cùng thông tin nguồn/context liên quan, giúp dễ kiểm tra kết quả retrieval và generation trong quá trình demo. | `app.py` và các module UI liên quan | Done |
| Tích hợp RAG Pipeline end-to-end | Kết nối các bước ingestion/indexing, hybrid retrieval, reranking, fallback và generation thành một luồng hỏi–đáp hoàn chỉnh từ giao diện người dùng đến kết quả cuối cùng. Đảm bảo output giữa các module tương thích với nhau. | `app.py`, retrieval/generation modules | Done |
| Evaluation – Đánh giá kết quả RAG | Thực hiện kiểm tra các câu hỏi thực tế liên quan đến quy định và quy chế của HCMUS nhằm đánh giá khả năng retrieval và chất lượng câu trả lời cuối cùng. Kiểm tra tính liên quan của context, độ đúng của câu trả lời và khả năng trả lời dựa trên nguồn được truy xuất. | Evaluation / test queries | Done |
| Integration & Debugging | Kiểm tra pipeline khi chạy thực tế, phát hiện và xử lý lỗi tích hợp giữa retrieval, embedding, generation và UI; đảm bảo ứng dụng có thể chạy end-to-end và hiển thị kết quả ổn định trên giao diện. | Các module tích hợp của project | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Thiết kế bước Generation theo hướng Grounded RAG, trong đó LLM chỉ được phép trả lời dựa trên context được retrieval từ hệ thống.

   **Lý do/evidence:** Với hệ thống tra cứu quy định của trường đại học, việc LLM tự tạo hoặc suy diễn thông tin có thể dẫn đến câu trả lời sai về quy chế, điều khoản hoặc quyền lợi của sinh viên. Vì vậy prompt được thiết kế để ưu tiên nội dung retrieved context và yêu cầu mô hình thể hiện rõ khi dữ liệu hiện tại chưa đủ để trả lời.

   **Trade-off:** Cách tiếp cận này có thể khiến hệ thống từ chối trả lời nhiều hơn khi retrieval chưa tìm đúng tài liệu, nhưng đổi lại giúp giảm hallucination và tăng độ tin cậy của câu trả lời.

2. **Quyết định:** Sử dụng Streamlit để xây dựng giao diện demo thay vì xây dựng frontend và backend riêng biệt.

   **Lý do/evidence:** Mục tiêu chính của giai đoạn hiện tại là kiểm thử và trình diễn RAG pipeline. Streamlit cho phép tích hợp trực tiếp Python pipeline với giao diện, giảm thời gian phát triển frontend và thuận tiện khi debug retrieval, generation cũng như các nguồn context được trả về.

   **Trade-off:** Streamlit phù hợp với prototype và demo nhưng hạn chế hơn về khả năng tùy biến giao diện, quản lý phiên người dùng và khả năng mở rộng so với kiến trúc frontend/backend độc lập.

3. **Quyết định:** Hiển thị context hoặc nguồn tham chiếu cùng với câu trả lời AI trên giao diện.

   **Lý do/evidence:** Việc chỉ hiển thị câu trả lời cuối cùng khiến người dùng khó xác minh AI đang dựa vào nội dung nào. Hiển thị source/context giúp kiểm tra nhanh độ chính xác của retrieval, hỗ trợ debug pipeline và tăng tính minh bạch của hệ thống RAG.

   **Trade-off:** Giao diện có thêm thông tin kỹ thuật và có thể dài hơn đối với người dùng thông thường, nhưng rất hữu ích trong quá trình đánh giá và demo hệ thống.

## Kiểm thử và kết quả

- Các query đã sử dụng để kiểm tra pipeline:
  - *"Quy định về việc hoãn thi và thi bù tại HCMUS"*
  - *"Mức xử lý kỷ luật khi sinh viên thi hộ hoặc nhờ người thi hộ"*
  - *"Quyết định 1175/QĐ-KHTN"*
  - Các câu hỏi tự nhiên có cách diễn đạt khác với từ khóa xuất hiện trực tiếp trong tài liệu.

- Luồng kiểm thử:
  `User Query → Hybrid Retrieval → RRF/Ranking → Context → LLM Generation → UI`

- Kết quả:
  - Pipeline có thể nhận câu hỏi trực tiếp từ giao diện và trả về câu trả lời dựa trên tài liệu đã index.
  - Kết quả retrieval được truyền đúng sang module Generation.
  - Câu trả lời cuối cùng có thể hiển thị cùng context/source để kiểm chứng.
  - Các thành phần retrieval và generation hoạt động thống nhất trong luồng end-to-end.
  - Giao diện Streamlit giúp kiểm thử nhanh nhiều query mà không cần chạy từng module độc lập từ terminal.

- Lỗi đã phát hiện và cách xử lý:
  - Phát hiện các trường hợp dữ liệu retrieval trả về chưa đúng định dạng mà module Generation/UI mong đợi; tiến hành chuẩn hóa output giữa các module trước khi hiển thị.
  - Phát hiện trường hợp LLM có xu hướng bổ sung thông tin ngoài retrieved context; điều chỉnh prompt để yêu cầu mô hình ưu tiên nguồn được cung cấp và không suy diễn khi thiếu bằng chứng.
  - Kiểm tra luồng lỗi khi retrieval không trả về context đủ tốt để tránh việc UI hoặc Generation bị lỗi và đảm bảo hệ thống vẫn phản hồi được cho người dùng.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Phần đánh giá hiện tại chủ yếu dựa trên tập câu hỏi kiểm thử và quan sát kết quả thực tế, chưa xây dựng một bộ evaluation dataset đủ lớn với ground-truth để đo định lượng riêng các chỉ số retrieval và generation.

- Giao diện hiện tại tập trung vào chức năng demo RAG nên chưa có các tính năng nâng cao như lịch sử hội thoại hoàn chỉnh, authentication, quản lý phiên người dùng hoặc dashboard phân tích chất lượng câu trả lời.

- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:
  - Xây dựng bộ evaluation dataset gồm `question – expected answer – expected source`.
  - Đánh giá riêng các chỉ số như Context Precision, Context Recall, Faithfulness và Answer Relevancy.
  - Cải thiện UI để hiển thị rõ tài liệu, đoạn trích và metadata của nguồn được sử dụng trong câu trả lời.
  - Bổ sung cơ chế theo dõi latency của từng bước retrieval và generation để tối ưu tốc độ pipeline.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng các phần việc tôi trực tiếp tham gia thực hiện trong hệ thống UniGuide HCMUS RAG và có thể giải thích hoặc chạy lại pipeline trong buổi demo.

- Ngày: 26/09/2026
- Tên thành viên: Bùi Văn Quang