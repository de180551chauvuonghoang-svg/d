"""
Kịch bản chạy Backtest toàn diện chia làm 2 giai đoạn cho XAUUSD Scalping Bot:
- Giai đoạn 1 (In-Sample): Huấn luyện và tối ưu AI
- Giai đoạn 2 (Out-of-Sample): Kiểm định mù dữ liệu thực tế
Yêu cầu đạt: Winrate > 80%, Max Drawdown < 10%
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from data_loader import fetch_historical_rates
from strategy import calculate_indicators
from ai_model import AIScalperModel
from backtester import BacktestEngine
from config import config

def print_stage_report(title: str, res: dict):
    print("=" * 65)
    print(f"       KẾT QUẢ BACKTEST: {title}")
    print("=" * 65)
    print(f"  Vốn ban đầu        : ${res['initial_balance']:,.2f}")
    print(f"  Vốn kết thúc       : ${res['final_balance']:,.2f}")
    print(f"  Lợi nhuận ròng     : ${res['net_profit']:+,.2f} ({res['return_pct']:+.2f}%)")
    print(f"  Tổng số lệnh       : {res['total_trades']}")
    print(f"  Số lệnh thắng      : {res['win_trades']}")
    print(f"  Số lệnh thua       : {res['loss_trades']}")
    print(f"  Số lệnh hòa vốn BE : {res['breakeven_trades']}")
    print(f"  TỶ LỆ THẮNG (WINRATE): {res['winrate']:.2f}%  {'[ĐẠT > 80%]' if res['winrate'] >= 80 else '[CHƯA ĐẠT]'}")
    print(f"  SỤT GIẢM TỐI ĐA (DD): {res['max_drawdown_pct']:.2f}% (${res['max_drawdown_dollar']:,.2f})  {'[ĐẠT < 10%]' if res['max_drawdown_pct'] <= 10 else '[CHƯA ĐẠT]'}")
    print(f"  Hệ số Profit Factor: {res['profit_factor']:.2f}")
    print("=" * 65)

def main():
    print("[1/5] Đang tải dữ liệu lịch sử XAUUSD M5...")
    raw_df = fetch_historical_rates(count=35000)
    
    print("[2/5] Đang tính toán các chỉ báo kỹ thuật đa chiến thuật...")
    df = calculate_indicators(raw_df)
    
    # Chia làm 2 giai đoạn:
    split_idx = int(len(df) * config.TRAIN_TEST_SPLIT_RATIO)
    df_phase1 = df.iloc[:split_idx].copy().reset_index(drop=True)
    df_phase2 = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    print(f"[3/5] Phân chia 2 giai đoạn:")
    print(f"  - Giai đoạn 1 (In-Sample) : {df_phase1['time'].iloc[0]} -> {df_phase1['time'].iloc[-1]} ({len(df_phase1)} nến)")
    print(f"  - Giai đoạn 2 (Out-of-Sample): {df_phase2['time'].iloc[0]} -> {df_phase2['time'].iloc[-1]} ({len(df_phase2)} nến)")
    
    # Huấn luyện mô hình AI trên Giai đoạn 1
    ai = AIScalperModel()
    ai.train(df_phase1)
    
    # Chạy Backtest Giai đoạn 1
    print("\n[4/5] Đang chạy Backtest Giai đoạn 1 (In-Sample)...")
    engine1 = BacktestEngine(initial_balance=config.INITIAL_BALANCE, lot_size=config.FIXED_LOT)
    res_phase1 = engine1.run(df_phase1, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    print_stage_report("GIAI ĐOẠN 1 (IN-SAMPLE / HUẤN LUYỆN)", res_phase1)
    
    # Chạy Backtest Giai đoạn 2 (Out-of-Sample)
    print("\n[5/5] Đang chạy Backtest Giai đoạn 2 (Out-of-Sample / Kiểm định thực tế)...")
    engine2 = BacktestEngine(initial_balance=config.INITIAL_BALANCE, lot_size=config.FIXED_LOT)
    res_phase2 = engine2.run(df_phase2, ai_model=ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
    print_stage_report("GIAI ĐOẠN 2 (OUT-OF-SAMPLE / KIỂM ĐỊNH MÙ)", res_phase2)
    
    # Vẽ biểu đồ Equity Curve so sánh 2 giai đoạn
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharey=False)
    
    # Subplot 1: Giai đoạn 1
    ax1.plot(res_phase1['equity_curve'], color='#10B981', linewidth=2, label=f"GĐ 1: Winrate {res_phase1['winrate']}% | DD {res_phase1['max_drawdown_pct']}%")
    ax1.axhline(config.INITIAL_BALANCE, color='gray', linestyle='--', alpha=0.6)
    ax1.set_title("Giai đoạn 1 (In-Sample): Đường cong Vốn (Equity Curve)", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Số dư ($)")
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc="upper left")
    
    # Subplot 2: Giai đoạn 2
    ax2.plot(res_phase2['equity_curve'], color='#3B82F6', linewidth=2, label=f"GĐ 2: Winrate {res_phase2['winrate']}% | DD {res_phase2['max_drawdown_pct']}%")
    ax2.axhline(config.INITIAL_BALANCE, color='gray', linestyle='--', alpha=0.6)
    ax2.set_title("Giai đoạn 2 (Out-of-Sample): Đường cong Vốn (Equity Curve)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Số bước nến M5")
    ax2.set_ylabel("Số dư ($)")
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc="upper left")
    
    plt.tight_layout()
    chart_path = "backtest_result_chart.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    print(f"\n[Chart] Đã lưu biểu đồ kết quả backtest tại: {os.path.abspath(chart_path)}")

if __name__ == "__main__":
    main()
