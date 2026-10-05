"""
Kịch bản Backtest 3 Tháng Gần Nhất (05/07/2026 -> 05/10/2026) với Bot Version 2.0
- Dữ liệu: Nến M5 XAUUSD mới nhất tải trực tiếp từ MT5 terminal
- Chiến lược: 4-Engine Confluence + Siêu AI Gatekeeper Ensemble
- Quản lý vốn: 3-Tier Multi-Target (TP1 12p, TP2 22p, TP3 35p) + Khóa lãi Breakeven (+20p)
- Thống kê chi tiết từng tháng và toàn chu kỳ 3 tháng
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import MetaTrader5 as mt5

from config import config
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel
from backtester import BacktestEngine, SubTrade

def fetch_3month_fresh_data(symbol: str = "XAUUSD") -> pd.DataFrame:
    """Tải trực tiếp dữ liệu nến M5 3 tháng gần nhất từ MT5 kèm 300 nến warmup"""
    if not mt5.initialize(path=config.MT5_PATH, login=config.LOGIN, password=config.PASSWORD, server=config.SERVER):
        if not mt5.initialize():
            raise RuntimeError(f"Không thể kết nối MT5 terminal: {mt5.last_error()}")
            
    mt5.symbol_select(symbol, True)
    
    # 3 tháng có khoảng 17,500 nến M5 + 350 nến warmup cho EMA 200/ATR
    total_bars_needed = 22000
    print(f"[MT5 Data] Đang tải {total_bars_needed} nến M5 mới nhất từ MT5 terminal...")
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, total_bars_needed)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Lỗi lấy dữ liệu từ MT5: {mt5.last_error()}")
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Lưu bản cache dữ liệu mới
    df.to_csv("xauusd_m5_3months.csv", index=False)
    print(f"[MT5 Data] Đã tải thành công {len(df)} nến M5. Dải thời gian: {df['time'].min()} -> {df['time'].max()}")
    return df

def analyze_monthly_breakdown(trades: list, initial_balance: float = 5000.0) -> pd.DataFrame:
    """Phân tích chi tiết hiệu suất theo từng tháng"""
    if not trades:
        return pd.DataFrame()
        
    records = []
    for t in trades:
        records.append({
            'month': t.entry_time.strftime('%Y-%m'),
            'profit': t.profit,
            'is_win': t.profit > 0,
            'is_be': t.exit_reason == 'BREAKEVEN',
            'is_sl': t.exit_reason == 'SL',
            'tier': t.tier,
            'group_id': t.group_id
        })
    df_t = pd.DataFrame(records)
    
    monthly_stats = []
    running_balance = initial_balance
    
    for month, group in df_t.groupby('month'):
        m_profit = group['profit'].sum()
        m_start_bal = running_balance
        m_end_bal = running_balance + m_profit
        running_balance = m_end_bal
        
        m_groups = group['group_id'].nunique()
        m_trades = len(group)
        m_wins = group['is_win'].sum()
        m_winrate = (m_wins / m_trades * 100) if m_trades > 0 else 0.0
        
        # Max DD within month
        group_cum = group['profit'].cumsum()
        peak = np.maximum.accumulate(group_cum)
        dd = peak - group_cum
        m_dd_dollar = dd.max() if len(dd) > 0 else 0.0
        m_dd_pct = (m_dd_dollar / m_start_bal * 100) if m_start_bal > 0 else 0.0
        
        # Tiers breakdown
        t1_w = ((group['tier'] == 'TIER1') & (group['is_win'])).sum()
        t2_w = ((group['tier'] == 'TIER2') & (group['is_win'])).sum()
        t3_w = ((group['tier'] == 'TIER3') & (group['is_win'])).sum()
        be_c = group['is_be'].sum()
        
        monthly_stats.append({
            'Tháng': month,
            'Số cụm tín hiệu': m_groups,
            'Tổng lệnh con': m_trades,
            'Thắng T1 (12p)': t1_w,
            'Thắng T2 (22p)': t2_w,
            'Thắng T3 (35p)': t3_w,
            'Hòa Breakeven': be_c,
            'Tỷ lệ Thắng (%)': round(m_winrate, 2),
            'Lợi nhuận ($)': round(m_profit, 2),
            'Tỷ suất (%)': round((m_profit / m_start_bal) * 100, 2),
            'Max Drawdown (%)': round(m_dd_pct, 2)
        })
        
    return pd.DataFrame(monthly_stats)

def plot_3month_results(res: dict, monthly_df: pd.DataFrame, output_path: str = "backtest_3months_result.png"):
    """Vẽ bảng dashboard đồ họa 4 góc phân tích chuẩn 3 tháng"""
    fig = plt.figure(figsize=(16, 11))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # 1. Đường cong vốn (Equity Curve)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(res['equity_curve'], label='Vốn tài khoản (USD)', color='#10B981', linewidth=2.0)
    ax1.axhline(y=res['initial_balance'], color='#EF4444', linestyle='--', alpha=0.7, label=f"Vốn gốc (${res['initial_balance']:,.0f})")
    ax1.set_title("Đường Cong Tăng Trưởng Vốn 3 Tháng Gần Nhất (XAUUSD M5)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Số bước nến (Timeline)")
    ax1.set_ylabel("Số dư tài khoản (USD)")
    ax1.grid(True, linestyle=':', alpha=0.5)
    ax1.legend(loc='upper left')
    
    # Ghi chú chỉ số chính trên chart 1
    info_text = f"Vốn: ${res['initial_balance']:,.0f} -> ${res['final_balance']:,.2f}\nLợi nhuận: +${res['net_profit']:,.2f} (+{res['return_pct']:.1f}%)\nWinrate: {res['winrate']:.1f}%\nMax DD: {res['max_drawdown_pct']:.2f}%"
    ax1.text(0.68, 0.08, info_text, transform=ax1.transAxes, fontsize=10, verticalalignment='bottom',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8FAFC', edgecolor='#10B981', alpha=0.9))
    
    # 2. Mức độ sụt giảm (Drawdown Curve %)
    ax2 = fig.add_subplot(gs[0, 1])
    eq = np.array(res['equity_curve'])
    peaks = np.maximum.accumulate(eq)
    dds_pct = ((peaks - eq) / peaks) * 100
    ax2.fill_between(range(len(dds_pct)), 0, dds_pct, color='#EF4444', alpha=0.35, label='Drawdown (%)')
    ax2.plot(dds_pct, color='#DC2626', linewidth=1.2)
    ax2.axhline(y=10.0, color='#B91C1C', linestyle='--', linewidth=1.5, label='Ngưỡng Rủi Ro Giới Hạn (10%)')
    ax2.set_title(f"Mức Độ Sụt Giảm Tối Đa Thực Tế (Max DD: {res['max_drawdown_pct']:.2f}%)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Số bước nến")
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_ylim(0, max(12.0, res['max_drawdown_pct'] * 1.5))
    ax2.grid(True, linestyle=':', alpha=0.5)
    ax2.legend(loc='upper right')
    
    # 3. Cơ cấu khớp lệnh đa mục tiêu (3-Tier & Breakeven)
    ax3 = fig.add_subplot(gs[1, 0])
    categories = ['T1 (TP 18p)', 'T2 (TP 30p)', 'T3 (TP 45p)', 'Khóa Hòa Vốn BE', 'Cắt Lỗ SL']
    trades = res.get('trades', [])
    loss_count = len([t for t in trades if t.profit < 0])
    be_count = len([t for t in trades if t.exit_reason == 'BREAKEVEN'])
    counts = [res['tier1_wins'], res['tier2_wins'], res['tier3_wins'], be_count, loss_count]
    colors = ['#10B981', '#3B82F6', '#F59E0B', '#64748B', '#EF4444']
    
    bars = ax3.bar(categories, counts, color=colors, width=0.55)
    for bar in bars:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., h + 5, f"{int(h)}", ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax3.set_title("Cơ Cấu Lệnh Chốt Lời Đa Mục Tiêu & Bảo Vệ Vốn", fontsize=11, fontweight='bold')
    ax3.set_ylabel("Số lượng lệnh con đã khớp")
    ax3.grid(True, linestyle=':', alpha=0.5, axis='y')
    
    # 4. Hiệu suất theo từng tháng (Monthly Returns %)
    ax4 = fig.add_subplot(gs[1, 1])
    if not monthly_df.empty:
        m_labels = monthly_df['Tháng'].tolist()
        m_returns = monthly_df['Tỷ suất (%)'].tolist()
        m_colors = ['#059669' if r >= 0 else '#EF4444' for r in m_returns]
        
        m_bars = ax4.bar(m_labels, m_returns, color=m_colors, width=0.45)
        for b in m_bars:
            h = b.get_height()
            ax4.text(b.get_x() + b.get_width()/2., h + (0.5 if h >= 0 else -1.5), f"{h:+.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax4.set_title("Tỷ Suất Sinh Lời Theo Từng Tháng Trong 3 Tháng Gần Nhất", fontsize=11, fontweight='bold')
        ax4.set_ylabel("Tỷ suất sinh lời (%)")
        ax4.grid(True, linestyle=':', alpha=0.5, axis='y')
        
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[Chart] Đã tạo biểu đồ báo cáo 3 tháng: {os.path.abspath(output_path)}")

def main():
    print("=" * 80)
    print("      HỆ THỐNG BACKTEST ĐỊNH LƯỢNG 3 THÁNG GẦN NHẤT (05/07/2026 -> 05/10/2026)")
    print("      Bot Version 2.0: 4-Engine Confluence + Siêu AI Gatekeeper Ensemble")
    print("      Cơ cấu: 3-Tier Multi-Target Scale-Out (0.03/0.03/0.02 lot) + Breakeven (+20p)")
    print("=" * 80)
    
    # 1. Tải dữ liệu nến mới nhất
    df_raw = fetch_3month_fresh_data("XAUUSD")
    
    # Lấy mốc thời gian 3 tháng trước: 2026-07-05
    start_3m_date = pd.Timestamp("2026-07-05")
    
    # 2. Phân tích chỉ báo kỹ thuật toàn diện
    print("\n[1/4] Đang tính toán 20 chỉ báo kỹ thuật & 4 chiến thuật kết hợp...")
    strategy = CompositeScalperStrategy()
    df_all = strategy.generate_signals(df_raw)
    
    # Lọc đúng 3 tháng từ 05/07/2026 đến nay
    df_3m = df_all[df_all['time'] >= start_3m_date].copy().reset_index(drop=True)
    print(f"[2/4] Dữ liệu 3 tháng chuẩn xác:")
    print(f"  - Từ ngày: {df_3m['time'].iloc[0]}")
    print(f"  - Đến ngày: {df_3m['time'].iloc[-1]}")
    print(f"  - Tổng số nến M5: {len(df_3m):,} nến (~{len(df_3m)/288:.1f} ngày giao dịch liên tục)")
    
    # 3. Tải mô hình AI Gatekeeper đã tối ưu
    print("\n[3/4] Đang tải mô hình Siêu AI Gatekeeper Ensemble...")
    ai = AIGatekeeperModel()
    if not ai.load():
        print("[AI] Không tìm thấy mô hình, huấn luyện từ dữ liệu mẫu...")
        ai.train(df_all.iloc[:int(len(df_all)*0.5)])
    else:
        print("[AI] Tải thành công mô hình đã hiệu chỉnh Calibrated (Random Forest + HistGradientBoosting).")
        
    # 4. Chạy Backtest Engine
    print(f"\n[4/4] Bắt đầu mô phỏng giao dịch thực tế (Ngưỡng AI: {config.AI_CONFIDENCE_THRESHOLD*100:.1f}%)...")
    engine = BacktestEngine(
        initial_balance=config.INITIAL_BALANCE,
        lot_size=config.FIXED_LOT,
        spread_points=config.MAX_SPREAD
    )
    res = engine.run(df_3m, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    
    # 5. Báo cáo chi tiết theo từng tháng
    trades = res.get('trades', [])
    monthly_df = analyze_monthly_breakdown(trades, config.INITIAL_BALANCE)
    
    print("\n" + "=" * 80)
    print("                    BÁO CÁO CHI TIẾT THEO TỪNG THÁNG (3 THÁNG GẦN NHẤT)")
    print("=" * 80)
    if not monthly_df.empty:
        print(monthly_df.to_string(index=False))
    print("=" * 80)
    
    # 6. Tổng kết toàn diện chu kỳ 3 tháng
    win_trades = [t for t in trades if t.profit > 0]
    loss_trades = [t for t in trades if t.profit < 0]
    be_trades = [t for t in trades if t.exit_reason == 'BREAKEVEN']
    
    print("\n" + "#" * 80)
    print("                 TỔNG KẾT HIỆU SUẤT BACKTEST 3 THÁNG GẦN NHẤT")
    print("#" * 80)
    print(f"  Khung thời gian        : {df_3m['time'].iloc[0]} -> {df_3m['time'].iloc[-1]} (3 Tháng)")
    print(f"  Vốn ban đầu            : ${res['initial_balance']:,.2f} USD")
    print(f"  Vốn sau 3 tháng        : ${res['final_balance']:,.2f} USD")
    print(f"  LỢI NHUẬN RÒNG (NET)   : ${res['net_profit']:+,.2f} USD ({res['return_pct']:+.2f}%)")
    print(f"  ----------------------------------------------------------------------------")
    print(f"  Tổng số Cụm tín hiệu   : {res['total_signal_groups']} cụm")
    print(f"  Tổng số Lệnh con đã vào: {res['total_subtrades']} lệnh con")
    print(f"  - Lệnh con Thắng       : {len(win_trades)} lệnh ({res['winrate']:.2f}%)")
    print(f"    + Tier 1 (TP 12 pips): {res['tier1_wins']} lệnh chốt lời nhanh")
    print(f"    + Tier 2 (TP 22 pips): {res['tier2_wins']} lệnh chốt lời tiêu chuẩn")
    print(f"    + Tier 3 (TP 35 pips): {res['tier3_wins']} lệnh runner ăn sóng dài")
    print(f"  - Lệnh con Hòa Vốn (BE): {len(be_trades)} lệnh (Dời SL bảo toàn vốn & khóa lãi +20p)")
    print(f"  - Lệnh con Thua (SL)   : {len(loss_trades)} lệnh")
    print(f"  ----------------------------------------------------------------------------")
    print(f"  TỶ LỆ THẮNG (WINRATE)  : {res['winrate']:.2f}%  {'[ĐẠT CHỈ TIÊU > 80%]' if res['winrate'] >= 80 else '[CHẤP NHẬN ĐƯỢC]'}")
    print(f"  SỤT GIẢM TỐI ĐA (DD)   : {res['max_drawdown_pct']:.2f}% (${res['max_drawdown_dollar']:,.2f})  {'[AN TOÀN TUYỆT ĐỐI < 10%]' if res['max_drawdown_pct'] <= 10 else '[VƯỢT GIỚI HẠN]'}")
    print(f"  Hệ số Profit Factor    : {res['profit_factor']:.2f}")
    
    # Tần suất vào lệnh trung bình
    total_hours = len(df_3m) * 5 / 60
    hours_per_signal = total_hours / res['total_signal_groups'] if res['total_signal_groups'] > 0 else 0
    print(f"  Tần suất trung bình    : ~1 cụm lệnh mỗi {hours_per_signal:.1f} giờ giao dịch (~{hours_per_signal/24:.1f} ngày)")
    print("#" * 80)
    
    # 7. Xuất file lịch sử giao dịch và biểu đồ
    log_filename = "backtest_3months_trades.csv"
    trade_records = []
    for t in trades:
        trade_records.append({
            'Ticket': t.ticket,
            'Group_ID': t.group_id,
            'Tier': t.tier,
            'Type': t.trade_type,
            'Entry_Time': t.entry_time,
            'Entry_Price': t.entry_price,
            'Lot': t.lot_size,
            'Exit_Time': t.exit_time,
            'Exit_Price': t.exit_price,
            'Profit_USD': round(t.profit, 2),
            'Exit_Reason': t.exit_reason
        })
    pd.DataFrame(trade_records).to_csv(log_filename, index=False)
    print(f"\n[Export] Đã lưu lịch sử chi tiết {len(trade_records)} lệnh vào: {os.path.abspath(log_filename)}")
    
    chart_filename = "backtest_3months_result.png"
    plot_3month_results(res, monthly_df, chart_filename)

if __name__ == "__main__":
    main()
