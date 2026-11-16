# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 | R1 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research 2026, *Towards a Science of Scaling Agent Systems* (tài liệu tham khảo bài giảng Lab 8, slide 68–69; bằng chứng thực nghiệm dạng benchmark). |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Với các tác vụ có phụ thuộc trạng thái tuần tự cao, việc mở rộng thêm agent/investigator làm tăng chi phí gọi công cụ và giao tiếp nhưng không tự động cải thiện tỷ lệ thành công so với kiến trúc đơn giản hơn. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận trong bài lab bị giới hạn bởi `MockLLM` mô phỏng, tập 14 claim public (`data/public_claims.jsonl`), bảng giá giả lập (`config/pricing.yaml`) và bộ quy tắc xác định sẵn của LogiX-VN; không suy rộng cho các tác vụ tìm kiếm song song nhiều nguồn không phụ thuộc. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Khi giữ cố định `MockLLM`, corpus, 5 seed và giá tool/token, việc chuyển từ `workflow` (tuần tự 1 luồng) sang `single` (vòng ReAct) hoặc `orchestrator` (thêm investigator chỉ đọc + `handoff`) sẽ giữ nguyên `pass_rate = 1.000` và `seed_variance = 0.000000`, nhưng làm `cost_per_success_vnd` tăng từ mức ~29 VND lên khoảng 39–57 VND. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Biến giữ cố định: `MockLLM`, `as_of=2026-11-15`, `config/tools.manifest.v1.1.yaml`, `seeds=[11,22,33,44,55]`, `data/public_claims.jsonl`, `config/pricing.yaml`, evaluator `lab8.metrics`, DB SQLite mới mỗi trial. Biến duy nhất thay đổi: topology (`workflow` vs `single` vs `orchestrator` vs `swarm`). |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: lệch kiểm chứng dữ liệu do tin chữ trong ticket ở `swarm` seed 55 (`T02`) và tăng chi phí tool thừa ở kiến trúc nhiều tầng. Đo bằng: `pass_rate`, `pass^5`, `seed_variance`, `cost_per_success_vnd`, `mean_steps`, `mean_tool_calls`, cùng `secret_leak = 0` và `approval_bypass = 0`. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json` (dẫn chứng cụ thể: `R-workflow-C-001-s11`, `R-single-C-001-s11`, `R-orchestrator-C-001-s11`, và trial fail `R-swarm-C-002-s55`)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng với giả thuyết.** Trên 70 trial mỗi shape (14 claim × 5 seed): `workflow` đạt `pass_rate = 1.000`, `pass^5 = 1.000`, `seed_variance = 0.000000`, `cost_per_success_vnd = 28.79`, `mean_steps = 3.79`, `mean_tool_calls = 2.79`. `single` giữ `1.000 / 1.000 / 0.000000` nhưng `cost/success` tăng lên `39.08` VND (+35.8%), `mean_steps = 8.29`, `mean_model_calls = 4.71`. `orchestrator` giữ `1.000 / 1.000 / 0.000000` nhưng `cost/success` tăng lên `56.65` VND (+96.8%), `mean_tool_calls = 5.57`. Trong khi đó `swarm` tụt xuống `pass_rate = 0.986`, `pass^5 = 0.929`, `seed_variance = 0.000816`, `cost/success = 49.57` VND vì lỗi `status resolved != denied` ở `R-swarm-C-002-s55`.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
