# Tổng quan Map `restaurant.sdf`

Mô hình nhà hàng cho TurtleBot4. Quy ước trục: **X** = trái/phải, **Y** = trước/sau (bếp nằm phía **−Y**), **Z** = cao. Đơn vị: mét.

> Lưu ý: chiều cao (Z) cố định để mặt bàn bếp luôn khớp với đường ray giao đồ ở **z ≈ 1.1 m**.

## Sơ đồ bố trí (nhìn từ trên xuống)

```
                  Bàn (t1..t6) + ghế + mã QR
        ┌───────────────────────────────────────┐  y ≈ 0   (CROSSBAR, dài 8 m)
        │                                         │
                          │ │
                          │ │  Hành lang thẳng (TRACK STEM)
                          │ │  dài 6.7 m
                          │ │
                  ┌───────┴─┴───────┐
                  │     BẾP 6×2 m   │  y ≈ −8.1
                  └─────────────────┘
```

## 1. Bếp (Kitchen hub) — quanh `(0, −8.1)`

| Thành phần | Kích thước (X×Y×Z) | Ghi chú |
|---|---|---|
| Thân bếp (base) | 6.0 × 2.0 × 1.0 | Khối chính, có va chạm |
| Mặt quầy trên | 6.4 × 2.4 × 0.02 | Ở z = 1.1 m |
| Tường sau | 6.0 × 0.2 × 1.0 | z = 1.5 m |
| Dải đèn neon | 5.0 × 0.1 × 0.02 | Trang trí, z = 1.7 m |
| Tường hông trái/phải | 0.2 × 2.1 × 2.0 | Ở x = ±3.1, bao 2 bên bếp |

## 2. Đường ray giao đồ (Delivery track) — cao ~1.1 m

| Thành phần | Kích thước (X×Y×Z) | Vị trí |
|---|---|---|
| Hành lang thẳng (stem) | 0.6 × 6.7 × 0.02 | tâm `(0, −3.65)`, nối bếp ↔ crossbar |
| → bệ đỡ stem | 0.5 × 6.7 × 1.1 | trụ chống xuống sàn |
| Thanh ngang (crossbar) | 8.0 × 0.6 × 0.02 | tâm `(0, 0)`, dọc theo dãy bàn |
| → bệ đỡ crossbar | 8.0 × 0.5 × 1.1 | trụ chống xuống sàn |
| Tường viền cam stem (sw_l/r) | 0.02 × 6.7 × 0.3 | x = ±0.3 |
| Tường viền cam crossbar (tw/bw/el/er) | dày 0.02, cao 0.3 | viền 2 mép + 2 đầu thanh ngang |

**Hành lang robot di chuyển:** rộng ~0.6 m, dài ~6.7 m (bếp → khu bàn), rồi rẽ dọc thanh ngang dài 8 m.

## 3. Bàn ăn (t1–t6) + ghế + mã QR

- **Bàn:** model Cafe table tải từ Gazebo Fuel, đường kính ~0.8 m. Vị trí (X, Y):

| Bàn | Vị trí | Bàn | Vị trí |
|---|---|---|---|
| t1 | (−3.3, 1.1) | t4 | (1.3, 1.1) |
| t2 | (−2.3, −1.1) | t5 | (2.3, −1.1) |
| t3 | (−1.3, 1.1) | t6 | (3.3, 1.1) |

- **Ghế (t1c–t6c):** mesh ghế, đặt cách tâm bàn 0.4 m ở phía xa hành lang.
- **Mã QR/ArUco (q1–q6):** tấm 0.1 × 0.005 × 0.1 m, gắn trên tường thanh ngang ở **z = 1.25 m** (tầm camera robot), mỗi bàn 1 mã.

## 4. Khác

| Thành phần | Kích thước | Ghi chú |
|---|---|---|
| Sàn (ground_plane) | 100 × 100 | Mặt phẳng, có va chạm |
| Đèn `sun` | — | Đèn directional, không đổ bóng |
| Điểm spawn robot | `x=1.0, y=0.0, yaw=3.14159` | Trong hành lang thanh ngang |
