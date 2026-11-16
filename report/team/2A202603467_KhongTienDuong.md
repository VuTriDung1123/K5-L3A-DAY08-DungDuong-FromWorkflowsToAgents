# Báo cáo cá nhân — Khổng Tiến Dương

## 1. Thông tin thành viên

- Họ tên: Khổng Tiến Dương
- MSSV: 2A202603467
- Email: khongtienduongcv@gmail.com
- GitHub: https://github.com/khongtienduongcv-byte

## 2. Phần việc phụ trách

- Shape C (`orchestrator`): điều phối investigator chỉ đọc, xây handoff đã lọc dữ liệu và xử lý kết quả để đưa ra quyết định refund.
- Phối hợp kiểm tra độ bền khi retry/crash, idempotency và các điều kiện bảo vệ approval/secret ở mốc M3 (CP4).
- Benchmark và Research Card theo phân công trong [TEAM.md](../../TEAM.md).

## 3. Đóng góp cụ thể

- Cài đặt luồng orchestrator: tra cứu claim, xử lý thiếu thông tin, tạo handoff theo allowlist, chạy investigator chỉ đọc, lấy quote từ dữ liệu đơn hàng và gọi `issue_refund` với toàn bộ quote.
- Giữ quyền ghi refund ở orchestrator/host; investigator không được gọi tool ghi. Handoff và trace chỉ mang dữ liệu đã được cho phép, không chuyển tiếp parent secret hoặc ngữ cảnh thô.
- Chuyển tiếp `crash_at` để crash được phát sinh đúng tại durability layer; retry dựa trên ledger/idempotency của host.
- Commit triển khai Shape C: `a036fbb` (`Shape2`).

## 4. Bằng chứng

- `python -m pytest -q -m student -o addopts= tests/test_public_matrix.py -k orchestrator` (chạy trong `src/`): **62 passed**.
- `python -m pytest -q -o addopts= tests/test_handoff_secret.py tests/test_crash_suite.py` (chạy trong `src/`): **4 passed**, gồm kiểm tra handoff không lộ secret và crash safety 20 điểm.
- Các test liên quan: `test_t12_crash_before_checkpoint_does_not_double_pay`, `test_allowlist_drops_parent_secret_and_headers`, `test_worker_cannot_receive_issue_refund`, `test_twenty_crash_points_are_safe`.

## 5. Công cụ AI đã dùng

- Antigravity: hỗ trợ đọc hiểu luồng Shape C, rà soát thay đổi và hỗ trợ kiểm tra test.
- Tự đối chiếu với contract/checkpoint của repo và chạy các lệnh pytest nêu trên; kết quả test là căn cứ xác nhận, không mặc định chấp nhận nội dung do AI đề xuất.

## 6. Tự đánh giá

- Hoàn thành phần Shape C và xác nhận các test student, handoff-secret, crash safety liên quan đều đạt.
- Qua phần M3/CP4, tôi hiểu rõ hơn rằng kiểm soát quyền ghi phải nằm ở host, secret phải được loại bỏ tại ranh giới handoff/trace, và tính an toàn sau crash cần được kiểm chứng bằng retry thực tế.
- Hướng cải thiện: ghi lại run ID và số liệu benchmark/ablation cụ thể trong báo cáo sau mỗi lần chạy để bằng chứng dễ tái lập hơn.
