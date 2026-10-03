"""
Modular 2-Stage Backtest Runner
Executes In-Sample training & Out-of-Sample validation
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from typing import Dict, Any

from src.core.interfaces import BaseStrategy, BaseAIModel
from src.core.logger import log
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel
from data_loader import fetch_historical_rates
from backtester import BacktestEngine
from config import config

class BacktestRunner:
    def __init__(
        self,
        strategy: BaseStrategy = None,
        ai_model: BaseAIModel = None,
        initial_balance: float = None,
        fixed_lot: float = None
    ):
        self.strategy = strategy or CompositeScalperStrategy()
        self.ai = ai_model or AIGatekeeperModel()
        self.initial_balance = initial_balance or config.INITIAL_BALANCE
        self.fixed_lot = fixed_lot or config.FIXED_LOT

    def run_all_stages(self, count: int = 35000, chart_output: str = "backtest_result_chart.png") -> Dict[str, Any]:
        log.info(f"Bắt đầu tải {count} nến lịch sử {config.SYMBOL}...")
        raw_df = fetch_historical_rates(count=count)
        
        log.info("Tính toán tín hiệu từ Strategy Engine...")
        df = self.strategy.generate_signals(raw_df)
        
        # Chia 2 giai đoạn: In-Sample (60%) & Out-of-Sample (40%)
        split_idx = int(len(df) * config.TRAIN_TEST_SPLIT_RATIO)
        df_p1 = df.iloc[:split_idx].copy().reset_index(drop=True)
        df_p2 = df.iloc[split_idx:].copy().reset_index(drop=True)
        
        log.info(f"Giai đoạn 1 (In-Sample): {df_p1['time'].iloc[0]} -> {df_p1['time'].iloc[-1]} ({len(df_p1)} nến)")
        log.info(f"Giai đoạn 2 (Out-of-Sample): {df_p2['time'].iloc[0]} -> {df_p2['time'].iloc[-1]} ({len(df_p2)} nến)")
        
        # Huấn luyện AI trên Giai đoạn 1
        self.ai.train(df_p1)
        
        # Backtest Giai đoạn 1
        log.info("Chạy Backtest Giai đoạn 1 (In-Sample)...")
        eng1 = BacktestEngine(self.initial_balance, self.fixed_lot)
        res1 = eng1.run(df_p1, ai_model=self.ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
        
        # Backtest Giai đoạn 2
        log.info("Chạy Backtest Giai đoạn 2 (Out-of-Sample)...")
        eng2 = BacktestEngine(self.initial_balance, self.fixed_lot)
        res2 = eng2.run(df_p2, ai_model=self.ai, confidence_threshold=config.AI_CONFIDENCE_THRESHOLD)
        
        # Xuất biểu đồ
        self._plot_results(res1, res2, chart_output)
        
        return {
            "phase1": res1,
            "phase2": res2,
            "chart_path": chart_output
        }

    def _plot_results(self, res1: dict, res2: dict, output_path: str):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        ax1.plot(res1['equity_curve'], color='#10B981', linewidth=2, 
                 label=f"GĐ 1: Winrate {res1['winrate']}% | DD {res1['max_drawdown_pct']}% | Lãi +${res1['net_profit']}")
        ax1.axhline(self.initial_balance, color='gray', linestyle='--', alpha=0.6)
        ax1.set_title("Giai đoạn 1 (In-Sample): Đường cong Vốn (Equity Curve)", fontsize=12, fontweight='bold')
        ax1.set_ylabel("Số dư ($)")
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend(loc="upper left")
        
        ax2.plot(res2['equity_curve'], color='#3B82F6', linewidth=2, 
                 label=f"GĐ 2: Winrate {res2['winrate']}% | DD {res2['max_drawdown_pct']}% | Lãi +${res2['net_profit']}")
        ax2.axhline(self.initial_balance, color='gray', linestyle='--', alpha=0.6)
        ax2.set_title("Giai đoạn 2 (Out-of-Sample): Đường cong Vốn (Equity Curve)", fontsize=12, fontweight='bold')
        ax2.set_xlabel("Số bước nến M5")
        ax2.set_ylabel("Số dư ($)")
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc="upper left")
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=200)
        plt.close()
        log.info(f"Đã lưu biểu đồ so sánh vốn tại: {os.path.abspath(output_path)}")
