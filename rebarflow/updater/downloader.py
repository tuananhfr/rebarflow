"""Tải installer về %TEMP% và chạy — bước 2 của luồng update."""

import subprocess
import tempfile
from pathlib import Path

import requests

from rebarflow.updater.version_check import UpdateInfo


class DownloadError(Exception):
    """Message tiếng Việt hướng người dùng."""


def download_installer(info: UpdateInfo, progress_cb=None) -> Path:
    """Tải setup.exe về %TEMP%, verify đúng kích thước. progress_cb(done, total)."""
    dest = Path(tempfile.gettempdir()) / f"rebarflow-setup-{info.version}.exe"
    try:
        with requests.get(info.url, stream=True, timeout=30) as r:
            r.raise_for_status()
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=256 * 1024):
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb:
                        progress_cb(done, info.size)
    except Exception as e:
        raise DownloadError(f"Tải bản cập nhật thất bại: {e}") from e

    if info.size and dest.stat().st_size != info.size:
        dest.unlink(missing_ok=True)
        raise DownloadError(
            "File tải về không đúng kích thước (mạng chập chờn?) — thử lại."
        )
    return dest


def run_installer(path: Path) -> None:
    """Chạy Inno Setup installer chế độ im lặng; app phải tự thoát ngay sau đó
    để installer ghi đè được thư mục cài đặt (/CLOSEAPPLICATIONS hỗ trợ thêm)."""
    subprocess.Popen([str(path), "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])
