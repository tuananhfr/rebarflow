# PyInstaller spec — build: python -m PyInstaller --noconfirm packaging/rebarflow.spec
# Output: dist/rebarflow/ (onedir — khởi động nhanh, updater cài đè dễ)

from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "rebarflow" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "docs"), "docs")],   # GHI-CHU-CONG-THUC-GOC.md đi kèm app
    hiddenimports=[],
    # KHÔNG exclude "unittest": ezdxf import nó lúc runtime (đã dính lỗi thật)
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rebarflow",
    console=False,              # app GUI — không hiện cửa sổ console
    icon=None,                  # icon default (đã chốt), thay ở đây khi có .ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="rebarflow",
)
