"""Đọc file .mdb export từ SAFE → SafeModel.

Bảng bắt buộc : Program Control (check đơn vị), Strip Forces.
Bảng optional : Object Geometry - Design Strips (cần cho DXF),
                Slab Properties 02 - Solid Slabs (chỉ hiển thị tham khảo).
"""

from rebarflow.constants import (
    SAFE_REQUIRED_UNITS,
    TBL_PROGRAM_CONTROL,
    TBL_SLAB_PROPS,
    TBL_STRIP_FORCES,
    TBL_STRIP_GEOMETRY,
)
from rebarflow.core.mdb_reader import MdbFile, TableNotFoundError
from rebarflow.core.models import SafeModel, StripForceRow, StripGeometry


class SafeImportError(Exception):
    """Lỗi chặn khi import file SAFE — message tiếng Việt hướng người dùng."""


def load_safe(path: str) -> SafeModel:
    mdb = MdbFile(path)

    try:
        control_rows = mdb.read_table(TBL_PROGRAM_CONTROL)
    except TableNotFoundError as e:
        raise SafeImportError(str(e)) from e
    if not control_rows:
        raise SafeImportError(f"Bảng «{TBL_PROGRAM_CONTROL}» rỗng — file export lỗi?")
    control = control_rows[0]

    units = control.get("CurrUnits")
    if units != SAFE_REQUIRED_UNITS:
        raise SafeImportError(
            f"Sai đơn vị: file đang là «{units}». "
            f"Trong SAFE chuyển đơn vị {SAFE_REQUIRED_UNITS} rồi export lại."
        )

    try:
        force_rows = mdb.read_table(TBL_STRIP_FORCES)
    except TableNotFoundError as e:
        raise SafeImportError(str(e)) from e
    forces = [_parse_force_row(r) for r in force_rows]
    if not forces:
        raise SafeImportError(f"Bảng «{TBL_STRIP_FORCES}» không có dòng dữ liệu nào.")

    missing: list[str] = []
    geometry = _load_geometry(mdb, missing)
    slab_props = _load_slab_props(mdb, missing)

    program = str(control.get("ProgramName", "SAFE"))
    version = control.get("Version")
    if version:
        program = f"{program} {version}"

    return SafeModel(
        source_path=mdb.path,
        program=program,
        forces=forces,
        geometry=geometry,
        slab_props=slab_props,
        missing_tables=missing,
    )


def _parse_force_row(r: dict) -> StripForceRow:
    return StripForceRow(
        strip=str(r["Strip"]),
        station=float(r["Station"]),
        location=str(r.get("Location") or ""),
        output_case=str(r.get("OutputCase") or ""),
        case_type=str(r.get("CaseType") or ""),
        p=float(r.get("P") or 0.0),
        v2=float(r.get("V2") or 0.0),
        t=float(r.get("T") or 0.0),
        m3=float(r.get("M3") or 0.0),
        global_x=float(r.get("GlobalX") or 0.0),
        global_y=float(r.get("GlobalY") or 0.0),
        cut_width=float(r["CutWidth"]),
    )


def _load_geometry(mdb: MdbFile, missing: list[str]) -> list[StripGeometry]:
    try:
        rows = mdb.read_table(TBL_STRIP_GEOMETRY)
    except TableNotFoundError:
        missing.append(TBL_STRIP_GEOMETRY)
        return []

    by_strip: dict[str, list[dict]] = {}
    for r in rows:
        by_strip.setdefault(str(r["Strip"]), []).append(r)

    geos = []
    for strip, rs in by_strip.items():
        if len(rs) < 2:
            continue  # strip lỗi geometry — bỏ qua, DXF sẽ không vẽ strip này
        a, b = rs[0], rs[1]
        geos.append(
            StripGeometry(
                strip=strip,
                x1=float(a["GlobalX"]), y1=float(a["GlobalY"]),
                x2=float(b["GlobalX"]), y2=float(b["GlobalY"]),
            )
        )
    return geos


def _load_slab_props(mdb: MdbFile, missing: list[str]) -> list[dict]:
    try:
        return mdb.read_table(TBL_SLAB_PROPS)
    except TableNotFoundError:
        missing.append(TBL_SLAB_PROPS)
        return []
