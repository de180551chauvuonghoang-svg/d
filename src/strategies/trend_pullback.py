"""
Trend-Pullback Scalping Strategy (EMA 20/50/200 Ribbon + Dynamic Retest)
"""
import pandas as pd
from src.core.interfaces import BaseStrategy
from src.indicators.technical import ema, rsi

class TrendPullbackStrategy(BaseStrategy):
    def __init__(self, ema_fast: int = 20, ema_med: int = 50, ema_slow: int = 200):
        super().__init__(name="TrendPullback_Scalper")
        self.ema_fast = ema_fast
        self.ema_med = ema_med
        self.ema_slow = ema_slow

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        e_fast = ema(data['close'], self.ema_fast)
        e_med = ema(data['close'], self.ema_med)
        e_slow = ema(data['close'], self.ema_slow)
        rsi_14 = rsi(data['close'], 14)
        
        bullish_trend = (data['close'] > e_slow) & (e_fast > e_med)
        bearish_trend = (data['close'] < e_slow) & (e_fast < e_med)
        
        # BUY: Xu hướng tăng, giá hồi test về dải EMA 50, RSI ở nhịp tích lũy 40 - 55
        buy_signal = bullish_trend & (data['close'] >= e_med * 0.998) & (data['close'] <= e_med * 1.002) & (rsi_14 > 40) & (rsi_14 < 55)
        
        # SELL: Xu hướng giảm, giá hồi test về dải EMA 50, RSI ở nhịp tích lũy 45 - 60
        sell_signal = bearish_trend & (data['close'] <= e_med * 1.002) & (data['close'] >= e_med * 0.998) & (rsi_14 > 45) & (rsi_14 < 60)
        
        data['tp_signal_buy'] = buy_signal
        data['tp_signal_sell'] = sell_signal
        return data
