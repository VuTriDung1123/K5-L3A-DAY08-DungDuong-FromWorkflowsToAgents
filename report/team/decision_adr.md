# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: b99e06a
- Run id dẫn chứng: R-workflow-C-001-s11 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.79
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng bộ 14 claim public (`data/public_claims.jsonl`), 5 seed (`11,22,33,44,55`), cùng bảng giá (`config/pricing.yaml`) và cùng `MockLLM` (`src/reports/benchmark.json`), `workflow` đạt độ chính xác tuyệt đối (`pass_rate = 1.000`, `pass^5 = 1.000`, `seed_variance = 0.000000`) với chi phí mô phỏng thấp nhất (`28.79 VND/success`, tổng `2015.30 VND` cho 70 trial) và trung bình chỉ `3.79` bước (`p95_steps = 4.0`, `mean_model_calls = 1.0`, `mean_tool_calls = 2.79`). Vì quy trình xử lý claim hoàn phí là xác định theo luật (`get_claim_view` → `lookup_order` → `compute_compensation` → `durability.issue_refund`), `workflow` giữ toàn bộ quyết định tiền và quyền truy cập trong code, chỉ dùng model để soạn câu chữ, qua đó là kiến trúc **ít tự chủ nhất mà vẫn hoàn thành 100% bài toán**.

## Có đáng đổi lấy multi-agent không

Không đáng đổi trong bài toán này. So với `workflow`, `single` (`cost/success = 39.08 VND`, `mean_steps = 8.29`) đắt hơn 35.8%, `orchestrator` (`cost/success = 56.65 VND`, `mean_tool_calls = 5.57`) đắt hơn 96.8% nhưng đều chỉ đạt cùng `pass_rate = 1.000`; còn `swarm` tham chiếu vừa đắt hơn (`49.57 VND/success`) vừa bị giảm độ tin cậy (`pass_rate = 0.986`, `pass^5 = 0.929`, `seed_variance = 0.000816`) do lỗi ở seed 55 (`R-swarm-C-002-s55` tin số ngày trễ trong ticket thay vì cột `delay_days`). Quyết định này chỉ đảo lại sang `single` hoặc `orchestrator` nếu nghiệp vụ xuất hiện tình huống bán cấu trúc mà bước đọc cố định không xử lý được (ví dụ phải trích xuất nhiều chứng từ rời rạc hoặc cần điều phối nhiều investigator truy vấn các nguồn độc lập) khiến `workflow` tụt `pass_rate` đáng kể so với agent.

## Trace và bằng chứng

Trace của `workflow` ghi các event theo cấu trúc tối giản: `claim_view` (chỉ gồm `found`, `claim_id`, `order_id`), `lookup_order` (output đã lọc `ORDER_FIELDS`), `quote` (output của `compute_compensation`), `decision` (`status`, `reason`), `issue_refund` (`ok`, `reason`, `conflict`), và `error`. Nhóm cố ý **không** ghi `parent_secret`, `raw_headers`, `approval_id`, câu chữ thô của `ticket`, cũng như các trường PII trong bảng `orders` (`phone`, `address`, `item_name`, `internal_note`) vào trace hoặc stdout. Nếu có log nằm ngoài thư mục `traces/` hoặc sai tên `<run_id>*` khiến scanner của grader không đọc được, nguyên tắc fail-closed xem đó là rủi ro rò rỉ vì đội security không thể chứng minh nội dung ngoài vùng quét là sạch.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75. Các số liệu trên được đo trên 14 claim public; năng lực tổng quát trên dữ liệu mới sẽ được kiểm chứng tiếp qua bộ hidden của giảng viên.
