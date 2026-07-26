"""Golden test aggregate: gom nội lực per strip từ sheet Data phải khớp sheet D1.

Tool quét ĐỦ dữ liệu (đúng), VBA gốc có 2 lỗi vòng lặp (PLAN.md §6.2):
bỏ sót 9 dòng cuối + shear so sánh sai dấu. Vì vậy mỗi giá trị golden được
chấp nhận nếu khớp kết quả ĐÚNG *hoặc* khớp kết quả mô phỏng-VBA (known diff);
khớp kiểu nào được ghi nhận in ra cuối test. Lệch cả hai → FAIL thật."""

import pytest

from rebarflow.core.models import StripForceRow
from rebarflow.core.strip_aggregate import aggregate

REL = 1e-9

_known_diffs: list[str] = []


def _rows(golden_forces) -> list[StripForceRow]:
    return [
        StripForceRow(
            strip=str(f["strip"]), station=float(f["station"]),
            location=str(f["location"]), output_case=str(f["output_case"]),
            case_type=str(f["case_type"]), p=float(f["p"] or 0),
            v2=float(f["v2"] or 0), t=float(f["t"] or 0), m3=float(f["m3"] or 0),
            global_x=float(f["global_x"] or 0), global_y=float(f["global_y"] or 0),
            cut_width=float(f["cut_width"]),
        )
        for f in golden_forces
    ]


def _vba_sim(all_rows: list[StripForceRow]) -> dict[str, dict]:
    """Mô phỏng đúng vòng lặp VBA tinhthepmax (kể cả 2 lỗi) để phân loại known diff."""
    n = len(all_rows)
    scanned = all_rows[: max(0, n - 9)]  # VBA: For Z = 10 To ndt → sót 9 dòng cuối
    strips: list[str] = []
    for r in all_rows:  # danh sách strip thì VBA quét đủ (Do While ... <> "")
        if r.strip not in strips:
            strips.append(r.strip)
    out = {}
    for s in strips:
        rows = [r for r in scanned if r.strip == s]
        mo1, k1 = 0.0, None
        for r in rows:
            if r.m3 > mo1:
                mo1, k1 = r.m3, r
        mo2, k2 = 0.0, None
        for r in rows:
            if r.m3 < mo2:
                mo2, k2 = r.m3, r
        q, k3 = 0.0, None
        for r in rows:
            if abs(r.v2) > q:  # lỗi VBA: so |V| với q CÓ DẤU
                q, k3 = r.v2, r
        first = rows[0] if rows else None
        rp, rn = k1 or first, k2 or first
        out[s] = {
            "m_pos": mo1, "m_neg": mo2,
            "width": rp.cut_width if rp else None,
            "m_pos_combo": rp.output_case if rp else None,
            "m_pos_station": rp.station if rp else None,
            "m_neg_combo": rn.output_case if rn else None,
            "m_neg_station": rn.station if rn else None,
            "shear": k3.v2 if k3 else 0.0,
        }
    return out


def _match(actual, expected) -> bool:
    if isinstance(expected, str) or expected is None:
        return str(actual) == str(expected)
    return actual == pytest.approx(float(expected), rel=REL, abs=1e-9)


def test_aggregate_khop_sheet_d1(golden_forces, golden_d1):
    rows = _rows(golden_forces)
    ours = {e.strip: e for e in aggregate(rows)}
    vba = _vba_sim(rows)

    assert len(ours) == len(golden_d1["rows"]), (
        f"số strip: tool {len(ours)} != golden {len(golden_d1['rows'])}"
    )

    failures = []
    for g in golden_d1["rows"]:
        s = g["strip"]
        e = ours.get(s)
        assert e is not None, f"tool không có strip {s}"
        checks = [
            ("m_pos", e.m_pos), ("m_neg", e.m_neg), ("width", e.width),
            ("m_pos_combo", e.m_pos_combo), ("m_pos_station", e.m_pos_station),
            ("m_neg_combo", e.m_neg_combo), ("m_neg_station", e.m_neg_station),
            ("shear", e.v_max),
        ]
        for field, actual in checks:
            expected = g[field]
            if _match(actual, expected):
                continue
            if _match(vba[s][field], expected):  # VBA-sim khớp → known diff, tool ĐÚNG hơn
                _known_diffs.append(
                    f"{s}.{field}: tool={actual!r} | Excel(golden)={expected!r} ← lỗi vòng lặp VBA"
                )
                continue
            failures.append(f"{s}.{field}: tool={actual!r}, golden={expected!r}, vba_sim={vba[s][field]!r}")

    assert not failures, "Lệch KHÔNG giải thích được:\n" + "\n".join(failures)
    if _known_diffs:
        print("\n=== KNOWN DIFFS (lỗi vòng lặp VBA gốc — tool đúng hơn) ===")
        for d in _known_diffs:
            print(" ", d)
