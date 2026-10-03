"""
Module Backtest 2 giai đoạn (In-Sample & Out-of-Sample) cho XAUUSD Scalping Bot
Mục tiêu: Winrate > 80%, Maximum Drawdown < 10% với vốn $5000 đòn bẩy 1:100
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
import matplotlib.pyplot as plt
from config import config

@dataclass
class Trade:
    ticket: int
    trade_type: str        # 'BUY' hoặc 'SELL'
    entry_time: pd.Timestamp
    entry_price: float
    lot_size: float
    tp: float
    sl: float
    exit_time: pd.Timestamp = None
    exit_price: float = 0.0
    profit: float = 0.0
    exit_reason: str = ""   # 'TP', 'SL', 'BREAKEVEN', 'TIMEOUT'
    is_breakeven_active: bool = False

class BacktestEngine:
    def __init__(self, initial_balance: float = 5000.0, lot_size: float = 0.08, spread_points: float = 35.0):
        self.initial_balance = initial_balance
        self.lot_size = lot_size
        self.spread = spread_points * 0.01   # Quy đổi sang USD trên 1 oz vàng
        
        self.tp_val = config.TP_POINTS * 0.01
        self.sl_val = config.SL_POINTS * 0.01
        self.be_trigger = config.BREAKEVEN_TRIGGER_POINTS * 0.01
        self.be_lock = config.BREAKEVEN_LOCK_POINTS * 0.01
        
    def run(self, df: pd.DataFrame, ai_model=None, confidence_threshold: float = 0.72) -> Dict:
        """
        Chạy mô phỏng giao dịch chi tiết từng nến
        """
        data = df.copy().reset_index(drop=True)
        balance = self.initial_balance
        equity = self.initial_balance
        
        equity_curve = [balance]
        times = [data['time'].iloc[0]]
        trades: List[Trade] = []
        active_trade: Trade = None
        ticket_counter = 1
        
        # Dự đoán AI trước nếu có mô hình
        buy_probs = np.zeros(len(data))
        sell_probs = np.zeros(len(data))
        if ai_model is not None:
            buy_probs = ai_model.predict_confidence(data, "BUY")
            sell_probs = ai_model.predict_confidence(data, "SELL")
            
        peak_balance = self.initial_balance
        max_drawdown_dollar = 0.0
        max_drawdown_pct = 0.0
        
        for i in range(len(data)):
            bar = data.iloc[i]
            curr_time = bar['time']
            curr_open = bar['open']
            curr_high = bar['high']
            curr_low = bar['low']
            curr_close = bar['close']
            
            # 1. Quản lý lệnh đang mở (Active Trade)
            if active_trade is not None:
                # Kiểm tra cho lệnh BUY
                if active_trade.trade_type == 'BUY':
                    # Kiểm tra kích hoạt Breakeven (Dời SL lên có lời)
                    if not active_trade.is_breakeven_active:
                        if curr_high >= active_trade.entry_price + self.be_trigger:
                            active_trade.is_breakeven_active = True
                            active_trade.sl = active_trade.entry_price + self.be_lock
                            
                    # Kiểm tra chạm Take Profit
                    if curr_high >= active_trade.tp:
                        active_trade.exit_time = curr_time
                        active_trade.exit_price = active_trade.tp
                        # Lợi nhuận = (Exit - Entry) * Contract Size (100) * Lot
                        active_trade.profit = (active_trade.exit_price - active_trade.entry_price) * 100 * active_trade.lot_size
                        active_trade.exit_reason = 'TP'
                        balance += active_trade.profit
                        trades.append(active_trade)
                        active_trade = None
                        
                    # Kiểm tra chạm Stop Loss
                    elif curr_low <= active_trade.sl:
                        active_trade.exit_time = curr_time
                        active_trade.exit_price = active_trade.sl
                        active_trade.profit = (active_trade.exit_price - active_trade.entry_price) * 100 * active_trade.lot_size
                        active_trade.exit_reason = 'BREAKEVEN' if active_trade.is_breakeven_active else 'SL'
                        balance += active_trade.profit
                        trades.append(active_trade)
                        active_trade = None
                        
                # Kiểm tra cho lệnh SELL
                elif active_trade.trade_type == 'SELL':
                    # Kiểm tra kích hoạt Breakeven
                    if not active_trade.is_breakeven_active:
                        if curr_low <= active_trade.entry_price - self.be_trigger:
                            active_trade.is_breakeven_active = True
                            active_trade.sl = active_trade.entry_price - self.be_lock
                            
                    # Kiểm tra chạm Take Profit
                    if curr_low <= active_trade.tp:
                        active_trade.exit_time = curr_time
                        active_trade.exit_price = active_trade.tp
                        active_trade.profit = (active_trade.entry_price - active_trade.exit_price) * 100 * active_trade.lot_size
                        active_trade.exit_reason = 'TP'
                        balance += active_trade.profit
                        trades.append(active_trade)
                        active_trade = None
                        
                    # Kiểm tra chạm Stop Loss
                    elif curr_high >= active_trade.sl:
                        active_trade.exit_time = curr_time
                        active_trade.exit_price = active_trade.sl
                        active_trade.profit = (active_trade.entry_price - active_trade.exit_price) * 100 * active_trade.lot_size
                        active_trade.exit_reason = 'BREAKEVEN' if active_trade.is_breakeven_active else 'SL'
                        balance += active_trade.profit
                        trades.append(active_trade)
                        active_trade = None
                        
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
            
            # 2. Xem xét mở lệnh mới (nếu chưa có lệnh nào đang mở)
            if active_trade is None and i < len(data) - 1:
                # Kiểm tra tín hiệu BUY
                is_buy = bar['raw_signal_buy']
                if ai_model is not None:
                    is_buy = is_buy and (buy_probs[i] >= confidence_threshold)
                    
                # Kiểm tra tín hiệu SELL
                is_sell = bar['raw_signal_sell']
                if ai_model is not None:
                    is_sell = is_sell and (sell_probs[i] >= confidence_threshold)
                    
                if is_buy and not is_sell:
                    # Mở lệnh BUY với giá Ask (Close + Spread)
                    entry_p = curr_close + self.spread
                    active_trade = Trade(
                        ticket=ticket_counter,
                        trade_type='BUY',
                        entry_time=curr_time,
                        entry_price=entry_p,
                        lot_size=self.lot_size,
                        tp=entry_p + self.tp_val,
                        sl=entry_p - self.sl_val
                    )
                    ticket_counter += 1
                    
                elif is_sell and not is_buy:
                    # Mở lệnh SELL với giá Bid (Close)
                    entry_p = curr_close
                    active_trade = Trade(
                        ticket=ticket_counter,
                        trade_type='SELL',
                        entry_time=curr_time,
                        entry_price=entry_p,
                        lot_size=self.lot_size,
                        tp=entry_p - self.tp_val,
                        sl=entry_p + self.sl_val
                    )
                    ticket_counter += 1
                    
        # Tổng kết chỉ số
        total_trades = len(trades)
        if total_trades > 0:
            win_trades = [t for t in trades if t.profit > 0]
            loss_trades = [t for t in trades if t.profit < 0]
            be_trades = [t for t in trades if t.exit_reason == 'BREAKEVEN']
            
            winrate = (len(win_trades) / total_trades) * 100.0
            gross_profit = sum(t.profit for t in win_trades)
            gross_loss = abs(sum(t.profit for t in loss_trades))
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 99.99
            net_profit = balance - self.initial_balance
            return_pct = (net_profit / self.initial_balance) * 100.0
        else:
            winrate = 0.0
            profit_factor = 0.0
            net_profit = 0.0
            return_pct = 0.0
            win_trades, loss_trades, be_trades = [], [], []

        return {
            'initial_balance': self.initial_balance,
            'final_balance': round(balance, 2),
            'net_profit': round(net_profit, 2),
            'return_pct': round(return_pct, 2),
            'total_trades': total_trades,
            'win_trades': len(win_trades),
            'loss_trades': len(loss_trades),
            'breakeven_trades': len(be_trades),
            'winrate': round(winrate, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown_dollar': round(max_drawdown_dollar, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'trades': trades,
            'equity_curve': equity_curve,
            'times': times
        }
