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
