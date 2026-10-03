"""
Core Abstract Interfaces defining system boundaries for modular extension
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from src.core.types import TradeSignal, Position, ClosedTrade, OrderType

class BaseStrategy(ABC):
    """Giao diện chuẩn cho tất cả các chiến thuật giao dịch"""
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nhận DataFrame nến, tính toán và thêm cột tín hiệu:
        'raw_signal_buy', 'raw_signal_sell'
        """
        pass

class BaseAIModel(ABC):
    """Giao diện chuẩn cho các mô hình AI/Machine Learning"""
    @abstractmethod
    def train(self, df_train: pd.DataFrame) -> None:
        """Huấn luyện mô hình từ dữ liệu lịch sử"""
        pass

    @abstractmethod
    def predict_confidence(self, features_df: pd.DataFrame, signal_type: str) -> List[float]:
        """Dự đoán xác suất thành công của tín hiệu P(Win)"""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Lưu trọng số mô hình"""
        pass

    @abstractmethod
    def load(self, filepath: str) -> bool:
        """Tải mô hình đã lưu"""
        pass

class BaseRiskManager(ABC):
    """Giao diện chuẩn cho hệ thống quản trị rủi ro & bảo vệ vốn"""
    @abstractmethod
    def calculate_lot_size(self, balance: float, sl_points: float) -> float:
        """Tính khối lượng vào lệnh chuẩn theo số dư và rủi ro"""
        pass

    @abstractmethod
    def should_allow_entry(self, current_positions: List[Position], spread: float) -> bool:
        """Kiểm tra điều kiện an toàn trước khi vào lệnh"""
        pass

    @abstractmethod
    def update_positions_protection(self, positions: List[Position], current_price: float) -> List[Dict[str, Any]]:
        """Kiểm tra và trả về các lệnh cần dời SL (Breakeven / Trailing)"""
        pass

class BaseBroker(ABC):
    """Giao diện trừu tượng kết nối sàn (MT5, MT4, Binance, Simulated)"""
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        pass

    @abstractmethod
    def open_order(self, symbol: str, order_type: OrderType, volume: float, sl: float, tp: float, comment: str) -> Optional[int]:
        pass

    @abstractmethod
    def modify_order(self, ticket: int, new_sl: float, new_tp: float) -> bool:
        pass

    @abstractmethod
    def close_order(self, ticket: int) -> bool:
        pass

    @abstractmethod
    def get_open_positions(self, symbol: str, magic: int) -> List[Position]:
        pass
