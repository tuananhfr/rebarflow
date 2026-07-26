# PLAN — rebarFlow v1.0

> App desktop Windows thay thế file `tinh Dai coc - GOC.xls` (Excel VBA): import file `.mdb` xuất từ SAFE/ETABS → tính thép đài cọc theo TCVN 5574 → xuất bản vẽ DXF (mở bằng AutoCAD) + báo cáo xlsx.
>
> Tài liệu này đủ chi tiết để dev đọc và code được mà không cần mở file Excel gốc. Đọc kèm: `GHI-CHU-CONG-THUC-GOC.md` (quyết định về công thức).

---

## 0. Tóm tắt quyết định đã chốt

| Hạng mục | Quyết định |
|---|---|
| Nền tảng | Windows desktop, Python 3.11+, PySide6 |
| Đọc .mdb | `access-parser` (pure Python, KHÔNG cần cài Access/driver) |
| Xuất CAD | Sinh file **DXF** bằng `ezdxf` (không COM automation, không cần AutoCAD cài trên máy) |
| Chế độ tính **mặc định** | `EXCEL_COMPAT` — tái hiện file Excel gốc 100% (tác giả file đã xác nhận công thức là chủ ý) |
| Chế độ phụ | `TCVN_STRICT` — sửa 2 điểm lệch đơn vị/h₀, user bật tay nếu muốn |
| Update | Check GitHub Releases khi khởi động → thông báo → tải installer |
| Đóng gói | PyInstaller (onedir) + Inno Setup → `rebarflow-setup-x.y.z.exe` |
| Kiểm chứng | Golden test: output chế độ `EXCEL_COMPAT` phải khớp số liệu sheet `D1` file gốc |

---

## 1. Luồng sử dụng (user flow)

```
┌────────────────────────────────────────────────────────────────────┐
│ 1. Kỹ sư chạy SAFE → File > Export > .mdb                          │
│    (bắt buộc tick các bảng: Program Control, Strip Forces,         │
│     Slab Properties 02, Object Geometry - Design Strips)           │
│ 2. Mở rebarFlow → [Mở file SAFE .mdb]                              │
│    → app validate đơn vị "KN, m, C" + đủ bảng, báo lỗi rõ nếu thiếu│
│ 3. App gom nội lực per strip → bảng kết quả                        │
│ 4. Kỹ sư chỉnh: mác BT/thép, h đài, lớp bảo vệ, Ø + khoảng cách    │
│    từng strip → cột Check tự tính lại ngay                          │
│ 5. [Xuất DXF] → mở bằng AutoCAD, thấy strip + text thép y như      │
│    macro cũ vẽ │ [Xuất báo cáo] → xlsx giống trang in sheet D1     │
│                                                                    │
│ Luồng phụ: [Mở file ETABS .mdb] (9.7.4 hoặc 2017) → map phản lực   │
│ chân cột → [Xuất DXF phản lực]: điểm + text "Fz = xxT"             │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tech stack & dependencies

```toml
# pyproject.toml (đoạn chính)
[project]
name = "rebarflow"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.7",
    "ezdxf>=1.3",
    "openpyxl>=3.1",       # xuất báo cáo xlsx
    "access-parser>=0.0.6", # đọc .mdb
    "requests>=2.31",       # check update
    "packaging>=24.0",      # so sánh semver
]
[project.optional-dependencies]
dev = ["pytest>=8", "pandas", "xlrd", "pyinstaller>=6"]
```

Lý do chọn:
- `access-parser`: đã test đọc thành công `MONG.mdb` mẫu, thuần Python. **Lưu ý:** bảng không tồn tại trong file sẽ raise/log — phải catch (xem §5.4).
- `ezdxf`: chuẩn de-facto sinh DXF từ Python, AutoCAD mở trực tiếp.
- PyInstaller **onedir** (không onefile): khởi động nhanh, thư mục cài đặt rõ ràng cho updater.

---

## 3. Cấu trúc thư mục project

Nguyên tắc: mỗi file một trách nhiệm, entry chỉ compose. KHÔNG dồn logic vào main hay UI.

```
rebarflow/
├─ pyproject.toml
├─ README.md
├─ rebarflow/
│  ├─ __init__.py
│  ├─ __version__.py          # __version__ = "1.0.0"  ← single source, mọi nơi import từ đây
│  ├─ main.py                 # entry: QApplication + MainWindow + updater.check_async(). KHÔNG logic
│  ├─ config.py               # đọc/ghi config user: %APPDATA%/rebarFlow/config.json
│  ├─ constants.py            # bảng vật liệu, defaults (Ø20a200, cover 35/100...), enum CalcMode
│  ├─ core/                   # ❗ KHÔNG import gì từ ui/ hay PySide6 — pure logic, test được
│  │  ├─ models.py            # dataclasses: StripForceRow, StripGeometry, StripDesign, JointReaction...
│  │  ├─ mdb_reader.py        # wrapper access-parser: open, list_tables, read_table→list[dict]
│  │  ├─ safe_import.py       # đọc file SAFE: validate units + bảng, trả SafeModel
│  │  ├─ etabs_import.py      # đọc file ETABS 9.7.4/2017: tự nhận diện phiên bản, trả EtabsModel
│  │  ├─ strip_aggregate.py   # gom per strip: M+ max, M− min, |V| max (thuật toán §6.2)
│  │  └─ rebar_calc.py        # công thức As + check tỷ lệ (công thức §6.3–6.5) — 2 mode
│  ├─ export/
│  │  ├─ dxf_style.py         # hằng số vẽ: layer, màu, text height, offset (spec §7.3)
│  │  ├─ dxf_strips.py        # DXF mặt bằng strips + text thép (spec §7.1)
│  │  ├─ dxf_reactions.py     # DXF map phản lực (spec §7.2)
│  │  └─ report_xlsx.py       # báo cáo xlsx giống trang in D1 (spec §8)
│  ├─ ui/
│  │  ├─ main_window.py       # QMainWindow: toolbar + 2 tab + statusbar. Chỉ wiring
│  │  ├─ strips_tab.py        # tab chính: params_panel + results_table + nút xuất
│  │  ├─ reactions_tab.py     # tab phản lực: bảng joint + filter combo + nút xuất
│  │  ├─ params_panel.py      # form thông số vật liệu/cover/mode (spec §9.2)
│  │  ├─ results_table.py     # QTableView + StripResultsModel (editable, spec §9.3)
│  │  ├─ settings_dialog.py   # cài đặt mặc định + tùy chọn DXF
│  │  ├─ update_dialog.py     # dialog "Có bản mới x.y.z" + changelog + nút tải
│  │  └─ workers.py           # QThread: ImportWorker, ExportWorker (UI không bao giờ block)
│  └─ updater/
│     ├─ version_check.py     # gọi GitHub API, so sánh semver (spec §10)
│     └─ downloader.py        # tải installer về %TEMP%, verify size, chạy
├─ tests/
│  ├─ golden/
│  │  ├─ golden_d1.json       # số liệu kỳ vọng trích từ file Excel gốc
│  │  └─ strip_forces_sample.json
│  ├─ tools/extract_golden.py # script trích golden từ file gốc (chạy 1 lần, §11.1)
│  ├─ test_rebar_calc.py
│  ├─ test_strip_aggregate.py
│  ├─ test_safe_import.py     # dùng MONG.mdb làm fixture
│  └─ test_version_check.py
├─ packaging/
│  ├─ rebarflow.spec          # PyInstaller
│  ├─ installer.iss           # Inno Setup
│  └─ build.ps1               # 1 lệnh: test → pyinstaller → inno → ra setup.exe
└─ docs/
   └─ GHI-CHU-CONG-THUC-GOC.md  # copy từ root repo hiện tại
