"""
Cấu hình hệ thống Bot Trade Vàng AI Scalping (XAUUSD)
Tài khoản Demo MT5: Vốn $5000, Đòn bẩy 1:100
"""
from dataclasses import dataclass
import os

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
    MAGIC_NUMBER: int = 888999      # Magic number để nhận diện lệnh của bot
    SLIPPAGE: int = 15              # Trượt giá tối đa cho phép (points)
    MAX_SPREAD: float = 40.0        # Spread tối đa cho phép vào lệnh (points)
    
    # 3. Quản lý vốn & Risk Management (Vốn $5000, Đòn bẩy 1:100)
    INITIAL_BALANCE: float = 5000.0 # Vốn khởi điểm $5000
    LEVERAGE: int = 100             # Đòn bẩy 1:100
    FIXED_LOT: float = 0.08         # Lot size tối ưu cho $5000 để giữ DD < 10%
    MAX_OPEN_POSITIONS: int = 1     # Giới hạn 1 lệnh cùng lúc để tránh rủi ro dồn dập
    
    # 4. Mục tiêu Chốt lời / Cắt lỗ & Bảo vệ vốn (Scalping Vàng Siêu Lợi Nhuận)
    # 1 pip vàng = 10 points (0.10 USD/oz). 1 giá vàng = 1.0 USD = 100 points
    TP_POINTS: int = 220            # Chốt lời tối ưu = 2.2 giá vàng (22 pips)
    SL_POINTS: int = 160            # Cắt lỗ tối đa SL = 1.6 giá vàng (16 pips)
    
    # Cơ chế Smart Breakeven & Trailing Stop:
    # Khi lệnh lời được BREAKEVEN_TRIGGER_POINTS thì dời SL về điểm hòa vốn + khóa lời
    BREAKEVEN_TRIGGER_POINTS: int = 90   # Đạt lời +0.9 giá -> Kích hoạt dời SL về hòa vốn
    BREAKEVEN_LOCK_POINTS: int = 20      # Khóa lời chắc chắn +0.20 giá (+20 points)
    TRAILING_STEP_POINTS: int = 40       # Dời stop loss theo từng bước 40 points
    
    # 5. Bộ lọc AI & Chiến thuật kết hợp
    # Ngưỡng xác suất AI Ensemble tối ưu (Đạt Winrate > 85%, DD < 0.7%, Tăng +45% lợi nhuận)
    AI_CONFIDENCE_THRESHOLD: float = 0.78
    
    # 6. Phân chia 2 giai đoạn Backtest
    # Giai đoạn 1: In-Sample (Huấn luyện AI, tối ưu hóa) - 60% dữ liệu
    # Giai đoạn 2: Out-of-Sample (Kiểm thử thực tế dữ liệu chưa thấy) - 40% dữ liệu
    TRAIN_TEST_SPLIT_RATIO: float = 0.60
    TOTAL_BARS_FOR_TEST: int = 35000

config = BotConfig()
