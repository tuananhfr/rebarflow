"""Golden test LÕI: công thức As + check phải khớp từng con số sheet D1 file gốc
(chế độ EXCEL_COMPAT), và mode TCVN_STRICT phải luôn ra thép >= EXCEL_COMPAT."""

import json
from pathlib import Path

import pytest

from rebarflow.core.models import CalcMode, MaterialParams, StripDesign, StripEnvelope
from rebarflow.core.rebar_calc import calc_strip

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "golden_d1.json").read_text(encoding="utf-8")
)

REL = 1e-9


def _make_design(row: dict) -> StripDesign:
    env = StripEnvelope(
        strip=row["strip"],
        width=row["width"],
        m_pos=0.0 if row["m_pos"] in ("-", None) else float(row["m_pos"]),
        m_pos_combo="", m_pos_station=0.0,
        m_neg=0.0 if row["m_neg"] in ("-", None) else float(row["m_neg"]),
        m_neg_combo="", m_neg_station=0.0,
        v_max=0.0, v_combo="",
    )
    return StripDesign(
        env=env, h=float(row["h"]),
        dia_top=row["dia_top"], spacing_top=row["spa_top"],
        dia_bot=row["dia_bot"], spacing_bot=row["spa_bot"],
    )


def _mat(mode: CalcMode) -> MaterialParams:
    p = GOLDEN["params"]
    return MaterialParams(
        concrete=p["concrete"], steel=p["steel"],
        cover_top_mm=float(p["cover_top_mm"]), cover_bot_mm=float(p["cover_bot_mm"]),
        as_ham_cm2=float(p["as_ham_cm2"]), mode=mode,
    )


def _assert_value(actual, expected, what: str):
    if isinstance(expected, str):  # "CT" hoặc "-"
        assert actual == expected, f"{what}: {actual!r} != {expected!r}"
    else:
        got = 0.0 if actual is None else actual
        assert got == pytest.approx(float(expected), rel=REL, abs=1e-12), (
            f"{what}: {got} != {expected}"
        )


@pytest.mark.parametrize("row", GOLDEN["rows"], ids=[r["strip"] for r in GOLDEN["rows"]])
def test_excel_compat_khop_sheet_d1(row):
    d = _make_design(row)
    calc_strip(d, _mat(CalcMode.EXCEL_COMPAT))
    _assert_value(d.as_top_req, row["as_top"], f"{row['strip']} as_top")
    _assert_value(d.as_bot_req, row["as_bot"], f"{row['strip']} as_bot")
    _assert_value(d.check_top, row["check_top"], f"{row['strip']} check_top")
    _assert_value(d.check_bot, row["check_bot"], f"{row['strip']} check_bot")


@pytest.mark.parametrize("row", GOLDEN["rows"], ids=[r["strip"] for r in GOLDEN["rows"]])
def test_tcvn_strict_ra_thep_nhieu_hon(row):
    """Sanity: mode TCVN chuẩn luôn yêu cầu thép >= mode giống Excel."""
    d_compat, d_strict = _make_design(row), _make_design(row)
    calc_strip(d_compat, _mat(CalcMode.EXCEL_COMPAT))
    calc_strip(d_strict, _mat(CalcMode.TCVN_STRICT))
    for a, b in ((d_strict.as_top_req, d_compat.as_top_req),
                 (d_strict.as_bot_req, d_compat.as_bot_req)):
        if a is not None and b is not None:
            assert a >= b - 1e-12
