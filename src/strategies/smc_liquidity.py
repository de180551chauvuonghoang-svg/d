"""
Smart Money Concepts (SMC) & Liquidity Sweep Scalping Strategy
Exploits institutional stop hunts, liquidity sweeps, and Fair Value Gaps (FVG) on Gold
"""
import pandas as pd
from src.core.interfaces import BaseStrategy
from src.indicators.technical import detect_liquidity_sweep, detect_fvg, rsi, candlestick_features

class SMCLiquidityStrategy(BaseStrategy):
    def __init__(self, sweep_lookback: int = 24):
        super().__init__(name="SMC_LiquiditySweep_Scalper")
        self.sweep_lookback = sweep_lookback

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        # 1. Phát hiện quét thanh khoản (Liquidity Sweep)
        bullish_sweep, bearish_sweep = detect_liquidity_sweep(
            data['high'], data['low'], data['close'], lookback=self.sweep_lookback
        )
        data['smc_bullish_sweep'] = bullish_sweep
        data['smc_bearish_sweep'] = bearish_sweep
        
        # 2. Phát hiện Fair Value Gap
        bull_fvg, bear_fvg = detect_fvg(data['high'], data['low'])
        data['smc_bull_fvg'] = bull_fvg
        data['smc_bear_fvg'] = bear_fvg
        
        # 3. Phân tích hình thái nến phản ứng
        _, upper_wick_ratio, lower_wick_ratio = candlestick_features(
            data['open'], data['high'], data['low'], data['close']
        )
        rsi_7 = rsi(data['close'], 7)
        
        # BUY SIGNAL: Quét đáy thanh khoản (Stop Hunt) + Râu nến dưới dài từ chối giá + RSI quá bán hồi phục
        buy_signal = (bullish_sweep == 1) & (lower_wick_ratio > 0.30) & (rsi_7 < 38)
        
        # SELL SIGNAL: Quét đỉnh thanh khoản + Râu nến trên dài từ chối giá + RSI quá mua quay đầu
        sell_signal = (bearish_sweep == 1) & (upper_wick_ratio > 0.30) & (rsi_7 > 62)
        
        data['smc_signal_buy'] = buy_signal
        data['smc_signal_sell'] = sell_signal
        return data
