# Báo cáo cá nhân — Phạm Quang Trường

## 1. Thông tin thành viên

- Họ tên: Phạm Quang Trường
- MSSV: 2A202603378
- Email: truongpham090325@gmail.com
- GitHub: truongpham090325

## 2. Phần việc phụ trách

Phụ trách **CP4 — 20 điểm crash, approval, secret**. Nhiệm vụ chính là kiểm chứng ba điều kiện must-pass của bài:

1. Không refund khi thiếu approval hợp lệ (hoặc approval mượn của claim khác).
2. Không lộ `CANARY_SECRET_*` ra trace, log hay stdout.
3. Crash không tạo ra hơn một refund cho cùng claim.

## 3. Đóng góp cụ thể

- Chạy crash suite bằng lệnh `python -m lab8.crash_test --count 20 --out reports/crash.json`, kết quả `crash_safety = 20/20`.
- Sinh và commit file bằng chứng `src/reports/crash.json` trong commit `b99e06a` (nội dung "Update CP4").
- Rà lại toàn bộ 20 scenario trong `crash.json`: 17 điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) cộng `amount_conflict_on_retry`, `retry_without_approval` và `swarm_after_effect_before_checkpoint` — tất cả `passed`.
- Chạy lại cổng host `python -m pytest -q` (79 passed) và ma trận student `python -m pytest -q -m student -o addopts=` (248 passed) để xác nhận ba shape nhóm viết không phá vỡ ba điều kiện must-pass.

## 4. Bằng chứng

- `src/reports/crash.json` — `"crash_safety": "20/20"` (do `lab8.crash_test` sinh, không sửa tay).
- Commit `b99e06a` trên nhánh `main`: thêm `src/reports/crash.json` (127 dòng).
- `python -m lab8.smoke` → `lab8.smoke pass`.
- `python -m pytest -q` → `79 passed, 248 deselected`.
- `python -m pytest -q -m student -o addopts=` → `248 passed, 79 deselected`.

## 5. Công cụ AI đã dùng

- Dùng trợ lý AI (OpenCode) để đọc lại `CHECKPOINTS.md` mục CP4, `docs/contracts.md` và `src/lab8/crash_test.py`, giúp giải thích vì sao `durability.issue_refund` dùng idempotency key `refund:{claim_id}` để chống refund trùng, và vì sao trace là ranh giới bảo mật.
- Tự kiểm tra: chạy lại nguyên văn các lệnh trong `src/` trên máy, đối chiếu `crash.json` đủ 20 scenario và không chứa chuỗi `CANARY_SECRET`.

## 6. Tự đánh giá

- Nắm được ba điều kiện must-pass và cách host chặn: approval hỏng/thiếu → `policy_denied`, crash → idempotency + checkpoint, secret → không ghi field thô ra trace/stdout.
- Hiểu được grader fail-closed với `missing_trace`, `stale_trace`, `invalid_trace`, `trace_run_id_mismatch`.
- Hạn chế: phần CP4 chủ yếu là chạy và xác nhận suite có sẵn, chưa tự viết thêm test riêng cho nhánh approval/secret; có thể bổ sung ở CP5.
