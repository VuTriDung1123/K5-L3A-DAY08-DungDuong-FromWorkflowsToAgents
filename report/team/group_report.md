# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: DungDuongTruong
- Thành viên: xem [TEAM.md](../../TEAM.md)
- Commit chốt (trùng [decision_adr.md](decision_adr.md)): `b99e06a`

## 2. Mục tiêu và cách tiếp cận

Bài toán xử lý yêu cầu hoàn phí vận chuyển và bồi thường hư hỏng hàng hóa của LogiX-VN đòi hỏi tuân thủ chặt chẽ luật nghiệp vụ (`is_current`, `effective_date <= 2026-11-15`, không cộng dồn điều khoản, trần hoàn tiền theo đơn, kiểm tra `approval_id` thuộc đúng claim) đồng thời đảm bảo tính bền vững khi retry/crash và cô lập dữ liệu nhạy cảm (`CANARY_SECRET_*`, PII đơn hàng). Mục tiêu của nhóm là cài đặt cùng một `run_claim` trên ba kiến trúc tăng dần mức tự chủ (**Shape A `workflow`**, **Shape B `single`**, **Shape C `orchestrator`**) để so sánh công bằng với **Shape D `swarm`** có sẵn, từ đó chọn kiến trúc **ít tự chủ nhất nhưng vẫn đạt đầy đủ yêu cầu về độ đúng, an toàn và chi phí**.

Nhóm triển khai theo đúng thứ tự các checkpoint:
1. **CP1 (Vũ Trí Dũng):** Thiết lập repo nhóm, cài môi trường, chạy `lab8.smoke` và cổng host `pytest -q`, rà soát contract (`RunResult`, `Trace contract v1`, `business_rules.md`) và phân chia công việc.
2. **CP2–CP3 (Vũ Trí Dũng & Khổng Tiến Dương):** Vũ Trí Dũng cài đặt Shape A (`workflow.py`), Shape B (`single.py`) và bổ sung unit test (`test_shapes_workflow_single.py`); Khổng Tiến Dương cài đặt Shape C (`orchestrator.py`) với cơ chế handoff allowlist và investigator chỉ đọc. Cả ba shape đều truyền quote đầy đủ và `crash_at` vào `durability.issue_refund`, không nuốt `InjectedCrash`.
3. **CP4 (Phạm Quang Trường):** Chạy bộ kiểm thử 20 kịch bản crash (`lab8.crash_test`) và tạo bằng chứng `src/reports/crash.json`.
4. **CP5 (Vũ Trí Dũng):** Chạy benchmark 4 shape × 14 claim × 5 seed (`src/reports/benchmark.json`), hoàn thiện ADR, Research Card, báo cáo nhóm và chạy `lab8.check_submission`.

## 3. Giải pháp

### Ranh giới Code / Model và Nguyên tắc an toàn chung
- **Code quyết định hoàn toàn:** truy vấn phạm vi sở hữu đơn (`lookup_order` kiểm tra `principal_id`), lọc policy hiệu lực (`lookup_policy`), tính số tiền hoàn tất định (`compute_compensation`), kiểm tra `approval_id` / hạn dùng / trần theo đơn (`durability.issue_refund` với idempotency key `refund:{claim_id}` trong cùng transaction SQLite với audit `refund_committed`). Chữ trong `ticket` luôn được xem là dữ liệu người dùng không đáng tin cậy, không dùng số ngày trễ hay tên clause trong ticket để tính tiền.
- **Model (`MockLLM`) bị giới hạn:** chỉ dùng để soạn câu chữ phản hồi (`draft`), ghi nhận bước suy luận (`react_step`) hoặc đọc hiểu không làm thay đổi trạng thái tiền (`parse`).

