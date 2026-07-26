"""Test import file SAFE thật (MONG.mdb — fixture có thật từ SAFE 2016,
đặc biệt: file này THIẾU bảng geometry → phải import được, không chặn)."""

import pytest

from rebarflow.constants import TBL_STRIP_GEOMETRY
from rebarflow.core.safe_import import load_safe


@pytest.fixture(scope="module")
def model(mong_mdb_path):
    return load_safe(mong_mdb_path)


def test_doc_duoc_va_dung_so_dong(model):
    assert len(model.forces) == 1592
    assert "SAFE" in model.program


def test_thieu_bang_geometry_khong_chan(model):
    assert TBL_STRIP_GEOMETRY in model.missing_tables
    assert model.geometry == []


def test_du_lieu_dong_dau(model):
    r = model.forces[0]
    assert r.strip == "CSA1"
    assert r.station == pytest.approx(0.0)
    assert r.output_case == "CBB"
    assert r.cut_width == pytest.approx(2.1)
