"""Dialog "Có bản cập nhật": version + changelog + [Tải & cài] [Để sau] [Bỏ qua]."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from rebarflow.__version__ import __version__
from rebarflow.ui.workers import FuncWorker
from rebarflow.updater.downloader import download_installer, run_installer
from rebarflow.updater.version_check import UpdateInfo


class UpdateDialog(QDialog):
    """result codes: Accepted = đã chạy installer (app phải quit);
    dùng thuộc tính `skipped` để biết user chọn 'Bỏ qua bản này'."""

    def __init__(self, info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Có bản cập nhật")
        self.resize(480, 360)
        self._info = info
        self._worker: FuncWorker | None = None
        self.skipped = False

        root = QVBoxLayout(self)
        head = QLabel(
            f"<b>rebarFlow {info.version}</b> đã có (bản đang dùng: {__version__})"
        )
        head.setTextFormat(Qt.RichText)
        root.addWidget(head)

        notes = QTextBrowser()
        notes.setMarkdown(info.notes or "_(không có ghi chú phát hành)_")
        notes.setOpenExternalLinks(True)
        root.addWidget(notes, stretch=1)

        row = QHBoxLayout()
        skip = QPushButton("Bỏ qua bản này")
        later = QPushButton("Để sau")
        install = QPushButton("Tải && cài đặt")
        install.setDefault(True)
        row.addWidget(skip)
        row.addStretch()
        row.addWidget(later)
        row.addWidget(install)
        root.addLayout(row)

        later.clicked.connect(self.reject)
        skip.clicked.connect(self._skip)
        install.clicked.connect(self._install)

    def _skip(self):
        self.skipped = True
        self.reject()

    def _install(self):
        progress = QProgressDialog("Đang tải bản cập nhật…", "", 0, 100, self)
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        def do_download():
            def cb(done, total):
                if total:
                    progress.setValue(int(done * 100 / total))
            return download_installer(self._info, progress_cb=cb)

        self._worker = FuncWorker(do_download)
        self._worker.finished_ok.connect(
            lambda path: (progress.close(), run_installer(path), self.accept())
        )
        self._worker.failed.connect(
            lambda msg: (progress.close(), QMessageBox.critical(self, "Lỗi", msg))
        )
        self._worker.start()
