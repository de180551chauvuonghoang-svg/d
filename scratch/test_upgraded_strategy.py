import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import numpy as np
from src.indicators.technical import (
    ema, bollinger_bands, keltner_channel, rsi, atr, adx, macd,
    stochastic, candlestick_features, detect_liquidity_sweep, detect_fvg
)

# 1. Load data
df = pd.read_csv('xauusd_m5_3months.csv')
if not pd.api.types.is_datetime64_any_dtype(df['time']):
    df['time'] = pd.to_datetime(df['time'])

# 2. Calculate indicators
data = df.copy()
data['ema_20'] = ema(data['close'], 20)
data['ema_50'] = ema(data['close'], 50)
data['ema_200'] = ema(data['close'], 200)

data['bb_upper'], data['bb_mid'], data['bb_lower'], data['bb_pct_b'], data['bb_width'] = bollinger_bands(data['close'], 20, 2.0)
kc_up, _, kc_low = keltner_channel(data['high'], data['low'], data['close'], 20, 1.5)
data['kc_squeeze'] = ((data['bb_lower'] > kc_low) & (data['bb_upper'] < kc_up)).astype(int)
squeeze_fired = (data['kc_squeeze'].shift(1) == 1) & (data['kc_squeeze'] == 0)

data['rsi_7'] = rsi(data['close'], 7)
data['rsi_14'] = rsi(data['close'], 14)
data['atr_14'] = atr(data['high'], data['low'], data['close'], 14)
data['adx_14'] = adx(data['high'], data['low'], data['close'], 14)
_, _, data['macd_hist'] = macd(data['close'], 12, 26, 9)

_, upper_wick, lower_wick = candlestick_features(data['open'], data['high'], data['low'], data['close'])
bull_sw, bear_sw = detect_liquidity_sweep(data['high'], data['low'], data['close'], 24)

data['hour'] = data['time'].dt.hour
is_safe_session = ~data['hour'].isin([22, 23, 0])

# Sub-signals
tp_buy = (data['close'] > data['ema_200']) & (data['ema_20'] > data['ema_50']) & (data['close'] >= data['ema_50'] * 0.998) & (data['close'] <= data['ema_50'] * 1.002) & (data['rsi_14'] > 40) & (data['rsi_14'] < 55)
tp_sell = (data['close'] < data['ema_200']) & (data['ema_20'] < data['ema_50']) & (data['close'] <= data['ema_50'] * 1.002) & (data['close'] >= data['ema_50'] * 0.998) & (data['rsi_14'] > 45) & (data['rsi_14'] < 60)

smc_buy = (bull_sw == 1) & (lower_wick > 0.25) & (data['rsi_7'] < 38)
smc_sell = (bear_sw == 1) & (upper_wick > 0.25) & (data['rsi_7'] > 62)

sqz_buy = squeeze_fired & (data['macd_hist'] > 0) & (data['macd_hist'] > data['macd_hist'].shift(1)) & (data['close'] > data['ema_200']) & (data['adx_14'] > 18)
sqz_sell = squeeze_fired & (data['macd_hist'] < 0) & (data['macd_hist'] < data['macd_hist'].shift(1)) & (data['close'] < data['ema_200']) & (data['adx_14'] > 18)

mr_buy = (data['bb_pct_b'] < 0.15) & (data['rsi_7'] < 30) & (lower_wick > 0.25)
mr_sell = (data['bb_pct_b'] > 0.85) & (data['rsi_7'] > 70) & (upper_wick > 0.25)

# Trend alignment
bullish_trend = (data['close'] > data['ema_200']) & (data['ema_50'] > data['ema_200'])
bearish_trend = (data['close'] < data['ema_200']) & (data['ema_50'] < data['ema_200'])
is_trending = data['adx_14'] > 22

# UPGRADED CONFLUENCE LOGIC:
# NEVER counter-trend!
signal_buy = is_safe_session & (
    (bullish_trend & (tp_buy | sqz_buy)) |
    (smc_buy & (data['close'] > data['ema_50'])) |
    (~is_trending & ~bearish_trend & mr_buy)
)

signal_sell = is_safe_session & (
    (bearish_trend & (tp_sell | sqz_sell)) |
    (smc_sell & (data['close'] < data['ema_50'])) |
    (~is_trending & ~bullish_trend & mr_sell)
)

data['signal_buy'] = signal_buy
data['signal_sell'] = signal_sell

print(f"Total BUY signals: {signal_buy.sum()}, Total SELL signals: {signal_sell.sum()}")

# 3. Simulate Trades with realistic parameters
# SL = 3.50 USD (35 pips), TP1 = 3.50 (0.03 lot), TP2 = 5.50 (0.03 lot), TP3 = 8.50 (0.02 lot)
# BE trigger = 2.50 USD, BE lock = 0.50 USD, Spread = 0.25 USD
sl_dist = 3.50
tp1_dist = 3.50
tp2_dist = 5.50
tp3_dist = 8.50
be_trigger = 2.50
be_lock = 0.50
spread = 0.25

balance = 5000.0
peak_balance = 5000.0
max_dd = 0.0

active_trades = []
closed_trades = []

start_date = pd.Timestamp("2026-07-05")
test_data = data[data['time'] >= start_date].copy().reset_index(drop=True)

