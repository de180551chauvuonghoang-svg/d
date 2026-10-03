"""
Live Trading Engine (Modular Event Loop)
Orchestrates Broker, Strategy, AI Gatekeeper, and Risk Manager
"""
import time
import sys
import pandas as pd
from typing import Optional
from src.core.interfaces import BaseBroker, BaseStrategy, BaseAIModel, BaseRiskManager
from src.core.types import OrderType, Position
from src.core.logger import log
from src.brokers.mt5_broker import MT5Broker
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel
from src.risk.risk_manager import StandardRiskManager
from config import config

class LiveTradingEngine:
    def __init__(
        self,
        broker: Optional[BaseBroker] = None,
        strategy: Optional[BaseStrategy] = None,
        ai_model: Optional[BaseAIModel] = None,
        risk_manager: Optional[BaseRiskManager] = None
    ):
        self.broker = broker or MT5Broker()
        self.strategy = strategy or CompositeScalperStrategy()
        self.ai = ai_model or AIGatekeeperModel()
        self.risk = risk_manager or StandardRiskManager()
        self.is_running = False

    def start(self, poll_interval: int = 3):
        log.info("Khởi động Live Trading Engine...")
        
        # 1. Kết nối Broker
        if not self.broker.connect():
            log.error("Không thể kết nối sàn giao dịch. Dừng hệ thống.")
            return
            
        # 2. Tải trọng số mô hình AI
        if not self.ai.load():
            log.warning("Chưa có file mô hình AI! Vui lòng chạy backtest trước để huấn luyện AI.")
            return
            
        acc = self.broker.get_account_info()
        log.info(f"Tài khoản sẵn sàng: Balance ${acc.get('balance', 0):,.2f} | Leverage 1:{acc.get('leverage', 100)}")
        
        self.is_running = True
        log.info(f"Bắt đầu vòng lặp giao dịch tự động trên {config.SYMBOL} ({config.TIMEFRAME})...")
        
        try:
            while self.is_running:
                self.process_cycle()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            log.info("Nhận lệnh dừng (Ctrl+C). Đang tắt engine an toàn...")
        finally:
            self.broker.disconnect()
            log.info("Engine đã dừng hoàn tất.")

    def process_cycle(self):
        # 1. Bảo vệ các vị thế đang mở (Breakeven & Trailing)
        open_positions = self.broker.get_open_positions(config.SYMBOL)
        sym_info = self.broker.get_symbol_info(config.SYMBOL)
        if not sym_info:
            return
            
        if open_positions:
            protections = self.risk.update_positions_protection(
                open_positions, sym_info.bid, sym_info.ask, sym_info.point
            )
            for mod in protections:
                log.info(f"Bảo vệ vị thế: #{mod['ticket']} đạt +{mod['profit_pts']:.0f} pts. Dời SL về {mod['new_sl']}")
                self.broker.modify_order(mod['ticket'], mod['new_sl'], mod['new_tp'])
                
        # 2. Kiểm tra điều kiện quản trị rủi ro trước khi vào lệnh
        if not self.risk.should_allow_entry(open_positions, sym_info.spread):
            return
            
        # 3. Lấy dữ liệu nến mới nhất
        df_raw = self.broker.get_market_data(config.SYMBOL, config.TIMEFRAME, 250)
        if df_raw.empty or len(df_raw) < 210:
            return
            
        # 4. Phân tích đa chiến thuật
        df_sig = self.strategy.generate_signals(df_raw)
        if df_sig.empty:
            return
            
        last_bar = df_sig.iloc[-1]
        feature_row = df_sig.iloc[[-1]]
        
        # 5. Đánh giá và lọc lệnh qua AI
        if last_bar.get('raw_signal_buy', False):
            prob = self.ai.predict_confidence(feature_row, "BUY")[0]
            log.info(f"[Tín hiệu BUY] AI đánh giá xác suất thắng: {prob * 100:.1f}%")
            
            if prob >= config.AI_CONFIDENCE_THRESHOLD:
                log.info(f"[AI PHÊ DUYỆT] Xác suất {prob * 100:.1f}% >= {config.AI_CONFIDENCE_THRESHOLD * 100:.0f}%. Vào lệnh BUY!")
                sl = sym_info.ask - (config.SL_POINTS * sym_info.point)
                tp = sym_info.ask + (config.TP_POINTS * sym_info.point)
                self.broker.open_order(config.SYMBOL, OrderType.BUY, config.FIXED_LOT, sl, tp, "AI Scalper BUY")
                
        elif last_bar.get('raw_signal_sell', False):
            prob = self.ai.predict_confidence(feature_row, "SELL")[0]
            log.info(f"[Tín hiệu SELL] AI đánh giá xác suất thắng: {prob * 100:.1f}%")
            
            if prob >= config.AI_CONFIDENCE_THRESHOLD:
                log.info(f"[AI PHÊ DUYỆT] Xác suất {prob * 100:.1f}% >= {config.AI_CONFIDENCE_THRESHOLD * 100:.0f}%. Vào lệnh SELL!")
                sl = sym_info.bid + (config.SL_POINTS * sym_info.point)
                tp = sym_info.bid - (config.TP_POINTS * sym_info.point)
                self.broker.open_order(config.SYMBOL, OrderType.SELL, config.FIXED_LOT, sl, tp, "AI Scalper SELL")
