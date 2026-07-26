"""Công thức tính As + check bố trí thép — LÕI của app.

Tái hiện đúng các ô Z21/AA21/AB21/AC21/N21/O21/T21/U21 sheet D1 file gốc.
Hai chỗ đánh dấu ❗ là CHỦ Ý của tác giả file gốc (đã xác nhận 07/2026) —
KHÔNG "sửa cho đúng" trong mode EXCEL_COMPAT. Chi tiết và lý do:
docs/GHI-CHU-CONG-THUC-GOC.md.

Đơn vị: M kN·m, b/h₀ m, Rb sau quy đổi kN/m², Rs MPa (×1000 → kN/m²)
→ As ra m², nhân 1e4 → cm².
"""

import math

from rebarflow.constants import CHECK_RATIO_MAX, CONCRETE, STEEL
from rebarflow.core.models import CalcMode, MaterialParams, StripDesign


def calc_strip(d: StripDesign, mat: MaterialParams) -> None:
    """Điền as_top_req, as_bot_req, check_top, check_bot vào d (in-place)."""
    rb_raw = CONCRETE[mat.concrete][0]      # kG/cm², vd 130 (ô J12)
    rs_mpa = STEEL[mat.steel][0] / 10       # → MPa, vd 350   (ô J13)

    if mat.mode is CalcMode.EXCEL_COMPAT:
        rb = rb_raw * 1000                  # ❗ giống hệt Excel: 130 → 130_000
    else:
        rb = rb_raw / 10 * 1000             # 130 kG/cm² → 13 MPa → 13_000 kN/m²

    h0_top = d.h - mat.cover_top_mm / 1000  # m
    h0_bot = d.h - mat.cover_bot_mm / 1000
    b = d.env.width

    # ---- THÉP TRÊN từ M− (ô Z21 → AA21 → N21) ----
    d.as_top_req, overflow_top = _as_required(
        m=-d.env.m_neg, rb=rb, rs_mpa=rs_mpa, b=b, h0_zeta=h0_top, h0_as=h0_top
    )

    # ---- THÉP DƯỚI từ M+ (ô AB21 → AC21 → O21) ----
    # ❗ EXCEL_COMPAT: ζ tính bằng h₀ của lớp TRÊN, As lại dùng h₀ lớp DƯỚI
    h0_zeta_bot = h0_top if mat.mode is CalcMode.EXCEL_COMPAT else h0_bot
    d.as_bot_req, overflow_bot = _as_required(
        m=d.env.m_pos, rb=rb, rs_mpa=rs_mpa, b=b, h0_zeta=h0_zeta_bot, h0_as=h0_bot
    )

    # ---- CHECK (ô T21/U21) — F16 "thép sàn hầm" chỉ cộng cho thép TRÊN ----
    d.check_top = (
        "CT" if overflow_top
        else check_ratio(d.dia_top, d.spacing_top, b, d.as_top_req, extra_cm2=mat.as_ham_cm2)
    )
    d.check_bot = (
        "CT" if overflow_bot
        else check_ratio(d.dia_bot, d.spacing_bot, b, d.as_bot_req)
    )


def _as_required(
    m: float, rb: float, rs_mpa: float, b: float, h0_zeta: float, h0_as: float
) -> tuple[float | None, bool]:
    """As yêu cầu (cm²). Trả (as_req, overflow).

    m = 0 → As = 0 (semantics VBA, check sẽ ra "CT").
    1 − 2αm < 0 (Excel ra #NUM!) → (None, True): tiết diện không đủ,
    caller set check "CT"; UI gợi ý tăng h đài / mác bê tông.
    """
    alpha = m / (rb * b * h0_zeta**2)
    disc = 1 - 2 * alpha
    if disc < 0:
        return None, True
    zeta = 0.5 * (1 + math.sqrt(disc))
    return m / (zeta * rs_mpa * 1000 * h0_as) * 1e4, False


def check_ratio(
    dia_mm: float, spacing_mm: float, width_m: float,
    as_req: float | None, extra_cm2: float = 0.0,
) -> float | str:
    """Tỷ lệ As bố trí / As yêu cầu (ô T21/U21) — trả float RAW, UI tự làm tròn.

    as_req None → "-" ; as_req 0 → "CT" ; tỷ lệ >= 5 → "CT".
    """
    if as_req is None:
        return "-"
    if as_req == 0:
        return "CT"
    provided = math.pi * (dia_mm / 10) ** 2 / 4 * (width_m * 1000 / spacing_mm) + extra_cm2
    ratio = provided / as_req
    return ratio if ratio < CHECK_RATIO_MAX else "CT"
