"""Panel thông số bên trái tab strips: vật liệu, cover, chế độ tính, defaults.

Đổi bất kỳ giá trị nào → emit `params_changed` (tab tự recalc toàn bảng).
Nút "Áp mặc định cho tất cả dòng" → emit `apply_defaults`.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from rebarflow.constants import CONCRETE, STEEL
from rebarflow.core.models import CalcMode, MaterialParams
from rebarflow.ui.results_table import DIA_RANGE, SPACING_RANGE

_MODE_HELP = (
    "«Giống Excel gốc» (mặc định): tái hiện 100% công thức file Excel cũ,\n"
    "kể cả 2 điểm đặc thù đã được tác giả file xác nhận là chủ ý:\n"
    "  1) Rb tra bảng (kG/cm²) dùng trực tiếp ×1000 trong công thức αm;\n"
    "  2) ζ thép dưới tính với h₀ theo lớp bảo vệ TRÊN.\n\n"
    "«TCVN chuẩn sách»: sửa 2 điểm trên theo đúng đơn vị/h₀ —\n"
    "lượng thép ra NHIỀU HƠN một chút (thiên về an toàn).\n\n"
    "Chi tiết: docs/GHI-CHU-CONG-THUC-GOC.md trong repo."
)


class ParamsPanel(QWidget):
    params_changed = Signal()
    apply_defaults = Signal(float, int, int)   # h, dia, spacing

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        root = QVBoxLayout(self)

        # ---- vật liệu ----
        mat_box = QGroupBox("Vật liệu")
        form = QFormLayout(mat_box)
        self.concrete = QComboBox()
        self.concrete.addItems(CONCRETE.keys())
        self.concrete.setCurrentText(cfg["concrete"])
        self.lbl_rb = QLabel()
        form.addRow("Mác bê tông", self.concrete)
        form.addRow("", self.lbl_rb)
        self.steel = QComboBox()
        self.steel.addItems(STEEL.keys())
        self.steel.setCurrentText(cfg["steel"])
        self.lbl_rs = QLabel()
        form.addRow("Mác thép", self.steel)
        form.addRow("", self.lbl_rs)
        root.addWidget(mat_box)

        # ---- thông số đài ----
        cap_box = QGroupBox("Thông số")
        form2 = QFormLayout(cap_box)
        self.cover_top = _dspin(0, 200, cfg["cover_top_mm"], " mm")
        self.cover_bot = _dspin(0, 300, cfg["cover_bot_mm"], " mm")
        self.as_ham = _dspin(0, 100, cfg["as_ham_cm2"], " cm²", decimals=2)
        form2.addRow("Lớp bảo vệ trên", self.cover_top)
        form2.addRow("Lớp bảo vệ dưới", self.cover_bot)
        form2.addRow("Thép sàn hầm", self.as_ham)
        root.addWidget(cap_box)

        # ---- chế độ tính ----
        mode_box = QGroupBox("Chế độ tính")
        mv = QVBoxLayout(mode_box)
        self.mode_excel = QRadioButton("Giống Excel gốc (mặc định)")
        self.mode_tcvn = QRadioButton("TCVN chuẩn sách")
        (self.mode_excel if cfg["mode"] == "excel_compat" else self.mode_tcvn).setChecked(True)
        help_btn = QPushButton("?")
        help_btn.setFixedWidth(24)
        help_btn.clicked.connect(
            lambda: QMessageBox.information(self, "Chế độ tính", _MODE_HELP)
        )
        row = QHBoxLayout()
        row.addWidget(self.mode_excel)
        row.addWidget(help_btn, alignment=Qt.AlignRight)
        mv.addLayout(row)
        mv.addWidget(self.mode_tcvn)
        root.addWidget(mode_box)

        # ---- defaults cho dòng mới ----
        def_box = QGroupBox("Mặc định (áp khi mở file)")
        form3 = QFormLayout(def_box)
        self.h_dai = _dspin(0.1, 10, cfg["h_dai_m"], " m", decimals=2, step=0.05)
        self.dia = _spin(*DIA_RANGE, int(cfg["dia_mm"]), " mm", step=2)
        self.spacing = _spin(*SPACING_RANGE, int(cfg["spacing_mm"]), " mm", step=25)
        form3.addRow("h đài", self.h_dai)
        form3.addRow("Ø thép", self.dia)
        form3.addRow("Khoảng cách a", self.spacing)
        btn = QPushButton("Áp mặc định cho tất cả dòng")
        btn.clicked.connect(
            lambda: self.apply_defaults.emit(
                self.h_dai.value(), self.dia.value(), self.spacing.value()
            )
        )
        form3.addRow(btn)
        root.addWidget(def_box)
        root.addStretch()

        for w in (self.concrete, self.steel):
            w.currentTextChanged.connect(self._on_change)
        for w in (self.cover_top, self.cover_bot, self.as_ham):
            w.valueChanged.connect(self._on_change)
        self.mode_excel.toggled.connect(self._on_change)
        self._update_labels()

    def _on_change(self, *_):
        self._update_labels()
        self.params_changed.emit()

    def _update_labels(self):
        self.lbl_rb.setText(f"Rb tra bảng = {CONCRETE[self.concrete.currentText()][0]:g} kG/cm²")
        self.lbl_rs.setText(f"Rs = {STEEL[self.steel.currentText()][0] / 10:g} MPa")

    def material(self) -> MaterialParams:
        return MaterialParams(
            concrete=self.concrete.currentText(),
            steel=self.steel.currentText(),
            cover_top_mm=self.cover_top.value(),
            cover_bot_mm=self.cover_bot.value(),
            as_ham_cm2=self.as_ham.value(),
            mode=CalcMode.EXCEL_COMPAT if self.mode_excel.isChecked() else CalcMode.TCVN_STRICT,
        )

    def defaults(self) -> tuple[float, int, int]:
        return self.h_dai.value(), self.dia.value(), self.spacing.value()

    def save_to_config(self, cfg: dict) -> None:
        m = self.material()
        cfg.update(
            concrete=m.concrete, steel=m.steel,
            cover_top_mm=m.cover_top_mm, cover_bot_mm=m.cover_bot_mm,
            as_ham_cm2=m.as_ham_cm2, mode=m.mode.value,
            h_dai_m=self.h_dai.value(), dia_mm=self.dia.value(),
            spacing_mm=self.spacing.value(),
        )


def _dspin(lo, hi, val, suffix, decimals=1, step=1.0) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(decimals)
    s.setSingleStep(step)
    s.setValue(float(val))
    s.setSuffix(suffix)
    return s


def _spin(lo, hi, val, suffix, step=1) -> QSpinBox:
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setSingleStep(step)
    s.setValue(val)
    s.setSuffix(suffix)
    return s
