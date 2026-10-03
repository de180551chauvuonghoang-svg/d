"""
Composite Multi-Strategy Engine
Combines multiple sub-strategies and adds session volatility filters
"""
import pandas as pd
from typing import List
from src.core.interfaces import BaseStrategy
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.trend_pullback import TrendPullbackStrategy
from src.indicators.technical import (
    ema, bollinger_bands, rsi, atr, stochastic, candlestick_features
)

class CompositeScalperStrategy(BaseStrategy):
    """
    Chiến thuật tổng hợp: Kết hợp nhiều chiến thuật thành viên + Lọc phiên an toàn
    """
    def __init__(self, strategies: List[BaseStrategy] = None):
        super().__init__(name="Composite_AI_Scalper")
        self.sub_strategies = strategies or [
            MeanReversionStrategy(),
            TrendPullbackStrategy()
        ]

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        # 1. Tính toán tất cả các chỉ số nền tảng (Base Indicators)
        data['ema_20'] = ema(data['close'], 20)
        data['ema_50'] = ema(data['close'], 50)
        data['ema_200'] = ema(data['close'], 200)
        
        data['trend_bullish'] = data['close'] > data['ema_200']
        data['trend_bearish'] = data['close'] < data['ema_200']
        data['dist_ema_50'] = (data['close'] - data['ema_50']) / data['close']
        data['dist_ema_200'] = (data['close'] - data['ema_200']) / data['close']
        
        data['bb_upper'], data['bb_middle'], data['bb_lower'], data['bb_pct_b'], data['bb_width'] = bollinger_bands(data['close'])
        data['rsi_7'] = rsi(data['close'], 7)
        data['rsi_14'] = rsi(data['close'], 14)
        
        data['atr_14'] = atr(data['high'], data['low'], data['close'], 14)
        data['atr_ratio'] = data['atr_14'] / (data['close'] + 1e-6)
        
        data['stoch_k'], data['stoch_d'] = stochastic(data['high'], data['low'], data['close'])
        data['body_ratio'], data['upper_wick_ratio'], data['lower_wick_ratio'] = candlestick_features(
            data['open'], data['high'], data['low'], data['close']
        )
        
        # 2. Lọc thời gian phiên giao dịch an toàn
        if not pd.api.types.is_datetime64_any_dtype(data['time']):
            data['time'] = pd.to_datetime(data['time'])
        data['hour'] = data['time'].dt.hour
        data['day_of_week'] = data['time'].dt.dayofweek
        data['is_safe_session'] = ~data['hour'].isin([22, 23, 0])
        
        # 3. Chạy từng chiến thuật thành phần
        for strat in self.sub_strategies:
            data = strat.generate_signals(data)
            
        # 4. Hợp nhất tín hiệu thô (Raw Signal Confluence)
        raw_buy = False
        raw_sell = False
        
        if 'mr_signal_buy' in data.columns and 'tp_signal_buy' in data.columns:
            raw_buy = data['mr_signal_buy'] | data['tp_signal_buy']
            raw_sell = data['mr_signal_sell'] | data['tp_signal_sell']
            
        data['raw_signal_buy'] = raw_buy & data['is_safe_session']
        data['raw_signal_sell'] = raw_sell & data['is_safe_session']
        
        return data.dropna().reset_index(drop=True)
