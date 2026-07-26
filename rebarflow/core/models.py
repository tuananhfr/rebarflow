"""Data models thuần (dataclass) — KHÔNG import PySide6 hay bất kỳ thứ gì từ ui/."""

from dataclasses import dataclass, field
from enum import Enum

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


class CalcMode(Enum):
    EXCEL_COMPAT = "excel_compat"   # mặc định — tái hiện file Excel gốc 100%
    TCVN_STRICT = "tcvn_strict"     # sửa 2 điểm lệch (docs/GHI-CHU-CONG-THUC-GOC.md)


@dataclass
class StripForceRow:
    """1 dòng bảng "Strip Forces" trong mdb SAFE."""

    strip: str
    station: float          # m
    location: str           # "Before"/"After"
    output_case: str        # tên tổ hợp, vd "BAO"
    case_type: str          # "Combination"
    p: float                # kN
    v2: float               # kN — lực cắt
    t: float                # kN·m
    m3: float               # kN·m — moment dùng tính thép
    global_x: float
    global_y: float
    cut_width: float        # m — bề rộng strip tại vị trí cắt


@dataclass
class StripGeometry:
    """1 strip = 2 điểm đầu-cuối (bảng "Object Geometry - Design Strips")."""

    strip: str
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class SafeModel:
    source_path: str
    program: str                          # "SAFE 2016"...
    forces: list[StripForceRow]
    geometry: list[StripGeometry]         # RỖNG nếu file thiếu bảng geometry (vẫn hợp lệ)
    slab_props: list[dict]
    missing_tables: list[str] = field(default_factory=list)


@dataclass
class StripEnvelope:
    """Kết quả gom nội lực per strip (output của strip_aggregate).

    m_pos/m_neg = 0.0 khi strip không có moment dương/âm — GIỮ semantics của
    VBA gốc (mo1/mo2 khởi tạo 0) để As=0 và check="CT" khớp file gốc.
    """

    strip: str
    width: float            # CutWidth tại dòng có M+ max (fallback: dòng đầu strip)
    m_pos: float
    m_pos_combo: str
    m_pos_station: float
    m_neg: float
    m_neg_combo: str
    m_neg_station: float
    v_max: float            # lực cắt có |V| lớn nhất, GIỮ DẤU
    v_combo: str


@dataclass
class MaterialParams:
    """Thông số chung do user chọn trên panel."""

    concrete: str = DEFAULT_CONCRETE
    steel: str = DEFAULT_STEEL
    cover_top_mm: float = DEFAULT_COVER_TOP_MM
    cover_bot_mm: float = DEFAULT_COVER_BOT_MM
    as_ham_cm2: float = DEFAULT_AS_HAM_CM2
    mode: CalcMode = CalcMode.EXCEL_COMPAT


@dataclass
class StripDesign:
    """1 dòng bảng kết quả: envelope + input user + kết quả engine điền vào."""

    env: StripEnvelope
    pile_cap_name: str = ""                 # "Tên Đài" — user nhập tay
    h: float = DEFAULT_H_DAI_M              # h đài (m) — user chỉnh được từng dòng
    dia_top: int = DEFAULT_DIA_MM           # Ø thép trên (mm)
    spacing_top: int = DEFAULT_SPACING_MM   # a thép trên (mm)
    dia_bot: int = DEFAULT_DIA_MM
    spacing_bot: int = DEFAULT_SPACING_MM
    # engine điền (rebar_calc.calc_strip):
    as_top_req: float | None = None         # cm²; None → hiển thị "-"
    as_bot_req: float | None = None
    check_top: float | str = ""             # tỷ lệ (raw float), "CT", hoặc "-"
    check_bot: float | str = ""


@dataclass
class JointReaction:
    """Phản lực chân cột từ ETABS (đơn vị Ton 9.7.4 / tonf 2017)."""

    story: str
    point: str
    output_case: str
    fz: float
    x: float | None = None      # điền sau khi join với bảng coordinates
    y: float | None = None


@dataclass
class EtabsModel:
    source_path: str
    version: str                # "9.7.4" | "2017"
    reactions: list[JointReaction]
    missing_tables: list[str] = field(default_factory=list)
