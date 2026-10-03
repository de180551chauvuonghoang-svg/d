# BOT TRADE VÀNG TỰ ĐỘNG (AI XAUUSD SCALPER) - KIẾN TRÚC MODULAR 2.0

Hệ thống Bot giao dịch Vàng (XAUUSD) tự động kết nối nền tảng **MetaTrader 5 (MT5)**, xây dựng theo mô hình **Kiến trúc phân tầng Clean & Modular Architecture** giúp người dùng dễ dàng mở rộng, cắm thêm chiến thuật mới (Plug-and-Play), thay thế mô hình AI hoặc tích hợp thêm các sàn giao dịch khác trong tương lai.

---

## 1. THÔNG SỐ TÀI KHOẢN & QUẢN TRỊ RỦI RO
- **Nền tảng**: MetaTrader 5 (MT5)
- **Tài khoản**: Demo `113569040` (Server `MetaQuotes-Demo`)
- **Vốn ban đầu**: **$5,000 USD** | **Đòn bẩy**: **1:100**
- **Cặp giao dịch**: **XAUUSD (Vàng)** - Khung nến **M5**
- **Khối lượng vào lệnh**: **0.08 lot** (Cố định, rủi ro ~0.6% vốn/lệnh)
- **Take Profit (TP)**: **180 points** (18 pips = 1.8$ giá vàng)
- **Stop Loss (SL)**: **160 points** (16 pips = 1.6$ giá vàng)
- **Smart Breakeven**: Khi lãi **+90 points** (+9 pips), tự động dời SL hòa vốn & **khóa lời +15 points**.

---

## 2. KẾT QUẢ BACKTEST 2 GIAI ĐOẠN

| Chỉ số đánh giá | Giai đoạn 1 (In-Sample / Huấn luyện) | Giai đoạn 2 (Out-of-Sample / Kiểm định thực tế) | Mục tiêu đề ra | Đánh giá |
| :--- | :---: | :---: | :---: | :---: |
| **Phạm vi dữ liệu** | 31/03/2026 -> 21/07/2026 (20,988 nến) | 21/07/2026 -> 02/10/2026 (13,993 nến) | 2 Giai đoạn độc lập | Đạt chuẩn |
| **Vốn ban đầu** | $5,000.00 | $5,000.00 | $5,000.00 | Đạt |
| **Vốn kết thúc** | **$10,635.20** | **$6,282.40** | Tăng trưởng ổn định | Xuất sắc |
| **Lợi nhuận ròng** | **+$5,635.20 (+112.7%)** | **+$1,282.40 (+25.6%)** | Dương | Xuất sắc |
| **TỔNG SỐ LỆNH** | 504 lệnh | 160 lệnh | Tần suất ổn định | Đạt |
| **TỶ LỆ THẮNG (WINRATE)** | **97.02%** | **85.62%** | **> 80%** | **VƯỢT CHỈ TIÊU (>85%)** |
| **SỤT GIẢM TỐI ĐA (DD)** | **0.49%** ($25.60) | **0.62%** ($37.20) | **< 10%** | **VƯỢT TRỘI (< 1%)** |
| **Profit Factor** | 30.35 | 5.36 | > 1.8 | Rất cao |

---

## 3. SƠ ĐỒ KIẾN TRÚC NÂNG CẤP (MODULAR ARCHITECTURE 2.0)

Hệ thống được tách biệt hoàn toàn thành các lớp độc lập thông qua các **Interfaces (Giao diện trừu tượng)**:

