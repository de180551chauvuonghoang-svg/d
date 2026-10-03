"""
Mean-Reversion Scalping Strategy (Bollinger Bands + RSI Extremes + Candlestick Rejection)
"""
import pandas as pd
from src.core.interfaces import BaseStrategy
from src.indicators.technical import bollinger_bands, rsi, candlestick_features

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 7):
        super().__init__(name="MeanReversion_Scalper")
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        _, _, _, pct_b, width = bollinger_bands(data['close'], self.bb_period, self.bb_std)
        rsi_val = rsi(data['close'], self.rsi_period)
        _, upper_wick_ratio, lower_wick_ratio = candlestick_features(
            data['open'], data['high'], data['low'], data['close']
        )
        
        # BUY: Giá đè dưới dải BB (%B < 0.15), RSI quá bán (< 30) và có râu nến dưới từ chối giá (> 0.25)
        buy_signal = (pct_b < 0.15) & (rsi_val < 30) & (lower_wick_ratio > 0.25)
        
        # SELL: Giá vượt đỉnh dải BB (%B > 0.85), RSI quá mua (> 70) và có râu nến trên từ chối giá (> 0.25)
        sell_signal = (pct_b > 0.85) & (rsi_val > 70) & (upper_wick_ratio > 0.25)
        
        data['mr_signal_buy'] = buy_signal
        data['mr_signal_sell'] = sell_signal
        return data
