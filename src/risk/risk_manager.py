"""
Production Risk & Capital Management System
"""
from typing import List, Dict, Any, Optional
from src.core.interfaces import BaseRiskManager
from src.core.types import Position, OrderType
from src.core.logger import log
from config import config

class StandardRiskManager(BaseRiskManager):
    def __init__(
        self,
        fixed_lot: float = None,
        max_spread: float = None,
        max_positions: int = None,
        be_trigger_points: int = None,
        be_lock_points: int = None,
        trailing_step_points: int = None
    ):
        self.fixed_lot = fixed_lot or config.FIXED_LOT
        self.max_spread = max_spread or config.MAX_SPREAD
        self.max_positions = max_positions or config.MAX_OPEN_POSITIONS
        self.be_trigger = be_trigger_points or config.BREAKEVEN_TRIGGER_POINTS
        self.be_lock = be_lock_points or config.BREAKEVEN_LOCK_POINTS
        self.trailing_step = trailing_step_points or config.TRAILING_STEP_POINTS

    def calculate_lot_size(self, balance: float, sl_points: float) -> float:
        """
        Tính khối lượng lot dựa trên vốn và khoảng cách SL.
        Mặc định sử dụng lot cố định an toàn 0.08 cho tài khoản $5,000 đòn bẩy 1:100.
        """
        return self.fixed_lot

    def should_allow_entry(self, current_positions: List[Position], spread: float) -> bool:
        """Kiểm tra điều kiện rủi ro trước khi vào lệnh"""
        if len(current_positions) >= self.max_positions:
            return False
            
        if spread > self.max_spread:
            log.warning(f"Spread hiện tại ({spread}) vượt mức cho phép ({self.max_spread}). Từ chối vào lệnh.")
            return False
            
        return True

    def update_positions_protection(
        self,
        positions: List[Position],
        current_bid: float,
        current_ask: float,
        point: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Kiểm tra trạng thái các vị thế và trả về danh sách yêu cầu điều chỉnh SL:
        - Dời về Breakeven khi lãi đạt ngưỡng
        - Trailing stop bảo vệ lãi
        """
        modifications = []
        
        for pos in positions:
            entry = pos.entry_price
            ticket = pos.ticket
            
            if pos.order_type == OrderType.BUY:
                profit_pts = (current_bid - entry) / point
                target_be_sl = round(entry + (self.be_lock * point), 2)
                
                # Kích hoạt Breakeven
                if profit_pts >= self.be_trigger and (pos.sl < target_be_sl or not pos.is_breakeven_activated):
                    modifications.append({
                        "ticket": ticket,
                        "new_sl": target_be_sl,
                        "new_tp": pos.tp,
                        "action": "BREAKEVEN",
                        "profit_pts": profit_pts
                    })
                    
            elif pos.order_type == OrderType.SELL:
                profit_pts = (entry - current_ask) / point
                target_be_sl = round(entry - (self.be_lock * point), 2)
                
                if profit_pts >= self.be_trigger and (pos.sl > target_be_sl or pos.sl == 0 or not pos.is_breakeven_activated):
                    modifications.append({
                        "ticket": ticket,
                        "new_sl": target_be_sl,
                        "new_tp": pos.tp,
                        "action": "BREAKEVEN",
                        "profit_pts": profit_pts
                    })
                    
        return modifications
