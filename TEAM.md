# Team

## Thông tin nhóm

- Tên nhóm: DungDuong
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-DungDuong-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/VuTriDung1123/K5-L3A-DAY08-DungDuong-FromWorkflowsToAgents | nhánh `main` | commit chốt (cập nhật ở CP5)

## Thành viên

| STT | Họ tên           | MSSV        | Email                      | GitHub                | Vai trò |
| --: | ---------------- | ----------- | -------------------------- | --------------------- | ------- |
|   1 | Vũ Trí Dũng      | 2A202603478 | dungvutri25@gmail.com      | VuTriDung1123         | Nhóm trưởng; Integration, Shape A (`workflow`), Shape B (`single`), Trace/ADR |
|   2 | Khổng Tiến Dương | 2A202603467 | khongtienduongcv@gmail.com | khongtienduongcv-byte | Shape C (`orchestrator`), Handoff/Durability/Crash, Benchmark & Research Card |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.
- Nhóm 2 người (DungDuong):
  - **Vũ Trí Dũng (`2A202603478`):** Nhóm trưởng; quản lý repo & integration (`check_submission`), cài đặt Shape A (`src/lab8/shapes/workflow.py`) và Shape B (`src/lab8/shapes/single.py`), kiểm tra Trace Contract v1, viết test cho `workflow`/`single` trong `src/tests/`, chủ trì `report/team/decision_adr.md` và phần tổng hợp trong `report/team/group_report.md`.
  - **Khổng Tiến Dương (`2A202603467`):** Cài đặt Shape C (`src/lab8/shapes/orchestrator.py`) cùng `make_handoff` và investigator chỉ đọc, kiểm tra tích hợp `durability.issue_refund` / `crash_at` / idempotency trên các shape, chạy `lab8.benchmark` và `lab8.crash_test`, viết test cho `orchestrator`/handoff/crash trong `src/tests/`, chủ trì `report/team/research_card.md` và phần kết quả trong `report/team/group_report.md`.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| ----- | --- | ------ | --------------------- |
|       |     |        |                       |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