### Ba shape nhóm cài đặt
- **Shape A — `workflow` ([workflow.py](../../src/lab8/shapes/workflow.py)):** Luồng Python tất định theo thứ tự cố định: `get_claim_view` → kiểm tra thiếu `order_id` (`needs_info`) → `lookup_order` (`escalated` nếu không `visible`) → `compute_compensation` (`denied` nếu quote = 0) → `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với quote đầy đủ (`resolved` / `denied` / `failed` khi conflict). Chỉ gọi `complete(..., purpose="draft")` để mô phỏng tạo văn bản phản hồi. Trace ghi: `claim_view`, `lookup_order`, `quote`, `decision`, `issue_refund`, `error`.
- **Shape B — `single` ([single.py](../../src/lab8/shapes/single.py)):** Dùng `lab8.runtime.run_react(..., max_steps=8, worker=True)` ép agent chỉ được chọn các tool trong `READONLY_TOOLS` (`get_claim_view` → `lookup_order` → `lookup_refund_history` → `compute_compensation`). Agent đếm đầy đủ `model_calls` và `tool_calls` vào `Budget`. Khi vòng ReAct kết thúc, code của shape bên ngoài mới gọi `durability.issue_refund` với quote đầy đủ và `crash_at`. Trace ghi: `react_step`, `tool_result`, `quote`, `decision`, `issue_refund`.
- **Shape C — `orchestrator` ([orchestrator.py](../../src/lab8/shapes/orchestrator.py)):** Orchestrator đọc thông tin tối thiểu của claim (không `SELECT *` toàn bộ bảng gồm secret), xử lý nhánh thiếu `order_id` (`needs_info`), sau đó tạo gói handoff qua `lab8.handoff.make_handoff(...)` với `facts={}` và danh sách `allowed_tools` chỉ đọc (`lookup_order`, `lookup_policy`, `compute_compensation`, `lookup_refund_history`). `make_handoff` lọc theo allowlist `ALLOWED_FIELDS` và kiểm tra chặn mọi `CANARY_SECRET_*` / `parent_secret` / `raw_headers` trước khi truyền cho `run_readonly_investigators`. Trace ghi handoff đã sanitize (`handoff`), kết quả investigator (`investigator`), `quote`, `crash`, `refund_outcome`.

## 4. Kết quả

Số liệu tổng hợp từ [`src/reports/benchmark.json`](../../src/reports/benchmark.json) (14 claim public × 5 seed `11, 22, 33, 44, 55` = 70 trial/shape, `as_of = 2026-11-15`, mỗi trial một file SQLite riêng):

| Shape | Pass rate | Pass^5 | Seed min–max | Seed variance | Cost/success (VND) | Mean steps | p95 steps | Mean model / tool calls |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `workflow` | **1.000** | **1.000** | `1.000–1.000` | `0.000000` | **28.79** | 3.79 | 4.0 | 1.00 / 2.79 |
| `single` | 1.000 | 1.000 | `1.000–1.000` | `0.000000` | 39.08 | 8.29 | 9.0 | 4.71 / 3.64 |
| `orchestrator` | 1.000 | 1.000 | `1.000–1.000` | `0.000000` | 56.65 | 3.43 | 4.0 | 1.00 / 5.57 |
| `swarm` | 0.986 | 0.929 | `0.929–1.000` | `0.000816` | 49.57 | 2.80 | 3.0 | 3.00 / 4.66 |

- **Phân tích lỗi ở `swarm`:** Chỉ có 1 trial fail trên 70 trial là `R-swarm-C-002-s55` (`status resolved != denied`) do ở seed chia hết cho 5, `swarm_reference` tin số ngày trễ ghi trong ticket thay vì cột `delay_days` của đơn hàng. Ba shape nhóm viết đều tránh được lỗi này nhờ giữ phần tra đơn và tính bồi thường hoàn toàn trong code.
- **Crash safety ([`src/reports/crash.json`](../../src/reports/crash.json)):** Đạt **`20/20`** (`CR-01`..`CR-20`: `before_effect` ×5, `after_effect_before_checkpoint` ×7, `after_checkpoint` ×5, `amount_conflict_on_retry`, `retry_without_approval`, `swarm_after_effect_before_checkpoint`).
- **Bộ kiểm thử tự động:** `pytest -q` đạt `79 passed` (54 test cổng host + 25 test nhóm viết trong `src/tests/test_shapes_workflow_single.py`); `pytest -q -m student -o addopts=` đạt `248 passed` (62/62 cho mỗi shape trong cả 4 shape).
- **Hidden self-check (`student_drop/`):** Chưa có gói `student_drop/` tại thời điểm chạy CP5 trên máy nên chưa chạy bước tự kiểm không nhãn; `lab8.check_submission` kiểm tra format cả 3 shape trên tập public ở seed 11 đạt `12/12` cho cả `workflow`, `single`, `orchestrator`.

Quyết định kiến trúc chi tiết: xem [`decision_adr.md`](decision_adr.md). Phiếu nghiên cứu và ablation R1: xem [`research_card.md`](research_card.md).

## 5. Khó khăn và cách xử lý

1. **Lọc test theo tên shape bằng `pytest -k single` bị lẫn test của shape khác:**
   - Lệnh `.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= -k single` ban đầu khớp luôn hàm `test_public_single_run_cases` của cả 4 shape (nên hiện fail của `orchestrator` khi chưa làm xong).
   - **Cách xử lý:** Lọc rõ `pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"` để kiểm tra đúng 62 test của Shape B (`62 passed`), sau đó chạy toàn bộ `-m student` khi Shape C hoàn tất (`248 passed`).
