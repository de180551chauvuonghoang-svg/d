import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import numpy as np
from src.ml.ai_gatekeeper import AIGatekeeperModel
from src.strategies.composite import CompositeScalperStrategy
from backtester import BacktestEngine
from config import config

# 1. Load data & indicators
df_raw = pd.read_csv('xauusd_m5_3months.csv')
strat = CompositeScalperStrategy()
df_all = strat.generate_signals(df_raw)

start_date = pd.Timestamp("2026-07-05")
df_3m = df_all[df_all['time'] >= start_date].copy().reset_index(drop=True)

ai = AIGatekeeperModel()
ai.load()

print(f"Data bars: {len(df_3m)}")

# Test several configurations:
# Base config: SL 16p, TP1 12p, TP2 22p, TP3 35p, BE 9p
# Config A: SL 25p, TP1 20p, TP2 35p, TP3 50p, BE 15p, Lock 5p
# Config B: SL 30p, TP1 30p, TP2 50p, TP3 75p, BE 20p, Lock 8p
# Config C: Pure Trend Filter (No counter-trend SELL when bullish)

configs = [
    {"name": "Base (Current)", "sl": 160, "tp1": 120, "tp2": 220, "tp3": 350, "be_trig": 90, "be_lock": 20, "th": 0.775},
    {"name": "Config A (Balanced)", "sl": 240, "tp1": 200, "tp2": 320, "tp3": 480, "be_trig": 140, "be_lock": 30, "th": 0.775},
    {"name": "Config B (Pro Scalp)", "sl": 280, "tp1": 250, "tp2": 400, "tp3": 600, "be_trig": 160, "be_lock": 40, "th": 0.775},
    {"name": "Config C (High Conf)", "sl": 200, "tp1": 160, "tp2": 280, "tp3": 420, "be_trig": 110, "be_lock": 30, "th": 0.800},
]

for cfg in configs:
    # Update config parameters
    config.SL_POINTS = cfg['sl']
    config.TIER1_TP_POINTS = cfg['tp1']
    config.TIER2_TP_POINTS = cfg['tp2']
    config.TIER3_TP_POINTS = cfg['tp3']
    config.BREAKEVEN_TRIGGER_POINTS = cfg['be_trig']
    config.BREAKEVEN_LOCK_POINTS = cfg['be_lock']
    config.AI_CONFIDENCE_THRESHOLD = cfg['th']
    
    engine = BacktestEngine(
        initial_balance=5000.0,
        lot_size=0.08,
        spread_points=25.0
    )
    # custom be trigger
    engine.be_trigger = cfg['be_trig'] * 0.01
    engine.be_lock = cfg['be_lock'] * 0.01
    
    res = engine.run(df_3m, ai_model=ai, confidence_threshold=cfg['th'])
    
    t_df = pd.DataFrame(res['trades'])
    if len(t_df) > 0:
        t_df['Month'] = pd.to_datetime(t_df['exit_time']).dt.to_period('M')
        m_stats = []
        for m, g in t_df.groupby('Month'):
            w = (g['profit'] > 0).sum()
            tot = len(g)
            p = g['profit'].sum()
            m_stats.append(f"{m}: {w/tot*100:.1f}% (${p:+.0f})")
            
        print(f"\n[{cfg['name']}]: Trades={res['total_subtrades']} ({res['total_signal_groups']} clusters), Winrate={res['winrate']:.2f}%, Profit=+${res['net_profit']:.2f} (+{res['return_pct']:.1f}%), MaxDD={res['max_drawdown_pct']:.2f}%, PF={res['profit_factor']:.2f}")
        print("  Monthly: " + " | ".join(m_stats))
