"""
Module tải và xử lý dữ liệu nến từ MetaTrader 5 cho XAUUSD
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from datetime import datetime
from config import config

def init_mt5(login: int = None, password: str = None, server: str = None, path: str = None):
    """Khởi tạo kết nối MT5 với thông tin đăng nhập"""
    login = login or config.LOGIN
    password = password or config.PASSWORD
    server = server or config.SERVER
    path = path or config.MT5_PATH
    
    if not mt5.initialize(path=path, login=login, password=password, server=server):
        err = mt5.last_error()
        # Thử khởi tạo không tham số nếu terminal đã mở sẵn
        if not mt5.initialize():
            raise RuntimeError(f"Không thể kết nối MT5. Lỗi: {err}")
    
    acc_info = mt5.account_info()
    if acc_info is None:
        raise RuntimeError(f"Không lấy được thông tin tài khoản MT5: {mt5.last_error()}")
    
    return acc_info

def fetch_historical_rates(symbol: str = None, count: int = 35000, timeframe=mt5.TIMEFRAME_M5, cache_file: str = "xauusd_m5.csv"):
    """
    Tải dữ liệu lịch sử nến từ MT5 hoặc đọc từ bộ nhớ cache
    """
    symbol = symbol or config.SYMBOL
    
    # Kiểm tra cache
    if os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file)
            df['time'] = pd.to_datetime(df['time'])
            if len(df) >= count * 0.8:
                print(f"[Data] Đã tải {len(df)} nến từ cache {cache_file}")
                return df
        except Exception:
            pass

    # Kết nối MT5 để tải dữ liệu mới nhất
    init_mt5()
    print(f"[MT5] Đang tải {count} nến {symbol} từ MT5...")
    
    # Kiểm tra symbol
    if not mt5.symbol_select(symbol, True):
        raise ValueError(f"Không tìm thấy hoặc không kích hoạt được cặp {symbol} trên MT5")
        
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Không lấy được dữ liệu nến: {mt5.last_error()}")
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Lưu cache
    df.to_csv(cache_file, index=False)
    print(f"[Data] Đã tải và lưu {len(df)} nến từ {df['time'].min()} đến {df['time'].max()}")
    return df

if __name__ == "__main__":
    df = fetch_historical_rates(count=1000)
    print(df.head())
