import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backtester import BacktestEngine
from src.ml.ai_gatekeeper import AIGatekeeperModel
from src.strategies.composite import CompositeScalperStrategy
import pandas as pd
from config import config

df_raw = pd.read_csv('xauusd_m5_3months.csv')
strat = CompositeScalperStrategy()
df_all = strat.generate_signals(df_raw)
start_date = pd.Timestamp('2026-07-05')
df_3m = df_all[df_all['time'] >= start_date].copy().reset_index(drop=True)

ai = AIGatekeeperModel()
ai.load()

# Test Best Configuration
config.SL_POINTS = 200
config.TIER1_TP_POINTS = 180
config.TIER2_TP_POINTS = 300
config.TIER3_TP_POINTS = 450
config.BREAKEVEN_TRIGGER_POINTS = 120
config.BREAKEVEN_LOCK_POINTS = 30
config.AI_CONFIDENCE_THRESHOLD = 0.785

engine = BacktestEngine(initial_balance=5000.0, lot_size=0.08, spread_points=25.0)
engine.be_trigger = 1.20
engine.be_lock = 0.30

res = engine.run(df_3m, ai_model=ai, confidence_threshold=0.785)
t_df = pd.DataFrame(res['trades'])
t_df['Month'] = pd.to_datetime(t_df['exit_time']).dt.to_period('M')

print("=== KET QUA PHUONG AN TOI UU TOAN DIEN ===")
print(f"Total sub-trades: {res['total_subtrades']} ({res['total_signal_groups']} clusters)")
print(f"Winrate: {res['winrate']:.2f}%")
print(f"Net Profit: +${res['net_profit']:.2f} (+{res['return_pct']:.1f}%)")
print(f"Max Drawdown: {res['max_drawdown_pct']:.2f}%")
print(f"Profit Factor: {res['profit_factor']:.2f}")
for m, g in t_df.groupby('Month'):
    w = (g['profit'] > 0).sum()
    tot = len(g)
    p = g['profit'].sum()
    print(f"  Thang {m}: {w}/{tot} ({w/tot*100:.1f}%) | Lai: +${p:.2f}")
