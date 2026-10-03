"""
Core Domain Types and Data Structures
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import pandas as pd

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class ExitReason(Enum):
    TAKE_PROFIT = "TP"
    STOP_LOSS = "SL"
    BREAKEVEN = "BREAKEVEN"
    TRAILING_STOP = "TRAILING_STOP"
    MANUAL = "MANUAL"
    TIMEOUT = "TIMEOUT"

class MarketRegime(Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"

@dataclass
class TradeSignal:
    timestamp: pd.Timestamp
    symbol: str
    order_type: OrderType
    strategy_name: str
    confidence: float = 1.0
    suggested_entry: float = 0.0
    suggested_sl: float = 0.0
    suggested_tp: float = 0.0
    metadata: dict = field(default_factory=dict)

@dataclass
class Position:
    ticket: int
    symbol: str
    order_type: OrderType
    volume: float
    entry_price: float
    entry_time: pd.Timestamp
    sl: float
    tp: float
    current_price: float = 0.0
    profit: float = 0.0
    magic: int = 0
    is_breakeven_activated: bool = False
    metadata: dict = field(default_factory=dict)

@dataclass
class ClosedTrade:
    ticket: int
    symbol: str
    order_type: OrderType
    volume: float
    entry_price: float
    entry_time: pd.Timestamp
    exit_price: float
    exit_time: pd.Timestamp
    profit: float
    exit_reason: ExitReason
    commission: float = 0.0
    swap: float = 0.0
    pnl_percent: float = 0.0
