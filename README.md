# rebarFlow

App desktop Windows tính **thép đài cọc** từ file `.mdb` export bởi SAFE/ETABS, xuất bản vẽ **DXF** (mở bằng AutoCAD) + báo cáo xlsx — thay thế quy trình file Excel VBA cũ (không chạy được trên LibreOffice).

- Kế hoạch chi tiết (mức hướng-dẫn-code): [PLAN.md](PLAN.md)
- Quyết định về công thức so với file Excel gốc: [docs/GHI-CHU-CONG-THUC-GOC.md](docs/GHI-CHU-CONG-THUC-GOC.md)

## Trạng thái

- [x] **M1** — core engine (đọc mdb, gom nội lực per strip, công thức As 2 chế độ) + golden tests + CLI
- [x] **M2** — xuất DXF (strips + map phản lực) + báo cáo xlsx
- [x] **M3** — UI desktop (PySide6)
- [x] **M4** — auto-update (GitHub Releases) + installer (PyInstaller + Inno Setup)
- [ ] **M5** — beta chạy song song với Excel trên dự án thật

## Chạy app

```bash
pip install -e .[dev]
python -m rebarflow.main        # mở app desktop (2 tab: Thép đài / Phản lực chân cột)
```

## CLI (không cần UI)

```bash
python -m rebarflow.cli duong/dan/file_safe.mdb          # chế độ giống Excel gốc (mặc định)
python -m rebarflow.cli duong/dan/file_safe.mdb --mode tcvn --h 1.2
python -m rebarflow.cli file.mdb --dxf banve.dxf --report baocao.xlsx   # xuất bản vẽ + báo cáo
```

## Test

```bash
pytest
```

**Lưu ý:** file dữ liệu dự án thật (`.mdb`, `.xls`) và golden data trích từ chúng **không commit** vào repo (xem `.gitignore`). Để chạy đủ golden tests trên máy mới: đặt file gốc vào `tests/fixtures/` rồi chạy `python tests/tools/extract_golden.py`.

## Build installer & phát hành

```powershell
powershell -File packaging\build.ps1
# → chạy pytest → PyInstaller (dist\rebarflow\) → Inno Setup (dist\rebarflow-setup-x.y.z.exe)
# Cần cài Inno Setup 6: https://jrsoftware.org/isdl.php
```

Quy trình phát hành bản mới:
1. Sửa `rebarflow/__version__.py` (vd `"1.1.0"`)
2. `powershell -File packaging\build.ps1`
3. Tạo GitHub Release tag `v1.1.0` trên repo này, body = changelog, đính kèm `rebarflow-setup-1.1.0.exe`
4. Mọi máy đang chạy bản cũ sẽ tự thấy thông báo cập nhật ở lần mở app sau (check nền qua GitHub Releases API; máy không có mạng vẫn dùng app bình thường)
