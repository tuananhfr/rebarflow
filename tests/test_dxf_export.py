"""Test xuất DXF: ghi file rồi đọc lại bằng ezdxf, kiểm tra entity/vị trí/layer/góc.

Dùng dữ liệu synthetic (1 strip ngang + 1 strip dọc) để test độc lập với golden;
thêm 1 test tích hợp với geometry thật trích từ file gốc (skip nếu chưa có golden).
"""

import json
import math
from pathlib import Path

import ezdxf
import pytest

from rebarflow.core.models import (
    JointReaction,
    StripDesign,
    StripEnvelope,
    StripGeometry,
)
from rebarflow.export import dxf_style as st
from rebarflow.export.dxf_reactions import export_reactions_dxf, filter_reactions
from rebarflow.export.dxf_strips import export_strips_dxf

GEOMETRY_JSON = Path(__file__).parent / "golden" / "geometry_sample.json"


def _design(strip: str, dia_top=18, spa_top=200, dia_bot=14, spa_bot=150) -> StripDesign:
    env = StripEnvelope(
        strip=strip, width=1.05, m_pos=100.0, m_pos_combo="BAO", m_pos_station=0.0,
        m_neg=-200.0, m_neg_combo="BAO", m_neg_station=0.5, v_max=300.0, v_combo="BAO",
    )
    return StripDesign(env=env, dia_top=dia_top, spacing_top=spa_top,
                       dia_bot=dia_bot, spacing_bot=spa_bot)


def test_strips_ngang_doc(tmp_path):
    designs = [_design("CSA1"), _design("CSB1")]
    geos = [
        StripGeometry(strip="CSA1", x1=0.0, y1=2.0, x2=5.0, y2=2.0),   # ngang
        StripGeometry(strip="CSB1", x1=1.0, y1=0.0, x2=1.0, y2=4.0),   # dọc
    ]
    out = tmp_path / "strips.dxf"
    skipped = export_strips_dxf(designs, geos, str(out))
    assert skipped == []

    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    polys = list(msp.query("LWPOLYLINE"))
    texts = list(msp.query("TEXT"))
    assert len(polys) == 2
    assert len(texts) == 6  # 3 dòng text mỗi strip

    # strip ngang → layer đỏ, tọa độ nhân 1000
    p_ngang = next(p for p in polys if p.dxf.layer == st.LAYER_STRIP_X)
    pts = [(v[0], v[1]) for v in p_ngang.get_points()]
    assert pts == [(0.0, 2000.0), (5000.0, 2000.0)]

    # strip dọc → layer xanh, text xoay 90°
    t_doc = [t for t in texts if t.dxf.layer == st.LAYER_STRIP_Y]
    assert all(t.dxf.rotation == pytest.approx(90.0) for t in t_doc)
    contents = {t.dxf.text for t in t_doc}
    assert contents == {"DUOI-D14 A150", "TREN-D18 A200", "CSB1"}

    # vị trí text strip ngang: x = max(x)+200, các dòng cách nhau 400 theo Y
    t_ngang = sorted(
        (t for t in texts if t.dxf.layer == st.LAYER_STRIP_X),
        key=lambda t: t.dxf.insert[1],
    )
    assert t_ngang[0].dxf.insert[0] == pytest.approx(5200.0)
    assert t_ngang[0].dxf.text == "DUOI-D14 A150"
    ys = [t.dxf.insert[1] for t in t_ngang]
    assert ys == pytest.approx([2000.0, 2400.0, 2800.0])


def test_strip_thieu_geometry_bi_bo_qua(tmp_path):
    designs = [_design("CSA1"), _design("KHONG_CO_GEO")]
    geos = [StripGeometry(strip="CSA1", x1=0, y1=0, x2=1, y2=0)]
    out = tmp_path / "strips.dxf"
    assert export_strips_dxf(designs, geos, str(out)) == ["KHONG_CO_GEO"]


def test_reactions(tmp_path):
    reactions = [
        JointReaction(story="Base", point="1", output_case="TH1", fz=299.755, x=-3.2, y=10.5),
        JointReaction(story="Base", point="1", output_case="TH2", fz=150.0, x=-3.2, y=10.5),
        JointReaction(story="Base", point="2", output_case="TH1", fz=54.16, x=0.0, y=0.0),
        JointReaction(story="Base", point="3", output_case="TH1", fz=99.0),  # chưa có tọa độ
    ]
    # lọc theo combo
    th1 = filter_reactions(reactions, case="TH1")
    assert [r.point for r in th1] == ["1", "2"]
    # |Fz| max mỗi điểm
    best = filter_reactions(reactions, max_per_point=True)
    assert {r.point: r.fz for r in best} == {"1": 299.755, "2": 54.16}

    out = tmp_path / "reactions.dxf"
    assert export_reactions_dxf(th1, str(out)) == 2
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    assert len(list(msp.query("POINT"))) == 2
    texts = {t.dxf.text for t in msp.query("TEXT")}
    assert texts == {"Fz = 299.8T", "Fz = 54.2T"}  # giống VBA: Round(fz,1) & "T"
    t = next(t for t in msp.query("TEXT") if t.dxf.text == "Fz = 54.2T")
    assert (t.dxf.insert[0], t.dxf.insert[1]) == (200.0, 200.0)


@pytest.mark.skipif(not GEOMETRY_JSON.exists(), reason="chưa có golden geometry (xem tests/golden/README.md)")
def test_tich_hop_geometry_that(tmp_path, golden_d1):
    rows = json.loads(GEOMETRY_JSON.read_text(encoding="utf-8"))
    by_strip: dict[str, list[dict]] = {}
    for r in rows:
        by_strip.setdefault(str(r["strip"]), []).append(r)
    geos = [
        StripGeometry(strip=s, x1=p[0]["x"], y1=p[0]["y"], x2=p[1]["x"], y2=p[1]["y"])
        for s, p in by_strip.items() if len(p) >= 2
    ]
    designs = [_design(g["strip"]) for g in golden_d1["rows"]]

    out = tmp_path / "real.dxf"
    skipped = export_strips_dxf(designs, geos, str(out))
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    n_drawn = len(designs) - len(skipped)
    assert n_drawn > 0
    assert len(list(msp.query("LWPOLYLINE"))) == n_drawn
    assert len(list(msp.query("TEXT"))) == 3 * n_drawn
