"""
Kịch bản Backtest Riêng Biệt cho Phiên Bản 2 (Version 2 - Đa Chiến Thuật & Siêu AI Ensemble)
Bao gồm:
- Phân tích chi tiết 2 giai đoạn (In-Sample & Out-of-Sample)
- Thống kê chuyên sâu: Buy vs Sell, Lãi trung bình, Drawdown, Chuỗi thắng liên tiếp
- Xuất nhật ký giao dịch chi tiết ra file CSV: backtest_trades_v2.csv
- Xuất biểu đồ phân tích 4 khung trực quan: backtest_result_v2.png
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from data_loader import fetch_historical_rates
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel
from backtester import BacktestEngine
from config import config

def print_banner():
    print("=" * 70)
    print("      HỆ THỐNG BACKTEST ĐỘC LẬP - VERSION 2 (XAUUSD AI SCALPER)")
    print("      Đa Động Cơ Chiến Thuật (BB, EMA, SMC, Squeeze) + Siêu AI Ensemble")
    print("=" * 70)

def print_detailed_metrics(stage_name: str, res: dict):
    trades = res.get('trades', [])
    win_trades = [t for t in trades if t.profit > 0]
    loss_trades = [t for t in trades if t.profit < 0]
    be_trades = [t for t in trades if t.exit_reason == 'BREAKEVEN']
    
    buy_trades = [t for t in trades if t.trade_type == 'BUY']
    sell_trades = [t for t in trades if t.trade_type == 'SELL']
    
    buy_wins = [t for t in buy_trades if t.profit > 0]
    sell_wins = [t for t in sell_trades if t.profit > 0]
    
    buy_winrate = (len(buy_wins) / len(buy_trades) * 100.0) if buy_trades else 0.0
    sell_winrate = (len(sell_wins) / len(sell_trades) * 100.0) if sell_trades else 0.0
    
    avg_win = np.mean([t.profit for t in win_trades]) if win_trades else 0.0
    avg_loss = np.mean([abs(t.profit) for t in loss_trades]) if loss_trades else 0.0
    
    # Tính chuỗi thắng liên tiếp tối đa
    max_streak = 0
    curr_streak = 0
    for t in trades:
        if t.profit >= 0:
            curr_streak += 1
            if curr_streak > max_streak:
                max_streak = curr_streak
        else:
            curr_streak = 0

    print("\n" + "#" * 70)
    print(f"       BÁO CÁO CHI TIẾT: {stage_name}")
    print("#" * 70)
    print(f"  Vốn khởi điểm       : ${res['initial_balance']:,.2f} USD")
    print(f"  Vốn kết thúc        : ${res['final_balance']:,.2f} USD")
    print(f"  LỢI NHUẬN RÒNG      : ${res['net_profit']:+,.2f} USD ({res['return_pct']:+.2f}%)")
    print(f"  -------------------------------------------------------------")
    print(f"  Tổng số lệnh        : {res['total_trades']} lệnh")
    print(f"  Số lệnh Thắng       : {len(win_trades)} lệnh ({res['winrate']:.2f}%)")
    print(f"  Số lệnh Thua        : {len(loss_trades)} lệnh")
    print(f"  Số lệnh Hòa vốn (BE): {len(be_trades)} lệnh (Được bảo vệ vốn)")
    print(f"  -------------------------------------------------------------")
    print(f"  Lệnh BUY            : {len(buy_trades)} lệnh | Tỷ lệ thắng BUY: {buy_winrate:.2f}%")
    print(f"  Lệnh SELL           : {len(sell_trades)} lệnh | Tỷ lệ thắng SELL: {sell_winrate:.2f}%")
    print(f"  -------------------------------------------------------------")
    print(f"  Lãi trung bình/lệnh : ${avg_win:.2f}")
    print(f"  Lỗ trung bình/lệnh  : ${avg_loss:.2f}")
    print(f"  Hệ số Profit Factor : {res['profit_factor']:.2f}")
    print(f"  Chuỗi thắng dài nhất: {max_streak} lệnh liên tiếp")
    print(f"  SỤT GIẢM TỐI ĐA (DD): {res['max_drawdown_pct']:.2f}% (${res['max_drawdown_dollar']:,.2f})  {'[AN TOÀN TUYỆT ĐỐI < 10%]' if res['max_drawdown_pct'] <= 10 else '[CHƯA ĐẠT]'}")
    print("#" * 70)

def export_trade_logs(res1: dict, res2: dict, filename: str = "backtest_trades_v2.csv"):
    """Xuất toàn bộ lịch sử lệnh chi tiết của cả 2 giai đoạn ra file CSV"""
    records = []
    
    for t in res1.get('trades', []):
        records.append({
            'Stage': 'Giai_Đoạn_1_InSample',
            'Ticket': t.ticket,
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
            'Stage': 'Giai_Đoạn_2_OutOfSample',
            'Ticket': t.ticket,
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
    print(f"\n[Export] Đã xuất nhật ký chi tiết {len(df_trades)} lệnh ra file: {os.path.abspath(filename)}")

def plot_version2_visuals(res1: dict, res2: dict, output_path: str = "backtest_result_v2.png"):
    """Vẽ bảng dashboard 4 khung phân tích chuyên sâu Version 2"""
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # 1. Đường cong vốn Giai đoạn 1 (In-Sample)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(res1['equity_curve'], color='#059669', linewidth=2, label=f"Vốn: +${res1['net_profit']:,.0f} (+{res1['return_pct']}%)")
    ax1.axhline(config.INITIAL_BALANCE, color='gray', linestyle='--', alpha=0.6)
    ax1.set_title(f"Giai đoạn 1 (In-Sample): Tăng trưởng vốn\nWinrate: {res1['winrate']}% | Max DD: {res1['max_drawdown_pct']}%", fontsize=11, fontweight='bold', color='#065f46')
    ax1.set_ylabel("Số dư tài khoản ($)")
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc="upper left")
    
    # 2. Đường cong vốn Giai đoạn 2 (Out-of-Sample / Dữ liệu thực tế)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(res2['equity_curve'], color='#2563EB', linewidth=2, label=f"Vốn: +${res2['net_profit']:,.0f} (+{res2['return_pct']}%)")
    ax2.axhline(config.INITIAL_BALANCE, color='gray', linestyle='--', alpha=0.6)
    ax2.set_title(f"Giai đoạn 2 (Out-of-Sample): Dữ liệu thực tế mù\nWinrate: {res2['winrate']}% | Max DD: {res2['max_drawdown_pct']}%", fontsize=11, fontweight='bold', color='#1e40af')
    ax2.set_ylabel("Số dư tài khoản ($)")
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc="upper left")
    
    # 3. Phân bổ kết quả lệnh (Win vs Loss vs Breakeven)
    ax3 = fig.add_subplot(gs[1, 0])
    categories = ['Thắng (TP)', 'Hòa vốn (BE)', 'Thua (SL)']
    
    g1_counts = [res1['win_trades'] - res1['breakeven_trades'], res1['breakeven_trades'], res1['loss_trades']]
    g2_counts = [res2['win_trades'] - res2['breakeven_trades'], res2['breakeven_trades'], res2['loss_trades']]
    
    x = np.arange(len(categories))
    width = 0.35
    ax3.bar(x - width/2, g1_counts, width, label='GĐ 1 (In-Sample)', color='#10B981')
    ax3.bar(x + width/2, g2_counts, width, label='GĐ 2 (Out-of-Sample)', color='#3B82F6')
    ax3.set_xticks(x)
    ax3.set_xticklabels(categories, fontweight='bold')
    ax3.set_ylabel("Số lượng lệnh")
    ax3.set_title("Cơ cấu Lệnh Giao Dịch 2 Giai Đoạn", fontsize=11, fontweight='bold')
    ax3.grid(True, linestyle=':', alpha=0.5, axis='y')
    ax3.legend()
    
    # 4. Tỷ lệ Lợi nhuận vs Sụt giảm (Profit vs Drawdown Comparison)
    ax4 = fig.add_subplot(gs[1, 1])
    metrics = ['Lợi nhuận ròng (%)', 'Sụt giảm tối đa DD (%)']
    g1_vals = [res1['return_pct'], res1['max_drawdown_pct']]
    g2_vals = [res2['return_pct'], res2['max_drawdown_pct']]
    
    x2 = np.arange(len(metrics))
    ax4.bar(x2 - width/2, g1_vals, width, label='GĐ 1', color='#059669')
    ax4.bar(x2 + width/2, g2_vals, width, label='GĐ 2', color='#1D4ED8')
    ax4.set_xticks(x2)
    ax4.set_xticklabels(metrics, fontweight='bold')
    ax4.set_ylabel("Tỷ lệ phần trăm (%)")
    ax4.set_title("Hiệu Quả Sinh Lời vs Quản Trị Rủi Ro DD", fontsize=11, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.5, axis='y')
    ax4.legend()
    
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[Chart] Đã tạo biểu đồ phân tích Dashboard Version 2: {os.path.abspath(output_path)}")

def main():
    print_banner()
    
    print("[1/5] Đang tải 35,000 nến M5 XAUUSD từ MetaTrader 5...")
    raw_df = fetch_historical_rates(count=35000)
    
    print("[2/5] Đang tính toán 4 động cơ chiến thuật Version 2 (Mean Reversion, Pullback, SMC Liquidity, Squeeze)...")
    strategy = CompositeScalperStrategy()
    df = strategy.generate_signals(raw_df)
    
    split_idx = int(len(df) * config.TRAIN_TEST_SPLIT_RATIO)
    df_p1 = df.iloc[:split_idx].copy().reset_index(drop=True)
    df_p2 = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    print(f"[3/5] Phân chia 2 giai đoạn kiểm định độc lập:")
    print(f"  - Giai đoạn 1 (In-Sample): {df_p1['time'].iloc[0]} -> {df_p1['time'].iloc[-1]} ({len(df_p1)} nến)")
    print(f"  - Giai đoạn 2 (Out-of-Sample): {df_p2['time'].iloc[0]} -> {df_p2['time'].iloc[-1]} ({len(df_p2)} nến)")
    
    print("\n[4/5] Đang huấn luyện Siêu Mô hình AI Ensemble (Random Forest + HistGradientBoosting)...")
    ai = AIGatekeeperModel()
    ai.train(df_p1)
    
    print("\n[5/5] Đang thực thi Backtest chi tiết 2 giai đoạn...")
    eng1 = BacktestEngine(config.INITIAL_BALANCE, config.FIXED_LOT)
    res1 = eng1.run(df_p1, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    print_detailed_metrics("GIAI ĐOẠN 1 (IN-SAMPLE / HUẤN LUYỆN)", res1)
    
    eng2 = BacktestEngine(config.INITIAL_BALANCE, config.FIXED_LOT)
    res2 = eng2.run(df_p2, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    print_detailed_metrics("GIAI ĐOẠN 2 (OUT-OF-SAMPLE / KIỂM ĐỊNH MÙ THỰC TẾ)", res2)
    
    # Xuất file CSV chi tiết
    export_trade_logs(res1, res2, "backtest_trades_v2.csv")
    
    # Xuất hình ảnh Dashboard Version 2
    plot_version2_visuals(res1, res2, "backtest_result_v2.png")
    
    print("\n" + "=" * 70)
    print("  HOÀN TẤT BACKTEST VERSION 2!")
    print(f"  - Giai đoạn 1: Winrate {res1['winrate']}% | Lãi +${res1['net_profit']:,.2f} (+{res1['return_pct']}%) | DD {res1['max_drawdown_pct']}%")
    print(f"  - Giai đoạn 2: Winrate {res2['winrate']}% | Lãi +${res2['net_profit']:,.2f} (+{res2['return_pct']}%) | DD {res2['max_drawdown_pct']}%")
    print("=" * 70)

if __name__ == "__main__":
    main()
