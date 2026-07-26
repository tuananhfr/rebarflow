"""Tab «Phản lực chân cột»: bảng joint + filter combo + xuất DXF map phản lực."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from rebarflow.core.models import EtabsModel, JointReaction
from rebarflow.export.dxf_reactions import export_reactions_dxf, filter_reactions
from rebarflow.export.dxf_style import DxfStyle

_HEADERS = ["Story", "Point", "Tổ hợp", "Fz (T)", "X (m)", "Y (m)"]


class ReactionsModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[JointReaction] = []

    def set_rows(self, rows: list[JointReaction]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(_HEADERS)

    def headerData(self, s, o, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and o == Qt.Horizontal:
            return _HEADERS[s]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role != Qt.DisplayRole:
            return None
        r = self._rows[index.row()]
        vals = [r.story, r.point, r.output_case, f"{r.fz:.2f}",
                "-" if r.x is None else f"{r.x:.3f}",
                "-" if r.y is None else f"{r.y:.3f}"]
        return vals[index.column()]


class ReactionsTab(QWidget):
    status_message = Signal(str)

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._etabs: EtabsModel | None = None

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Tổ hợp:"))
        self.combo = QComboBox()
        self.combo.addItem("(tất cả)")
        bar.addWidget(self.combo)
        self.max_per_point = QCheckBox("Chỉ |Fz| max mỗi điểm")
        bar.addWidget(self.max_per_point)
        bar.addStretch()
        self.info = QLabel("Chưa có dữ liệu — bấm «Mở ETABS .mdb» trên thanh công cụ.")
        bar.addWidget(self.info)

        self.model = ReactionsModel(self)
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)

        root = QVBoxLayout(self)
        root.addLayout(bar)
        root.addWidget(self.view)

        self.combo.currentTextChanged.connect(self._refresh)
        self.max_per_point.toggled.connect(self._refresh)

    def load_etabs_model(self, m: EtabsModel) -> None:
        self._etabs = m
        cases = sorted({r.output_case for r in m.reactions})
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("(tất cả)")
        self.combo.addItems(cases)
        self.combo.blockSignals(False)
        self._refresh()
        n_xy = sum(1 for r in m.reactions if r.x is not None)
        self.info.setText(f"ETABS {m.version} — {len(m.reactions)} phản lực, {n_xy} có tọa độ")
        self.status_message.emit(
            f"ETABS {m.version}: {len(m.reactions)} dòng phản lực"
            + (f"  |  ⚠ thiếu bảng «{'», «'.join(m.missing_tables)}»" if m.missing_tables else "")
        )

    def has_data(self) -> bool:
        return self._etabs is not None

    def _filtered(self) -> list[JointReaction]:
        if not self._etabs:
            return []
        case = self.combo.currentText()
        return filter_reactions(
            self._etabs.reactions,
            case=None if case == "(tất cả)" else case,
            max_per_point=self.max_per_point.isChecked(),
        )

    def _refresh(self, *_) -> None:
        self.model.set_rows(self._filtered())

    def export_dxf(self, path: str) -> None:
        n = export_reactions_dxf(self._filtered(), path, DxfStyle.from_config(self._cfg))
        self.status_message.emit(f"Đã xuất DXF phản lực ({n} điểm): {path}")
