"""
Module tính toán chỉ báo kỹ thuật và tạo tín hiệu giao dịch đa chiến thuật
"""
import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán toàn diện các chỉ báo kỹ thuật:
    - EMA (20, 50, 200)
    - Bollinger Bands (20, 2)
    - RSI (7, 14)
    - ATR (14)
    - Stochastic Oscillator (14, 3, 3)
    - Price Action (Tỷ lệ râu nến, thân nến)
    """
    data = df.copy()
    
    # 1. Đường trung bình lũy thừa (EMA)
    data['ema_20'] = data['close'].ewm(span=20, adjust=False).mean()
    data['ema_50'] = data['close'].ewm(span=50, adjust=False).mean()
    data['ema_200'] = data['close'].ewm(span=200, adjust=False).mean()
    
    # Xu hướng xu hướng dài hạn
    data['trend_bullish'] = data['close'] > data['ema_200']
    data['trend_bearish'] = data['close'] < data['ema_200']
    
    # Khoảng cách tới EMA (chuẩn hóa theo giá)
    data['dist_ema_50'] = (data['close'] - data['ema_50']) / data['close']
    data['dist_ema_200'] = (data['close'] - data['ema_200']) / data['close']
    
    # 2. Dải Bollinger Bands (20, 2)
    sma_20 = data['close'].rolling(window=20).mean()
    std_20 = data['close'].rolling(window=20).std()
    data['bb_upper'] = sma_20 + (2.0 * std_20)
    data['bb_lower'] = sma_20 - (2.0 * std_20)
    data['bb_middle'] = sma_20
    data['bb_pct_b'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'] + 1e-6)
    data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / (data['bb_middle'] + 1e-6)
    
    # 3. Chỉ số sức mạnh tương đối RSI (14 & 7)
    for period in [7, 14]:
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-6)
        data[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
    # 4. Độ biến động trung bình ATR (14)
    high_low = data['high'] - data['low']
    high_close = (data['high'] - data['close'].shift()).abs()
    low_close = (data['low'] - data['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['atr_14'] = tr.rolling(window=14).mean()
    data['atr_ratio'] = data['atr_14'] / (data['close'] + 1e-6)
    
    # 5. Dao động Stochastic (%K, %D)
    low_14 = data['low'].rolling(window=14).min()
    high_14 = data['high'].rolling(window=14).max()
    data['stoch_k'] = 100 * ((data['close'] - low_14) / (high_14 - low_14 + 1e-6))
    data['stoch_d'] = data['stoch_k'].rolling(window=3).mean()
    
    # 6. Price Action Candlesticks
    candle_range = data['high'] - data['low'] + 1e-6
    data['body_size'] = (data['close'] - data['open']).abs()
    data['body_ratio'] = data['body_size'] / candle_range
    data['upper_wick'] = data['high'] - data[['close', 'open']].max(axis=1)
    data['lower_wick'] = data[['close', 'open']].min(axis=1) - data['low']
    data['upper_wick_ratio'] = data['upper_wick'] / candle_range
    data['lower_wick_ratio'] = data['lower_wick'] / candle_range
    
    # 7. Thời gian và phiên giao dịch
    if pd.api.types.is_datetime64_any_dtype(data['time']):
        data['hour'] = data['time'].dt.hour
        data['day_of_week'] = data['time'].dt.dayofweek
    else:
        time_col = pd.to_datetime(data['time'])
        data['hour'] = time_col.dt.hour
        data['day_of_week'] = time_col.dt.dayofweek
        
    # Lọc phiên an toàn (tránh giờ giao phiên 23h - 01h có spread giãn cao)
    data['is_safe_session'] = ~data['hour'].isin([22, 23, 0])
    
    # Tạo tín hiệu quy tắc gốc (Base Rule Signals):
    # Tín hiệu BUY:
    #   - Điều kiện 1 (Mean Reversion): Giá chạm đáy BB (%B < 0.15) & RSI_7 < 30 & có râu nến dưới từ chối giá (lower_wick_ratio > 0.3)
    #   - HOẶC Điều kiện 2 (Trend Pullback): Xu hướng tăng (Close > EMA200 & EMA20 > EMA50) & Giá hồi về gần EMA50 & RSI_14 vừa bật lên từ 35-50
    cond_buy_reversion = (data['bb_pct_b'] < 0.15) & (data['rsi_7'] < 30) & (data['lower_wick_ratio'] > 0.25)
    cond_buy_pullback = data['trend_bullish'] & (data['close'] >= data['ema_50'] * 0.998) & (data['close'] <= data['ema_50'] * 1.002) & (data['rsi_14'] > 40) & (data['rsi_14'] < 55)
    data['raw_signal_buy'] = (cond_buy_reversion | cond_buy_pullback) & data['is_safe_session']
    
    # Tín hiệu SELL:
    #   - Điều kiện 1 (Mean Reversion): Giá chạm đỉnh BB (%B > 0.85) & RSI_7 > 70 & có râu nến trên từ chối giá (upper_wick_ratio > 0.3)
    #   - HOẶC Điều kiện 2 (Trend Pullback): Xu hướng giảm (Close < EMA200 & EMA20 < EMA50) & Giá hồi về gần EMA50 & RSI_14 vừa chạm 50-65 rồi quay đầu
    cond_sell_reversion = (data['bb_pct_b'] > 0.85) & (data['rsi_7'] > 70) & (data['upper_wick_ratio'] > 0.25)
    cond_sell_pullback = data['trend_bearish'] & (data['close'] <= data['ema_50'] * 1.002) & (data['close'] >= data['ema_50'] * 0.998) & (data['rsi_14'] < 60) & (data['rsi_14'] > 45)
    data['raw_signal_sell'] = (cond_sell_reversion | cond_sell_pullback) & data['is_safe_session']
    
    return data.dropna().reset_index(drop=True)
