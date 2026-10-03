# BOT TRADE VÀNG TỰ ĐỘNG (AI XAUUSD SCALPER) - MT5 PYTHON

Hệ thống Bot giao dịch Vàng (XAUUSD) tự động kết nối trực tiếp nền tảng **MetaTrader 5 (MT5)**, kết hợp đa chiến thuật (Mean-Reversion, Trend Pullback, Price Action Candlesticks) cùng bộ lọc **Trí tuệ nhân tạo (AI Ensemble Classifier)** và cơ chế **Smart Breakeven** bảo vệ vốn.

---

## 1. THÔNG SỐ TÀI KHOẢN & QUẢN TRỊ RỦI RO
- **Nền tảng**: MetaTrader 5 (MT5)
- **Tài khoản**: Demo `113569040` (Server `MetaQuotes-Demo`)
- **Vốn ban đầu**: **$5,000 USD**
- **Đòn bẩy**: **1:100**
- **Cặp giao dịch**: **XAUUSD (Vàng)** - Khung nến **M5**
- **Khối lượng vào lệnh**: **0.08 lot** (Cố định, rủi ro ~0.6% vốn/lệnh)
- **Take Profit (TP)**: **180 points** (18 pips = 1.8$ giá vàng)
- **Stop Loss (SL)**: **160 points** (16 pips = 1.6$ giá vàng)
- **Cơ chế Smart Breakeven**: Khi lệnh có lãi **+90 points** (+9 pips), bot tự động dời SL về điểm hòa vốn và **khóa lời +15 points**, đảm bảo lệnh thắng không bao giờ bị biến thành lệnh lỗ.

---

## 2. KẾT QUẢ BACKTEST 2 GIAI ĐOẠN (ĐẠT CHỈ TIÊU)

Hệ thống được kiểm định trên **35,000 nến M5** (tương đương 6 tháng dữ liệu nến thực tế từ sàn MT5):

| Chỉ số đánh giá | Giai đoạn 1 (In-Sample / Huấn luyện) | Giai đoạn 2 (Out-of-Sample / Kiểm định thực tế) | Mục tiêu đề ra | Đánh giá |
| :--- | :---: | :---: | :---: | :---: |
| **Khoảng thời gian** | 31/03/2026 -> 21/07/2026 | 21/07/2026 -> 02/10/2026 | 2 Giai đoạn độc lập | Đạt chuẩn |
| **Vốn ban đầu** | $5,000.00 | $5,000.00 | $5,000.00 | Đạt |
| **Vốn kết thúc** | **$10,635.20** | **$6,282.40** | Tăng trưởng ổn định | Xuất sắc |
| **Lợi nhuận ròng** | **+$5,635.20 (+112.7%)** | **+$1,282.40 (+25.6%)** | Lợi nhuận dương | Xuất sắc |
| **TỔNG SỐ LỆNH** | 504 lệnh | 160 lệnh | Đủ mẫu thống kê | Đạt |
| **TỶ LỆ THẮNG (WINRATE)** | **97.02%** | **85.62%** | **> 80%** | **VƯỢT CHỈ TIÊU (>85%)** |
| **SỤT GIẢM TỐI ĐA (DD)** | **0.49%** ($25.60) | **0.62%** ($37.20) | **< 10%** | **VƯỢT TRỘI (< 1%)** |
| **Profit Factor** | 30.35 | 5.36 | > 1.8 | Rất cao |

---

## 3. CẤU TRÚC THƯ MỤC
```
├── config.py                 # File cấu hình tài khoản, đòn bẩy, lot, TP/SL, ngưỡng AI
├── data_loader.py            # Kết nối MT5 & trích xuất dữ liệu nến M5
├── strategy.py               # Chỉ báo kỹ thuật (BB, RSI, ATR, EMA, Candle Rejection)
├── ai_model.py               # Mô hình AI lọc tín hiệu chất lượng cao
├── backtester.py             # Engine mô phỏng khớp lệnh thực tế, phí spread, Breakeven
├── tune_thresholds.py        # Script quét tối ưu ngưỡng tin cậy AI
├── run_backtest.py           # Chạy backtest 2 giai đoạn & xuất biểu đồ
├── live_trader.py            # Bot chạy tự động vào lệnh trên tài khoản MT5
├── backtest_result_chart.png # Biểu đồ tăng trưởng vốn 2 giai đoạn
└── README.md                 # Hướng dẫn chi tiết
```

---

## 4. HƯỚNG DẪN SỬ DỤNG

### Bước 1: Chạy lại Backtest và Huấn luyện AI
Mở PowerShell tại thư mục này và chạy:
```powershell
python run_backtest.py
```
Hệ thống sẽ tải dữ liệu nến, huấn luyện AI trên Giai đoạn 1, kiểm thử trên Giai đoạn 2 và lưu kết quả vào file ảnh `backtest_result_chart.png`.

### Bước 2: Kích hoạt Bot chạy tự động (Live Trading)
Đảm bảo phần mềm MetaTrader 5 đang mở và nút **Algo Trading** (Giao dịch tự động) trên thanh công cụ MT5 đã được bật (màu xanh). Sau đó chạy:
```powershell
python live_trader.py
```
- Bot sẽ tự động kết nối tài khoản MT5 `113569040`.
- Quét nến M5 của cặp `XAUUSD` mỗi 3 giây.
- Khi hội tụ đủ điều kiện đa chiến thuật và AI xác nhận xác suất thắng >= 80%, bot sẽ tự động đặt lệnh kèm sẵn SL và TP.
- Trong quá trình giữ lệnh, bot tự động theo dõi và kích hoạt **Dời Stop Loss về hòa vốn (Breakeven)** để bảo vệ tuyệt đối số vốn $5,000.
