import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import MetaTrader5 as mt5
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel

if mt5.initialize():
    rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M5, 0, 50)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    strat = CompositeScalperStrategy()
    df_sig = strat.generate_signals(df)
    
    ai = AIGatekeeperModel()
    ai.load()
    
    print("--- LAST 6 M5 BARS ON MT5 ---")
    for i in range(-6, 0):
        bar = df_sig.iloc[i]
        frow = df_sig.iloc[[i]]
        p_buy = ai.predict_confidence(frow, "BUY")[0]
        p_sell = ai.predict_confidence(frow, "SELL")[0]
        print(f"Time: {bar['time']} | Open: {bar['open']} | High: {bar['high']} | Low: {bar['low']} | Close: {bar['close']}")
        print(f"  EMA20: {bar.get('ema_20', 0):.2f} | EMA50: {bar.get('ema_50', 0):.2f} | EMA200: {bar.get('ema_200', 0):.2f} | RSI7: {bar.get('rsi_7', 0):.1f}")
        print(f"  raw_buy: {bar.get('raw_signal_buy')} (prob: {p_buy:.3f}) | raw_sell: {bar.get('raw_signal_sell')} (prob: {p_sell:.3f})")
        print(f"  tp_sell: {bar.get('tp_signal_sell')} | smc_sell: {bar.get('smc_signal_sell')} | sqz_sell: {bar.get('sqz_signal_sell')} | mr_sell: {bar.get('mr_signal_sell')}")
    mt5.shutdown()
