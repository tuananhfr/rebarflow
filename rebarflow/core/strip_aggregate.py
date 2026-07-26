"""Gom nội lực per strip: M+ max, M− min, |V| max — tái hiện macro `tinhthepmax`.

Khác cố ý so với VBA gốc (lỗi vòng lặp, KHÔNG phải công thức — xem PLAN.md §6.2):
- quét đủ 100% dòng dữ liệu (VBA bỏ sót 9 dòng cuối do dùng nhầm ndt làm số dòng);
- shear max so sánh |V| với |V_max| (VBA so |V| với q CÓ DẤU nên sai khi V âm).
Semantics giữ nguyên VBA: không có moment dương/âm → m_pos/m_neg = 0.0
(để As=0, check="CT" khớp file gốc); dòng tham chiếu fallback = dòng đầu strip;
tie-break: dòng XUẤT HIỆN TRƯỚC thắng (VBA dùng so sánh strict > / <).
"""

from rebarflow.core.models import StripEnvelope, StripForceRow


def aggregate(forces: list[StripForceRow]) -> list[StripEnvelope]:
    order: list[str] = []
    by_strip: dict[str, list[StripForceRow]] = {}
    for r in forces:
        if r.strip not in by_strip:
            by_strip[r.strip] = []
            order.append(r.strip)
        by_strip[r.strip].append(r)

    out: list[StripEnvelope] = []
    for strip in order:
        rows = by_strip[strip]
        first = rows[0]

        pos_row = None
        for r in rows:  # max() cũng được, nhưng viết vòng lặp cho giống VBA tie-break
            if r.m3 > 0 and (pos_row is None or r.m3 > pos_row.m3):
                pos_row = r
        neg_row = None
        for r in rows:
            if r.m3 < 0 and (neg_row is None or r.m3 < neg_row.m3):
                neg_row = r
        v_row = first
        for r in rows:
            if abs(r.v2) > abs(v_row.v2):
                v_row = r

        rp = pos_row or first
        rn = neg_row or first
        out.append(
            StripEnvelope(
                strip=strip,
                width=rp.cut_width,
                m_pos=pos_row.m3 if pos_row else 0.0,
                m_pos_combo=rp.output_case,
                m_pos_station=rp.station,
                m_neg=neg_row.m3 if neg_row else 0.0,
                m_neg_combo=rn.output_case,
                m_neg_station=rn.station,
                v_max=v_row.v2,
                v_combo=v_row.output_case,
            )
        )
    return out
