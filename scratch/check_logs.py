import urllib.request
import json
import MetaTrader5 as mt5
import pandas as pd
import datetime

print("=== CHECK BOT STATUS & LOGS ===")
try:
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/bot/status")
    data = json.loads(res.read().decode())
    print("Is Running:", data.get("is_running"))
    print("Open Positions Count:", len(data.get("positions", [])))
    print("Logs:")
    for l in data.get("logs", [])[:25]:
        print(f"  [{l.get('time')}] [{l.get('level')}] {l.get('message')}")
except Exception as e:
    print("Error calling status API:", e)

print("\n=== MT5 DEALS INVESTIGATION ===")
if mt5.initialize():
    from_t = datetime.datetime.now() - datetime.timedelta(days=2)
    to_t = datetime.datetime.now() + datetime.timedelta(days=1)
    deals = mt5.history_deals_get(from_t, to_t)
    if deals:
        for d in deals:
            if d.symbol:
                dt = datetime.datetime.fromtimestamp(d.time).strftime("%Y-%m-%d %H:%M:%S")
                print(f"Deal #{d.ticket} | Order #{d.order} | Position #{d.position_id} | Type={d.type} | Entry={d.entry} | Vol={d.volume} | Price={d.price:.2f} | Profit=${d.profit:.2f} | Comm=${d.commission:.2f} | Swap=${d.swap:.2f} | Comment='{d.comment}' | Time={dt}")
    mt5.shutdown()