for i in range(len(test_data)):
    bar = test_data.iloc[i]
    c_time = bar['time']
    c_high = bar['high']
    c_low = bar['low']
    
    # Manage active trades
    rem = []
    # Group check for breakeven
    for t in active_trades:
        if not t['be_active']:
            if t['type'] == 'BUY' and (c_high >= t['entry'] + be_trigger):
                t['be_active'] = True
                t['sl'] = t['entry'] + be_lock
            elif t['type'] == 'SELL' and (c_low <= t['entry'] - be_trigger):
                t['be_active'] = True
                t['sl'] = t['entry'] - be_lock
                
        # Check TP / SL
        closed = False
        if t['type'] == 'BUY':
            if c_high >= t['tp']:
                pnl = (t['tp'] - t['entry'] - spread) * t['lot'] * 100
                balance += pnl
                t['profit'] = pnl
                t['reason'] = 'TP'
                t['exit_time'] = c_time
                closed_trades.append(t)
                closed = True
            elif c_low <= t['sl']:
                pnl = (t['sl'] - t['entry'] - spread) * t['lot'] * 100
                balance += pnl
                t['profit'] = pnl
                t['reason'] = 'BE' if t['be_active'] else 'SL'
                t['exit_time'] = c_time
                closed_trades.append(t)
                closed = True
        else: # SELL
            if c_low <= t['tp']:
                pnl = (t['entry'] - t['tp'] - spread) * t['lot'] * 100
                balance += pnl
                t['profit'] = pnl
                t['reason'] = 'TP'
                t['exit_time'] = c_time
                closed_trades.append(t)
                closed = True
            elif c_high >= t['sl']:
                pnl = (t['entry'] - t['sl'] - spread) * t['lot'] * 100
                balance += pnl
                t['profit'] = pnl
                t['reason'] = 'BE' if t['be_active'] else 'SL'
                t['exit_time'] = c_time
                closed_trades.append(t)
                closed = True
                
        if not closed:
            rem.append(t)
            
    active_trades = rem
    if balance > peak_balance:
        peak_balance = balance
    dd = (peak_balance - balance) / peak_balance * 100
    if dd > max_dd:
        max_dd = dd
        
    # Open new trade
    if len(active_trades) == 0 and i < len(test_data) - 1:
        if bar['signal_buy']:
            entry_p = bar['close'] + spread
            active_trades.extend([
                {'type': 'BUY', 'lot': 0.03, 'entry': entry_p, 'sl': entry_p - sl_dist, 'tp': entry_p + tp1_dist, 'be_active': False, 'tier': 'T1', 'entry_time': c_time},
                {'type': 'BUY', 'lot': 0.03, 'entry': entry_p, 'sl': entry_p - sl_dist, 'tp': entry_p + tp2_dist, 'be_active': False, 'tier': 'T2', 'entry_time': c_time},
                {'type': 'BUY', 'lot': 0.02, 'entry': entry_p, 'sl': entry_p - sl_dist, 'tp': entry_p + tp3_dist, 'be_active': False, 'tier': 'T3', 'entry_time': c_time},
            ])
        elif bar['signal_sell']:
            entry_p = bar['close']
            active_trades.extend([
                {'type': 'SELL', 'lot': 0.03, 'entry': entry_p, 'sl': entry_p + sl_dist, 'tp': entry_p - tp1_dist, 'be_active': False, 'tier': 'T1', 'entry_time': c_time},
                {'type': 'SELL', 'lot': 0.03, 'entry': entry_p, 'sl': entry_p + sl_dist, 'tp': entry_p - tp2_dist, 'be_active': False, 'tier': 'T2', 'entry_time': c_time},
                {'type': 'SELL', 'lot': 0.02, 'entry': entry_p, 'sl': entry_p - sl_dist, 'tp': entry_p - tp3_dist, 'be_active': False, 'tier': 'T3', 'entry_time': c_time},
            ])

df_res = pd.DataFrame(closed_trades)
if len(df_res) > 0:
    wins = (df_res['profit'] > 0).sum()
    total = len(df_res)
    wr = wins / total * 100
    pnl = df_res['profit'].sum()
    print("\n=== UPGRADED BACKTEST PERFORMANCE (3 MONTHS) ===")
    print(f"Total sub-trades: {total} ({total//3} clusters)")
    print(f"Winrate: {wr:.2f}% ({wins}/{total})")
    print(f"Initial: $5,000.00 -> Final: ${balance:.2f} USD")
    print(f"Net Profit: +${pnl:.2f} USD (+{(balance-5000)/50:.2f}%)")
    print(f"Max Drawdown: {max_dd:.2f}%")
    print("Breakdown by reason:")
    print(df_res['reason'].value_counts())
    
    df_res['Month'] = pd.to_datetime(df_res['exit_time']).dt.to_period('M')
    for m, g in df_res.groupby('Month'):
        m_wins = (g['profit'] > 0).sum()
        m_tot = len(g)
        m_pnl = g['profit'].sum()
        print(f"  Month {m}: {m_wins}/{m_tot} ({m_wins/m_tot*100:.1f}%) | Net PnL: +${m_pnl:.2f}")
