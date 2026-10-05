import pandas as pd

df = pd.read_csv('backtest_3months_trades.csv')
df['Entry_Time'] = pd.to_datetime(df['Entry_Time'])
df['Month'] = df['Entry_Time'].dt.to_period('M')

print("=== MONTHLY WINRATE BREAKDOWN ===")
for m, g in df.groupby('Month'):
    total_trades = len(g)
    total_clusters = len(g['Group_ID'].unique())
    win_trades = (g['Profit_USD'] > 0).sum()
    net_pnl = g['Profit_USD'].sum()
    tp_count = (g['Exit_Reason'] == 'TP').sum()
    be_count = (g['Exit_Reason'] == 'BREAKEVEN').sum()
    sl_count = (g['Exit_Reason'] == 'SL').sum()
    wr = win_trades / total_trades * 100
    
    # cluster winrate: cluster is win if pnl > 0
    cluster_pnl = g.groupby('Group_ID')['Profit_USD'].sum()
    cluster_wins = (cluster_pnl > 0).sum()
    cluster_wr = cluster_wins / total_clusters * 100
    
    print(f"Month {m}:")
    print(f"  - Sub-trades: {win_trades}/{total_trades} Win ({wr:.2f}%) | TP={tp_count}, BE={be_count}, SL={sl_count}")
    print(f"  - Clusters: {cluster_wins}/{total_clusters} Win ({cluster_wr:.2f}%)")
    print(f"  - Net PnL: ${net_pnl:.2f} USD")
    for tier, tg in g.groupby('Tier'):
        tw = (tg['Profit_USD'] > 0).sum()
        ttot = len(tg)
        print(f"    + Tier {tier}: {tw}/{ttot} ({tw/ttot*100:.1f}%)")

print("\n=== JULY LOSSES (2026-07) ===")
july_sl = df[(df['Month'] == '2026-07') & (df['Exit_Reason'] == 'SL')]
print(f"Total SL July: {len(july_sl)} trades ({len(july_sl)//3} clusters)")
print(july_sl[['Group_ID', 'Type', 'Entry_Time', 'Entry_Price', 'Exit_Time', 'Exit_Price', 'Profit_USD']].head(12))

print("\n=== AUGUST LOSSES (2026-08) ===")
aug_sl = df[(df['Month'] == '2026-08') & (df['Exit_Reason'] == 'SL')]
print(f"Total SL August: {len(aug_sl)} trades ({len(aug_sl)//3} clusters)")
print(aug_sl[['Group_ID', 'Type', 'Entry_Time', 'Entry_Price', 'Exit_Time', 'Exit_Price', 'Profit_USD']].head(12))

