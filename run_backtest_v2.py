"""
Kịch bản Backtest Độc Lập Version 2:
ÁP DỤNG CẢ 2 PHƯƠNG PHÁP:
1. Chia 3 Lệnh Đa Mục Tiêu (TP1 12 pips, TP2 22 pips, TP3 35 pips Runner)
2. Tinh chỉnh ngưỡng AI Ensemble (0.76) để tăng gấp nhiều lần số cơ hội vào lệnh
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from data_loader import fetch_historical_rates
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel
from backtester import BacktestEngine
from config import config

def print_banner():
    print("=" * 75)
    print("   HỆ THỐNG BACKTEST VERSION 2 - PHIÊN BẢN KẾT HỢP ĐA MỤC TIÊU & TĂNG TẦN SUẤT")
    print("   * PP1: Chia 3 Lệnh Con (0.03 lot TP1 12 pips | 0.03 lot TP2 22 pips | 0.02 lot TP3 35 pips)")
    print("   * PP2: AI Ensemble Ngưỡng 0.76 (Tối ưu hóa tần suất vào lệnh)")
    print("=" * 75)

def print_detailed_metrics(stage_name: str, res: dict):
    trades = res.get('trades', [])
    win_trades = [t for t in trades if t.profit > 0]
    loss_trades = [t for t in trades if t.profit < 0]
    be_trades = [t for t in trades if t.exit_reason == 'BREAKEVEN']
    
    avg_win = np.mean([t.profit for t in win_trades]) if win_trades else 0.0
    avg_loss = np.mean([abs(t.profit) for t in loss_trades]) if loss_trades else 0.0

    print("\n" + "#" * 75)
    print(f"        BÁO CÁO KẾT QUẢ: {stage_name}")
    print("#" * 75)
    print(f"  Vốn khởi điểm          : ${res['initial_balance']:,.2f} USD")
    print(f"  Vốn kết thúc           : ${res['final_balance']:,.2f} USD")
    print(f"  LỢI NHUẬN RÒNG         : ${res['net_profit']:+,.2f} USD ({res['return_pct']:+.2f}%)")
    print(f"  -------------------------------------------------------------------")
    print(f"  Tổng số Cụm tín hiệu   : {res['total_signal_groups']} cụm")
    print(f"  Tổng số Lệnh con đã vào: {res['total_subtrades']} lệnh")
    print(f"  - Số lệnh con Thắng    : {len(win_trades)} lệnh ({res['winrate']:.2f}%)")
    print(f"    + Lệnh 1 (TP 12 pips): {res['tier1_wins']} lệnh chốt lời nhanh thành công")
    print(f"    + Lệnh 2 (TP 22 pips): {res['tier2_wins']} lệnh chốt lời tiêu chuẩn")
    print(f"    + Lệnh 3 (TP 35 pips): {res['tier3_wins']} lệnh runner ăn sóng dài")
    print(f"  - Số lệnh Hòa vốn (BE) : {len(be_trades)} lệnh (Được bảo vệ vốn thành công)")
    print(f"  - Số lệnh Thua (SL)    : {len(loss_trades)} lệnh")
    print(f"  -------------------------------------------------------------------")
    print(f"  TỶ LỆ THẮNG (WINRATE)  : {res['winrate']:.2f}%  {'[ĐẠT MỤC TIÊU > 80%]' if res['winrate'] >= 80 else '[CHẤP NHẬN ĐƯỢC]'}")
    print(f"  SỤT GIẢM TỐI ĐA (DD)   : {res['max_drawdown_pct']:.2f}% (${res['max_drawdown_dollar']:,.2f})  {'[AN TOÀN TUYỆT ĐỐI < 10%]' if res['max_drawdown_pct'] <= 10 else '[CHƯA ĐẠT]'}")
    print(f"  Hệ số Profit Factor    : {res['profit_factor']:.2f}")
    print("#" * 75)

def export_trade_logs(res1: dict, res2: dict, filename: str = "backtest_trades_v2.csv"):
    records = []
    for t in res1.get('trades', []):
        records.append({
            'Stage': 'GĐ1_InSample',
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
        
    for t in res2.get('trades', []):
        records.append({
            'Stage': 'GĐ2_OutOfSample',
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
        
    df_trades = pd.DataFrame(records)
    df_trades.to_csv(filename, index=False)
    print(f"\n[Export] Đã lưu lịch sử chi tiết {len(df_trades)} lệnh ra: {os.path.abspath(filename)}")

def plot_version2_visuals(res1: dict, res2: dict, output_path: str = "backtest_result_v2.png"):
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # 1. Đường cong vốn Giai đoạn 1 (In-Sample)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(res1['equity_curve'], color='#059669', linewidth=2, label=f"Vốn: +${res1['net_profit']:,.0f} (+{res1['return_pct']}%)")
    ax1.axhline(config.INITIAL_BALANCE, color='gray', linestyle='--', alpha=0.6)
    ax1.set_title(f"Giai đoạn 1 (In-Sample): Tăng trưởng vốn\nWinrate: {res1['winrate']}% | Max DD: {res1['max_drawdown_pct']}%", fontsize=11, fontweight='bold', color='#065f46')
    ax1.set_ylabel("Số dư ($)")
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc="upper left")
    
    # 2. Đường cong vốn Giai đoạn 2 (Out-of-Sample)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(res2['equity_curve'], color='#2563EB', linewidth=2, label=f"Vốn: +${res2['net_profit']:,.0f} (+{res2['return_pct']}%)")
    ax2.axhline(config.INITIAL_BALANCE, color='gray', linestyle='--', alpha=0.6)
    ax2.set_title(f"Giai đoạn 2 (Out-of-Sample): Dữ liệu thực tế\nWinrate: {res2['winrate']}% | Max DD: {res2['max_drawdown_pct']}%", fontsize=11, fontweight='bold', color='#1e40af')
    ax2.set_ylabel("Số dư ($)")
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc="upper left")
    
    # 3. Phân bổ kết quả các tầng lệnh (Tier Breakdown)
    ax3 = fig.add_subplot(gs[1, 0])
    labels = ['TP1 (12p)', 'TP2 (22p)', 'TP3 (35p)', 'Hòa Vốn BE', 'Cắt Lỗ SL']
    g2_counts = [
        res2['tier1_wins'],
        res2['tier2_wins'],
        res2['tier3_wins'],
        res2['breakeven_trades'],
        res2['loss_trades']
    ]
    colors = ['#10B981', '#059669', '#047857', '#3B82F6', '#EF4444']
    ax3.bar(labels, g2_counts, color=colors, width=0.55)
    ax3.set_ylabel("Số lượng lệnh con")
    ax3.set_title("Cơ Cấu Lệnh Chốt Lời & Bảo Vệ Vốn (GĐ 2)", fontsize=11, fontweight='bold')
    ax3.grid(True, linestyle=':', alpha=0.5, axis='y')
    
    # 4. So sánh Lợi nhuận vs Drawdown
    ax4 = fig.add_subplot(gs[1, 1])
    metrics = ['Lợi nhuận ròng (%)', 'Sụt giảm tối đa DD (%)']
    g1_vals = [res1['return_pct'], res1['max_drawdown_pct']]
    g2_vals = [res2['return_pct'], res2['max_drawdown_pct']]
    
    x = np.arange(len(metrics))
    width = 0.35
    ax4.bar(x - width/2, g1_vals, width, label='Giai đoạn 1', color='#059669')
    ax4.bar(x + width/2, g2_vals, width, label='Giai đoạn 2', color='#1D4ED8')
    ax4.set_xticks(x)
    ax4.set_xticklabels(metrics, fontweight='bold')
    ax4.set_ylabel("Tỷ lệ (%)")
    ax4.set_title("So Sánh Tỷ Suất Sinh Lời vs Rủi Ro DD", fontsize=11, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.5, axis='y')
    ax4.legend()
    
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[Chart] Đã tạo biểu đồ Dashboard Version 2: {os.path.abspath(output_path)}")

def main():
    print_banner()
    
    print("[1/5] Đang tải 35,000 nến M5 XAUUSD từ MT5...")
    raw_df = fetch_historical_rates(count=35000)
    
    print("[2/5] Đang phân tích 4 động cơ chiến thuật kết hợp...")
    strategy = CompositeScalperStrategy()
    df = strategy.generate_signals(raw_df)
    
    split_idx = int(len(df) * config.TRAIN_TEST_SPLIT_RATIO)
    df_p1 = df.iloc[:split_idx].copy().reset_index(drop=True)
    df_p2 = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    print(f"[3/5] Phân chia 2 giai đoạn:")
    print(f"  - Giai đoạn 1 (In-Sample): {df_p1['time'].iloc[0]} -> {df_p1['time'].iloc[-1]} ({len(df_p1)} nến)")
    print(f"  - Giai đoạn 2 (Out-of-Sample): {df_p2['time'].iloc[0]} -> {df_p2['time'].iloc[-1]} ({len(df_p2)} nến)")
    
    print("\n[4/5] Đang tải mô hình AI Ensemble...")
    ai = AIGatekeeperModel()
    if not ai.load():
        ai.train(df_p1)
        
    print(f"\n[5/5] Đang thực thi Backtest Đa Mục Tiêu (Ngưỡng AI: {config.AI_CONFIDENCE_THRESHOLD * 100:.0f}%)...")
    eng1 = BacktestEngine(config.INITIAL_BALANCE, config.FIXED_LOT)
    res1 = eng1.run(df_p1, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    print_detailed_metrics("GIAI ĐOẠN 1 (IN-SAMPLE / HUẤN LUYỆN)", res1)
    
    eng2 = BacktestEngine(config.INITIAL_BALANCE, config.FIXED_LOT)
    res2 = eng2.run(df_p2, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    print_detailed_metrics("GIAI ĐOẠN 2 (OUT-OF-SAMPLE / KIỂM ĐỊNH MÙ THỰC TẾ)", res2)
    
    export_trade_logs(res1, res2, "backtest_trades_v2.csv")
    plot_version2_visuals(res1, res2, "backtest_result_v2.png")

if __name__ == "__main__":
    main()
