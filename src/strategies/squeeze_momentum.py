"""
Volatility Squeeze & Momentum Breakout Strategy
Detects Bollinger Bands squeeze inside Keltner Channels followed by MACD momentum explosion
"""
import pandas as pd
from src.core.interfaces import BaseStrategy
from src.indicators.technical import (
    bollinger_bands, keltner_channel, macd, adx, ema
)

class SqueezeMomentumStrategy(BaseStrategy):
    def __init__(self, bb_period: int = 20, kc_period: int = 20):
        super().__init__(name="Squeeze_Momentum_Scalper")
        self.bb_period = bb_period
        self.kc_period = kc_period

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        bb_upper, _, bb_lower, _, _ = bollinger_bands(data['close'], self.bb_period, 2.0)
        kc_upper, _, kc_lower = keltner_channel(data['high'], data['low'], data['close'], self.kc_period, 1.5)
        
        # Squeeze On: Dải BB nằm lọt hoàn toàn bên trong dải Keltner (Tích lũy nén cực độ)
        squeeze_on = (bb_lower > kc_lower) & (bb_upper < kc_upper)
        # Squeeze Fired: Vừa thoát nén ở nến trước đó
        squeeze_fired = (squeeze_on.shift(1) == True) & (squeeze_on == False)
        
        _, _, macd_hist = macd(data['close'], 12, 26, 9)
        adx_val = adx(data['high'], data['low'], data['close'], 14)
        ema_trend = ema(data['close'], 200)
        
        # BUY: Vừa bung nén + MACD Hist dương và dốc lên + Giá trên EMA 200 + ADX > 20
        buy_signal = squeeze_fired & (macd_hist > 0) & (macd_hist > macd_hist.shift(1)) & (data['close'] > ema_trend) & (adx_val > 18)
        
        # SELL: Vừa bung nén + MACD Hist âm và dốc xuống + Giá dưới EMA 200 + ADX > 20
        sell_signal = squeeze_fired & (macd_hist < 0) & (macd_hist < macd_hist.shift(1)) & (data['close'] < ema_trend) & (adx_val > 18)
        
        data['sqz_signal_buy'] = buy_signal
        data['sqz_signal_sell'] = sell_signal
        return data
