"""Bảng kết quả thép đài: QTableView + model editable.

Cột user sửa được: Tên Đài, h đài, Ø/a trên-dưới → sửa xong engine tính lại
NGAY dòng đó (calc nhẹ, đồng bộ). Cột Check tô màu xanh/đỏ/cam.
"""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QAction, QColor, QKeySequence, QPalette
from PySide6.QtWidgets import QApplication, QMenu, QTableView

from rebarflow.core.models import MaterialParams, StripDesign
from rebarflow.core.rebar_calc import calc_strip

# Màu check là pastel SÁNG cố định → chữ trong ô check phải ép ĐEN
# (nếu để chữ theo theme, dark mode sẽ ra chữ trắng trên nền sáng — tàng hình)
_COLOR_OK = QColor("#c6efce")
_COLOR_FAIL = QColor("#ffc7ce")
_COLOR_WARN = QColor("#ffeb9c")
_COLOR_CHECK_TEXT = QColor("#1a1a1a")


def _readonly_color() -> QColor:
    """Nền cột kết quả (readonly): lệch nhẹ so với nền theme hiện tại —
    sáng hơn trong dark mode, tối hơn trong light mode."""
    base = QApplication.palette().color(QPalette.Base)
    return base.lighter(130) if base.value() < 128 else base.darker(104)

_HEADERS = [
    "STT", "Tên Đài", "h đài\n(m)", "Strip", "Rộng\n(m)",
    "Tổ hợp", "Vị trí\n(m)", "M+\n(KNm)", "Tổ hợp", "Vị trí\n(m)",
    "M-\n(KNm)", "Shear\n(KN)", "Astop\n(cm2)", "Asbot\n(cm2)",
    "Ø trên", "a trên", "Ø dưới", "a dưới", "Check\ntrên", "Check\ndưới",
]
COL_NAME, COL_H = 1, 2
COL_DIA_TOP, COL_SPA_TOP, COL_DIA_BOT, COL_SPA_BOT = 14, 15, 16, 17
COL_CHECK_TOP, COL_CHECK_BOT = 18, 19
_EDITABLE = {COL_NAME, COL_H, COL_DIA_TOP, COL_SPA_TOP, COL_DIA_BOT, COL_SPA_BOT}

DIA_RANGE = (10, 40)
SPACING_RANGE = (50, 400)


class StripResultsModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._designs: list[StripDesign] = []
        self._mat = MaterialParams()

    # ---- API cho tab ----
    def set_designs(self, designs: list[StripDesign], mat: MaterialParams) -> None:
        self.beginResetModel()
        self._designs = designs
        self._mat = mat
        for d in self._designs:
            calc_strip(d, self._mat)
        self.endResetModel()

    def apply_material(self, mat: MaterialParams) -> None:
        self._mat = mat
        for d in self._designs:
            calc_strip(d, self._mat)
        if self._designs:
            self.dataChanged.emit(
                self.index(0, 0), self.index(len(self._designs) - 1, len(_HEADERS) - 1)
            )

    def apply_defaults_all(self, h: float, dia: int, spacing: int) -> None:
        for d in self._designs:
            d.h, d.dia_top, d.spacing_top = h, dia, spacing
            d.dia_bot, d.spacing_bot = dia, spacing
            calc_strip(d, self._mat)
        self.apply_material(self._mat)

    def apply_rebar_to_all(self, src_row: int) -> None:
        """Context menu: áp Ø/a của dòng src cho mọi strip."""
        if not (0 <= src_row < len(self._designs)):
            return
        s = self._designs[src_row]
        for d in self._designs:
            d.dia_top, d.spacing_top = s.dia_top, s.spacing_top
            d.dia_bot, d.spacing_bot = s.dia_bot, s.spacing_bot
            calc_strip(d, self._mat)
        self.apply_material(self._mat)

    def designs(self) -> list[StripDesign]:
        return self._designs

    def material(self) -> MaterialParams:
        return self._mat

    # ---- Qt model ----
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._designs)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return _HEADERS[section]
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in _EDITABLE:
            f |= Qt.ItemIsEditable
        return f

    def data(self, index, role=Qt.DisplayRole):
        d = self._designs[index.row()]
        col = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._value(d, index.row(), col, edit=(role == Qt.EditRole))
        if role == Qt.BackgroundRole:
            if col in (COL_CHECK_TOP, COL_CHECK_BOT):
                return _check_color(d.check_top if col == COL_CHECK_TOP else d.check_bot)
            if col not in _EDITABLE:
                return _readonly_color()
        if role == Qt.ForegroundRole and col in (COL_CHECK_TOP, COL_CHECK_BOT):
            v = d.check_top if col == COL_CHECK_TOP else d.check_bot
            if _check_color(v) is not None:   # có nền pastel sáng → chữ đen
                return _COLOR_CHECK_TEXT
        if role == Qt.TextAlignmentRole and col != COL_NAME:
            return int(Qt.AlignCenter)
        if role == Qt.ToolTipRole and col in (COL_CHECK_TOP, COL_CHECK_BOT):
            v = d.check_top if col == COL_CHECK_TOP else d.check_bot
            if v == "CT":
                req = d.as_top_req if col == COL_CHECK_TOP else d.as_bot_req
                if req is None:
                    return "αm quá lớn — tăng h đài hoặc mác bê tông"
                return "Cần xem lại: As=0 hoặc tỷ lệ bố trí/yêu cầu ≥ 5"
            if isinstance(v, float) and v < 1:
                return "Thiếu thép — tăng Ø hoặc giảm khoảng cách"
        return None

    def _value(self, d: StripDesign, row: int, col: int, edit: bool):
        e = d.env
        raw = [
            row + 1, d.pile_cap_name, d.h, e.strip, e.width,
            e.m_pos_combo, e.m_pos_station, e.m_pos, e.m_neg_combo, e.m_neg_station,
            e.m_neg, e.v_max, d.as_top_req, d.as_bot_req,
            d.dia_top, d.spacing_top, d.dia_bot, d.spacing_bot,
            d.check_top, d.check_bot,
        ][col]
        if edit:
            return raw
        if raw is None:
            return "-"
        if isinstance(raw, float):
            return f"{raw:.2f}"
        return raw

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        if role != Qt.EditRole or index.column() not in _EDITABLE:
            return False
        d = self._designs[index.row()]
        col = index.column()
        try:
            if col == COL_NAME:
                d.pile_cap_name = str(value).strip()
            elif col == COL_H:
                h = float(str(value).replace(",", "."))
                if h <= 0:
                    return False
                d.h = h
            else:
                v = int(float(str(value)))
                lo, hi = DIA_RANGE if col in (COL_DIA_TOP, COL_DIA_BOT) else SPACING_RANGE
                if not (lo <= v <= hi):
                    return False
                if col == COL_DIA_TOP:
                    d.dia_top = v
                elif col == COL_SPA_TOP:
                    d.spacing_top = v
                elif col == COL_DIA_BOT:
                    d.dia_bot = v
                else:
                    d.spacing_bot = v
        except (TypeError, ValueError):
            return False

        calc_strip(d, self._mat)
        row = index.row()
        self.dataChanged.emit(self.index(row, 0), self.index(row, len(_HEADERS) - 1))
        return True


def _check_color(v):
    if v == "CT":
        return _COLOR_WARN
    if isinstance(v, float):
        return _COLOR_OK if v >= 1 else _COLOR_FAIL
    return None


class ResultsTableView(QTableView):
    """View + context menu (áp Ø/a cho mọi strip, copy bảng)."""

    def __init__(self, model: StripResultsModel, parent=None):
        super().__init__(parent)
        self.setModel(model)
        self._model = model
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectItems)
        self.horizontalHeader().setDefaultSectionSize(70)
        self.setColumnWidth(0, 40)
        self.setColumnWidth(COL_NAME, 90)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

        copy = QAction("Copy", self)
        copy.setShortcut(QKeySequence.Copy)
        copy.triggered.connect(self.copy_table)
        self.addAction(copy)

    def _menu(self, pos):
        row = self.rowAt(pos.y())
        menu = QMenu(self)
        if row >= 0:
            act = menu.addAction("Áp Ø/a dòng này cho MỌI strip")
            act.triggered.connect(lambda: self._model.apply_rebar_to_all(row))
        menu.addAction("Copy cả bảng (dán được vào Excel/Calc)").triggered.connect(
            self.copy_table
        )
        menu.exec(self.viewport().mapToGlobal(pos))

    def copy_table(self):
        m = self._model
        lines = ["\t".join(h.replace("\n", " ") for h in _HEADERS)]
        for r in range(m.rowCount()):
            lines.append(
                "\t".join(str(m.index(r, c).data(Qt.DisplayRole)) for c in range(m.columnCount()))
            )
        QApplication.clipboard().setText("\n".join(lines))
