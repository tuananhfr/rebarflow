"""QThread worker chung: chạy 1 hàm blocking (đọc mdb...) ở thread nền.

UI không bao giờ block; lỗi trả về dạng message tiếng Việt qua signal `failed`.
"""

from PySide6.QtCore import QThread, Signal


class FuncWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args

    def run(self):
        try:
            self.finished_ok.emit(self._fn(*self._args))
        except Exception as e:  # noqa: BLE001 — mọi lỗi đều phải ra UI, không crash
            self.failed.emit(str(e))
