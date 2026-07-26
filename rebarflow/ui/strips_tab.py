"""Tab chính «Thép đài»: params panel (trái) + bảng kết quả (phải).

Giữ state: SafeModel đã load + list[StripDesign]. MainWindow gọi
`load_safe_model` / `export_dxf` / `export_report`.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from rebarflow.core.models import SafeModel, StripDesign
from rebarflow.core.strip_aggregate import aggregate
from rebarflow.export.dxf_strips import export_strips_dxf
from rebarflow.export.dxf_style import DxfStyle
from rebarflow.export.report_xlsx import export_report
from rebarflow.ui.params_panel import ParamsPanel
from rebarflow.ui.results_table import ResultsTableView, StripResultsModel


class StripsTab(QWidget):
    status_message = Signal(str)

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._safe: SafeModel | None = None

        self.panel = ParamsPanel(cfg)
        self.model = StripResultsModel(self)
        self.view = ResultsTableView(self.model)
        self._empty = QLabel(
            "Chưa có dữ liệu — bấm «Mở SAFE .mdb» trên thanh công cụ để bắt đầu."
        )

        right = QVBoxLayout()
        right.addWidget(self._empty)
        right.addWidget(self.view)
        self.view.hide()

        root = QHBoxLayout(self)
        root.addWidget(self.panel)
        root.addLayout(right, stretch=1)

        self.panel.params_changed.connect(self._on_params_changed)
        self.panel.apply_defaults.connect(self.model.apply_defaults_all)

    # ---- load ----
    def load_safe_model(self, safe: SafeModel) -> None:
        self._safe = safe
        h, dia, spacing = self.panel.defaults()
        designs = [
            StripDesign(env=e, h=h, dia_top=dia, spacing_top=spacing,
                        dia_bot=dia, spacing_bot=spacing)
            for e in aggregate(safe.forces)
        ]
        self.model.set_designs(designs, self.panel.material())
        self._empty.hide()
        self.view.show()

        msg = f"{safe.program} — {len(safe.forces)} dòng nội lực → {len(designs)} strips"
        for t in safe.missing_tables:
            msg += f"  |  ⚠ thiếu bảng «{t}»"
        self.status_message.emit(msg)
        if safe.missing_tables:
            QMessageBox.warning(
                self, "Thiếu bảng",
                "File thiếu các bảng sau (vẫn tính được thép):\n- "
                + "\n- ".join(safe.missing_tables)
                + "\n\nThiếu «Object Geometry - Design Strips» thì KHÔNG xuất được "
                "DXF strips — export lại từ SAFE và tick bảng này nếu cần bản vẽ.",
            )

    def has_data(self) -> bool:
        return bool(self.model.designs())

    def can_export_dxf(self) -> tuple[bool, str]:
        if not self.has_data():
            return False, "Chưa mở file SAFE nào."
        if not self._safe or not self._safe.geometry:
            return False, (
                "File không có bảng «Object Geometry - Design Strips» — "
                "export lại từ SAFE và tick bảng này."
            )
        return True, ""

    # ---- export ----
    def export_dxf(self, path: str) -> None:
        style = DxfStyle.from_config(self._cfg)
        skipped = export_strips_dxf(self.model.designs(), self._safe.geometry, path, style)
        msg = f"Đã xuất DXF: {path}"
        if skipped:
            msg += f"  (bỏ qua {len(skipped)} strip thiếu geometry)"
        self.status_message.emit(msg)

    def export_report(self, path: str) -> None:
        export_report(
            self.model.designs(), self.model.material(), path,
            source=self._safe.source_path if self._safe else "",
        )
        self.status_message.emit(f"Đã xuất báo cáo: {path}")

    # ---- params ----
    def _on_params_changed(self) -> None:
        self.model.apply_material(self.panel.material())
