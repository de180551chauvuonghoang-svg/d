"""
Cấu hình hệ thống Bot Trade Vàng AI Scalping (XAUUSD) - Version 2 Multi-Target
Tài khoản Demo MT5: Vốn $5000, Đòn bẩy 1:100
"""
from dataclasses import dataclass

@dataclass
class BotConfig:
    # 1. Cấu hình kết nối MT5
    MT5_PATH: str = r"D:\metatradexau\terminal64.exe"
    LOGIN: int = 113569040
    PASSWORD: str = "@oO5WwLm"
    SERVER: str = "MetaQuotes-Demo"
    
    # 2. Thông số cặp giao dịch
    SYMBOL: str = "XAUUSD"
    TIMEFRAME: str = "M5"           # Khung thời gian scalping chính: M5
    MAGIC_NUMBER: int = 888999      # Magic number nhận diện lệnh của bot
    SLIPPAGE: int = 15              # Trượt giá tối đa cho phép (points)
    MAX_SPREAD: float = 40.0        # Spread tối đa cho phép vào lệnh (points)
    
    # 3. Quản lý vốn & Risk Management (Vốn $5000, Đòn bẩy 1:100)
    INITIAL_BALANCE: float = 5000.0 # Vốn khởi điểm $5000
    LEVERAGE: int = 100             # Đòn bẩy 1:100
    FIXED_LOT: float = 0.20         # Tổng lot 0.20 cho vốn $5,000 (DD cực nhỏ ~1.7%, dưới xa trần 10%)
    MAX_OPEN_POSITIONS: int = 3     # Cho phép tối đa 3 lệnh con cùng 1 cụm tín hiệu
    
    # 4. Phương Pháp Chia 3 Lệnh Đa Mục Tiêu (3-Tier Multi-Target Scale-Out)
    # Tổng 3 lệnh = 0.08 + 0.07 + 0.05 = 0.20 lot
    ENABLE_MULTI_TIER: bool = True
    TIER1_LOT: float = 0.08         # Lệnh 1: Scalp nhanh (R:R 1:1) - TP +1.8 giá mang về +$14.40 USD
    TIER1_TP_POINTS: int = 180      # Chốt lời +1.8 giá (18 pips)
    
    TIER2_LOT: float = 0.07         # Lệnh 2: Scalp tiêu chuẩn (R:R 1:1.5) - TP +3.0 giá mang về +$21.00 USD
    TIER2_TP_POINTS: int = 300      # Chốt lời +3.0 giá (30 pips)
    
    TIER3_LOT: float = 0.05         # Lệnh 3: Runner theo trend (R:R 1:2.25) - TP +4.5 giá mang về +$22.50 USD
    TIER3_TP_POINTS: int = 450      # Chốt lời +4.5 giá (45 pips)
    
    # Stop Loss ban đầu cho cả 3 lệnh: Đủ rộng để thoát nhiễu nến M5 & Spread
    SL_POINTS: int = 200            # Cắt lỗ SL = 2.0 giá vàng (20 pips) - Rủi ro tối đa chỉ -$40 USD (0.8% vốn)
    
    # Cơ chế Smart Breakeven & Trailing Stop:
    # Khi giá chạy được +1.2 giá (+120 pts), dời SL về điểm hòa vốn + khóa chắc chắn +30 pts để bao trọn spread
    BREAKEVEN_TRIGGER_POINTS: int = 120   # Đạt lời +1.2 giá -> Dời SL hòa vốn
    BREAKEVEN_LOCK_POINTS: int = 30       # Khóa lời chắc chắn +0.30 giá (+30 points)
    TRAILING_STEP_POINTS: int = 40        # Dời stop loss theo từng bước 40 points
    
    # 5. Bộ lọc AI Ensemble & Tần suất lệnh
    # Ngưỡng 0.780: Đạt tỷ suất vàng (Lợi nhuận ~+98.4%, Winrate 87.6%, Max DD chỉ 1.72%)
    AI_CONFIDENCE_THRESHOLD: float = 0.780
    
    # 6. Phân chia 2 giai đoạn Backtest
    TRAIN_TEST_SPLIT_RATIO: float = 0.60
    TOTAL_BARS_FOR_TEST: int = 35000

config = BotConfig()
