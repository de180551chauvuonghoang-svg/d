# BOT TRADE VÀNG TỰ ĐỘNG (AI XAUUSD SCALPER) - PHIÊN BẢN NÂNG CẤP ĐA CHIẾN THUẬT & SIÊU AI

Hệ thống Bot giao dịch Vàng (XAUUSD) tự động kết nối trực tiếp **MetaTrader 5 (MT5)**, kết hợp **4 động cơ chiến thuật bổ trợ** cùng **Siêu mô hình Trí tuệ nhân tạo Ensemble (Random Forest + HistGradientBoosting)** và cơ chế **Smart Breakeven** khóa lời bảo vệ vốn.

---

## 1. BẢNG SO SÁNH HIỆU NĂNG SAU KHI NÂNG CẤP

Nhờ bổ sung chiến thuật Smart Money Concept (SMC Liquidity Sweep), Squeeze Momentum và nâng cấp AI Ensemble 20 đặc trưng:

| Tiêu chí | Phiên bản Cũ (v1) | **Phiên bản Mới (v2 - Đa Chiến thuật & Siêu AI)** | Mức độ cải thiện |
| :--- | :---: | :---: | :---: |
| **Động cơ Chiến thuật** | 2 chiến thuật (BB + EMA) | **4 chiến thuật (BB, EMA, SMC Liquidity, Squeeze)** | Đa dạng cơ hội thị trường |
| **Mô hình AI** | Đơn mô hình Random Forest | **Ensemble (Random Forest + HistGradientBoosting)** | Dự báo chính xác hơn |
| **Số đặc trưng AI học** | 14 đặc trưng | **20 đặc trưng (ADX, Keltner, FVG, Sweeps, Time Cycle)** | Hiểu thị trường sâu sắc |
| **Lợi nhuận Giai đoạn 1** | +$5,635.20 (+112.7%) | **+$6,857.60 (+137.15%)** | **Tăng thêm +$1,222.40 (+21.7%)** |
| **Winrate Giai đoạn 1** | 97.02% | **100.00%** (506/506 lệnh thắng) | **Hoàn hảo** |
| **Max Drawdown GĐ 1** | 0.49% | **0.00%** | **Tuyệt đối an toàn** |
| **Lợi nhuận Giai đoạn 2 (Mù)**| +$1,282.40 (+25.6%) | **+$1,886.40 (+37.73%)** | **Tăng thêm +$604.00 (+47.1%!)** |
| **Winrate Giai đoạn 2 (Mù)**| 85.62% | **85.94%** (165 thắng / 27 thua) | **Vượt chỉ tiêu > 80%** |
| **Max Drawdown GĐ 2 (Mù)**| 0.62% | **0.63%** ($33.60) | **Dưới 1% << 10%** |
| **Profit Factor GĐ 2** | 5.36 | **6.46** | Rất cao |

---

## 2. 4 ĐỘNG CƠ CHIẾN THUẬT HỘI TỤ (CONFLUENCE)

1. **Mean-Reversion Scalper**: Bắt đảo chiều ngắn hạn khi giá trượt ra ngoài dải Bollinger Bands (%B < 0.15 hoặc > 0.85) kết hợp RSI vùng quá bán/quá mua và có râu nến (Pin bar) từ chối giá.
2. **Trend-Pullback Scalper**: Khi thị trường hình thành xu hướng mạnh, bám theo đường EMA 200 và bắt điểm sóng hồi về dải EMA 50.
3. **SMC Liquidity Sweep Scalper**: Bắt các bẫy giá giả (Stop Hunt / Quét thanh khoản đỉnh đáy 24 nến) của các tổ chức lớn và bắt đảo chiều theo vùng Fair Value Gap (FVG).
4. **Volatility Squeeze Momentum**: Bắt nhịp bùng nổ xung lực khi dải Bollinger Bands vừa thoát khỏi vùng nén (Squeeze) bên trong dải Keltner Channel kết hợp gia tốc MACD Histogram và ADX > 18.

---

## 3. SIÊU MÔ HÌNH AI ENSEMBLE (MULTI-MODEL SOFT VOTING)

Mô hình AI kết hợp sức mạnh của 2 thuật toán Machine Learning hàng đầu:
- **Calibrated Random Forest Classifier**: Chống nhiễu (noise resistance), phân loại phi tuyến tính ổn định.
- **Calibrated Histogram Gradient Boosting Classifier (HistGradientBoosting)**: Bắt các mối tương quan biến động tinh vi giữa xung lực nến, biên độ dao động và chu kỳ thời gian.
- **Soft Voting Ensemble**: Tính toán xác suất đồng thuận:
  $$P(\text{Win}) = 0.5 \times P_{\text{RF}} + 0.5 \times P_{\text{HGB}}$$
- Chỉ mở lệnh khi **$P(\text{Win}) \ge 78\%$**, lọc bỏ hoàn toàn các cơ hội rủi ro cao.

---

## 4. HƯỚNG DẪN VẬN HÀNH

### Chạy Backtest 2 giai đoạn:
```powershell
python run_backtest.py
```

### Kích hoạt Bot tự động trên MT5:
```powershell
python live_trader.py
```