```

---

## 4. Data models (`core/models.py`)

Viết đúng như sau (dataclass thuần, không phụ thuộc UI):

```python
from dataclasses import dataclass, field
from enum import Enum

class CalcMode(Enum):
    EXCEL_COMPAT = "excel_compat"   # mặc định — tái hiện file gốc 100%
    TCVN_STRICT  = "tcvn_strict"    # sửa 2 điểm lệch (xem GHI-CHU-CONG-THUC-GOC.md)

@dataclass
class StripForceRow:            # 1 dòng bảng "Strip Forces" trong mdb SAFE
    strip: str                  # "CSA1"
    station: float              # m
    location: str               # "Before"/"After"
    output_case: str            # tên tổ hợp, vd "BAO"
    case_type: str              # "Combination"
    p: float                    # kN
    v2: float                   # kN (lực cắt)
    t: float                    # kN·m
    m3: float                   # kN·m (moment dùng để tính thép)
    global_x: float
    global_y: float
    cut_width: float            # m (bề rộng strip tại vị trí cắt)

@dataclass
class StripGeometry:            # 1 strip = 2 điểm đầu-cuối, bảng "Object Geometry - Design Strips"
    strip: str
    x1: float; y1: float        # m
    x2: float; y2: float

@dataclass
class SafeModel:                # kết quả đọc file SAFE mdb
    source_path: str
    units_ok: bool
    program: str                # "SAFE 2016"...
    forces: list[StripForceRow]
    geometry: list[StripGeometry]        # RỖNG nếu file thiếu bảng geometry (vẫn hợp lệ!)
    slab_props: list[dict]               # bảng Slab Properties 02 (chỉ hiển thị tham khảo)
    missing_tables: list[str]            # tên các bảng thiếu → UI hiển thị cảnh báo

@dataclass
class StripEnvelope:            # kết quả gom per strip (output của strip_aggregate)
    strip: str
    width: float                # CutWidth tại dòng có M+ max
    m_pos: float | None         # M+ max (None nếu strip không có moment dương)
    m_pos_combo: str; m_pos_station: float
    m_neg: float | None         # M− min (None nếu không có moment âm)
    m_neg_combo: str; m_neg_station: float
    v_max: float                # lực cắt có trị tuyệt đối lớn nhất (giữ dấu)
    v_combo: str

@dataclass
class StripDesign:              # 1 dòng bảng kết quả — envelope + input user + kết quả tính
    env: StripEnvelope
    pile_cap_name: str = ""     # "Tên Đài" — user nhập tay trên bảng
    h: float = 1.1              # h đài (m) — user chỉnh được từng dòng
    dia_top: int = 20;  spacing_top: int = 200     # Ø(mm), a(mm) — user chỉnh
    dia_bot: int = 20;  spacing_bot: int = 200
    # các field dưới do rebar_calc điền:
    as_top_req: float | None = None   # cm² ("None" hiển thị "-")
    as_bot_req: float | None = None
    check_top: float | str = ""       # tỷ lệ, hoặc "CT" (không đạt), hoặc "-"
    check_bot: float | str = ""

@dataclass
class JointReaction:            # phản lực chân cột từ ETABS
    story: str
    point: str
    output_case: str
    fz: float                   # đơn vị Ton (9.7.4) / tonf (2017)
    x: float | None             # tọa độ sau khi join với bảng coordinates
    y: float | None

@dataclass
class EtabsModel:
    source_path: str
    version: str                # "9.7.4" | "2017"
    units_ok: bool
    reactions: list[JointReaction]
    missing_tables: list[str]
