"""Entry point: chỉ compose QApplication + MainWindow. KHÔNG chứa logic."""

import sys

from PySide6.QtWidgets import QApplication

from rebarflow.__version__ import __version__
from rebarflow.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("rebarFlow")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("rebarFlow")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