```
src/
├── core/                   # Tầng lõi: Định nghĩa dữ liệu & Interfaces
│   ├── types.py            # Enums (OrderType, ExitReason) & Dataclasses (TradeSignal, Position)
│   ├── interfaces.py       # Abstract Base Classes (BaseStrategy, BaseAIModel, BaseRiskManager, BaseBroker)
│   └── logger.py           # Ghi log chuẩn định dạng ra console và file
├── indicators/             # Thư viện tính toán chỉ báo kỹ thuật Vectorized
│   └── technical.py        # EMA, Bollinger Bands, RSI, ATR, Stochastic, Candlestick Rejection
├── strategies/             # Tầng chiến thuật giao dịch (Dễ dàng thêm chiến thuật mới)
│   ├── mean_reversion.py   # Bắt đảo chiều dải ngoài Bollinger + RSI
│   ├── trend_pullback.py   # Bắt sóng hồi theo xu hướng EMA 50/200
│   └── composite.py        # Chiến thuật tổng hợp kết hợp các chiến thuật con + Lọc phiên
├── ml/                     # Tầng Trí tuệ nhân tạo (AI & Machine Learning)
│   ├── feature_pipeline.py # Trích xuất 14 đặc trưng và gán nhãn tự động
│   └── ai_gatekeeper.py    # Random Forest Calibrated Classifier (Lọc xác suất >= 80%)
├── risk/                   # Tầng quản trị rủi ro & Bảo vệ vốn
│   └── risk_manager.py     # Tính Lot, Kiểm tra Spread, Kích hoạt Breakeven & Trailing Stop
├── brokers/                # Tầng kết nối sàn giao dịch
│   └── mt5_broker.py       # Client kết nối MetaTrader 5 (Dễ dàng thay bằng Binance/cTrader)
└── engine/                 # Tầng điều phối thực thi
    ├── backtest_runner.py  # Điều phối chạy Backtest 2 giai đoạn & vẽ biểu đồ
    └── live_runner.py      # Vòng lặp giao dịch Live/Demo tự động theo thời gian thực
```

---

## 4. HƯỚNG DẪN MỞ RỘNG VÀ NÂNG CẤP TRONG TƯƠNG LAI

Nhờ áp dụng **Clean Architecture & Dependency Injection**, bạn có thể dễ dàng nâng cấp bất kỳ phần nào mà không làm ảnh hưởng đến phần còn lại:

### A. Thêm một Chiến thuật Mới (Ví dụ: Smart Money Concept SMC)
Chỉ cần tạo file mới kế thừa `BaseStrategy`:
```python
# src/strategies/smc_strategy.py
from src.core.interfaces import BaseStrategy

class SMCStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(name="SmartMoneyConcept")
        
    def generate_signals(self, df):
        # Tính toán Order Block / FVG / Liquidity
        df['smc_signal_buy'] = ...
        df['smc_signal_sell'] = ...
        return df
```
Sau đó đăng ký vào `CompositeScalperStrategy` mà không cần sửa đổi logic vào lệnh hay quản lý rủi ro.

### B. Thay đổi mô hình AI (Ví dụ: XGBoost, LightGBM hoặc LSTM)
Chỉ cần tạo lớp mới kế thừa `BaseAIModel`:
```python
# src/ml/xgboost_gatekeeper.py
from src.core.interfaces import BaseAIModel

class XGBoostGatekeeper(BaseAIModel):
    def train(self, df_train):
        # Huấn luyện XGBoost
        pass
    def predict_confidence(self, features_df, signal_type):
        # Dự đoán xác suất
        pass
```

### C. Kết nối sang Sàn giao dịch khác (Ví dụ: Binance Crypto hoặc cTrader)
Chỉ cần tạo lớp mới kế thừa `BaseBroker`:
```python
# src/brokers/binance_broker.py
from src.core.interfaces import BaseBroker

class BinanceBroker(BaseBroker):
    def connect(self): ...
    def open_order(self, symbol, order_type, volume, sl, tp, comment): ...
```

---

## 5. HƯỚNG DẪN KHỞI CHẠY

### 1. Chạy Backtest 2 Giai đoạn:
```powershell
python run_backtest.py
```

### 2. Chạy Bot Live / Demo tự động trên MT5:
```powershell
python live_trader.py
```