```

---

## 5. Đọc file .mdb (`core/mdb_reader.py`, `safe_import.py`, `etabs_import.py`)

### 5.1 Wrapper chung (`mdb_reader.py`)

```python
from access_parser import AccessParser

class MdbFile:
    def __init__(self, path: str):
        self._db = AccessParser(path)

    def table_names(self) -> list[str]:
        # bỏ bảng hệ thống
        return [t for t in self._db.catalog if not t.startswith("MSys")]

    def read_table(self, name: str) -> list[dict]:
        """Trả list[dict] (mỗi dict = 1 dòng). Raise TableNotFoundError nếu thiếu."""
        if name not in self._db.catalog:
            raise TableNotFoundError(name)
        cols = self._db.parse_table(name)      # dict: col -> list các giá trị
        keys = list(cols.keys())
        n = len(cols[keys[0]]) if keys else 0
        return [{k: cols[k][i] for k in keys} for i in range(n)]
```

**Quan trọng:** truy cột **theo TÊN**, không theo thứ tự (file Excel gốc dùng thứ tự cột vì CopyFromRecordset; mình có tên cột nên dùng tên — an toàn hơn, đã xác minh tên cột ở §5.2).

### 5.2 Import SAFE (`safe_import.py`)

Các bảng và cột (đã xác minh trên file `MONG.mdb` thật, SAFE 2016):

| Bảng | Bắt buộc? | Cột dùng |
|---|---|---|
| `Program Control` | ✅ | `CurrUnits` phải == `"KN, m, C"`, `ProgramName` (hiển thị) |
| `Strip Forces` | ✅ | `Strip, Station, Location, OutputCase, CaseType, P, V2, T, M3, GlobalX, GlobalY, CutWidth` |
| `Slab Properties 02 - Solid Slabs` | ⚠️ optional | `Slab, Type, MatProp, Thickness` |
| `Object Geometry - Design Strips` | ⚠️ optional | `Strip, Point, GlobalX, GlobalY` (mỗi strip 2 dòng = 2 điểm đầu-cuối) |

Thuật toán:
1. Mở file. Nếu thiếu `Program Control` hoặc `Strip Forces` → **lỗi chặn**, message: *"File thiếu bảng «X». Export lại từ SAFE và tick bảng này."*
2. Check `CurrUnits == "KN, m, C"` → sai thì **lỗi chặn**: *"Sai đơn vị: file đang là «...». Trong SAFE chuyển đơn vị KN-m-C rồi export lại."* (giống hệt hành vi `WRONG UNITS` của macro gốc).
3. Bảng geometry/slab thiếu → **không chặn**, thêm vào `missing_tables`; UI hiện cảnh báo vàng: *"Thiếu bảng Object Geometry - Design Strips — vẫn tính được thép, nhưng không xuất được DXF strips."* (File mẫu `MONG.mdb` thật sự thiếu bảng này — đây là case có thật, phải test.)
4. Geometry: gom 2 dòng liên tiếp cùng `Strip` thành 1 `StripGeometry` (điểm 1 = dòng có `Point` nhỏ hơn).

### 5.3 Import ETABS (`etabs_import.py`)

Tự nhận diện phiên bản bằng cách thử bảng:

| | ETABS 9.7.4 | ETABS 2017 |
|---|---|---|
| Bảng units | `Control Parameters`.`CurrUnits` == `"Ton-m"` | `Program Control`.`CurrUnits` == `"tonf, m, C"` |
| Bảng phản lực | `Support Reactions` → cột `Point, OutputCase?, FZ` (cột Fz tên `FZ`) | `Joint Reactions` → `Story, Label/UniqueName, OutputCase, FZ` |
| Bảng tọa độ | `Point Coordinates` → `Point, X, Y` | `Joint Coordinates Data`? → `Label/UniqueName, X, Y` |

**Đã chốt (user):** làm y theo mapping quan sát được từ file Excel gốc, không chờ file mdb ETABS mẫu. Thứ tự field theo sheet đã paste: 9.7.4 `Support Reactions` = (Story, Point, Load, FX, FY, FZ, MX, MY, MZ), `Point Coordinates` = (Point, X, Y, DZBelow); 2017 `Joint Reactions` = (Story, Label, UniqueName, OutputCase, FX, FY, FZ, MX, MY, MZ), coordinates = (Point/UniqueName, X, Y, DZBelow). Code đọc cột **theo tên với danh sách tên ứng viên** (vd Fz: `["FZ","Fz"]`, case: `["Load","OutputCase","Load Case/Combo"]`); nếu không khớp tên nào → lỗi rõ ràng in danh sách cột thực tế của file để bổ sung ứng viên (không đoán theo vị trí).

Join tọa độ: dict `point_name -> (x, y)` từ bảng coordinates, gán vào từng `JointReaction`. (Macro gốc join kiểu vòng lặp lỗi — mình join đúng bằng dict, kết quả tương đương trường hợp chạy được của macro.)

### 5.4 Xử lý lỗi đọc file

- `access-parser` có thể fail parse 1 bảng cụ thể (đã gặp: bảng có trong catalog nhưng `parse_table` trả None/raise). → catch mọi exception quanh `parse_table`, coi như bảng thiếu + log chi tiết vào file log (`%APPDATA%/rebarFlow/logs/`).
- File đang bị SAFE/Access mở khóa → catch `PermissionError`, message: *"File đang được mở bởi chương trình khác."*

---

## 6. Engine tính thép (`core/strip_aggregate.py` + `core/rebar_calc.py`)

### 6.1 Bảng vật liệu (`constants.py`) — số liệu trích NGUYÊN VĂN từ file gốc

```python
# Rb... đơn vị kG/cm² — GIỮ NGUYÊN đơn vị như bảng tra trong file gốc
CONCRETE = {  # grade: (Rb, Rk, Eb, Rb_ser, Rbt_ser)
    "B15":   (85,  7.5,  230_000, 110,   11.5),
    "B20":   (115, 9.0,  270_000, 150,   14),
    "B22.5": (130, 9.75, 285_000, 167.5, 15),
    "B25":   (145, 10.5, 300_000, 185,   16),
    "B30":   (170, 12.0, 325_000, 220,   18),
    "B35":   (195, 13.0, 345_000, 255,   19.5),
    "B40":   (220, 14.0, 360_000, 290,   21),
    "B45":   (250, 14.5, 370_000, 320,   22),
    "B50":   (275, 15.5, 390_000, 360,   23),
    "B60":   (330, 16.5, 400_000, 430,   25),
}
STEEL = {  # grade: (Rs, Rs_ser, Es) — kG/cm²
    "AI":     (2250, 2350, 2_100_000),
    "AII":    (2600, 2950, 2_100_000),
    "AIII":   (3500, 3500, 2_000_000),
    "CB300":  (2600, 2600, 2_100_000),
    "CB400":  (3500, 2800, 2_000_000),
    "CB500V": (4350, 3900, 2_000_000),
}
# Defaults (giống file gốc)
DEFAULT_CONCRETE = "B22.5"; DEFAULT_STEEL = "CB400"
DEFAULT_COVER_TOP_MM = 35.0; DEFAULT_COVER_BOT_MM = 100.0
DEFAULT_H_DAI_M = 1.1
DEFAULT_DIA_MM = 20; DEFAULT_SPACING_MM = 200
DEFAULT_AS_HAM_CM2 = 0.0     # ô F16 "Thep san ham" — thép sàn hầm cộng vào check thép TRÊN
CHECK_RATIO_MAX = 5.0        # tỷ lệ check >= 5 → hiển thị "CT"
```

Chọn mác trong UI = dropdown đúng key (KHÔNG dùng lookup gần đúng như VLOOKUP của Excel).

### 6.2 Gom nội lực per strip (`strip_aggregate.py`)

Tái hiện macro `tinhthepmax`, nhưng quét **toàn bộ** dòng dữ liệu:

```
def aggregate(forces: list[StripForceRow]) -> list[StripEnvelope]:
  1. unique strips THEO THỨ TỰ XUẤT HIỆN đầu tiên (giữ thứ tự để bảng kết quả
     giống trang in file gốc — CSA1, CSA2... rồi CSB1...)
  2. với mỗi strip s, xét mọi dòng r có r.strip == s:
     m_pos  = max(r.m3) nếu có dòng m3 > 0, ngược lại 0.0       # GIỮ semantics VBA (mo1=0):
     row+   = dòng đạt m_pos (nếu không có → dòng đầu tiên của strip; dùng cho width/combo/station)
     m_neg  = min(r.m3) nếu có dòng m3 < 0, ngược lại 0.0       # M=0 → As=0 → check "CT", khớp file gốc
     row-   = dòng đạt m_neg (nếu không có → dòng đầu tiên)
     v_max  = r.v2 của dòng có |r.v2| lớn nhất (so sánh abs, GIỮ DẤU khi hiển thị)
     width  = row+.cut_width
     → StripEnvelope(...)
