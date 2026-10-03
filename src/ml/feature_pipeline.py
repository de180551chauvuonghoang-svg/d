"""
ML Feature Pipeline and Labeling Engine
"""
import pandas as pd
import numpy as np
from typing import List
from config import config

DEFAULT_FEATURES: List[str] = [
    'bb_pct_b', 'bb_width',
    'rsi_7', 'rsi_14',
    'dist_ema_50', 'dist_ema_200',
    'stoch_k', 'stoch_d',
    'atr_ratio',
    'body_ratio', 'upper_wick_ratio', 'lower_wick_ratio',
    'hour', 'day_of_week'
]

def generate_training_labels(
    df: pd.DataFrame,
    tp_points: int = None,
    sl_points: int = None,
    be_trigger_points: int = None,
    max_holding_bars: int = 48
) -> pd.DataFrame:
    """
    Tạo nhãn giám sát (Supervised Target Labels):
    - 1: Giao dịch thành công (chạm TP hoặc kích hoạt Breakeven có lãi)
    - 0: Giao dịch thất bại (dính SL)
    """
    tp_val = (tp_points or config.TP_POINTS) * 0.01
    sl_val = (sl_points or config.SL_POINTS) * 0.01
    be_val = (be_trigger_points or config.BREAKEVEN_TRIGGER_POINTS) * 0.01
    
    data = df.copy()
    data['label_buy'] = np.nan
    data['label_sell'] = np.nan
    
    close_vals = data['close'].values
    high_vals = data['high'].values
    low_vals = data['low'].values
    n = len(data)
    
    for i in range(n - max_holding_bars):
        entry_price = close_vals[i]
        
        # BUY LABELING
        if data['raw_signal_buy'].iloc[i]:
            hit_tp = False
            hit_sl = False
            hit_be = False
            
            for j in range(i + 1, min(i + max_holding_bars, n)):
                curr_high = high_vals[j]
                curr_low = low_vals[j]
                
                if curr_high >= entry_price + be_val:
                    hit_be = True
                if curr_high >= entry_price + tp_val:
                    hit_tp = True
                    break
                    
                curr_sl = entry_price if hit_be else (entry_price - sl_val)
                if curr_low <= curr_sl:
                    if hit_be:
                        hit_tp = True
                    else:
                        hit_sl = True
                    break
                    
            if hit_tp:
                data.at[i, 'label_buy'] = 1
            elif hit_sl:
                data.at[i, 'label_buy'] = 0
                
        # SELL LABELING
        if data['raw_signal_sell'].iloc[i]:
            hit_tp = False
            hit_sl = False
            hit_be = False
            
            for j in range(i + 1, min(i + max_holding_bars, n)):
                curr_high = high_vals[j]
                curr_low = low_vals[j]
                
                if curr_low <= entry_price - be_val:
                    hit_be = True
                if curr_low <= entry_price - tp_val:
                    hit_tp = True
                    break
                    
                curr_sl = entry_price if hit_be else (entry_price + sl_val)
                if curr_high >= curr_sl:
                    if hit_be:
                        hit_tp = True
                    else:
                        hit_sl = True
                    break
                    
            if hit_tp:
                data.at[i, 'label_sell'] = 1
            elif hit_sl:
                data.at[i, 'label_sell'] = 0
                
    return data
