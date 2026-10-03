import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from data_loader import fetch_historical_rates
from strategy import calculate_indicators
from ai_model import AIScalperModel
from backtester import BacktestEngine
from config import config

raw_df = fetch_historical_rates(count=35000)
df = calculate_indicators(raw_df)
split_idx = int(len(df) * config.TRAIN_TEST_SPLIT_RATIO)
df_phase1 = df.iloc[:split_idx].copy().reset_index(drop=True)
df_phase2 = df.iloc[split_idx:].copy().reset_index(drop=True)

ai = AIScalperModel()
ai.load()

for thresh in [0.74, 0.76, 0.78, 0.80, 0.82, 0.85]:
    eng1 = BacktestEngine(5000, 0.08)
    res1 = eng1.run(df_phase1, ai, thresh)
    eng2 = BacktestEngine(5000, 0.08)
    res2 = eng2.run(df_phase2, ai, thresh)
    print(f"Thresh {thresh:.2f} | G1: WR={res1['winrate']}%, T={res1['total_trades']}, DD={res1['max_drawdown_pct']}%, Profit=+${res1['net_profit']} | G2: WR={res2['winrate']}%, T={res2['total_trades']}, DD={res2['max_drawdown_pct']}%, Profit=+${res2['net_profit']}")