```

**⚠️ 2 khác biệt cố ý so với VBA gốc** (đây là lỗi vòng lặp VBA, không phải công thức — tác giả chỉ xác nhận *công thức* đúng):
1. VBA quét `For Z = 10 To ndt` với `ndt` = SỐ DÒNG dữ liệu, trong khi dữ liệu nằm ở dòng 10..(9+ndt) → **VBA bỏ sót 9 dòng cuối** khi tìm max. Tool quét đủ 100% dòng.
2. VBA tìm shear max bằng `If Abs(V) > q` (so |V| với q **có dấu**) → kết quả sai khi có V âm. Tool so `|V|` với `|V_max|` — đúng nghĩa "lực cắt lớn nhất".

→ Hệ quả: golden test có thể lệch ở strip nào có max rơi vào 9 dòng cuối hoặc shear âm. Khi lệch, `extract_golden.py` phải in rõ nguyên nhân (xem §11.2). Shear chỉ để hiển thị, không tham gia tính As.

### 6.3 Công thức tính As (`rebar_calc.py`) — LÕI của app

Tái hiện đúng công thức các ô `Z21, AA21, AB21, AC21, N21, O21` sheet D1:

```python
import math

def calc_strip(d: StripDesign, mat: MaterialParams, mode: CalcMode) -> None:
    """Điền as_top_req, as_bot_req, check_top, check_bot vào d (in-place)."""
    Rb_raw = CONCRETE[mat.concrete][0]          # kG/cm², vd 130
    Rs     = STEEL[mat.steel][0] / 10           # → MPa, vd 350  (giống ô J13)

    if mode is CalcMode.EXCEL_COMPAT:
        Rb = Rb_raw * 1000                      # ❗ giống hệt Excel: 130 → 130_000 (xem ghi chú điểm 1)
    else:  # TCVN_STRICT
        Rb = Rb_raw / 10 * 1000                 # 130 kG/cm² → 13 MPa → 13_000 kN/m²

    h0_top = d.h - mat.cover_top_mm / 1000      # m — dùng cho thép trên
    h0_bot = d.h - mat.cover_bot_mm / 1000      # m — dùng cho As thép dưới
    b = d.env.width                             # m

    # ---- THÉP TRÊN (từ M−, ô Z21/AA21/N21) ----
    if d.env.m_neg is not None:
        alpha = -d.env.m_neg / (Rb * b * h0_top ** 2)
        zeta  = 0.5 * (1 + math.sqrt(1 - 2 * alpha))     # nếu 1-2α < 0 → thép quá tải, xem §6.4
        d.as_top_req = -d.env.m_neg / (zeta * Rs * 1000 * h0_top) * 1e4   # cm²
    else:
        d.as_top_req = None                     # hiển thị "-"

    # ---- THÉP DƯỚI (từ M+, ô AB21/AC21/O21) ----
    if d.env.m_pos is not None:
        h0_for_zeta = h0_top if mode is CalcMode.EXCEL_COMPAT else h0_bot   # ❗ điểm 2
        alpha = d.env.m_pos / (Rb * b * h0_for_zeta ** 2)
        zeta  = 0.5 * (1 + math.sqrt(1 - 2 * alpha))
        d.as_bot_req = d.env.m_pos / (zeta * Rs * 1000 * h0_bot) * 1e4     # cm²
    else:
        d.as_bot_req = None