2. **Thay đổi nhân sự và phân công thực tế trong nhóm:**
   - Nhóm ban đầu lên kế hoạch 2 thành viên (`DungDuong`), sau đó bổ sung thêm thành viên thứ 3 (Phạm Quang Trường, đổi tên nhóm thành `DungDuongTruong`).
   - **Cách xử lý:** Điều chỉnh lại bảng thành viên và bảng đóng góp trong [TEAM.md](../../TEAM.md) khớp chính xác theo lịch sử commit trên Git (`97dd89d`, `f829fc7`, `a036fbb`, `b99e06a`).
3. **Môi trường Windows dùng Python 3.14.0:**
   - Tài liệu khuyến nghị Python 3.11–3.13, máy phát triển cài Python 3.14.0 (`Windows AMD64`). Nhóm đã kiểm tra ngay từ CP1 bằng `lab8.smoke` (`lab8.smoke pass`) và giữ cổng `pytest -q` xanh liên tục.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong [TEAM.md](../../TEAM.md) (bảng đóng góp) và báo cáo cá nhân trong `report/team/`.

## 7. Hạn chế và hướng cải thiện

- `MockLLM` chỉ mô phỏng đầu ra và token theo seed/độ dài chuỗi, không phải mô hình ngôn ngữ thực tế; `latency` luôn là `unavailable` nên chưa đo được trade-off thời gian phản hồi thực tế giữa 1 lần gọi của `workflow` và nhiều vòng lặp của `single` / `orchestrator`.
- Bộ benchmark hiện tại mới đánh giá trên 14 claim public; các trường hợp injection phức tạp hơn hoặc biến thể Unicode/homoglyph trên bộ hidden cần bộ chấm chính thức xác nhận.
- Nếu trong thực tế xuất hiện ticket có đính kèm chứng từ phi cấu trúc (ảnh/văn bản nhiều bước cần đọc chéo trước khi phân loại), nhóm có thể chuyển từ `workflow` sang `single` hoặc `orchestrator` nhưng vẫn giữ nguyên cổng `durability.issue_refund` và `compute_compensation` bằng code.

## 8. Tài liệu tham khảo

- Tài liệu đề bài Lab 8 LogiX-VN: [README.md](../../README.md), [CHECKPOINTS.md](../../CHECKPOINTS.md), [docs/business_rules.md](../../docs/business_rules.md), [docs/contracts.md](../../docs/contracts.md), [docs/architecture.md](../../docs/architecture.md), [docs/metrics.md](../../docs/metrics.md).
- Google Research (2026), *Towards a Science of Scaling Agent Systems* (tài liệu tham khảo slide bài giảng Lab 8).
