"""Smoke test UI chạy offscreen (không cần màn hình): load MONG.mdb vào tab,
sửa 1 ô Ø thép → check tính lại; đổi chế độ tính → As đổi."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from rebarflow.config import DEFAULTS  # noqa: E402
from rebarflow.core.safe_import import load_safe  # noqa: E402
from rebarflow.ui.results_table import (  # noqa: E402
    COL_CHECK_BOT,
    COL_DIA_BOT,
    COL_H,
)
from rebarflow.ui.strips_tab import StripsTab  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def tab(app, mong_mdb_path, monkeypatch):
    t = StripsTab(dict(DEFAULTS))
    # chặn QMessageBox cảnh báo thiếu bảng (offscreen không có người bấm OK)
    monkeypatch.setattr(
        "rebarflow.ui.strips_tab.QMessageBox.warning", lambda *a, **k: None
    )
    t.load_safe_model(load_safe(mong_mdb_path))
    return t


def test_load_du_104_strips(tab):
    assert tab.model.rowCount() == 104
    assert tab.has_data()
    ok, why = tab.can_export_dxf()
    assert not ok and "Geometry" in why or "geometry" in why.lower()


def test_sua_o_thi_tinh_lai(tab):
    m = tab.model
    row = 0
    before = m.index(row, COL_CHECK_BOT).data(Qt.DisplayRole)  # D20a200 → ratio ≥5 → "CT"
    assert before == "CT"
    assert m.setData(m.index(row, COL_DIA_BOT), 10, Qt.EditRole)
    after = m.index(row, COL_CHECK_BOT).data(Qt.DisplayRole)
    assert after != "CT" and float(after) > 1  # Ø giảm → tỷ lệ rơi về vùng số, vẫn đạt

    # giá trị không hợp lệ bị từ chối
    assert not m.setData(m.index(row, COL_DIA_BOT), 99, Qt.EditRole)
    assert not m.setData(m.index(row, COL_H), -1, Qt.EditRole)


def test_doi_che_do_tinh_as_doi(tab):
    m = tab.model
    as_before = m.designs()[0].as_top_req
    tab.panel.mode_tcvn.setChecked(True)  # trigger params_changed → recalc
    as_after = m.designs()[0].as_top_req
    assert as_after > as_before  # TCVN chuẩn luôn ra nhiều thép hơn