```

Chú thích đơn vị để dev không hoang mang: `M` kN·m, `Rb` sau nhân 1000 hiểu là kN/m², `Rs*1000` → kN/m², `b, h0` m → As ra m², nhân `1e4` → cm². Hai dòng đánh dấu ❗ là 2 điểm "chủ ý của tác giả" — **không được "sửa cho đúng" trong mode EXCEL_COMPAT**.

### 6.4 Check bố trí thép (ô T21/U21)

```python
def check_ratio(dia_mm, spacing_mm, width_m, as_req, extra_cm2=0.0) -> float | str:
    if as_req is None: return "-"
    if as_req == 0:    return "CT"
    provided = math.pi * (dia_mm / 10) ** 2 / 4 * (width_m * 1000 / spacing_mm) + extra_cm2  # cm²
    ratio = provided / as_req
    return round(ratio, 2) if ratio < CHECK_RATIO_MAX else "CT"

# check_top = check_ratio(dia_top, spacing_top, width, as_top_req, extra_cm2=as_ham)  ← F16 chỉ cộng cho thép TRÊN
# check_bot = check_ratio(dia_bot, spacing_bot, width, as_bot_req)                    ← không cộng
```

UI tô màu ô check: `ratio >= 1` xanh (đạt), `< 1` đỏ (thiếu thép), `"CT"` cam (cần xem lại).

Edge case: nếu `1 - 2*alpha < 0` (tiết diện không đủ) → `math.sqrt` sẽ raise. Excel sẽ ra `#NUM!`. Tool: catch, set `as_req = None`, check = `"CT"`, tooltip *"αm quá lớn — tăng h đài hoặc mác bê tông"*.

### 6.5 Thứ tự tính lại (reactive)

Mỗi khi user sửa 1 ô (h, Ø, a, mác, cover, mode): chỉ cần gọi lại `calc_strip` cho dòng đó (hoặc mọi dòng nếu sửa tham số chung). Tính toán nhẹ (vài trăm strip × vài phép tính) → tính đồng bộ ngay trong slot, KHÔNG cần thread.

---

## 7. Xuất DXF (`export/`)

### 7.1 Mặt bằng strips + text thép (`dxf_strips.py`) — tái hiện macro `XUATAUTOCAD`

Spec vẽ (đơn vị bản vẽ = mm, tọa độ mdb là m → **nhân 1000**):

```
Với mỗi strip có geometry (x1,y1)-(x2,y2) và kết quả StripDesign:
1. Polyline 2 điểm: (x1*1000, y1*1000) → (x2*1000, y2*1000)
2. Góc strip: angle = atan2(dy, dx), chuẩn hóa về (-90°, 90°]
   Phân loại: NGANG nếu |angle| < 45°, DỌC nếu ngược lại
   (file gốc màu ĐỎ cho lớp strip ngang, XANH LÁ cho dọc — giữ nguyên)
3. Vị trí text (giống macro gốc):
   - NGANG:  tx = max(x1,x2)*1000 + 200 ; ty = y1*1000
   - DỌC:    ty = max(y1,y2)*1000 + 200 ; tx = x1*1000
4. Ghi 3 dòng text, height=250, rotation=angle, mỗi dòng cách nhau:
   NGANG: +400 theo Y │ DỌC: −400 theo X
   dòng 1: "DUOI-D{dia_bot} A{spacing_bot}"     ← thép dưới
   dòng 2: "TREN-D{dia_top} A{spacing_top}"     ← thép trên
   dòng 3: "{tên strip}"
5. Layer & màu:
   layer "RF_STRIP_X" màu đỏ (1)   ← strip ngang + text của nó
   layer "RF_STRIP_Y" màu xanh lá (3)
   (cải tiến so với macro gốc: có layer riêng thay vì vẽ hết vào layer hiện hành;
    màu để BYLAYER → AutoCAD nhìn y hệt trước)
```

Code khung:

```python
import ezdxf

def export_strips_dxf(designs: list[StripDesign], geos: dict[str, StripGeometry], path: str):
    doc = ezdxf.new("R2010")                     # DXF 2010 — AutoCAD 2010+ mở được
    doc.layers.add("RF_STRIP_X", color=1)
    doc.layers.add("RF_STRIP_Y", color=3)
    msp = doc.modelspace()
    for d in designs:
        g = geos.get(d.env.strip)
        if g is None: continue                   # strip không có geometry → bỏ qua, đã cảnh báo ở UI
        ...  # theo spec trên; text dùng msp.add_text(t, dxfattribs={"height":250, "rotation":deg, "layer":ly})
    doc.saveas(path)
```

**Definition of done:** mở DXF trong AutoCAD cạnh bản vẽ macro gốc từng vẽ → vị trí polyline, nội dung text, góc xoay, màu sắc giống nhau (chênh lệch vị trí text < 1mm).

