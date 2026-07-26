"""Bảng vật liệu + giá trị mặc định.

Số liệu trích NGUYÊN VĂN từ bảng tra AE20:AJ29 và AE32:AH37 sheet D1
của file gốc `tinh Dai coc - GOC.xls`. KHÔNG tự "sửa" đơn vị ở đây —
cách dùng các giá trị này nằm trong core/rebar_calc.py (xem
docs/GHI-CHU-CONG-THUC-GOC.md).
"""

# grade: (Rb, Rk, Eb, Rb_ser, Rbt_ser) — đơn vị kG/cm² như bảng tra gốc
CONCRETE: dict[str, tuple[float, float, float, float, float]] = {
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

# grade: (Rs, Rs_ser, Es) — kG/cm²
STEEL: dict[str, tuple[float, float, float]] = {
    "AI":     (2250, 2350, 2_100_000),
    "AII":    (2600, 2950, 2_100_000),
    "AIII":   (3500, 3500, 2_000_000),
    "CB300":  (2600, 2600, 2_100_000),
    "CB400":  (3500, 2800, 2_000_000),
    "CB500V": (4350, 3900, 2_000_000),
}

# Defaults — giống các ô input mặc định của file gốc
DEFAULT_CONCRETE = "B22.5"
DEFAULT_STEEL = "CB400"
DEFAULT_COVER_TOP_MM = 35.0    # ô F12
DEFAULT_COVER_BOT_MM = 100.0   # ô F13
DEFAULT_H_DAI_M = 1.1          # ô D12/D21
DEFAULT_DIA_MM = 20            # VBA tinhthepmax điền 20 khi ô trống
DEFAULT_SPACING_MM = 200
DEFAULT_AS_HAM_CM2 = 0.0       # ô F16 "Thep san ham" — chỉ cộng vào check thép TRÊN

CHECK_RATIO_MAX = 5.0          # tỷ lệ check >= 5 → hiển thị "CT" (ô T21/U21)

SAFE_REQUIRED_UNITS = "KN, m, C"
ETABS_974_REQUIRED_UNITS = "Ton-m"
ETABS_2017_REQUIRED_UNITS = "tonf, m, C"

TBL_PROGRAM_CONTROL = "Program Control"
TBL_STRIP_FORCES = "Strip Forces"
TBL_STRIP_GEOMETRY = "Object Geometry - Design Strips"
TBL_SLAB_PROPS = "Slab Properties 02 - Solid Slabs"