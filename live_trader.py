"""
Bot Trade Vàng Tự Động (AI XAUUSD Live/Demo Scalper)
Kết nối trực tiếp MetaTrader 5, tự động quét nến, phân tích đa chiến thuật + AI,
tự động vào lệnh, dời Stop Loss hòa vốn (Breakeven) và chốt lời an toàn.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import os
import datetime
import pandas as pd
import numpy as np
import MetaTrader5 as mt5

from config import config
from strategy import calculate_indicators
from ai_model import AIScalperModel, FEATURES
from data_loader import init_mt5

class XAUUSDLiveBot:
    def __init__(self):
        self.config = config
        self.ai = AIScalperModel()
        self.is_running = False
        self.last_checked_bar_time = None
        
    def start(self):
        print("=" * 65)
        print("    KHỞI ĐỘNG BOT TRADE VÀNG TỰ ĐỘNG - AI SCALPER XAUUSD")
        print("=" * 65)
        
        # 1. Kết nối MT5
        acc = init_mt5()
        print(f"[MT5] Kết nối thành công!")
        print(f"  - Tài khoản : {acc.login} ({acc.server})")
        print(f"  - Số dư     : ${acc.balance:,.2f} USD")
        print(f"  - Equity    : ${acc.equity:,.2f} USD")
        print(f"  - Đòn bẩy   : 1:{acc.leverage}")
        print(f"  - AutoTrade : {'Cho phép' if acc.trade_expert else 'CHƯA BẬT (Hãy bật Algo Trading)'}")
        
        # 2. Tải mô hình AI
        if not self.ai.load():
            print("[AI] Không tìm thấy file mô hình 'ai_scalper_model.joblib'.")
            print("[AI] Vui lòng chạy 'python run_backtest.py' trước để huấn luyện mô hình!")
            return
        print("[AI] Đã tải mô hình AI thành công!")
        
        # 3. Kiểm tra Symbol
        if not mt5.symbol_select(self.config.SYMBOL, True):
            print(f"[Lỗi] Không chọn được cặp {self.config.SYMBOL}")
            return
            
        sym_info = mt5.symbol_info(self.config.SYMBOL)
        print(f"[Symbol] {self.config.SYMBOL} | Digits: {sym_info.digits} | Point: {sym_info.point} | Spread hiện tại: {sym_info.spread}")
        
        self.is_running = True
        print(f"\n[Bot] Bắt đầu quét thị trường khung {self.config.TIMEFRAME}...")
        print(f"  - Lot vào lệnh   : {self.config.FIXED_LOT}")
        print(f"  - TP kỳ vọng     : {self.config.TP_POINTS} points ({self.config.TP_POINTS * 0.01:.2f} USD)")
        print(f"  - SL bảo vệ      : {self.config.SL_POINTS} points ({self.config.SL_POINTS * 0.01:.2f} USD)")
        print(f"  - Ngưỡng kích hoạt BE : {self.config.BREAKEVEN_TRIGGER_POINTS} points")
        print(f"  - Ngưỡng tin cậy AI   : {self.config.AI_CONFIDENCE_THRESHOLD * 100:.0f}%")
        print("-" * 65)
        
        try:
            while self.is_running:
                self.tick_cycle()
                time.sleep(3)  # Quét mỗi 3 giây
        except KeyboardInterrupt:
            print("\n[Bot] Đã nhận lệnh dừng từ bàn phím (Ctrl+C). Đang tắt bot an toàn...")
        finally:
            mt5.shutdown()
            print("[Bot] Đã ngắt kết nối MT5. Tạm biệt!")
            
    def get_open_bot_positions(self):
        """Lấy danh sách lệnh đang mở do bot quản lý"""
        positions = mt5.positions_get(symbol=self.config.SYMBOL)
        if positions is None:
            return []
        return [p for p in positions if p.magic == self.config.MAGIC_NUMBER]

    def manage_active_positions(self):
        """Quản lý các lệnh đang chạy: Tự động dời SL về hòa vốn (Breakeven) và Trailing Stop"""
        positions = self.get_open_bot_positions()
        sym_info = mt5.symbol_info(self.config.SYMBOL)
        if not sym_info:
            return
            
        for pos in positions:
            entry_price = pos.price_open
            current_sl = pos.sl
            current_tp = pos.tp
            ticket = pos.ticket
            
            # Quản lý lệnh BUY
            if pos.type == mt5.ORDER_TYPE_BUY:
                current_price = sym_info.bid
                profit_points = (current_price - entry_price) / sym_info.point
                
                # Nếu giá đã đạt ngưỡng Breakeven và SL vẫn còn dưới điểm hòa vốn
                target_be_sl = entry_price + (self.config.BREAKEVEN_LOCK_POINTS * sym_info.point)
                if profit_points >= self.config.BREAKEVEN_TRIGGER_POINTS and current_sl < target_be_sl:
                    print(f"[BẢO VỆ] Lệnh BUY #{ticket} lời +{profit_points:.0f} points. Đang dời SL về Breakeven (+{self.config.BREAKEVEN_LOCK_POINTS} points)...")
                    self.modify_position(ticket, target_be_sl, current_tp)
                    
            # Quản lý lệnh SELL
            elif pos.type == mt5.ORDER_TYPE_SELL:
                current_price = sym_info.ask
                profit_points = (entry_price - current_price) / sym_info.point
                
                # Nếu giá đã giảm sâu đạt ngưỡng Breakeven và SL vẫn ở trên
                target_be_sl = entry_price - (self.config.BREAKEVEN_LOCK_POINTS * sym_info.point)
                if profit_points >= self.config.BREAKEVEN_TRIGGER_POINTS and (current_sl == 0 or current_sl > target_be_sl):
                    print(f"[BẢO VỆ] Lệnh SELL #{ticket} lời +{profit_points:.0f} points. Đang dời SL về Breakeven (+{self.config.BREAKEVEN_LOCK_POINTS} points)...")
                    self.modify_position(ticket, target_be_sl, current_tp)

    def modify_position(self, ticket: int, new_sl: float, new_tp: float):
        """Gửi yêu cầu dời SL / TP lên sàn"""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": round(new_sl, 2),
            "tp": round(new_tp, 2)
        }
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"[Thành công] Đã dời SL lệnh #{ticket} về {new_sl:.2f}")
        else:
            print(f"[Cảnh báo] Dời SL lệnh #{ticket} thất bại: {res.comment} (Code: {res.retcode})")

    def is_market_open_vn(self) -> tuple:
        """
        Kiểm tra trạng thái thị trường Vàng (XAUUSD) theo giờ Việt Nam (UTC+7):
        - Đóng cửa cuối tuần: Từ ~05:00 sáng Thứ Bảy đến ~05:00 sáng Thứ Hai.
        - Mở cửa: Từ 05:00 sáng Thứ Hai đến 05:00 sáng Thứ Bảy (24/5 liên tục).
        """
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=T2, 1=T3, 2=T4, 3=T5, 4=T6, 5=T7, 6=CN
        hour = now.hour
        
        # Thứ Bảy từ 05h00 sáng trở đi
        if weekday == 5 and hour >= 5:
            return False, "Hôm nay là Thứ Bảy (theo giờ VN). Thị trường Vàng quốc tế đang đóng cửa nghỉ cuối tuần."
            
        # Chủ Nhật cả ngày
        if weekday == 6:
            return False, "Hôm nay là Chủ Nhật (theo giờ VN). Thị trường Vàng quốc tế đang đóng cửa nghỉ cuối tuần."
            
        # Rạng sáng Thứ Hai trước 05h00 sáng
        if weekday == 0 and hour < 5:
            return False, "Rạng sáng Thứ Hai (trước 05:00 sáng giờ VN). Thị trường Vàng chưa mở phiên tuần mới."
            
        return True, "Thị trường Vàng đang mở cửa giao dịch."

    def tick_cycle(self):
        """Chu kỳ kiểm tra nến và xử lý tín hiệu"""
        # 1. Kiểm tra lịch thị trường (Nghỉ Thứ Bảy & Chủ Nhật theo giờ Việt Nam)
        is_open, msg = self.is_market_open_vn()
        if not is_open:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now_str}] [CHẾ ĐỘ CHỜ / STANDBY] {msg}")
            print("                --> Bot sẽ tự động thức dậy và bắt đầu quét lệnh ngay khi thị trường mở cửa vào rạng sáng Thứ Hai (~05:00 - 06:00 giờ VN)!\n")
            time.sleep(27)  # Ngủ thêm để kiểm tra mỗi 30s khi thị trường đóng cửa
            return

        # 2. Cập nhật và bảo vệ các lệnh đang mở
        self.manage_active_positions()
        
        # 3. Kiểm tra số lượng lệnh đang mở
        open_pos = self.get_open_bot_positions()
        if len(open_pos) >= self.config.MAX_OPEN_POSITIONS:
            return  # Đang có lệnh chạy, không mở thêm để đảm bảo an toàn vốn
            
        # 3. Kiểm tra Spread
        sym_info = mt5.symbol_info(self.config.SYMBOL)
        if sym_info is None:
            return
        if sym_info.spread > self.config.MAX_SPREAD:
            return  # Spread giãn, bỏ qua
            
        # 4. Lấy dữ liệu nến M5 gần nhất (250 nến để tính đủ EMA200, BB, RSI)
        rates = mt5.copy_rates_from_pos(self.config.SYMBOL, mt5.TIMEFRAME_M5, 0, 250)
        if rates is None or len(rates) < 210:
            return
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        last_bar_time = df['time'].iloc[-1]
        
        # 5. Tính toán chỉ báo kỹ thuật
        df_ind = calculate_indicators(df)
        if len(df_ind) == 0:
            return
            
        current_bar = df_ind.iloc[-1]
        features_row = df_ind.iloc[[-1]]
        
        # 6. Kiểm tra tín hiệu BUY
        if current_bar['raw_signal_buy']:
            prob_win = self.ai.predict_confidence(features_row, "BUY")[0]
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{now_str}] [Tín hiệu] BUY xuất hiện! AI đánh giá xác suất thắng: {prob_win * 100:.1f}%")
            
            if prob_win >= self.config.AI_CONFIDENCE_THRESHOLD:
                print(f"[AI PHÊ DUYỆT] Xác suất {prob_win * 100:.1f}% >= {self.config.AI_CONFIDENCE_THRESHOLD * 100:.0f}%. Mở lệnh BUY!")
                self.open_trade(mt5.ORDER_TYPE_BUY, sym_info.ask, sym_info)
                
        # 7. Kiểm tra tín hiệu SELL
        elif current_bar['raw_signal_sell']:
            prob_win = self.ai.predict_confidence(features_row, "SELL")[0]
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{now_str}] [Tín hiệu] SELL xuất hiện! AI đánh giá xác suất thắng: {prob_win * 100:.1f}%")
            
            if prob_win >= self.config.AI_CONFIDENCE_THRESHOLD:
                print(f"[AI PHÊ DUYỆT] Xác suất {prob_win * 100:.1f}% >= {self.config.AI_CONFIDENCE_THRESHOLD * 100:.0f}%. Mở lệnh SELL!")
                self.open_trade(mt5.ORDER_TYPE_SELL, sym_info.bid, sym_info)

    def open_trade(self, order_type: int, price: float, sym_info):
        """Mở cụm 3 lệnh đa mục tiêu (TP1: 12p, TP2: 22p, TP3: 35p) với SL chung và quản lý Breakeven đồng bộ"""
        point = sym_info.point
        is_buy = (order_type == mt5.ORDER_TYPE_BUY)
        type_str = "BUY" if is_buy else "SELL"
        init_sl = round(price - (self.config.SL_POINTS * point), 2) if is_buy else round(price + (self.config.SL_POINTS * point), 2)
        
        tiers = [
            ("TIER 1 (Scalp 12p)", self.config.TIER1_LOT, self.config.TIER1_TP_POINTS),
            ("TIER 2 (Standard 22p)", self.config.TIER2_LOT, self.config.TIER2_TP_POINTS),
            ("TIER 3 (Runner 35p)", self.config.TIER3_LOT, self.config.TIER3_TP_POINTS),
        ]
        
        for name, lot, tp_pts in tiers:
            tp_price = round(price + (tp_pts * point), 2) if is_buy else round(price - (tp_pts * point), 2)
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.SYMBOL,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": init_sl,
                "tp": tp_price,
                "deviation": self.config.SLIPPAGE,
                "magic": self.config.MAGIC_NUMBER,
                "comment": f"AI Scalper {name}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            res = mt5.order_send(request)
            if res.retcode != mt5.TRADE_RETCODE_DONE:
                request["type_filling"] = mt5.ORDER_FILLING_RETURN
                res = mt5.order_send(request)
                
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"==> [KHỚP LỆNH] {name}: {type_str} {lot} lot tại {price:.2f} | SL: {init_sl} | TP: {tp_price} | Ticket #{res.order}")
            else:
                print(f"[LỖI ĐẶT LỆNH] {name}: Mã lỗi {res.retcode}, Chi tiết: {res.comment}")

if __name__ == "__main__":
    bot = XAUUSDLiveBot()
    bot.start()
