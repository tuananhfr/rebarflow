"""DXF mặt bằng strips + text thép — tái hiện bản vẽ của macro `XUATAUTOCAD`.

Mỗi strip: polyline 2 điểm + 3 dòng text xoay theo phương strip
("DUOI-D{Ø} A{a}", "TREN-D{Ø} A{a}", tên strip). Strip phương ngang màu đỏ,
phương dọc màu xanh lá (layer riêng, màu BYLAYER).
"""

import math

import ezdxf

from rebarflow.core.models import StripDesign, StripGeometry
from rebarflow.export import dxf_style as st


def export_strips_dxf(
    designs: list[StripDesign],
    geometries: list[StripGeometry],
    path: str,
) -> list[str]:
    """Ghi file DXF. Trả về danh sách strip bị bỏ qua vì không có geometry
    (caller hiển thị cảnh báo)."""
    geos = {g.strip: g for g in geometries}
    doc = ezdxf.new(st.DXF_VERSION)
    doc.layers.add(st.LAYER_STRIP_X, color=st.COLOR_STRIP_X)
    doc.layers.add(st.LAYER_STRIP_Y, color=st.COLOR_STRIP_Y)
    msp = doc.modelspace()

    skipped: list[str] = []
    for d in designs:
        g = geos.get(d.env.strip)
        if g is None:
            skipped.append(d.env.strip)
            continue
        _draw_strip(msp, d, g)

    doc.saveas(path)
    return skipped


def _strip_angle_deg(x1: float, y1: float, x2: float, y2: float) -> float:
    """Góc strip, chuẩn hóa về (-90°, 90°] — text không bao giờ bị lộn ngược."""
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    if angle <= -90:
        angle += 180
    elif angle > 90:
        angle -= 180
    return angle


def _draw_strip(msp, d: StripDesign, g: StripGeometry) -> None:
    x1, y1 = g.x1 * st.SCALE, g.y1 * st.SCALE
    x2, y2 = g.x2 * st.SCALE, g.y2 * st.SCALE

    angle = _strip_angle_deg(x1, y1, x2, y2)
    horizontal = abs(angle) < 45
    layer = st.LAYER_STRIP_X if horizontal else st.LAYER_STRIP_Y

    msp.add_lwpolyline([(x1, y1), (x2, y2)], dxfattribs={"layer": layer})

    # vị trí text: giống macro gốc — ngoài đầu strip phía tọa độ lớn
    if horizontal:
        tx, ty = max(x1, x2) + st.TEXT_OFFSET, y1
    else:
        tx, ty = x1, max(y1, y2) + st.TEXT_OFFSET

    lines = (
        f"DUOI-D{d.dia_bot} A{d.spacing_bot}",
        f"TREN-D{d.dia_top} A{d.spacing_top}",
        d.env.strip,
    )
    for i, content in enumerate(lines):
        if horizontal:
            pos = (tx, ty + i * st.LINE_SPACING)
        else:
            pos = (tx - i * st.LINE_SPACING, ty)
        text = msp.add_text(
            content,
            dxfattribs={"height": st.TEXT_HEIGHT, "rotation": angle, "layer": layer},
        )
        text.set_placement(pos)