### 7.2 Map phản lực (`dxf_reactions.py`) — tái hiện `XUATCHANCOT`

```
Input: list[JointReaction] (đã join tọa độ), filter combo do user chọn trên UI
Với mỗi joint:
1. POINT tại (x*1000, y*1000), layer "RF_REACTION" màu xanh lá
2. TEXT "Fz = {round(fz,1)}T" tại (x*1000+200, y*1000+200), height=250
Filter combo trên UI (cải tiến so với macro gốc — macro vẽ đè mọi combo lên nhau):
   - dropdown chọn 1 OutputCase, hoặc
   - option "Fz max mỗi điểm" (lấy max |Fz| per point)
   Mặc định: combo đầu tiên trong file.
```

### 7.3 `dxf_style.py`

Toàn bộ hằng số vẽ (text height 250, offset 200/400, tên layer, màu, DXF version) đặt ở đây — user chỉnh được trong Settings dialog (lưu vào config.json).

---

## 8. Báo cáo xlsx (`export/report_xlsx.py`)

Tái hiện trang in `$B$1:$U$(20+n)` của sheet D1:

```
Dòng 1   : "TÍNH TOÁN THÉP ĐÀI CỌC"  (merge, đậm, cỡ lớn)
Dòng 2-3 : "Tính toán sàn theo dải Strip trong SAFE ... TCVN 5574:2012" + tên file mdb + ngày giờ
Khối VẬT LIỆU: mác BT + Rb │ mác thép + Rs │ cover trên/dưới │ chế độ tính (GHI RÕ
  "Chế độ: giống Excel gốc" hay "Chế độ: TCVN chuẩn" — để bản in tự giải thích)
Bảng kết quả, header 2 dòng giống hệt file gốc:
  STT│Tên Đài│h đài(m)│Strip│Rộng(m)│Tổ hợp│Vị trí(m)│M+(KNm)│Tổ hợp│Vị trí(m)│M−(KNm)│Shear(KN)
     │Astop(cm²)│Asbot(cm²)│Thép trên(Ø,a)│Thép dưới(Ø,a)│Check trên│Check dưới
  - None → "-", check tô màu như UI (fill xanh/đỏ/cam)
  - Border kẻ bảng, font Times New Roman 11 (giống file in truyền thống VN)
Chân trang: "Xuất từ rebarFlow vX.Y.Z — {ngày giờ}"
```

(PDF: v1 chưa cần — user in từ xlsx. Ghi vào backlog v1.1: xuất PDF trực tiếp.)

---

## 9. UI (PySide6)

### 9.1 MainWindow

```
┌──────────────────────────────────────────────────────────────┐
│ [📂 Mở SAFE .mdb] [📂 Mở ETABS .mdb] │ [📐 Xuất DXF] [📊 Xuất báo cáo] │ [⚙] [🔄 Update] │
├──────────────────────────────────────────────────────────────┤
│ Tab: [Thép đài (strips)] [Phản lực chân cột]                 │
│ ┌─ Params panel (trái, cố định ~280px) ─┐ ┌─ Results table ─┐│
│ │ Mác BT      [B22.5 ▾]  Rb=130 kG/cm²  │ │ (§9.3)          ││
│ │ Mác thép    [CB400 ▾]  Rs=350 MPa     │ │                 ││
│ │ h đài mặc định [1.10] m               │ │                 ││
│ │ Cover trên  [35] mm │ dưới [100] mm   │ │                 ││
│ │ Thép sàn hầm [0.0] cm²                │ │                 ││
│ │ Ø/a mặc định [20]/[200] mm            │ │                 ││
│ │ Chế độ tính (•) Giống Excel gốc       │ │                 ││
│ │             ( ) TCVN chuẩn  [?]       │ │                 ││
│ └───────────────────────────────────────┘ └─────────────────┘│
│ Status: MONG.mdb │ SAFE 2016 │ KN,m,C ✔ │ 14 strips │ ⚠ thiếu bảng geometry │
└──────────────────────────────────────────────────────────────┘
```

- Nút `[?]` cạnh chế độ tính → mở popup tóm tắt nội dung `GHI-CHU-CONG-THUC-GOC.md`.
- Đổi bất kỳ thông số nào ở panel → recalc toàn bộ + refresh bảng (signal `paramsChanged`).

### 9.2 Params panel (`params_panel.py`)

- Emit 1 signal duy nhất `params_changed(MaterialParams)`.
- Rb/Rs hiển thị readonly cạnh dropdown (tra từ `constants.py`) để kỹ sư đối chiếu.

### 9.3 Results table (`results_table.py`)

`QTableView` + `QAbstractTableModel` (KHÔNG dùng QTableWidget — dữ liệu vài trăm dòng, cần model/view sạch):

| Cột | Nguồn | Edit? |
|---|---|---|
| STT, Strip, Rộng, Tổ hợp±, Vị trí±, M+, M−, Shear | envelope | ❌ |
| Tên Đài | user | ✅ text |
| h đài | user (default từ panel) | ✅ float, >0 |
| Astop, Asbot | engine | ❌ (nền xám nhạt) |
| Ø trên, a trên, Ø dưới, a dưới | user | ✅ (Ø: spinbox 10–40 bước 2; a: spinbox 50–400 bước 25) |
| Check trên, Check dưới | engine | ❌ — nền xanh/đỏ/cam theo §6.4 |

- `setData()` → cập nhật `StripDesign` → gọi `calc_strip` dòng đó → emit `dataChanged` cho 4 cột kết quả.
- Context menu: "Áp Ø/a này cho mọi strip", "Copy bảng (paste được vào Excel/Calc)".

