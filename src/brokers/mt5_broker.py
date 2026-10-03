"""
MetaTrader 5 Production Broker Implementation
"""
import MetaTrader5 as mt5
import pandas as pd
from typing import List, Dict, Any, Optional
from src.core.interfaces import BaseBroker
from src.core.types import OrderType, Position
from src.core.logger import log
from config import config

class MT5Broker(BaseBroker):
    def __init__(
        self,
        path: str = None,
        login: int = None,
        password: str = None,
        server: str = None,
        magic: int = None
    ):
        self.path = path or config.MT5_PATH
        self.login = login or config.LOGIN
        self.password = password or config.PASSWORD
        self.server = server or config.SERVER
        self.magic = magic or config.MAGIC_NUMBER
        self.is_connected = False

    def connect(self) -> bool:
        if not mt5.initialize(path=self.path, login=self.login, password=self.password, server=self.server):
            if not mt5.initialize():
                log.error(f"Kết nối MT5 thất bại: {mt5.last_error()}")
                return False
                
        self.is_connected = True
        acc = mt5.account_info()
        log.info(f"Kết nối MT5 thành công: Login {acc.login} | Server {acc.server} | Balance ${acc.balance:,.2f}")
        return True

    def disconnect(self) -> None:
        if self.is_connected:
            mt5.shutdown()
            self.is_connected = False
            log.info("Đã ngắt kết nối MT5.")

    def get_account_info(self) -> Dict[str, Any]:
        acc = mt5.account_info()
        return acc._asdict() if acc else {}

    def get_symbol_info(self, symbol: str):
        if not mt5.symbol_select(symbol, True):
            log.error(f"Không thể chọn symbol {symbol}")
            return None
        return mt5.symbol_info(symbol)

    def get_market_data(self, symbol: str, timeframe: str = "M5", count: int = 250) -> pd.DataFrame:
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_M5)
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def open_order(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        sl: float,
        tp: float,
        comment: str = "AI Scalper"
    ) -> Optional[int]:
        sym_info = self.get_symbol_info(symbol)
        if not sym_info:
            return None
            
        is_buy = (order_type == OrderType.BUY)
        mt5_order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
        price = sym_info.ask if is_buy else sym_info.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "sl": round(sl, sym_info.digits),
            "tp": round(tp, sym_info.digits),
            "deviation": config.SLIPPAGE,
            "magic": self.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode != mt5.TRADE_RETCODE_DONE:
            # Fallback sang ORDER_FILLING_RETURN nếu sàn không hỗ trợ IOC
            request["type_filling"] = mt5.ORDER_FILLING_RETURN
            res = mt5.order_send(request)
            
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log.info(f"Khớp lệnh thành công: {order_type.value} {volume} lot tại {price:.2f} (Ticket #{res.order})")
            return res.order
        else:
            log.error(f"Lỗi mở lệnh {order_type.value}: {res.comment} (Code {res.retcode})")
            return None

    def modify_order(self, ticket: int, new_sl: float, new_tp: float) -> bool:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": round(new_sl, 2),
            "tp": round(new_tp, 2)
        }
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log.info(f"Đã dời SL lệnh #{ticket} thành công sang {new_sl:.2f}")
            return True
        log.warning(f"Dời SL lệnh #{ticket} thất bại: {res.comment}")
        return False

    def close_order(self, ticket: int) -> bool:
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
            
        p = pos[0]
        sym_info = self.get_symbol_info(p.symbol)
        close_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = sym_info.bid if p.type == mt5.ORDER_TYPE_BUY else sym_info.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": close_type,
            "price": price,
            "deviation": config.SLIPPAGE,
            "magic": self.magic,
            "comment": "Close by Bot"
        }
        res = mt5.order_send(request)
        return res.retcode == mt5.TRADE_RETCODE_DONE

    def get_open_positions(self, symbol: str = None, magic: int = None) -> List[Position]:
        sym = symbol or config.SYMBOL
        mag = magic if magic is not None else self.magic
        
        raw_positions = mt5.positions_get(symbol=sym)
        if raw_positions is None:
            return []
            
        positions = []
        for p in raw_positions:
            if mag is not None and p.magic != mag:
                continue
            order_type = OrderType.BUY if p.type == mt5.ORDER_TYPE_BUY else OrderType.SELL
            positions.append(Position(
                ticket=p.ticket,
                symbol=p.symbol,
                order_type=order_type,
                volume=p.volume,
                entry_price=p.price_open,
                entry_time=pd.to_datetime(p.time, unit='s'),
                sl=p.sl,
                tp=p.tp,
                current_price=p.price_current,
                profit=p.profit,
                magic=p.magic
            ))
        return positions
