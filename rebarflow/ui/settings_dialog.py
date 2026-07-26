"""Dialog cài đặt: thông số vẽ DXF (lưu vào config.json)."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self._cfg = cfg

        root = QVBoxLayout(self)
        root.addWidget(QLabel("Thông số bản vẽ DXF (đơn vị bản vẽ: mm)"))
        form = QFormLayout()
        self.text_height = _spin(cfg["dxf_text_height"], 10, 5000)
        self.text_offset = _spin(cfg["dxf_text_offset"], 0, 5000)
        self.line_spacing = _spin(cfg["dxf_line_spacing"], 10, 5000)
        form.addRow("Chiều cao chữ", self.text_height)
        form.addRow("Đẩy chữ khỏi strip/điểm", self.text_offset)
        form.addRow("Khoảng cách dòng chữ", self.line_spacing)
        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def accept(self):
        self._cfg["dxf_text_height"] = self.text_height.value()
        self._cfg["dxf_text_offset"] = self.text_offset.value()
        self._cfg["dxf_line_spacing"] = self.line_spacing.value()
        super().accept()


def _spin(val, lo, hi) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(0)
    s.setValue(float(val))
    return s
