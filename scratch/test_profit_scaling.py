import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import numpy as np
from src.ml.ai_gatekeeper import AIGatekeeperModel
from src.strategies.composite import CompositeScalperStrategy
from backtester import BacktestEngine
from config import config

df_raw = pd.read_csv('xauusd_m5_3months.csv')
strat = CompositeScalperStrategy()
df_all = strat.generate_signals(df_raw)
start_date = pd.Timestamp('2026-07-05')
df_3m = df_all[df_all['time'] >= start_date].copy().reset_index(drop=True)

ai = AIGatekeeperModel()
ai.load()

# Test various lot sizes and AI thresholds with our upgraded robust R:R
# SL = 20p, TP1 = 18p, TP2 = 30p, TP3 = 45p, BE = 12p (+3p)
config.SL_POINTS = 200
config.TIER1_TP_POINTS = 180
config.TIER2_TP_POINTS = 300
config.TIER3_TP_POINTS = 450
config.BREAKEVEN_TRIGGER_POINTS = 120
config.BREAKEVEN_LOCK_POINTS = 30

experiments = [
    {"name": "0.08 lot (Thresh 0.785)", "lot": 0.08, "t1": 0.03, "t2": 0.03, "t3": 0.02, "th": 0.785},
    {"name": "0.15 lot (Thresh 0.785)", "lot": 0.15, "t1": 0.06, "t2": 0.05, "t3": 0.04, "th": 0.785},
    {"name": "0.20 lot (Thresh 0.785)", "lot": 0.20, "t1": 0.08, "t2": 0.07, "t3": 0.05, "th": 0.785},
    {"name": "0.25 lot (Thresh 0.785)", "lot": 0.25, "t1": 0.10, "t2": 0.09, "t3": 0.06, "th": 0.785},
    {"name": "0.20 lot (Thresh 0.780)", "lot": 0.20, "t1": 0.08, "t2": 0.07, "t3": 0.05, "th": 0.780},
    {"name": "0.25 lot (Thresh 0.780)", "lot": 0.25, "t1": 0.10, "t2": 0.09, "t3": 0.06, "th": 0.780},
]

print("=== PROFIT SCALING COMPARISON ($5,000 Capital, 1:100 Leverage) ===")
for exp in experiments:
    config.FIXED_LOT = exp['lot']
    config.TIER1_LOT = exp['t1']
    config.TIER2_LOT = exp['t2']
    config.TIER3_LOT = exp['t3']
    config.AI_CONFIDENCE_THRESHOLD = exp['th']
    
    engine = BacktestEngine(initial_balance=5000.0, lot_size=exp['lot'], spread_points=25.0)
    engine.be_trigger = 1.20
    engine.be_lock = 0.30
    
    res = engine.run(df_3m, ai_model=ai, confidence_threshold=exp['th'])
    
    # Check monthly
    t_df = pd.DataFrame(res['trades'])
    t_df['Month'] = pd.to_datetime(t_df['exit_time']).dt.to_period('M')
    m_info = []
    for m, g in t_df.groupby('Month'):
        p = g['profit'].sum()
        w = (g['profit'] > 0).sum()
        m_info.append(f"{m}: ${p:+.0f}")
        
    print(f"\n[{exp['name']}]:")
    print(f"  -> Profit: +${res['net_profit']:,.2f} USD (+{res['return_pct']:.1f}%) | Max DD: {res['max_drawdown_pct']:.2f}% (${res['max_drawdown_dollar']:.1f})")
    print(f"  -> Winrate: {res['winrate']:.2f}% ({res['total_signal_groups']} clusters, {res['total_subtrades']} trades) | Profit Factor: {res['profit_factor']:.2f}")
    print(f"  -> Monthly: {' | '.join(m_info)}")

