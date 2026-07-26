# Ghi chú công thức file gốc `tinh Dai coc - GOC.xls`

> Ngày ghi: 26/07/2026
> Mục đích: lưu vết 2 điểm "bất thường" trong công thức file Excel gốc, đã hỏi tác giả file và được xác nhận là **chủ ý — giữ nguyên**. Nếu sau này có thắc mắc về kết quả tính thép của tool rebarFlow, đọc lại file này trước.

## Bối cảnh

File Excel gốc (VBA) tính thép đài cọc từ dữ liệu SAFE export (.mdb), theo TCVN 5574:2012, cấu kiện chịu uốn:

```
αm = M / (Rb · b · h₀²)
ζ  = 0.5 · (1 + √(1 − 2·αm))
As = M / (ζ · Rs · h₀)
```

Khi chuyển thành app rebarFlow, phát hiện 2 điểm khác với cách hiểu "chuẩn sách" của công thức trên. Đã hỏi trực tiếp tác giả file (07/2026), câu trả lời: **các công thức trong file đều đúng như chủ ý** → tool tái hiện y nguyên.

## Điểm 1 — Đơn vị Rb trong công thức αm

- Ô `J12` (sheet D1) tra bảng ra **Rb = 130** — đơn vị bảng tra là **kG/cm²** (ứng mác B22.5).
- Công thức αm (cột ẩn `Z21`): `αm = M / (J12 × 1000 × b × h₀²)` — tức dùng giá trị 130 nhân 1000 như thể là MPa (→ 130.000 kN/m²), trong khi quy đổi "chuẩn sách" B22.5 có Rb = 13 MPa = 13.000 kN/m².
- Trong khi đó Rs (`J13`) **có** chia `/10` để đổi kG/cm² → MPa.
- **Hệ quả số học:** αm nhỏ đi 10 lần → ζ ≈ 1 → lượng thép yêu cầu tính ra **ít hơn ~2–8%** so với tính với Rb quy đổi chuẩn.
- **Kết luận:** tác giả xác nhận đúng chủ ý. Tool giữ nguyên: `Rb_dùng = giá_trị_tra_bảng × 1000 (kN/m²)`.

## Điểm 2 — h₀ khi tính ζ cho thép lớp dưới

- ζ thép dưới (cột ẩn `AB21`) tính với `h₀ = h − F12/1000` (F12 = lớp bảo vệ **trên**, 35mm).
- Nhưng As thép dưới (`O21`) dùng `h₀ = h − F13/1000` (F13 = lớp bảo vệ **dưới**, 100mm).
- Tức ζ và As của cùng lớp thép dưới dùng 2 giá trị h₀ khác nhau.
- **Kết luận:** tác giả xác nhận đúng chủ ý. Tool giữ nguyên đúng như vậy.

## Điểm 3 — Bảng thiếu trong file mdb (không phải công thức, chỉ là hành vi tool)

- File SAFE export có thể thiếu bảng `Object Geometry - Design Strips` (do không tick khi export). Ví dụ: file mẫu `MONG.mdb` trong folder này bị thiếu.
- Tool xử lý: **vẫn tính thép bình thường** (tính toán không cần bảng này), chỉ **chặn phần xuất DXF strips** và báo rõ: "Thiếu bảng Object Geometry - Design Strips — export lại từ SAFE, nhớ tick bảng này."
- Các bảng bắt buộc để tính: `Program Control` (check đơn vị `KN, m, C`), `Strip Forces`, `Slab Properties 02 - Solid Slabs`.

## Quyết định cho tool rebarFlow

| Hạng mục | Quyết định |
|---|---|
| Chế độ tính **mặc định** | **Giống Excel gốc 100%** (theo xác nhận của tác giả file) |
| Chế độ "TCVN chuẩn sách" (sửa điểm 1 + 2) | Vẫn cài trong tool, là **tùy chọn bật tay** — để tham khảo/so sánh khi cần |
| Golden test | Kết quả tool (chế độ mặc định) phải khớp giá trị đã tính sẵn trong sheet D1 của file gốc |

## Tra cứu nhanh vị trí công thức trong file gốc (sheet D1)

| Ô | Nội dung |
|---|---|
| `I9`, `I10` | Mác bê tông / mác thép (chọn) |
| `J12` | Rb tra bảng (kG/cm², bảng `AE20:AJ29`) |
| `J13` | Rs tra bảng /10 (bảng `AE32:AH37`) |
| `F12`, `F13` | Lớp bảo vệ trên (35) / dưới (100) mm |
| `F14` | μ min = 0.0005 |
| `F16` | Thép sàn hầm cộng thêm (cm²) |
| `Z21`, `AA21` | αm, ζ cho thép trên (từ M−) |
| `AB21`, `AC21` | αm, ζ cho thép dưới (từ M+) — αm dùng cover trên (điểm 2) |
| `N21`, `O21` | As top / As bot yêu cầu (cm²) |
| `P:S` | Ø + khoảng cách thép trên/dưới (user chọn) |
| `T21`, `U21` | Check As bố trí / As yêu cầu (≥1 và <5, không thì "CT") |