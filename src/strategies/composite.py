"""
Composite Multi-Strategy Confluence Engine 2.0
Combines 4 complementary high-probability strategies:
1. Mean-Reversion Scalper (Bollinger + RSI Extreme)
2. Trend-Pullback Scalper (EMA Ribbon Dynamic Support/Resistance)
3. SMC Liquidity Sweep Scalper (Stop hunts & FVG imbalances)
4. Squeeze Momentum Scalper (Volatility compression breakout)
"""
import pandas as pd
import numpy as np
from typing import List
from src.core.interfaces import BaseStrategy
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.trend_pullback import TrendPullbackStrategy
from src.strategies.smc_liquidity import SMCLiquidityStrategy
from src.strategies.squeeze_momentum import SqueezeMomentumStrategy
from src.indicators.technical import (
    ema, bollinger_bands, rsi, atr, stochastic, candlestick_features,
    macd, keltner_channel, adx, detect_fvg, detect_liquidity_sweep
)

class CompositeScalperStrategy(BaseStrategy):
    def __init__(self, strategies: List[BaseStrategy] = None):
        super().__init__(name="Composite_AI_Confluence_4Engine")
        self.sub_strategies = strategies or [
            MeanReversionStrategy(),
            TrendPullbackStrategy(),
            SMCLiquidityStrategy(),
            SqueezeMomentumStrategy()
        ]

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        # 1. Đường trung bình động lũy thừa (EMA)
        data['ema_20'] = ema(data['close'], 20)
        data['ema_50'] = ema(data['close'], 50)
        data['ema_200'] = ema(data['close'], 200)
        
        data['trend_bullish'] = data['close'] > data['ema_200']
        data['trend_bearish'] = data['close'] < data['ema_200']
        data['dist_ema_50'] = (data['close'] - data['ema_50']) / data['close']
        data['dist_ema_200'] = (data['close'] - data['ema_200']) / data['close']
        
        # 2. Dải Bollinger Bands
        data['bb_upper'], data['bb_middle'], data['bb_lower'], data['bb_pct_b'], data['bb_width'] = bollinger_bands(data['close'])
        
        # 3. Keltner Channel & Squeeze
        kc_up, kc_mid, kc_low = keltner_channel(data['high'], data['low'], data['close'], 20, 1.5)
        data['kc_squeeze'] = ((data['bb_lower'] > kc_low) & (data['bb_upper'] < kc_up)).astype(int)
        
        # 4. Chỉ báo RSI đa chu kỳ
        data['rsi_7'] = rsi(data['close'], 7)
        data['rsi_14'] = rsi(data['close'], 14)
        
        # 5. ATR & ADX
        data['atr_14'] = atr(data['high'], data['low'], data['close'], 14)
        data['atr_ratio'] = data['atr_14'] / (data['close'] + 1e-6)
        data['adx_14'] = adx(data['high'], data['low'], data['close'], 14)
        
        # 6. MACD
        _, _, data['macd_hist'] = macd(data['close'], 12, 26, 9)
        data['macd_hist_ratio'] = data['macd_hist'] / (data['close'] + 1e-6)
        
        # 7. Dao động Stochastic
        data['stoch_k'], data['stoch_d'] = stochastic(data['high'], data['low'], data['close'])
        
        # 8. Price Action Candlesticks
        data['body_ratio'], data['upper_wick_ratio'], data['lower_wick_ratio'] = candlestick_features(
            data['open'], data['high'], data['low'], data['close']
        )
        
        # 9. Smart Money Concept (SMC) & Liquidity Sweeps
        bull_sw, bear_sw = detect_liquidity_sweep(data['high'], data['low'], data['close'], 24)
        data['liquidity_sweep_bull'] = bull_sw
        data['liquidity_sweep_bear'] = bear_sw
        
        # 10. Thời gian phiên giao dịch & Cyclical Encodings (Mã hóa chu kỳ giờ)
        if not pd.api.types.is_datetime64_any_dtype(data['time']):
            data['time'] = pd.to_datetime(data['time'])
        data['hour'] = data['time'].dt.hour
        data['day_of_week'] = data['time'].dt.dayofweek
        data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24.0)
        data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24.0)
        
        # Lọc phiên an toàn (tránh giờ giãn spread lúc 22h, 23h, 00h)
        data['is_safe_session'] = ~data['hour'].isin([22, 23, 0])
        
        # 11. Chạy từng chiến thuật thành phần
        for strat in self.sub_strategies:
            data = strat.generate_signals(data)
            
        # 12. Lọc bỏ cản tàu (Counter-Trend Filter) cho Mean Reversion:
        # Nếu thị trường có sóng mạnh (ADX > 20) và nến trên EMA200, TUYỆT ĐỐI KHÔNG SELL Mean Reversion
        if 'mr_signal_sell' in data.columns:
            data['mr_signal_sell'] = data['mr_signal_sell'] & ~(data['trend_bullish'] & (data['adx_14'] > 20))
        # Nếu thị trường có sóng giảm mạnh (ADX > 20) và nến dưới EMA200, TUYỆT ĐỐI KHÔNG BUY Mean Reversion
        if 'mr_signal_buy' in data.columns:
            data['mr_signal_buy'] = data['mr_signal_buy'] & ~(data['trend_bearish'] & (data['adx_14'] > 20))

        # 13. Hợp nhất các tín hiệu gốc
        signal_buy_cols = [c for c in ['mr_signal_buy', 'tp_signal_buy', 'smc_signal_buy', 'sqz_signal_buy'] if c in data.columns]
        signal_sell_cols = [c for c in ['mr_signal_sell', 'tp_signal_sell', 'smc_signal_sell', 'sqz_signal_sell'] if c in data.columns]
        
        raw_buy = data[signal_buy_cols].any(axis=1) if signal_buy_cols else pd.Series(False, index=data.index)
        raw_sell = data[signal_sell_cols].any(axis=1) if signal_sell_cols else pd.Series(False, index=data.index)
        
        data['raw_signal_buy'] = raw_buy & data['is_safe_session']
        data['raw_signal_sell'] = raw_sell & data['is_safe_session']
        
        return data.dropna().reset_index(drop=True)
