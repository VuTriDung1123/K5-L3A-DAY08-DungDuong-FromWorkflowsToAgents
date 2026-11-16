# Team

## Thông tin nhóm

- Tên nhóm: DungDuongTruong
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-DungDuong-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/VuTriDung1123/K5-L3A-DAY08-DungDuong-FromWorkflowsToAgents | nhánh `main` | commit chốt (cập nhật ở CP5)

## Thành viên

| STT | Họ tên            | MSSV        | Email                      | GitHub                | Vai trò                                                                                 |
| --: | ----------------- | ----------- | -------------------------- | --------------------- | --------------------------------------------------------------------------------------- |
|   1 | Vũ Trí Dũng       | 2A202603478 | dungvutri25@gmail.com      | VuTriDung1123         | Nhóm trưởng; CP1, Shape A (`workflow`), Shape B (`single`), Test, Benchmark, ADR & Báo cáo |
|   2 | Khổng Tiến Dương  | 2A202603467 | khongtienduongcv@gmail.com | khongtienduongcv-byte | CP2/CP3 Shape C (`orchestrator`), Handoff allowlist & Trace sanitize                    |
|   3 | Phạm Quang Trường | 2A202603378 | truongpham090325@gmail.com | truongpham090325      | CP4 Crash suite (`lab8.crash_test`, `src/reports/crash.json` 20/20)                     |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.
- Nhóm 3 người thực tế (`DungDuongTruong`, đối chiếu theo lịch sử git):
  - **Vũ Trí Dũng (`2A202603478`):** Nhóm trưởng; CP1 (thiết lập repo nhóm & smoke check), CP2/CP3 cài đặt Shape A (`src/lab8/shapes/workflow.py`) và Shape B (`src/lab8/shapes/single.py`), viết unit test `src/tests/test_shapes_workflow_single.py`, CP5 chạy `lab8.benchmark`, kiểm tra `lab8.check_submission`, hoàn thiện `decision_adr.md`, `research_card.md`, `group_report.md` và báo cáo cá nhân.
  - **Khổng Tiến Dương (`2A202603467`):** CP2/CP3 cài đặt Shape C (`src/lab8/shapes/orchestrator.py`) với `make_handoff`, `run_readonly_investigators`, trace sanitize và `crash_at`.
  - **Phạm Quang Trường (`2A202603378`):** CP4 chạy kiểm chứng crash suite 20 điểm và xuất bằng chứng `src/reports/crash.json` (`20/20`).

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| ----- | --- | ------ | --------------------- |
| Vũ Trí Dũng (`2A202603478`) | Nhóm trưởng; Shape A (`workflow`), Shape B (`single`), Benchmark & Báo cáo | `97dd89d`, `f829fc7` | `src/tests/test_shapes_workflow_single.py` (25 test cases cho `workflow` & `single`); chạy `pytest -q` (79 passed) & `-m student` |
| Khổng Tiến Dương (`2A202603467`) | Shape C (`orchestrator`), Handoff & Trace sanitize | `a036fbb` | `src/tests/test_public_matrix.py` (`orchestrator`: 62/62 passed khi chạy `-m student`) |
| Phạm Quang Trường (`2A202603378`) | Crash safety verification (CP4) | `b99e06a` | `python -m lab8.crash_test --count 20 --out reports/crash.json` (20/20 passed, `CR-01`..`CR-20`) |

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
