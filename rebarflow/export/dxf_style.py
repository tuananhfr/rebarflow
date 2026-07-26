"""Hằng số vẽ DXF — giá trị mặc định lấy đúng theo macro `XUATAUTOCAD` gốc.

Tách riêng để Settings dialog (M3) cho user chỉnh và lưu vào config.json.
"""

SCALE = 1000            # tọa độ mdb là m → bản vẽ mm (VBA nhân 1000)
TEXT_HEIGHT = 250       # chiều cao text (VBA AddText ... 250)
TEXT_OFFSET = 200       # đẩy text khỏi đầu strip / điểm phản lực (VBA +200)
LINE_SPACING = 400      # khoảng cách giữa các dòng text (VBA +400)

# Màu theo VBA gốc: strip phương ngang ĐỎ (acRed=1), phương dọc XANH LÁ (acGreen=3).
# Cải tiến: vẽ vào layer riêng, entity để màu BYLAYER → nhìn y hệt macro cũ.
LAYER_STRIP_X = "RF_STRIP_X"
COLOR_STRIP_X = 1       # đỏ
LAYER_STRIP_Y = "RF_STRIP_Y"
COLOR_STRIP_Y = 3       # xanh lá
LAYER_REACTION = "RF_REACTION"
COLOR_REACTION = 3      # VBA: Phanluc.Color = acGreen

DXF_VERSION = "R2010"   # AutoCAD 2010+ mở được


from dataclasses import dataclass


@dataclass
class DxfStyle:
    """Các giá trị user chỉnh được trong Settings dialog (lưu vào config.json)."""

    text_height: float = TEXT_HEIGHT
    text_offset: float = TEXT_OFFSET
    line_spacing: float = LINE_SPACING

    @classmethod
    def from_config(cls, cfg: dict) -> "DxfStyle":
        return cls(
            text_height=float(cfg.get("dxf_text_height", TEXT_HEIGHT)),
            text_offset=float(cfg.get("dxf_text_offset", TEXT_OFFSET)),
            line_spacing=float(cfg.get("dxf_line_spacing", LINE_SPACING)),
        )


DEFAULT_STYLE = DxfStyle()
