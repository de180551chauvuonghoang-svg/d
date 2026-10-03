"""
Module Backtest 2 Giai Đoạn Đa Mục Tiêu (3-Tier Multi-Target Scale-Out Engine)
Mô phỏng chính xác phương pháp chia 3 lệnh con: TP1 (12 pips), TP2 (22 pips), TP3 (35 pips Runner)
kết hợp dời Breakeven đồng bộ cho toàn bộ cụm lệnh.
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from config import config

@dataclass
class SubTrade:
    ticket: int
    group_id: int          # ID cụm lệnh chung
    tier: str              # 'TIER1', 'TIER2', 'TIER3'
    trade_type: str        # 'BUY' hoặc 'SELL'
    entry_time: pd.Timestamp
    entry_price: float
    lot_size: float
    tp: float
    sl: float
    exit_time: Optional[pd.Timestamp] = None
    exit_price: float = 0.0
    profit: float = 0.0
    exit_reason: str = ""  # 'TP', 'SL', 'BREAKEVEN', 'TRAILING'
    is_breakeven_active: bool = False

class BacktestEngine:
    def __init__(self, initial_balance: float = 5000.0, lot_size: float = 0.08, spread_points: float = 35.0):
        self.initial_balance = initial_balance
        self.total_lot = lot_size
        self.spread = spread_points * 0.01  # USD trên 1 oz vàng
        
        self.t1_lot = config.TIER1_LOT
        self.t1_tp_val = config.TIER1_TP_POINTS * 0.01
        
        self.t2_lot = config.TIER2_LOT
        self.t2_tp_val = config.TIER2_TP_POINTS * 0.01
        
        self.t3_lot = config.TIER3_LOT
        self.t3_tp_val = config.TIER3_TP_POINTS * 0.01
        
        self.sl_val = config.SL_POINTS * 0.01
        self.be_trigger = config.BREAKEVEN_TRIGGER_POINTS * 0.01
        self.be_lock = config.BREAKEVEN_LOCK_POINTS * 0.01

    def run(self, df: pd.DataFrame, ai_model=None, confidence_threshold: float = 0.76) -> Dict:
        data = df.copy().reset_index(drop=True)
        balance = self.initial_balance
        peak_balance = self.initial_balance
        max_drawdown_dollar = 0.0
        max_drawdown_pct = 0.0
        
        equity_curve = [balance]
        times = [data['time'].iloc[0]]
        
        closed_trades: List[SubTrade] = []
        active_trades: List[SubTrade] = []
        ticket_counter = 1
        group_counter = 1
        
        # Dự đoán xác suất AI
        buy_probs = np.zeros(len(data))
        sell_probs = np.zeros(len(data))
        if ai_model is not None:
            buy_probs = ai_model.predict_confidence(data, "BUY")
            sell_probs = ai_model.predict_confidence(data, "SELL")
            
        for i in range(len(data)):
            bar = data.iloc[i]
            curr_time = bar['time']
            curr_high = bar['high']
            curr_low = bar['low']
            curr_close = bar['close']
            
            # 1. Quản lý và xử lý các lệnh đang mở (Active SubTrades)
            remaining_trades = []
            
            # Nhóm các lệnh theo group_id để dời Breakeven đồng bộ
            groups = {}
            for t in active_trades:
                groups.setdefault(t.group_id, []).append(t)
                
            for group_id, g_trades in groups.items():
                first_trade = g_trades[0]
                entry_p = first_trade.entry_price
                is_buy = (first_trade.trade_type == 'BUY')
                
                # Kiểm tra kích hoạt Breakeven cho cả cụm
                if not first_trade.is_breakeven_active:
                    hit_be = (curr_high >= entry_p + self.be_trigger) if is_buy else (curr_low <= entry_p - self.be_trigger)
                    if hit_be:
                        target_sl = (entry_p + self.be_lock) if is_buy else (entry_p - self.be_lock)
                        for t in g_trades:
                            t.is_breakeven_active = True
                            t.sl = target_sl
                            
                # Duyệt từng lệnh con trong cụm để kiểm tra TP / SL
                for t in g_trades:
                    closed = False
                    
                    if is_buy:
                        # Kiểm tra TP
                        if curr_high >= t.tp:
                            t.exit_time = curr_time
                            t.exit_price = t.tp
                            t.profit = (t.exit_price - t.entry_price) * 100 * t.lot_size
                            t.exit_reason = 'TP'
                            balance += t.profit
                            closed_trades.append(t)
                            closed = True
                        # Kiểm tra SL
                        elif curr_low <= t.sl:
                            t.exit_time = curr_time
                            t.exit_price = t.sl
                            t.profit = (t.exit_price - t.entry_price) * 100 * t.lot_size
                            t.exit_reason = 'BREAKEVEN' if t.is_breakeven_active else 'SL'
                            balance += t.profit
                            closed_trades.append(t)
                            closed = True
                    else: # SELL
                        # Kiểm tra TP
                        if curr_low <= t.tp:
                            t.exit_time = curr_time
                            t.exit_price = t.tp
                            t.profit = (t.entry_price - t.exit_price) * 100 * t.lot_size
                            t.exit_reason = 'TP'
                            balance += t.profit
                            closed_trades.append(t)
                            closed = True
                        # Kiểm tra SL
                        elif curr_high >= t.sl:
                            t.exit_time = curr_time
                            t.exit_price = t.sl
                            t.profit = (t.entry_price - t.exit_price) * 100 * t.lot_size
                            t.exit_reason = 'BREAKEVEN' if t.is_breakeven_active else 'SL'
                            balance += t.profit
                            closed_trades.append(t)
                            closed = True
                            
                    if not closed:
                        remaining_trades.append(t)
                        
            active_trades = remaining_trades
            
            # Cập nhật Drawdown
            if balance > peak_balance:
                peak_balance = balance
            dd_dollar = peak_balance - balance
            dd_pct = (dd_dollar / peak_balance) * 100.0 if peak_balance > 0 else 0.0
            if dd_dollar > max_drawdown_dollar:
                max_drawdown_dollar = dd_dollar
            if dd_pct > max_drawdown_pct:
                max_drawdown_pct = dd_pct
                
            equity_curve.append(balance)
            times.append(curr_time)
            
            # 2. Xem xét mở cụm 3 lệnh mới (nếu chưa có cụm lệnh nào đang mở)
            if len(active_trades) == 0 and i < len(data) - 1:
                is_buy = bar['raw_signal_buy']
                if ai_model is not None:
                    is_buy = is_buy and (buy_probs[i] >= confidence_threshold)
                    
                is_sell = bar['raw_signal_sell']
                if ai_model is not None:
                    is_sell = is_sell and (sell_probs[i] >= confidence_threshold)
                    
                if is_buy and not is_sell:
                    entry_p = curr_close + self.spread
                    init_sl = entry_p - self.sl_val
                    
                    # Lệnh 1: TP1 (0.03 lot)
                    t1 = SubTrade(ticket_counter, group_counter, 'TIER1', 'BUY', curr_time, entry_p, self.t1_lot, entry_p + self.t1_tp_val, init_sl)
                    # Lệnh 2: TP2 (0.03 lot)
                    t2 = SubTrade(ticket_counter + 1, group_counter, 'TIER2', 'BUY', curr_time, entry_p, self.t2_lot, entry_p + self.t2_tp_val, init_sl)
                    # Lệnh 3: TP3 (0.02 lot)
                    t3 = SubTrade(ticket_counter + 2, group_counter, 'TIER3', 'BUY', curr_time, entry_p, self.t3_lot, entry_p + self.t3_tp_val, init_sl)
                    
                    active_trades.extend([t1, t2, t3])
                    ticket_counter += 3
                    group_counter += 1
                    
                elif is_sell and not is_buy:
                    entry_p = curr_close
                    init_sl = entry_p + self.sl_val
                    
                    t1 = SubTrade(ticket_counter, group_counter, 'TIER1', 'SELL', curr_time, entry_p, self.t1_lot, entry_p - self.t1_tp_val, init_sl)
                    t2 = SubTrade(ticket_counter + 1, group_counter, 'TIER2', 'SELL', curr_time, entry_p, self.t2_lot, entry_p - self.t2_tp_val, init_sl)
                    t3 = SubTrade(ticket_counter + 2, group_counter, 'TIER3', 'SELL', curr_time, entry_p, self.t3_lot, entry_p - self.t3_tp_val, init_sl)
                    
                    active_trades.extend([t1, t2, t3])
                    ticket_counter += 3
                    group_counter += 1

        # Tổng kết chỉ số
        total_subtrades = len(closed_trades)
        win_subtrades = [t for t in closed_trades if t.profit > 0]
        loss_subtrades = [t for t in closed_trades if t.profit < 0]
        be_subtrades = [t for t in closed_trades if t.exit_reason == 'BREAKEVEN']
        
        # Thống kê theo cụm (Group Signals)
        group_ids = set(t.group_id for t in closed_trades)
        total_signal_groups = len(group_ids)
        
        winrate = (len(win_subtrades) / total_subtrades * 100.0) if total_subtrades > 0 else 0.0
        gross_profit = sum(t.profit for t in win_subtrades)
        gross_loss = abs(sum(t.profit for t in loss_subtrades))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 99.99
        net_profit = balance - self.initial_balance
        return_pct = (net_profit / self.initial_balance) * 100.0

        return {
            'initial_balance': self.initial_balance,
            'final_balance': round(balance, 2),
            'net_profit': round(net_profit, 2),
            'return_pct': round(return_pct, 2),
            'total_signal_groups': total_signal_groups,
            'total_subtrades': total_subtrades,
            'win_trades': len(win_subtrades),
            'loss_trades': len(loss_subtrades),
            'breakeven_trades': len(be_subtrades),
            'tier1_wins': len([t for t in win_subtrades if t.tier == 'TIER1']),
            'tier2_wins': len([t for t in win_subtrades if t.tier == 'TIER2']),
            'tier3_wins': len([t for t in win_subtrades if t.tier == 'TIER3']),
            'winrate': round(winrate, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown_dollar': round(max_drawdown_dollar, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'trades': closed_trades,
            'equity_curve': equity_curve,
            'times': times
        }
