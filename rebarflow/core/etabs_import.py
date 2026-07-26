"""Đọc file .mdb export từ ETABS (9.7.4 hoặc 2017) → EtabsModel (map phản lực Fz).

Tự nhận diện phiên bản theo bảng có trong file. Mapping cột chốt theo file Excel
gốc (PLAN.md §5.3); đọc cột theo TÊN với danh sách ứng viên — nếu file thật
dùng tên khác, lỗi sẽ in danh sách cột thực tế để bổ sung ứng viên.
"""

from rebarflow.constants import ETABS_974_REQUIRED_UNITS, ETABS_2017_REQUIRED_UNITS
from rebarflow.core.mdb_reader import MdbFile, TableNotFoundError
from rebarflow.core.models import EtabsModel, JointReaction


class EtabsImportError(Exception):
    """Lỗi chặn khi import file ETABS — message tiếng Việt hướng người dùng."""


# tên cột ứng viên (file ETABS các bản có thể đặt tên hơi khác nhau)
_CAND_POINT = ["Point", "Label", "PointID", "Joint", "UniqueName", "Unique Name"]
_CAND_CASE = ["Load", "OutputCase", "Output Case", "LoadCase", "Load Case/Combo"]
_CAND_FZ = ["FZ", "Fz"]
_CAND_STORY = ["Story", "StoryName"]
_CAND_X = ["X", "GlobalX"]
_CAND_Y = ["Y", "GlobalY"]


def load_etabs(path: str) -> EtabsModel:
    mdb = MdbFile(path)

    if mdb.has_table("Support Reactions"):          # ETABS 9.7.4
        version = "9.7.4"
        _check_units(mdb, "Control Parameters", ETABS_974_REQUIRED_UNITS)
        reactions = _read_reactions(mdb, "Support Reactions")
        coords_table = "Point Coordinates"
    elif mdb.has_table("Joint Reactions"):          # ETABS 2017+
        version = "2017"
        _check_units(mdb, "Program Control", ETABS_2017_REQUIRED_UNITS)
        reactions = _read_reactions(mdb, "Joint Reactions")
        coords_table = _find_coords_table_2017(mdb)
    else:
        raise EtabsImportError(
            "Không nhận diện được file ETABS: thiếu cả bảng «Support Reactions» "
            "(9.7.4) lẫn «Joint Reactions» (2017). Export lại và tick bảng phản lực. "
            f"Các bảng hiện có: {', '.join(mdb.table_names())}"
        )

    missing: list[str] = []
    _join_coordinates(mdb, coords_table, reactions, missing)

    return EtabsModel(
        source_path=mdb.path,
        version=version,
        reactions=reactions,
        missing_tables=missing,
    )


def _check_units(mdb: MdbFile, control_table: str, required: str) -> None:
    try:
        rows = mdb.read_table(control_table)
    except TableNotFoundError as e:
        raise EtabsImportError(str(e)) from e
    units = rows[0].get("CurrUnits") if rows else None
    if units != required:
        raise EtabsImportError(
            f"Sai đơn vị: file đang là «{units}». "
            f"Trong ETABS chuyển đơn vị «{required}» rồi export lại."
        )


def _pick(row: dict, candidates: list[str], table: str) -> str:
    for c in candidates:
        if c in row:
            return c
    raise EtabsImportError(
        f"Không nhận diện được cột trong bảng «{table}». "
        f"Cột hiện có: {', '.join(row.keys())}. "
        f"Cần một trong: {', '.join(candidates)} — báo lại dev để bổ sung."
    )


def _read_reactions(mdb: MdbFile, table: str) -> list[JointReaction]:
    try:
        rows = mdb.read_table(table)
    except TableNotFoundError as e:
        raise EtabsImportError(str(e)) from e
    if not rows:
        raise EtabsImportError(f"Bảng «{table}» không có dòng dữ liệu nào.")

    k_point = _pick(rows[0], _CAND_POINT, table)
    k_case = _pick(rows[0], _CAND_CASE, table)
    k_fz = _pick(rows[0], _CAND_FZ, table)
    k_story = next((c for c in _CAND_STORY if c in rows[0]), None)

    return [
        JointReaction(
            story=str(r[k_story]) if k_story else "",
            point=str(r[k_point]),
            output_case=str(r[k_case]),
            fz=float(r[k_fz] or 0.0),
        )
        for r in rows
    ]


def _find_coords_table_2017(mdb: MdbFile) -> str:
    for name in ("Joint Coordinates Data", "Point Object Connectivity", "Objects and Elements - Joints"):
        if mdb.has_table(name):
            return name
    # fallback: bảng nào có chữ Coordinates
    for name in mdb.table_names():
        if "Coordinates" in name:
            return name
    return "Joint Coordinates Data"  # sẽ rơi vào missing_tables ở bước join


def _join_coordinates(
    mdb: MdbFile, table: str, reactions: list[JointReaction], missing: list[str]
) -> None:
    """Gán (x, y) cho từng phản lực theo tên point. Thiếu bảng tọa độ → không chặn
    (bảng phản lực vẫn xem được), chỉ không xuất được DXF."""
    try:
        rows = mdb.read_table(table)
    except TableNotFoundError:
        missing.append(table)
        return
    if not rows:
        missing.append(table)
        return

    k_point = _pick(rows[0], _CAND_POINT, table)
    k_x = _pick(rows[0], _CAND_X, table)
    k_y = _pick(rows[0], _CAND_Y, table)
    coords = {str(r[k_point]): (float(r[k_x]), float(r[k_y])) for r in rows}

    for jr in reactions:
        xy = coords.get(jr.point)
        if xy:
            jr.x, jr.y = xy
