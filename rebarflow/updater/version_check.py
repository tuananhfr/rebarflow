"""Check bản mới trên GitHub Releases (repo public tuananhfr/rebarflow).

Gọi trong thread nền khi khởi động app; MỌI lỗi mạng phải được caller nuốt
im lặng — app hoạt động bình thường khi không có internet.
"""

from dataclasses import dataclass

import requests
from packaging import version as _version

OWNER = "tuananhfr"
REPO = "rebarflow"
API_LATEST = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"


@dataclass
class UpdateInfo:
    version: str        # "1.1.0"
    notes: str          # body của release (markdown changelog)
    url: str            # link tải setup.exe
    size: int           # bytes — verify sau khi tải


def check_update(current: str, timeout: float = 5.0) -> UpdateInfo | None:
    """Trả UpdateInfo nếu có bản mới hơn `current`, ngược lại None.

    Raise exception khi lỗi mạng/API — caller quyết định nuốt hay báo
    (check tự động: nuốt; check tay từ toolbar: báo).
    """
    r = requests.get(
        API_LATEST, timeout=timeout,
        headers={"Accept": "application/vnd.github+json"},
    )
    r.raise_for_status()
    data = r.json()

    latest = str(data.get("tag_name", "")).lstrip("vV").strip()
    if not latest:
        return None
    if _version.parse(latest) <= _version.parse(current):
        return None

    asset = next(
        (a for a in data.get("assets", []) if a.get("name", "").endswith(".exe")),
        None,
    )
    if asset is None:       # release không đính kèm installer → coi như không có
        return None

    return UpdateInfo(
        version=latest,
        notes=data.get("body") or "",
        url=asset["browser_download_url"],
        size=int(asset.get("size", 0)),
    )
