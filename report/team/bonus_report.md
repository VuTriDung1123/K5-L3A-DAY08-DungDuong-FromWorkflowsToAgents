# Bonus report: B2

- Topic + nguồn (tên, năm, slide): **B2 · Gắn nhãn lỗi theo MAST** — MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* (slide 35, 45).
- CLAIM của nguồn (1 câu): 14 failure mode của hệ thống multi-agent LLM chia thành 3 nhóm (`system design`, `inter-agent misalignment`, `task verification`) và phân loại đáng tin cậy bằng quy chuẩn hành vi (human annotation đạt $\kappa = 0.88$).
- BOUNDARY (model / dataset / setup): Kết luận gốc xây dựng trên trace hội thoại dài của multi-agent LLM thật; trong Lab 8 LogiX-VN bị giới hạn bởi `MockLLM`, 14 claim public (`data/public_claims.jsonl`), 5 seed và 3 biến thể hỏng tạo chủ đích (lỗi đơn nguồn, ít nhiễu hơn LLM thực).
- HYPOTHESIS trên LogiX: Một tagger viết bằng luật hành vi đọc `reports/benchmark.json` và `traces/*.json` (không nhìn tên shape) có thể phân tách chính xác lỗi của `swarm` ở seed 55 và 3 biến thể hỏng chủ đích vào đúng 3 nhóm MAST với Cohen's $\kappa \ge 0.85$ so với bộ 18 trial gán nhãn tay.
- Biến cố định / biến thay đổi: Cố định `public_claims.jsonl` (14 claim), `seeds=[11,22,33,44,55]`, `as_of=2026-11-15`, `MockLLM`, `config/pricing.yaml`, evaluator `lab8.metrics`, và cùng bộ luật `classify_failure`; thay đổi kiến trúc chạy (`workflow`, `single`, `orchestrator`, `swarm`, `faulty_handoff_drop`, `faulty_stale_clause`, `faulty_skip_approval`).
- Lệnh tái lập (copy-paste được, chạy trong `src/`):
  ```text
  python -m bonus.mast_tag --benchmark reports/benchmark.json --traces-dir traces --out reports/bonus_mast.json
  ```
- File report + run id: `src/reports/bonus_mast.json` (mẫu run id từng nhóm: `R-swarm-C-002-s55`, `R-faulty_handoff_drop-C-001-s11`, `R-faulty_stale_clause-C-002-s11`, `R-faulty_skip_approval-C-007-s11`).

## Kết quả

### 1. Bảng phân bố lỗi theo `shape × nhóm MAST` (70 trial/shape, trích từ `src/reports/bonus_mast.json`)

| Shape | Pass rate | `system_design` | `inter_agent_misalignment` | `task_verification` | Tổng trial fail |
| --- | ---: | ---: | ---: | ---: | ---: |
| `workflow` | 1.000 | 0 | 0 | 0 | 0 |
| `single` | 1.000 | 0 | 0 | 0 | 0 |
| `orchestrator` | 1.000 | 0 | 0 | 0 | 0 |
| `swarm` | 0.986 | 0 | 0 | **1** | 1 |
| `faulty_handoff_drop` | 0.357 | 0 | **45** | 0 | 45 |
| `faulty_stale_clause` | 0.786 | 0 | 0 | **15** | 15 |
| `faulty_skip_approval` | 0.857 | **10** | 0 | 0 | 10 |
| **Tổng (490 trials)** | — | **10** | **45** | **16** | **71** |

- Cổng an toàn của 3 biến thể bonus (`test_bonus_mast.py`): **0 secret leak / 0 PII leak** ở mọi trace.

### 2. Đối chiếu tagger với 18 trial fail gán nhãn tay (`gold_validation`)

- Tập gán nhãn tay gồm **18 trial fail** (6 `system_design`, 6 `inter_agent_misalignment`, 6 `task_verification` gồm cả `R-swarm-C-002-s55`).
- Kết quả đối chiếu: `agree = 18/18` (`agreement = 1.000`, `expected_agreement = 0.333333`, **Cohen's $\kappa = 1.000$**).

### 3. Trả lời câu hỏi của B2

- **Lỗi seed 55 của `swarm` (`R-swarm-C-002-s55`) thuộc nhóm nào?**
  → Thuộc **`task_verification`** (`FM-3.2: Incorrect or Incomplete Verification`). Ở `seed % 5 == 0`, `swarm_reference` ghi nhận `model_override` (lấy `delay_days = 5` do `MockLLM` parse từ chữ trong ticket thay vì đối chiếu lại cột `delay_days = 2` của đơn `O-202`), dẫn tới báo hoàn `20000` VND thay vì từ chối.
- **Mitigation nào sửa đúng nhóm lỗi đó (MAST slide 35)?**
  → Nhóm mitigation **Verification / Cross-check against authoritative state**: tách kiểm chứng ra khỏi câu chữ người dùng bằng **deterministic code verifier** đối chiếu trực tiếp mọi field tính tiền với structured DB record (`lookup_order` + `compute_compensation`), giống cách `workflow`, `single` và `orchestrator` bỏ qua `parsed_delay` từ ticket (hoặc bổ sung code verifier ở đầu ra của `swarm`).

## Kết luận

Kết quả trên LogiX-VN **ủng hộ** giả thuyết ở mức hệ thống có trace có cấu trúc: `classify_failure` phân loại đúng 71/71 trial fail và khớp 18/18 nhãn tay ($\kappa = 1.000$) chỉ dựa trên `reason` và sự kiện trong `traces/*.json` (`skipped_host_gate`, đối chiếu `handoff.facts` với `lookup_order.order`, `model_override`, `clause_check.is_current`). Tuy nhiên, kết luận về độ chính xác phân loại sẽ **đảo ngược** (giảm xuống gần hoặc thấp hơn mức $\kappa = 0.88$ của MAST) nếu trace không ghi cấu trúc hóa sự kiện ranh giới hoặc nếu một trial mắc nhiều lỗi chồng chéo giữa misaligned handoff và thiếu bước kiểm chứng cùng lúc.

## Giới hạn

- `MockLLM` chỉ mô phỏng đầu ra theo seed và `latency` là `unavailable`, không có lỗi suy luận ngôn ngữ tự do mơ hồ như LLM thật.
- Tập public chỉ có 14 claim (và `swarm` chỉ tạo ra 1 trial fail tự nhiên là `R-swarm-C-002-s55`), nên 70/71 trial fail còn lại đến từ 3 biến thể lỗi thiết kế có chủ đích với dấu hiệu rõ ràng trong trace — đó là lý do $\kappa = 1.000$ trên bộ này cao hơn $\kappa = 0.88$ khi gán nhãn hội thoại LLM tự do trong paper MAST.
