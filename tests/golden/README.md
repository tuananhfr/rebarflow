# Golden data (không commit)

Các file `*.json` ở thư mục này là dữ liệu kỳ vọng trích từ file Excel gốc của
dự án thật → **không push lên repo** (xem `.gitignore` gốc repo).

Tạo lại trên máy mới:

1. Đặt `tinh Dai coc - GOC.xls` vào `tests/fixtures/`, convert sang xlsx:
   `soffice --headless --convert-to xlsx --outdir tests/fixtures "tests/fixtures/tinh Dai coc - GOC.xls"`
2. Chạy: `python tests/tools/extract_golden.py`
3. Đặt thêm `MONG.mdb` vào `tests/fixtures/` cho test import.

`KNOWN_DIFFS.md` (commit được) ghi các chênh lệch đã giải thích giữa tool và
file gốc — sinh từ `pytest tests/test_strip_aggregate.py -s`.
