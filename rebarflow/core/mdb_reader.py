"""Wrapper quanh access-parser: đọc file .mdb thuần Python, không cần Access/driver.

Mọi module import chỗ này thay vì đụng trực tiếp access_parser — để sau này
đổi thư viện đọc mdb (nếu gặp file không parse được) chỉ sửa 1 file.
"""

import logging

from access_parser import AccessParser

log = logging.getLogger(__name__)


class MdbError(Exception):
    """Lỗi mở/đọc file mdb — message hướng người dùng, tiếng Việt."""


class TableNotFoundError(MdbError):
    def __init__(self, table: str):
        super().__init__(
            f"File thiếu bảng «{table}». Export lại từ SAFE/ETABS và tick bảng này."
        )
        self.table = table


class MdbFile:
    def __init__(self, path: str):
        try:
            self._db = AccessParser(str(path))
        except PermissionError as e:
            raise MdbError(
                "Không mở được file (đang bị chương trình khác khóa?). "
                "Đóng SAFE/Access rồi thử lại."
            ) from e
        except Exception as e:
            raise MdbError(f"File không đọc được như một database Access hợp lệ: {e}") from e
        self.path = str(path)

    def table_names(self) -> list[str]:
        return [t for t in self._db.catalog if not t.startswith("MSys")]

    def has_table(self, name: str) -> bool:
        return name in self._db.catalog

    def read_table(self, name: str) -> list[dict]:
        """Trả list[dict], mỗi dict một dòng (key = tên cột).

        Raise TableNotFoundError nếu bảng không tồn tại HOẶC access-parser
        fail parse bảng đó (đã gặp thực tế) — caller quyết định chặn hay bỏ qua.
        """
        if not self.has_table(name):
            raise TableNotFoundError(name)
        try:
            cols = self._db.parse_table(name)
        except Exception as e:
            log.warning("access-parser fail parse bảng %r: %s", name, e)
            raise TableNotFoundError(name) from e
        if not cols:
            return []
        keys = list(cols.keys())
        n = len(cols[keys[0]])
        return [{k: cols[k][i] for k in keys} for i in range(n)]
