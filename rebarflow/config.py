"""Đọc/ghi config user: %APPDATA%/rebarFlow/config.json.

Giữ dạng dict phẳng đơn giản — mọi giá trị panel/settings + thư mục lần cuối.
File hỏng/thiếu → dùng defaults, không bao giờ crash vì config.
"""

import json
import logging
import os
from pathlib import Path

from rebarflow.constants import (
    DEFAULT_AS_HAM_CM2,
    DEFAULT_CONCRETE,
    DEFAULT_COVER_BOT_MM,
    DEFAULT_COVER_TOP_MM,
    DEFAULT_DIA_MM,
    DEFAULT_H_DAI_M,
    DEFAULT_SPACING_MM,
    DEFAULT_STEEL,
)

log = logging.getLogger(__name__)

CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "rebarFlow"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: dict = {
    "concrete": DEFAULT_CONCRETE,
    "steel": DEFAULT_STEEL,
    "cover_top_mm": DEFAULT_COVER_TOP_MM,
    "cover_bot_mm": DEFAULT_COVER_BOT_MM,
    "as_ham_cm2": DEFAULT_AS_HAM_CM2,
    "mode": "excel_compat",
    "h_dai_m": DEFAULT_H_DAI_M,
    "dia_mm": DEFAULT_DIA_MM,
    "spacing_mm": DEFAULT_SPACING_MM,
    # DXF style (Settings dialog)
    "dxf_text_height": 250.0,
    "dxf_text_offset": 200.0,
    "dxf_line_spacing": 400.0,
    "last_dir": "",
    "skip_version": "",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    except FileNotFoundError:
        pass
    except Exception as e:
        log.warning("Config hỏng, dùng defaults: %s", e)
    return cfg


def save(cfg: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(cfg, indent=1, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        log.warning("Không lưu được config: %s", e)
