# Known diffs — tool vs file Excel gốc (golden sheet D1)

> Sinh từ `tests/test_strip_aggregate.py` (chạy `pytest tests/test_strip_aggregate.py -s`).
> Đây là các giá trị tool ra KHÁC sheet D1 file gốc, nhưng mỗi chênh lệch đều được
> test chứng minh là do **2 lỗi vòng lặp VBA** của file gốc (PLAN.md §6.2):
> (a) quét max bỏ sót 9 dòng cuối dữ liệu; (b) tìm shear max so sánh |V| với biến có dấu.
> Tool quét đúng, đủ — tức **tool đúng hơn file gốc** ở các dòng này.

## Tổng hợp (dữ liệu golden trích 26/07/2026 — 33 strips, 488 dòng nội lực)

- **17 chênh lệch shear** (lỗi b, một số cộng hưởng lỗi a). Shear chỉ hiển thị,
  KHÔNG tham gia tính As → không ảnh hưởng lượng thép.
- **1 chênh lệch moment âm — ẢNH HƯỞNG THẬT:**

| Strip | Tool (đúng) | Excel gốc | Hệ quả trong bản tính cũ |
|---|---|---|---|
| CSB18 | M− = **−1077.26** kNm | −851.08 kNm | Moment âm max của CSB18 nằm trong 9 dòng cuối bị VBA bỏ sót → file gốc tính thiếu ~27% moment → **thép trên CSB18 của bản tính cũ bị thiếu tương ứng** |

## Chi tiết 18 dòng

```
CSA2.shear : tool=-132.99   | Excel=13.91
CSA6.shear : tool=-984.06   | Excel=0
CSB3.shear : tool=-585.32   | Excel=0
CSB5.shear : tool=-1205.18  | Excel=0
CSB7.shear : tool=-2610.80  | Excel=0
CSB8.shear : tool=-960.52   | Excel=21.90
CSB9.shear : tool=-1317.34  | Excel=0
CSA10.shear: tool=-1526.14  | Excel=1405.38
CSA11.shear: tool=-1215.19  | Excel=1024.26
CSA14.shear: tool=-2198.46  | Excel=0
CSA15.shear: tool=-2005.66  | Excel=0
CSA16.shear: tool=-119.69   | Excel=-14.58
CSA18.shear: tool=-51.53    | Excel=44.09
CSB10.shear: tool=-1080.54  | Excel=0
CSB14.shear: tool=-325.57   | Excel=-71.12
CSB17.shear: tool=-136.80   | Excel=-16.68
CSB18.m_neg: tool=-1077.26  | Excel=-851.08   ← duy nhất ảnh hưởng lượng thép
```

Công thức tính As (từ M → As, check Ø/a) khớp file gốc **100%, cả 33 dòng** —
xem `tests/test_rebar_calc.py` (66 assertions pass).