### 9.4 Workers (`workers.py`)

- `ImportWorker(QThread)`: đọc mdb + aggregate ở thread nền, emit `finished(SafeModel | EtabsModel)` / `failed(str)`. UI hiện `QProgressDialog` không xác định (file mdb có thể vài chục MB).
- Export DXF/xlsx nhanh → chạy đồng bộ, chỉ hiện toast "Đã xuất: <path> [Mở thư mục]".

### 9.5 Config (`config.py`)

`%APPDATA%/rebarFlow/config.json`: mọi giá trị panel + settings + thư mục lần cuối + `skip_version` (cho updater). Load khi mở app, save khi đóng.

---

## 10. Updater (`updater/`)

### 10.1 Check version (`version_check.py`)

```python
API = "https://api.github.com/repos/{owner}/rebarflow-releases/releases/latest"
# repo PUBLIC riêng chỉ chứa release (code app có thể để repo private khác)

def check_update(current: str) -> UpdateInfo | None:
    r = requests.get(API, timeout=5)                 # gọi trong QThread, timeout ngắn
    r.raise_for_status()
    data = r.json()
    latest = data["tag_name"].lstrip("v")            # tag dạng v1.2.0
    if packaging.version.parse(latest) <= packaging.version.parse(current):
        return None
    asset = next(a for a in data["assets"] if a["name"].endswith(".exe"))
    return UpdateInfo(version=latest, notes=data["body"],
                      url=asset["browser_download_url"], size=asset["size"])
```

- Gọi khi khởi động (delay 3s sau khi UI hiện, trong thread). **Mọi lỗi mạng → nuốt im lặng**, app hoạt động bình thường.
- Có bản mới → `update_dialog.py`: version + changelog (render markdown body) + `[Tải & cài đặt]` `[Để sau]` `[Bỏ qua bản này]` (lưu `skip_version` vào config).

### 10.2 Download & install (`downloader.py`)

1. Tải về `%TEMP%\rebarflow-setup-{ver}.exe` (stream + progress bar, verify đúng `size`).
2. `subprocess.Popen([exe, "/SILENT", "/CLOSEAPPLICATIONS"])` → `QApplication.quit()`.
3. Inno cài đè vào thư mục cũ, tạo lại shortcut. User mở lại app là bản mới.

### 10.3 Quy trình phát hành (cho maintainer)

```
1. Sửa __version__.py → "1.1.0"; cập nhật CHANGELOG.md
2. packaging/build.ps1  → chạy pytest, PyInstaller, Inno → rebarflow-setup-1.1.0.exe
3. GitHub: tạo release tag v1.1.0 trên repo releases, body = changelog, đính kèm setup.exe
→ Mọi máy đang chạy bản cũ sẽ tự thấy thông báo ở lần mở sau
```

---

## 11. Golden test — kiểm chứng tool khớp file gốc

### 11.1 Trích số liệu kỳ vọng (`tests/tools/extract_golden.py` — chạy 1 lần)

```
Input : "tinh Dai coc - GOC.xls" (convert sang xlsx bằng LibreOffice headless:
        soffice --headless --convert-to xlsx)
Đọc sheet D1 rows 21..(20+n) → mỗi dòng: strip, width, m_pos, m_neg, shear,
        as_top (N), as_bot (O), dia/spacing (P..S), check (T,U) — GIÁ TRỊ đã tính sẵn
Đọc sheet Data rows 10.. → toàn bộ strip forces (input tương ứng)
Output: tests/golden/golden_d1.json + strip_forces_sample.json
```

### 11.2 Test cases (pytest)

| Test | Nội dung | Pass khi |
|---|---|---|
| `test_rebar_calc_golden` | Với từng dòng golden: đưa (m_pos, m_neg, width, h=1.1, B22.5, CB400, cover 35/100, mode=EXCEL_COMPAT) vào `calc_strip` | `as_top`, `as_bot` khớp golden, sai số tương đối < 1e-9 |
| `test_check_golden` | check T/U với Ø/a trong golden | khớp từng giá trị/"CT"/"-" |
| `test_aggregate_golden` | chạy `aggregate` trên strip_forces_sample → so M+/M−/width per strip với golden | khớp; NẾU lệch → script in bảng đối chiếu và tự kiểm tra 2 nguyên nhân đã biết: (a) max nằm trong 9 dòng cuối VBA bỏ sót, (b) shear âm. Lệch đúng do (a)/(b) = chấp nhận, ghi vào file `tests/golden/KNOWN_DIFFS.md` |
| `test_safe_import_mong` | đọc `MONG.mdb` thật | units OK, 1592 dòng Strip Forces, `missing_tables` chứa `Object Geometry - Design Strips` |
| `test_tcvn_strict_direction` | so 2 mode trên cùng input | `As(TCVN_STRICT) >= As(EXCEL_COMPAT)` với mọi dòng golden (sanity — mode chuẩn luôn ra nhiều thép hơn) |

**Không phát hành khi golden test đỏ.** File `tinh Dai coc - GOC.xls` + `MONG.mdb` commit vào repo trong `tests/fixtures/`.

---

## 12. Packaging (`packaging/`)

- `rebarflow.spec`: onedir, `--windowed`, icon, thêm data files (icon, docs). Exclude module thừa (tkinter...).
- `installer.iss` (Inno Setup) — điểm chính:
  ```ini
  AppId={{B8C1E9D0-...-rebarflow}}     ; CỐ ĐỊNH — để update cài đè đúng chỗ
  DefaultDirName={autopf}\rebarFlow
  CloseApplications=yes                 ; hỗ trợ /CLOSEAPPLICATIONS từ updater
  [Files] Source: "dist\rebarflow\*"; Flags: recursesubdirs
  [Icons] Desktop + Start Menu
  ```
