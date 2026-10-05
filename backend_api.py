"""
Backend API Server (FastAPI + WebSocket + MetaTrader 5 Bridge)
Cung cấp REST API và Real-time WebSocket đồng bộ toàn bộ dữ liệu MT5 cho Frontend TypeScript
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import time
import json
import asyncio
import datetime
import threading
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config
from src.brokers.mt5_broker import MT5Broker
from src.strategies.composite import CompositeScalperStrategy
from src.ml.ai_gatekeeper import AIGatekeeperModel
from src.risk.risk_manager import StandardRiskManager
from src.core.types import OrderType

app = FastAPI(title="AI XAUUSD Scalper Real-Time Backend", version="2.0.0")

# CORS middleware cho phép Frontend TS kết nối mọi port (5173, 3000, ...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- QUẢN LÝ TRẠNG THÁI HỆ THỐNG -----------------
class SystemState:
    def __init__(self):
        self.bot_running: bool = False
        self.broker = MT5Broker()
        self.strategy = CompositeScalperStrategy()
        self.ai = AIGatekeeperModel()
        self.risk = StandardRiskManager()
        self.logs: List[Dict[str, Any]] = []
        self.max_logs: int = 150
        self.latest_analysis: Dict[str, Any] = {}
        self.latest_prediction: Dict[str, Any] = {
            "estimated_time": "Đang phân tích dữ liệu nến...",
            "estimated_bars": 0,
            "readiness_pct": 50,
            "bar_countdown": "05:00",
            "seconds_remaining": 300,
            "best_prob": 0.0,
            "target_prob": config.AI_CONFIDENCE_THRESHOLD,
            "status_text": "Đang khởi tạo thuật toán và đồng bộ dữ liệu MT5.",
            "status_level": "MONITORING",
            "checklist": {
                "market_open": True,
                "spread_ok": True,
                "confluence": False,
                "ai_ready": False
            }
        }
        self.connected_websockets: List[WebSocket] = []
        self.bot_thread: Optional[threading.Thread] = None

    def add_log(self, level: str, message: str):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {"time": now_str, "level": level, "message": message}
        self.logs.insert(0, entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop()

state = SystemState()

# ----------------- KIỂM TRA THỊ TRƯỜNG THEO GIỜ VN -----------------
def is_market_open_vn() -> tuple:
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=T2, 5=T7, 6=CN
    hour = now.hour
    if weekday == 5 and hour >= 5:
        return False, "Nghỉ cuối tuần (Thứ Bảy VN)"
    if weekday == 6:
        return False, "Nghỉ cuối tuần (Chủ Nhật VN)"
    if weekday == 0 and hour < 5:
        return False, "Chờ mở phiên tuần mới (Trước 05:00 sáng Thứ Hai)"
    return True, "Thị trường đang mở cửa"

# ----------------- VÒNG LẶP GIAO DỊCH NỀN CỦA BOT -----------------
def calculate_trade_prediction(last_bar, prob_buy: float, prob_sell: float, sym_info, open_pos_count: int, is_market_open: bool) -> dict:
    """Thuật toán dự đoán thông minh thời gian tới lệnh kế tiếp dựa trên hội tụ kỹ thuật & AI"""
    now = datetime.datetime.now()
    secs_into_candle = (now.minute % 5) * 60 + now.second
    secs_remaining = max(0, 300 - secs_into_candle)
    bar_countdown_str = f"{secs_remaining // 60:02d}:{secs_remaining % 60:02d}"

    if not is_market_open:
        return {
            "estimated_time": "Thị trường nghỉ giao dịch",
            "estimated_bars": 0,
            "readiness_pct": 0,
            "bar_countdown": bar_countdown_str,
            "seconds_remaining": secs_remaining,
            "best_prob": 0.0,
            "target_prob": config.AI_CONFIDENCE_THRESHOLD,
            "status_text": "Thị trường đang đóng cửa cuối tuần. Tự động giao dịch khi mở phiên Thứ Hai.",
            "status_level": "STANDBY",
            "checklist": {
                "market_open": False,
                "spread_ok": False,
                "confluence": False,
                "ai_ready": False
            }
        }

    if open_pos_count >= config.MAX_OPEN_POSITIONS:
        return {
            "estimated_time": "Đang có lệnh hoạt động",
            "estimated_bars": 0,
            "readiness_pct": 100,
            "bar_countdown": bar_countdown_str,
            "seconds_remaining": secs_remaining,
            "best_prob": max(prob_buy, prob_sell),
            "target_prob": config.AI_CONFIDENCE_THRESHOLD,
            "status_text": f"Đang giữ {open_pos_count} vị thế đa mục tiêu (TP1/TP2/TP3). Đợi chốt lời hoặc cắt lỗ trước khi vào lệnh mới.",
            "status_level": "ACTIVE_TRADE",
            "checklist": {
                "market_open": True,
                "spread_ok": True,
                "confluence": True,
                "ai_ready": True
            }
        }

    # Tính điểm sẵn sàng (Readiness Score 0 - 100)
    readiness = 0
    spread_ok = (sym_info.spread <= config.MAX_SPREAD) if sym_info else True
    if spread_ok:
        readiness += 10

    rsi = float(last_bar.get('rsi_7', 50)) if last_bar is not None else 50.0
    bb_pct_b = float(last_bar.get('bb_pct_b', 0.5)) if last_bar is not None else 0.5
    sqz = bool(last_bar.get('kc_squeeze', 0) == 1) if last_bar is not None else False

    # Độ lệch RSI tiến gần vùng quá bán (<35) hoặc quá mua (>65)
    if rsi <= 35 or rsi >= 65:
        readiness += 15
    elif rsi <= 42 or rsi >= 58:
        readiness += 8

    # Dải Bollinger Bands nén hoặc chạm cận
    if bb_pct_b <= 0.15 or bb_pct_b >= 0.85:
        readiness += 15
    elif bb_pct_b <= 0.30 or bb_pct_b >= 0.70:
        readiness += 8

    if sqz:
        readiness += 10

    raw_sig_buy = bool(last_bar.get('raw_signal_buy', False)) if last_bar is not None else False
    raw_sig_sell = bool(last_bar.get('raw_signal_sell', False)) if last_bar is not None else False
    confluence = raw_sig_buy or raw_sig_sell
    if confluence:
        readiness += 25

    best_prob = max(prob_buy, prob_sell)
    ai_points = min(25, int((best_prob / config.AI_CONFIDENCE_THRESHOLD) * 25))
    readiness += ai_points
    readiness = min(100, readiness)

    ai_ready = best_prob >= config.AI_CONFIDENCE_THRESHOLD

    if confluence and ai_ready:
        est_time = f"~1 - 2 phút (Đóng nến: {bar_countdown_str})"
        est_bars = 1
        status_text = "Hội tụ đủ 4 chiến thuật & AI duyệt xác suất thắng! Sắp mở 3 lệnh khi nến M5 kết thúc."
        status_level = "TRIGGER_IMMIMENT"
    elif best_prob >= 0.70 or readiness >= 75:
        est_time = "~5 - 15 phút (1 - 3 nến M5)"
        est_bars = 2
        status_text = f"Độ sẵn sàng cao ({readiness}%). Đang tích lũy setup và chờ AI đạt ngưỡng {config.AI_CONFIDENCE_THRESHOLD*100:.0f}%."
        status_level = "VERY_CLOSE"
    elif readiness >= 50 or best_prob >= 0.55:
        est_time = "~15 - 35 phút (3 - 7 nến M5)"
        est_bars = 5
        status_text = "Giá đang tiến sát vùng kích hoạt (Overbought/Oversold/Squeeze). Đang theo dõi nén biên độ."
        status_level = "APPROACHING"
    elif readiness >= 30:
        est_time = "~40 - 75 phút (8 - 15 nến M5)"
        est_bars = 10
        status_text = "Thị trường đang hình thành cấu trúc sóng. Chờ nhịp Pullback hoặc Breakout hợp lệ."
        status_level = "WAITING"
    else:
        est_time = "~1.5 - 2.5 giờ (Tần suất chuẩn)"
        est_bars = 25
        status_text = "Thị trường đi ngang / Sideway nhẹ. Bot bảo vệ an toàn vốn, chỉ kích hoạt khi xác suất thắng cao."
        status_level = "MONITORING"

    return {
        "estimated_time": est_time,
        "estimated_bars": est_bars,
        "readiness_pct": readiness,
        "bar_countdown": bar_countdown_str,
        "seconds_remaining": secs_remaining,
        "best_prob": round(best_prob, 3),
        "target_prob": config.AI_CONFIDENCE_THRESHOLD,
        "status_text": status_text,
        "status_level": status_level,
        "checklist": {
            "market_open": is_market_open,
            "spread_ok": spread_ok,
            "confluence": confluence,
            "ai_ready": ai_ready
        }
    }

def bot_worker_loop():
    """Luồng chạy nền tự động quét nến, bắt lệnh và quản lý Breakeven"""
    state.add_log("INFO", "Bot Trade Tự Động đã được KÍCH HOẠT.")
    
    while state.bot_running:
        try:
            # 1. Kiểm tra thị trường cuối tuần
            is_open, msg = is_market_open_vn()
            if not is_open:
                state.latest_prediction = calculate_trade_prediction(None, 0.0, 0.0, None, 0, False)
                time.sleep(10)
                continue
                
            # 2. Quản lý dời SL Breakeven cho các lệnh đang mở
            open_positions = state.broker.get_open_positions(config.SYMBOL)
            sym_info = state.broker.get_symbol_info(config.SYMBOL)
            if sym_info and open_positions:
                protections = state.risk.update_positions_protection(
                    open_positions, sym_info.bid, sym_info.ask, sym_info.point
                )
                for mod in protections:
                    state.add_log("SUCCESS", f"Dời SL Breakeven lệnh #{mod['ticket']} -> {mod['new_sl']} (+{mod['profit_pts']:.0f} pts)")
                    state.broker.modify_order(mod['ticket'], mod['new_sl'], mod['new_tp'])
                    
            # 3. Quét nến và tìm kiếm cơ hội nếu chưa đủ vị thế tối đa
            if sym_info and len(open_positions) < config.MAX_OPEN_POSITIONS:
                if sym_info.spread <= config.MAX_SPREAD:
                    df_raw = state.broker.get_market_data(config.SYMBOL, config.TIMEFRAME, 250)
                    if not df_raw.empty and len(df_raw) >= 210:
                        df_sig = state.strategy.generate_signals(df_raw)
                        last_bar = df_sig.iloc[-1]
                        feature_row = df_sig.iloc[[-1]]
                        
                        # Cập nhật phân tích thị trường thời gian thực
                        prob_buy = float(state.ai.predict_confidence(feature_row, "BUY")[0]) if state.ai.buy_rf else 0.0
                        prob_sell = float(state.ai.predict_confidence(feature_row, "SELL")[0]) if state.ai.sell_rf else 0.0
                        
                        state.latest_analysis = {
                            "time": str(last_bar['time']),
                            "rsi_7": round(float(last_bar.get('rsi_7', 50)), 1),
                            "rsi_14": round(float(last_bar.get('rsi_14', 50)), 1),
                            "bb_pct_b": round(float(last_bar.get('bb_pct_b', 0.5)), 2),
                            "adx_14": round(float(last_bar.get('adx_14', 20)), 1),
                            "trend": "BULLISH" if last_bar.get('trend_bullish') else ("BEARISH" if last_bar.get('trend_bearish') else "NEUTRAL"),
                            "squeeze_on": bool(last_bar.get('kc_squeeze', 0) == 1),
                            "liquidity_sweep_bull": bool(last_bar.get('liquidity_sweep_bull', 0) == 1),
                            "liquidity_sweep_bear": bool(last_bar.get('liquidity_sweep_bear', 0) == 1),
                            "prob_buy": round(prob_buy, 3),
                            "prob_sell": round(prob_sell, 3),
                            "signal_buy": bool(last_bar.get('raw_signal_buy', False)),
                            "signal_sell": bool(last_bar.get('raw_signal_sell', False))
                        }

                        # Cập nhật dự đoán thời điểm vào lệnh tiếp theo
                        state.latest_prediction = calculate_trade_prediction(
                            last_bar, prob_buy, prob_sell, sym_info, len(open_positions), is_open
                        )
                        
                        # Kích hoạt mở cụm 3 lệnh nếu AI chấp thuận
                        if last_bar.get('raw_signal_buy') and prob_buy >= config.AI_CONFIDENCE_THRESHOLD:
                            state.add_log("TRADE", f"AI Duyệt BUY ({prob_buy*100:.1f}%)! Đang mở cụm 3 lệnh đa mục tiêu...")
                            open_3tier_order(OrderType.BUY, sym_info.ask, sym_info)
                            
                        elif last_bar.get('raw_signal_sell') and prob_sell >= config.AI_CONFIDENCE_THRESHOLD:
                            state.add_log("TRADE", f"AI Duyệt SELL ({prob_sell*100:.1f}%)! Đang mở cụm 3 lệnh đa mục tiêu...")
                            open_3tier_order(OrderType.SELL, sym_info.bid, sym_info)
            elif sym_info and len(open_positions) >= config.MAX_OPEN_POSITIONS:
                state.latest_prediction = calculate_trade_prediction(
                    None, 0.0, 0.0, sym_info, len(open_positions), is_open
                )
                            
            time.sleep(3)
        except Exception as e:
            state.add_log("ERROR", f"Lỗi vòng lặp bot: {str(e)}")
            time.sleep(5)
            
    state.add_log("WARNING", "Bot Trade Tự Động đã TẠM DỪNG.")

def open_3tier_order(order_type: OrderType, price: float, sym_info):
    """Mở cụm 3 lệnh con TP1 (12p), TP2 (22p), TP3 (35p)"""
    point = sym_info.point
    is_buy = (order_type == OrderType.BUY)
    init_sl = round(price - (config.SL_POINTS * point), 2) if is_buy else round(price + (config.SL_POINTS * point), 2)
    
    tiers = [
        ("T1 (Scalp 12p)", config.TIER1_LOT, config.TIER1_TP_POINTS),
        ("T2 (Standard 22p)", config.TIER2_LOT, config.TIER2_TP_POINTS),
        ("T3 (Runner 35p)", config.TIER3_LOT, config.TIER3_TP_POINTS),
    ]
    
    for name, lot, tp_pts in tiers:
        tp = round(price + (tp_pts * point), 2) if is_buy else round(price - (tp_pts * point), 2)
        ticket = state.broker.open_order(config.SYMBOL, order_type, lot, init_sl, tp, f"AI Scalper {name}")
        if ticket:
            state.add_log("SUCCESS", f"Khớp lệnh {name}: {order_type.value} {lot} lot tại {price:.2f} (Vé #{ticket})")

# ----------------- KHỞI TẠO HỆ THỐNG KHI SERVER KHỞI CHẠY -----------------
@app.on_event("startup")
def startup_event():
    print("[Backend] Đang kết nối MetaTrader 5...")
    if state.broker.connect():
        state.add_log("INFO", f"Kết nối MT5 thành công (Tài khoản: {config.LOGIN})")
    else:
        state.add_log("ERROR", "Không thể kết nối MT5 terminal!")
        
    if state.ai.load():
        state.add_log("INFO", "Tải trọng số mô hình AI Ensemble thành công.")
    else:
        state.add_log("WARNING", "Chưa tìm thấy mô hình AI, vui lòng huấn luyện lại!")

    # TỰ ĐỘNG BẬT BOT KHI KHỞI CHẠY (1-Click Autostart)
    state.bot_running = True
    state.bot_thread = threading.Thread(target=bot_worker_loop, daemon=True)
    state.bot_thread.start()
    state.add_log("SUCCESS", "Hệ thống đã TỰ ĐỘNG KÍCH HOẠT Bot Trade và kết nối trực tiếp với MT5!")

@app.on_event("shutdown")
def shutdown_event():
    state.bot_running = False
    state.broker.disconnect()

# ----------------- REST API ENDPOINTS -----------------
@app.get("/api/status")
def get_system_status():
    acc = state.broker.get_account_info()
    sym_info = state.broker.get_symbol_info(config.SYMBOL)
    is_open, msg = is_market_open_vn()
    open_pos = state.broker.get_open_positions(config.SYMBOL)
    
    return {
        "bot_running": state.bot_running,
        "market_open": is_open,
        "market_status_message": msg,
        "symbol": config.SYMBOL,
        "timeframe": config.TIMEFRAME,
        "account": {
            "login": acc.get("login", config.LOGIN),
            "server": acc.get("server", config.SERVER),
            "balance": acc.get("balance", 5000.0),
            "equity": acc.get("equity", 5000.0),
            "floating_profit": acc.get("profit", 0.0),
            "margin": acc.get("margin", 0.0),
            "margin_free": acc.get("margin_free", 5000.0),
            "leverage": acc.get("leverage", 100)
        },
        "market": {
            "bid": sym_info.bid if sym_info else 0.0,
            "ask": sym_info.ask if sym_info else 0.0,
            "spread_points": sym_info.spread if sym_info else 0,
            "spread_usd": round(sym_info.spread * 0.01, 2) if sym_info else 0.0
        },
        "open_positions_count": len(open_pos),
        "ai_threshold": config.AI_CONFIDENCE_THRESHOLD,
        "analysis": state.latest_analysis,
        "prediction": state.latest_prediction,
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/positions")
def get_open_positions():
    raw_positions = state.broker.get_open_positions(config.SYMBOL)
    sym_info = state.broker.get_symbol_info(config.SYMBOL)
    positions_data = []
    
    for p in raw_positions:
        cur_price = sym_info.bid if p.order_type == OrderType.BUY else sym_info.ask
        diff_pts = (cur_price - p.entry_price) / sym_info.point if p.order_type == OrderType.BUY else (p.entry_price - cur_price) / sym_info.point
        is_be = (p.sl >= p.entry_price) if p.order_type == OrderType.BUY else (p.sl <= p.entry_price and p.sl > 0)
        
        positions_data.append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": p.order_type.value,
            "volume": p.volume,
            "entry_price": p.entry_price,
            "entry_time": str(p.entry_time),
            "sl": p.sl,
            "tp": p.tp,
            "current_price": cur_price,
            "profit": round(p.profit, 2),
            "profit_points": round(diff_pts, 0),
            "is_breakeven": is_be
        })
    return positions_data

@app.post("/api/bot/toggle")
def toggle_bot():
    state.bot_running = not state.bot_running
    if state.bot_running:
        state.bot_thread = threading.Thread(target=bot_worker_loop, daemon=True)
        state.bot_thread.start()
    return {"bot_running": state.bot_running}

@app.post("/api/trades/test-entry")
def test_trade_entry(direction: str = "BUY"):
    """Thử nghiệm vào ngay 1 cụm 3 lệnh (BUY hoặc SELL) để test chức năng tự động"""
    sym_info = state.broker.get_symbol_info(config.SYMBOL)
    if not sym_info:
        raise HTTPException(status_code=500, detail="Không lấy được thông tin thị trường MT5")
    
    order_type = OrderType.BUY if direction.upper() == "BUY" else OrderType.SELL
    price = sym_info.ask if order_type == OrderType.BUY else sym_info.bid
    
    state.add_log("TRADE", f"[TEST THỦ CÔNG] Yêu cầu test vào cụm 3 lệnh {order_type.value} tại giá {price:.2f}...")
    open_3tier_order(order_type, price, sym_info)
    
    open_positions = state.broker.get_open_positions(config.SYMBOL)
    return {
        "status": "success",
        "direction": direction.upper(),
        "price": price,
        "open_positions_count": len(open_positions),
        "message": f"Đã gửi lệnh {direction.upper()} 3-Tier tới MT5"
    }

@app.post("/api/trades/close-all")
def close_all_trades():
    positions = state.broker.get_open_positions(config.SYMBOL)
    closed = 0
    for p in positions:
        if state.broker.close_order(p.ticket):
            closed += 1
            state.add_log("WARNING", f"Khẩn cấp đóng lệnh #{p.ticket}")
    return {"closed_count": closed, "total": len(positions)}

@app.post("/api/trades/close/{ticket}")
def close_single_trade(ticket: int):
    success = state.broker.close_order(ticket)
    if success:
        state.add_log("INFO", f"Đã đóng thủ công lệnh #{ticket}")
        return {"status": "success", "ticket": ticket}
    raise HTTPException(status_code=400, detail="Không thể đóng lệnh")

@app.get("/api/logs")
def get_recent_logs():
    return state.logs

# ----------------- REAL-TIME WEBSOCKET STREAM -----------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.connected_websockets.append(websocket)
    state.add_log("INFO", "Giao diện Frontend TS đã kết nối WebSocket.")
    
    try:
        while True:
            # Thu thập toàn bộ trạng thái thời gian thực và đẩy về Client mỗi 1 giây
            acc = state.broker.get_account_info()
            sym_info = state.broker.get_symbol_info(config.SYMBOL)
            is_open, msg = is_market_open_vn()
            raw_pos = state.broker.get_open_positions(config.SYMBOL)
            
            # Tính toán đồng hồ đếm ngược nến M5 thời gian thực từng giây
            now_dt = datetime.datetime.now()
            secs_into_candle = (now_dt.minute % 5) * 60 + now_dt.second
            secs_remaining = max(0, 300 - secs_into_candle)
            bar_countdown_str = f"{secs_remaining // 60:02d}:{secs_remaining % 60:02d}"

            pred_payload = dict(state.latest_prediction) if state.latest_prediction else {}
            pred_payload["bar_countdown"] = bar_countdown_str
            pred_payload["seconds_remaining"] = secs_remaining
            
            positions_list = []
            for p in raw_pos:
                cur_p = (sym_info.bid if p.order_type == OrderType.BUY else sym_info.ask) if sym_info else p.entry_price
                diff_pts = ((cur_p - p.entry_price) / sym_info.point if p.order_type == OrderType.BUY else (p.entry_price - cur_p) / sym_info.point) if sym_info else 0
                is_be = (p.sl >= p.entry_price) if p.order_type == OrderType.BUY else (p.sl <= p.entry_price and p.sl > 0)
                positions_list.append({
                    "ticket": p.ticket,
                    "type": p.order_type.value,
                    "volume": p.volume,
                    "entry_price": p.entry_price,
                    "entry_time": str(p.entry_time),
                    "sl": p.sl,
                    "tp": p.tp,
                    "current_price": cur_p,
                    "profit": round(p.profit, 2),
                    "profit_points": round(diff_pts, 0),
                    "is_breakeven": is_be
                })
                
            payload = {
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "bot_running": state.bot_running,
                "market_open": is_open,
                "market_status_message": msg,
                "account": {
                    "login": acc.get("login", config.LOGIN),
                    "server": acc.get("server", config.SERVER),
                    "balance": acc.get("balance", 5000.0),
                    "equity": acc.get("equity", 5000.0),
                    "floating_profit": acc.get("profit", 0.0),
                    "margin": acc.get("margin", 0.0),
                    "margin_free": acc.get("margin_free", 5000.0),
                    "leverage": acc.get("leverage", 100)
                },
                "ticker": {
                    "symbol": config.SYMBOL,
                    "bid": sym_info.bid if sym_info else 0.0,
                    "ask": sym_info.ask if sym_info else 0.0,
                    "spread": sym_info.spread if sym_info else 0
                },
                "positions": positions_list,
                "analysis": state.latest_analysis,
                "prediction": pred_payload,
                "logs": state.logs[:25]
            }
            
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
            
    except WebSocketDisconnect:
        if websocket in state.connected_websockets:
            state.connected_websockets.remove(websocket)
    except Exception as e:
        if websocket in state.connected_websockets:
            state.connected_websockets.remove(websocket)

# ----------------- PHỤC VỤ GIAO DIỆN FRONTEND BUILD TĨNH (NẾU CÓ) -----------------
dist_dir = os.path.join(os.path.dirname(__file__), "dashboard", "dist")
if os.path.exists(dist_dir):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse
    
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Né các đường dẫn api và websocket
        if full_path.startswith("api") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(
            os.path.join(dist_dir, "index.html"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

if __name__ == "__main__":
    import uvicorn
    print("[Backend API] Khởi động Uvicorn server tại http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
