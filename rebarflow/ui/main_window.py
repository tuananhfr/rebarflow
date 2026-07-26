"""Cửa sổ chính: toolbar + 2 tab + status bar. Chỉ wiring — logic nằm ở tab/core."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QTabWidget,
    QToolBar,
)

from rebarflow import config
from rebarflow.__version__ import __version__
from rebarflow.core.etabs_import import load_etabs
from rebarflow.core.safe_import import load_safe
from rebarflow.ui.reactions_tab import ReactionsTab
from rebarflow.ui.settings_dialog import SettingsDialog
from rebarflow.ui.strips_tab import StripsTab
from rebarflow.ui.workers import FuncWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"rebarFlow v{__version__} — Tính thép đài cọc")
        self.resize(1280, 720)
        self._cfg = config.load()
        self._worker: FuncWorker | None = None
        self._progress: QProgressDialog | None = None

        self.strips_tab = StripsTab(self._cfg)
        self.reactions_tab = ReactionsTab(self._cfg)
        tabs = QTabWidget()
        tabs.addTab(self.strips_tab, "Thép đài (strips)")
        tabs.addTab(self.reactions_tab, "Phản lực chân cột")
        self._tabs = tabs
        self.setCentralWidget(tabs)

        tb = QToolBar("Chính")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(tb)
        tb.addAction("📂 Mở SAFE .mdb", self._open_safe)
        tb.addAction("📂 Mở ETABS .mdb", self._open_etabs)
        tb.addSeparator()
        tb.addAction("📐 Xuất DXF", self._export_dxf)
        tb.addAction("📊 Xuất báo cáo", self._export_report)
        tb.addSeparator()
        tb.addAction("⚙ Cài đặt", self._settings)

        self.statusBar().showMessage("Sẵn sàng — mở file SAFE .mdb để bắt đầu.")
        self.strips_tab.status_message.connect(self.statusBar().showMessage)
        self.reactions_tab.status_message.connect(self.statusBar().showMessage)

    # ---- mở file (worker nền + progress) ----
    def _open_safe(self):
        path = self._pick_mdb("Mở file SAFE .mdb")
        if path:
            self._run_import(load_safe, path, self._on_safe_loaded)

    def _open_etabs(self):
        path = self._pick_mdb("Mở file ETABS .mdb")
        if path:
            self._run_import(load_etabs, path, self._on_etabs_loaded)

    def _pick_mdb(self, title: str) -> str:
        path, _ = QFileDialog.getOpenFileName(
            self, title, self._cfg.get("last_dir", ""), "File Access (*.mdb)"
        )
        if path:
            self._cfg["last_dir"] = str(Path(path).parent)
        return path

    def _run_import(self, fn, path: str, on_ok):
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "Đang bận", "Đang đọc file khác, chờ xong đã.")
            return
        self._progress = QProgressDialog(f"Đang đọc {Path(path).name}…", "", 0, 0, self)
        self._progress.setCancelButton(None)
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setMinimumDuration(300)
        self._worker = FuncWorker(fn, path)
        self._worker.finished_ok.connect(lambda m: (self._close_progress(), on_ok(m)))
        self._worker.failed.connect(lambda e: (self._close_progress(), self._show_error(e)))
        self._worker.start()

    def _close_progress(self):
        if self._progress:
            self._progress.close()
            self._progress = None

    def _show_error(self, msg: str):
        QMessageBox.critical(self, "Lỗi đọc file", msg)

    def _on_safe_loaded(self, model):
        self.strips_tab.load_safe_model(model)
        self._tabs.setCurrentWidget(self.strips_tab)

    def _on_etabs_loaded(self, model):
        self.reactions_tab.load_etabs_model(model)
        self._tabs.setCurrentWidget(self.reactions_tab)

    # ---- xuất — theo tab đang mở ----
    def _export_dxf(self):
        if self._tabs.currentWidget() is self.reactions_tab:
            if not self.reactions_tab.has_data():
                QMessageBox.information(self, "Chưa có dữ liệu", "Mở file ETABS .mdb trước.")
                return
            path = self._pick_save("Xuất DXF phản lực", "phanluc.dxf", "DXF (*.dxf)")
            if path:
                self.reactions_tab.export_dxf(path)
            return
        ok, why = self.strips_tab.can_export_dxf()
        if not ok:
            QMessageBox.warning(self, "Không xuất được DXF", why)
            return
        path = self._pick_save("Xuất DXF strips", "thep_dai.dxf", "DXF (*.dxf)")
        if path:
            self.strips_tab.export_dxf(path)

    def _export_report(self):
        if not self.strips_tab.has_data():
            QMessageBox.information(self, "Chưa có dữ liệu", "Mở file SAFE .mdb trước.")
            return
        path = self._pick_save("Xuất báo cáo", "bao_cao_thep_dai.xlsx", "Excel (*.xlsx)")
        if path:
            self.strips_tab.export_report(path)

    def _pick_save(self, title: str, default_name: str, flt: str) -> str:
        start = str(Path(self._cfg.get("last_dir", "")) / default_name)
        path, _ = QFileDialog.getSaveFileName(self, title, start, flt)
        if path:
            self._cfg["last_dir"] = str(Path(path).parent)
        return path

    def _settings(self):
        if SettingsDialog(self._cfg, self).exec():
            config.save(self._cfg)

    # ---- đóng app: lưu config ----
    def closeEvent(self, event):
        self.strips_tab.panel.save_to_config(self._cfg)
        config.save(self._cfg)
        super().closeEvent(event)
