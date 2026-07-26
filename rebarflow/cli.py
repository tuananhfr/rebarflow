"""CLI tạm cho M1: chạy đủ luồng core không cần UI.

    python -m rebarflow.cli <file.mdb> [--mode excel|tcvn] [--h 1.1]

In bảng kết quả per strip ra console — dùng để smoke-test với file mdb thật
trước khi có UI (M3).
"""

import argparse
import sys

from rebarflow.constants import DEFAULT_H_DAI_M
from rebarflow.core.models import CalcMode, MaterialParams, StripDesign
from rebarflow.core.rebar_calc import calc_strip
from rebarflow.core.safe_import import SafeImportError, load_safe
from rebarflow.core.strip_aggregate import aggregate


def _fmt(v, nd=2):
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def main(argv: list[str] | None = None) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(prog="rebarflow", description="Tính thép đài cọc từ file SAFE .mdb")
    p.add_argument("mdb", help="đường dẫn file .mdb export từ SAFE")
    p.add_argument("--mode", choices=["excel", "tcvn"], default="excel",
                   help="excel = giống Excel gốc (mặc định), tcvn = TCVN chuẩn sách")
    p.add_argument("--h", type=float, default=DEFAULT_H_DAI_M, help="h đài (m), mặc định 1.1")
    args = p.parse_args(argv)

    try:
        model = load_safe(args.mdb)
    except (SafeImportError, Exception) as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 1

    print(f"File   : {model.source_path}")
    print(f"Nguồn  : {model.program} — {len(model.forces)} dòng Strip Forces")
    for t in model.missing_tables:
        print(f"⚠ Thiếu bảng «{t}»"
              + (" — vẫn tính được thép, nhưng không xuất được DXF strips." if "Geometry" in t else ""))

    mat = MaterialParams(mode=CalcMode.EXCEL_COMPAT if args.mode == "excel" else CalcMode.TCVN_STRICT)
    designs = [StripDesign(env=e, h=args.h) for e in aggregate(model.forces)]
    for d in designs:
        calc_strip(d, mat)

    cols = ["Strip", "Rộng", "M+", "Combo+", "M-", "Combo-", "Shear",
            "Astop", "Asbot", "Thép trên", "Thép dưới", "Ck.trên", "Ck.dưới"]
    rows = [
        [
            d.env.strip, _fmt(d.env.width), _fmt(d.env.m_pos, 1), d.env.m_pos_combo,
            _fmt(d.env.m_neg, 1), d.env.m_neg_combo, _fmt(d.env.v_max, 1),
            "-" if d.as_top_req is None else _fmt(d.as_top_req),
            "-" if d.as_bot_req is None else _fmt(d.as_bot_req),
            f"D{d.dia_top}a{d.spacing_top}", f"D{d.dia_bot}a{d.spacing_bot}",
            _fmt(d.check_top), _fmt(d.check_bot),
        ]
        for d in designs
    ]
    widths = [max(len(c), *(len(r[i]) for r in rows)) for i, c in enumerate(cols)]
    print()
    print("  ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)))
    print(f"\n{len(designs)} strips — chế độ: "
          + ("giống Excel gốc" if args.mode == "excel" else "TCVN chuẩn sách")
          + f" — h đài = {args.h} m (chỉnh bằng --h)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