- `build.ps1`: `pytest` (fail → dừng) → `pyinstaller` → `iscc` → in đường dẫn setup.exe. Version tự đọc từ `__version__.py` truyền vào iss qua `/D`.

---

## 13. Milestones & Definition of Done

| # | Nội dung | DoD (nghiệm thu) |
|---|---|---|
| **M1** | Skeleton + `core/` đầy đủ + golden tests | `pytest` xanh toàn bộ, bao gồm golden khớp file gốc. Chưa có UI — chạy được qua script CLI tạm `python -m rebarflow.cli <file.mdb>` in bảng kết quả ra console |
| **M2** | `export/`: DXF strips + DXF phản lực + báo cáo xlsx | Mở DXF bằng AutoCAD/LibreCAD đối chiếu bản vẽ macro gốc: giống vị trí/nội dung/màu. Xlsx in ra giống trang in D1 |
| **M3** | UI hoàn chỉnh (2 tab, bảng editable, recalc live, config) | Kỹ sư không-biết-code tự thao tác được toàn bộ luồng §1 không cần hướng dẫn quá 5 phút |
| **M4** | Updater + packaging + release v1.0.0 lên GitHub | Cài setup.exe trên máy Windows sạch (không Python/Office/AutoCAD) → chạy đủ luồng. Phát hành v1.0.1 thử → máy đó tự báo update và tự cài được |
| **M5** | Beta song song | Outsource chạy ≥ 2 dự án thật song song Excel (máy còn Excel) vs tool → số khớp, ký nghiệm thu |

Thứ tự code trong M1 (cho dev): `constants.py` → `models.py` → `rebar_calc.py` + `test_rebar_calc` (golden) → `mdb_reader.py` → `safe_import.py` + test với MONG.mdb → `strip_aggregate.py` + test → `cli.py`.

---

## 14. Convention & lưu ý chung cho dev

1. **`core/` và `export/` cấm import PySide6** — giữ pure để test không cần display. CI có thể chạy pytest headless.
2. Mỗi file một trách nhiệm (xem cây thư mục §3) — không gộp, không "god file". File nào bắt đầu gánh 2 việc → tách trước khi viết tiếp.
3. Số thực: dùng `float` thường (Excel cũng double) — KHÔNG dùng Decimal, để khớp golden bit-level tốt nhất có thể.
4. Mọi message lỗi hướng người dùng bằng **tiếng Việt, nói rõ cách khắc phục** (mẫu ở §5.2). Log kỹ thuật ghi file, tiếng Anh cũng được.
5. Hai chỗ đánh dấu ❗ trong `rebar_calc.py` phải kèm comment trỏ về `docs/GHI-CHU-CONG-THUC-GOC.md` — người mới đọc code sẽ tưởng là bug và "sửa giùm".
6. Đặt tên: strip/moment/shear... theo domain (tiếng Anh), nhưng string hiển thị UI thì tiếng Việt, gom trong module/`constants` để sau này dễ i18n.
7. Git: repo private `rebarflow` (code) + repo public `rebarflow-releases` (chỉ release + changelog). Commit fixtures (`MONG.mdb`, file xls gốc) vào repo code.

## 15. Rủi ro & phương án

| Rủi ro | Ứng phó |
|---|---|
| `access-parser` fail với mdb từ SAFE/ETABS phiên bản khác | Catch per-table (§5.4). Nếu gặp thật: fallback nhờ user export lại; phương án B (đánh giá sau): dùng `mdbtools` qua WSL/binary hoặc chuyển sang jackcess (Java) — CHƯA làm ở v1 |
| File mdb ETABS chưa có mẫu thật để test | §5.3 đã ghi cách xác minh tên cột; M1 làm SAFE trước, ETABS hoàn thiện khi user cung cấp file mẫu |
| Golden lệch do 2 lỗi vòng lặp VBA (§6.2) | Đã có quy trình KNOWN_DIFFS.md; nếu user muốn khớp tuyệt đối kể cả lỗi vòng lặp → thêm flag `--vba-bug-compat` (để dành, chưa làm) |
| Kỹ sư nghi ngờ số của tool | Báo cáo xlsx ghi rõ chế độ tính + phiên bản; bảng Astop/Asbot đối chiếu được bằng tay theo công thức §6.3 |
| GitHub bị chặn ở một số mạng công ty | Updater fail im lặng, app vẫn chạy; cài tay bằng setup.exe vẫn luôn được |

---

## 16. Việc còn mở — ĐÃ CHỐT HẾT (review 26/07/2026)

1. ~~Tên app~~ → **"rebarFlow"**, icon để default trước, đổi trước M4 nếu muốn.
2. ~~Repo GitHub~~ → account **cá nhân của user**.
3. ~~Cột "Tên Đài"~~ → **user gõ tay từng dòng, y như file Excel gốc**.
4. ~~ETABS~~ → **làm y theo 2 file mẫu đã có** (mapping từ sheet PHAN LUC trong file Excel, xem §5.3). Test với file mdb ETABS thật diễn ra ở M5 beta.

Ghi chú thêm sau khi soi file gốc lần cuối: bảng kết quả sheet D1 hiện chứa **33 dòng = output của `tinhthepmax`** (per strip) → golden test so thẳng với 33 dòng này. Dữ liệu sheet Data (487 dòng) là từ một file mdb cũ khác — KHÔNG phải `MONG.mdb` (1592 dòng) → golden aggregate dùng cặp (Data sheet → D1) trích từ chính file Excel, còn `MONG.mdb` chỉ làm fixture test import.