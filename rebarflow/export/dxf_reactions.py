"""DXF map phản lực chân cột — tái hiện macro `XUATCHANCOT`:
mỗi joint 1 POINT + text "Fz = {giá trị}T" màu xanh lá.

Cải tiến so với macro gốc (vẽ đè mọi combo lên nhau): caller lọc trước bằng
`filter_reactions` — theo 1 combo, hoặc lấy |Fz| max mỗi điểm.
"""

import ezdxf

from rebarflow.core.models import JointReaction
from rebarflow.export import dxf_style as st


def filter_reactions(
    reactions: list[JointReaction],
    case: str | None = None,
    max_per_point: bool = False,
) -> list[JointReaction]:
    """Bỏ joint chưa có tọa độ; lọc theo combo và/hoặc lấy |Fz| max mỗi điểm."""
    rs = [r for r in reactions if r.x is not None and r.y is not None]
    if case is not None:
        rs = [r for r in rs if r.output_case == case]
    if max_per_point:
        best: dict[str, JointReaction] = {}
        for r in rs:
            b = best.get(r.point)
            if b is None or abs(r.fz) > abs(b.fz):
                best[r.point] = r
        rs = list(best.values())
    return rs


def export_reactions_dxf(reactions: list[JointReaction], path: str) -> int:
    """Ghi file DXF, trả về số joint đã vẽ."""
    doc = ezdxf.new(st.DXF_VERSION)
    doc.layers.add(st.LAYER_REACTION, color=st.COLOR_REACTION)
    msp = doc.modelspace()

    n = 0
    for r in reactions:
        if r.x is None or r.y is None:
            continue
        x, y = r.x * st.SCALE, r.y * st.SCALE
        msp.add_point((x, y), dxfattribs={"layer": st.LAYER_REACTION})
        text = msp.add_text(
            f"Fz = {round(r.fz, 1)}T",       # giống VBA: "Fz = " & Round(..,1) & "T"
            dxfattribs={"height": st.TEXT_HEIGHT, "layer": st.LAYER_REACTION},
        )
        text.set_placement((x + st.TEXT_OFFSET, y + st.TEXT_OFFSET))
        n += 1

    doc.saveas(path)
    return n
