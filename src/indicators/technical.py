"""
Vectorized Technical Indicators Library
"""
import pandas as pd
import numpy as np

def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    """Bollinger Bands (Upper, Middle, Lower, %B, BandWidth)"""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + (num_std * std)
    lower = middle - (num_std * std)
    pct_b = (series - lower) / (upper - lower + 1e-6)
    width = (upper - lower) / (middle + 1e-6)
    return upper, middle, lower, pct_b, width

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-6)
    return 100 - (100 / (1 + rs))

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range"""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    """Stochastic Oscillator %K, %D"""
    low_min = low.rolling(window=k_period).min()
    high_max = high.rolling(window=k_period).max()
    k = 100 * ((close - low_min) / (high_max - low_min + 1e-6))
    d = k.rolling(window=d_period).mean()
    return k, d

def candlestick_features(open_p: pd.Series, high_p: pd.Series, low_p: pd.Series, close_p: pd.Series):
    """Trích xuất hình thái nến (Thân nến, Râu trên, Râu dưới)"""
    candle_range = high_p - low_p + 1e-6
    body_size = (close_p - open_p).abs()
    body_ratio = body_size / candle_range
    
    max_body = pd.concat([open_p, close_p], axis=1).max(axis=1)
    min_body = pd.concat([open_p, close_p], axis=1).min(axis=1)
    
    upper_wick = high_p - max_body
    lower_wick = min_body - low_p
    
    upper_wick_ratio = upper_wick / candle_range
    lower_wick_ratio = lower_wick / candle_range
    return body_ratio, upper_wick_ratio, lower_wick_ratio

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD Line, Signal Line, and Histogram"""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def keltner_channel(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20, multiplier: float = 1.5):
    """Keltner Channel (Upper, Middle, Lower)"""
    middle = ema(close, period)
    atr_val = atr(high, low, close, period)
    upper = middle + (multiplier * atr_val)
    lower = middle - (multiplier * atr_val)
    return upper, middle, lower

def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index (ADX) measuring trend strength"""
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)
    
    tr_val = atr(high, low, close, period) + 1e-6
    plus_di = 100 * (pd.Series(plus_dm, index=close.index).ewm(alpha=1/period).mean() / tr_val)
    minus_di = 100 * (pd.Series(minus_dm, index=close.index).ewm(alpha=1/period).mean() / tr_val)
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-6))
    return dx.ewm(alpha=1/period).mean()

def detect_fvg(high: pd.Series, low: pd.Series):
    """
    Phát hiện Fair Value Gap (Khoảng trống giá FVG 3 nến):
    - Bullish FVG: Low nến [i] > High nến [i-2]
    - Bearish FVG: High nến [i] < Low nến [i-2]
    """
    bullish_fvg = (low > high.shift(2)).astype(int)
    bearish_fvg = (high < low.shift(2)).astype(int)
    return bullish_fvg, bearish_fvg

def detect_liquidity_sweep(high: pd.Series, low: pd.Series, close: pd.Series, lookback: int = 20):
    """
    Quét thanh khoản (Liquidity Sweep):
    - Quét đỉnh (Bearish sweep): High vượt đỉnh [lookback] nến trước nhưng Close đóng cửa tụt lại bên dưới
    - Quét đáy (Bullish sweep): Low phá đáy [lookback] nến trước nhưng Close rút chân đóng cửa lên trên
    """
    prev_high = high.shift(1).rolling(window=lookback).max()
    prev_low = low.shift(1).rolling(window=lookback).min()
    
    bullish_sweep = (low < prev_low) & (close > prev_low)
    bearish_sweep = (high > prev_high) & (close < prev_high)
    return bullish_sweep.astype(int), bearish_sweep.astype(int)
