import { useState, useEffect, useRef } from 'react';
import { 
  Play, Pause, AlertOctagon, TrendingUp, TrendingDown, Shield, 
  Activity, DollarSign, Wallet, Layers, CheckCircle2, 
  Clock, Zap, Wifi, WifiOff, X, BarChart2, Timer
} from 'lucide-react';
import type { WebSocketPayload } from './types';

// Tự động thích ứng môi trường Deploy (Localhost, Remote Cloud VPS IP, hoặc Vercel)
const isBrowser = typeof window !== 'undefined';
const protocol = isBrowser && window.location.protocol === 'https:' ? 'https:' : 'http:';
const wsProtocol = isBrowser && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const currentHost = isBrowser ? window.location.host : '127.0.0.1:8000';

const API_URL = import.meta.env.VITE_API_URL || `${protocol}//${currentHost}`;
const WS_URL = import.meta.env.VITE_WS_URL || `${wsProtocol}//${currentHost}/ws`;

export function App() {
  const [data, setData] = useState<WebSocketPayload | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const logContainerRef = useRef<HTMLDivElement | null>(null);

  // Kết nối WebSocket thời gian thực tự động phục hồi kết nối
  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload: WebSocketPayload = JSON.parse(event.data);
          setData(payload);
        } catch (e) {
          console.error("Lỗi parse WS payload:", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Tự động cuộn log mới nhất
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [data?.logs]);

  // Hành động Bật/Tắt Bot
  const handleToggleBot = async () => {
    try {
      setActionLoading(true);
      await fetch(`${API_URL}/api/bot/toggle`, { method: 'POST' });
    } catch (e) {
      alert("Lỗi kết nối Backend API!");
    } finally {
      setActionLoading(false);
    }
  };

  // Hành động Đóng khẩn cấp tất cả lệnh
  const handleCloseAll = async () => {
    if (!window.confirm("BẠN CÓ CHẮC CHẮN muốn đóng khẩn cấp toàn bộ các lệnh đang mở trên MT5?")) return;
    try {
      setActionLoading(true);
      const res = await fetch(`${API_URL}/api/trades/close-all`, { method: 'POST' });
      const result = await res.json();
      alert(`Đã đóng ${result.closed_count} lệnh thành công!`);
    } catch (e) {
      alert("Lỗi đóng lệnh khẩn cấp!");
    } finally {
      setActionLoading(false);
    }
  };

  // Đóng 1 lệnh đơn lẻ
  const handleCloseSingle = async (ticket: number) => {
    if (!window.confirm(`Đóng lệnh #${ticket}?`)) return;
    try {
      await fetch(`${API_URL}/api/trades/close/${ticket}`, { method: 'POST' });
    } catch (e) {
      alert(`Lỗi đóng lệnh #${ticket}`);
    }
  };

  // Thử nghiệm vào lệnh tức thì (BUY / SELL cụm 3 lệnh)
  const handleTestEntry = async (direction: 'BUY' | 'SELL') => {
    if (!window.confirm(`Xác nhận thử nghiệm mở ngay cụm 3 lệnh ${direction} trên MT5 để kiểm tra chức năng tự động?`)) return;
    try {
      setActionLoading(true);
      const res = await fetch(`${API_URL}/api/trades/test-entry?direction=${direction}`, { method: 'POST' });
      const result = await res.json();
      if (res.ok) {
        alert(`[THÀNH CÔNG] ${result.message} tại giá ${result.price}!`);
      } else {
        alert(`[THẤT BẠI] ${result.detail || 'Không thể mở lệnh'}`);
      }
    } catch (e) {
      alert("Lỗi kết nối Backend API!");
    } finally {
      setActionLoading(false);
    }
  };

  const account = data?.account;
  const ticker = data?.ticker;
  const analysis = data?.analysis;
  const prediction = data?.prediction;
  const positions = data?.positions || [];
  const logs = data?.logs || [];
  const isMarketOpen = data?.market_open ?? false;
  const isBotRunning = data?.bot_running ?? false;

  const floatingProfit = account?.floating_profit || 0;
  const isProfitPositive = floatingProfit >= 0;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 1. TOP HEADER & NAVIGATION */}
      <header style={{ 
        borderBottom: '1px solid rgba(255,255,255,0.08)', 
        background: 'rgba(11, 15, 25, 0.85)', 
        backdropFilter: 'blur(16px)',
        position: 'sticky', top: 0, zIndex: 50,
        padding: '14px 28px'
      }}>
        <div style={{ maxWidth: '1600px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          
          {/* Logo & Identity */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ 
              width: '42px', height: '42px', borderRadius: '10px', 
              background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 20px rgba(245, 158, 11, 0.4)'
            }}>
              <Zap style={{ color: '#000', width: '24px', height: '24px' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.5px' }}>AI XAUUSD SCALPER PRO</h1>
                <span style={{ 
                  background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B', 
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 700 
                }}>V2.0 LIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                Forward Testing Dashboard • MetaTrader 5 Bridge
              </p>
            </div>
          </div>

          {/* Status Badges & Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            
            {/* WebSocket connection badge */}
            <div style={{ 
              display: 'flex', alignItems: 'center', gap: '6px', 
              background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${isConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              padding: '6px 12px', borderRadius: '8px', fontSize: '12px',
              color: isConnected ? '#10B981' : '#EF4444'
            }}>
              {isConnected ? <Wifi size={14} className="pulse-active" /> : <WifiOff size={14} />}
              <span>{isConnected ? "WS Live" : "Mất kết nối"}</span>
            </div>

            {/* Market Session Status */}
            <div style={{ 
              display: 'flex', alignItems: 'center', gap: '6px', 
              background: isMarketOpen ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
              border: `1px solid ${isMarketOpen ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
              padding: '6px 14px', borderRadius: '8px', fontSize: '12px',
              color: isMarketOpen ? '#10B981' : '#F59E0B'
            }}>
              <span style={{ 
                width: '8px', height: '8px', borderRadius: '50%', 
                background: isMarketOpen ? '#10B981' : '#F59E0B' 
              }} className={isMarketOpen ? "pulse-active" : "pulse-standby"}></span>
              <span>{isMarketOpen ? "Thị trường Mở Cửa" : "Nghỉ Cuối Tuần (Standby)"}</span>
            </div>

            {/* MT5 Account Pill */}
            <div style={{ 
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              padding: '6px 14px', borderRadius: '8px', fontSize: '12px', display: 'flex', gap: '6px'
            }}>
              <span style={{ color: '#94A3B8' }}>MT5 Demo:</span>
              <strong style={{ color: '#F8FAFC' }}>#{account?.login || 113569040}</strong>
              <span style={{ color: '#64748B' }}>({account?.server || 'MetaQuotes'})</span>
            </div>

            {/* Master Bot Action Button */}
            <button
              onClick={handleToggleBot}
              disabled={actionLoading}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 18px', borderRadius: '8px', fontWeight: 700, fontSize: '13px',
                cursor: 'pointer', border: 'none', transition: 'all 0.2s ease',
                background: isBotRunning ? '#EF4444' : 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                color: '#fff',
                boxShadow: isBotRunning ? '0 0 15px rgba(239, 68, 68, 0.4)' : '0 0 15px rgba(16, 185, 129, 0.4)'
              }}
            >
              {isBotRunning ? <Pause size={16} /> : <Play size={16} />}
              <span>{isBotRunning ? "DỪNG BOT" : "KÍCH HOẠT BOT"}</span>
            </button>

            {/* Panic Close All Button */}
            <button
              onClick={handleCloseAll}
              disabled={actionLoading || positions.length === 0}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 14px', borderRadius: '8px', fontWeight: 600, fontSize: '12px',
                cursor: positions.length === 0 ? 'not-allowed' : 'pointer',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#EF4444',
                opacity: positions.length === 0 ? 0.4 : 1
              }}
            >
              <AlertOctagon size={15} />
              <span>Đóng Tất Cả</span>
            </button>

          </div>
        </div>
      </header>

      {/* 2. MAIN DASHBOARD CONTENT */}
      <main style={{ maxWidth: '1600px', margin: '0 auto', padding: '24px 28px', flex: 1, width: '100%' }}>
        
        {/* Weekend Banner if Market is closed */}
        {!isMarketOpen && (
          <div style={{
            background: 'linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '12px', padding: '14px 20px', marginBottom: '24px',
            display: 'flex', alignItems: 'center', gap: '14px'
          }}>
            <Clock style={{ color: '#F59E0B', width: '24px', height: '24px', flexShrink: 0 }} />
            <div>
              <h4 style={{ color: '#F59E0B', fontWeight: 700, fontSize: '14px' }}>
                Thị trường Vàng Quốc Tế đang đóng cửa nghỉ cuối tuần (Thứ Bảy & Chủ Nhật theo giờ VN)
              </h4>
              <p style={{ color: '#CBD5E1', fontSize: '12px', marginTop: '2px' }}>
                Giá Vàng và nến trên MT5 đang tạm ngừng giao dịch. Khi bạn kích hoạt nút <strong>KÍCH HOẠT BOT</strong>, bot sẽ chuyển sang chế độ Standby và <strong>tự động bắt đầu quét giao dịch ngay khi sàn mở cửa vào rạng sáng Thứ Hai (~05:00 - 06:00 giờ VN)</strong>.
              </p>
            </div>
          </div>
        )}

        {/* METRICS KPI CARDS (5 Cards) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '24px' }}>
          
          {/* Card 1: Balance */}
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '12px', fontWeight: 600 }}>
              <span>SỐ DƯ (BALANCE)</span>
              <Wallet size={16} style={{ color: '#F59E0B' }} />
            </div>
            <div className="mono" style={{ fontSize: '26px', fontWeight: 800, marginTop: '8px', color: '#F8FAFC' }}>
              ${account ? account.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "5,000.00"}
            </div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '6px' }}>
              Vốn ban đầu: $5,000.00 USD
            </div>
          </div>

          {/* Card 2: Equity */}
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '12px', fontWeight: 600 }}>
              <span>TÀI SẢN (EQUITY)</span>
              <DollarSign size={16} style={{ color: '#3B82F6' }} />
            </div>
            <div className="mono" style={{ 
              fontSize: '26px', fontWeight: 800, marginTop: '8px', 
              color: isProfitPositive ? '#10B981' : '#EF4444' 
            }}>
              ${account ? account.equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "5,000.00"}
            </div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '6px' }}>
              Đòn bẩy: 1:{account?.leverage || 100}
            </div>
          </div>

          {/* Card 3: Floating PnL */}
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '12px', fontWeight: 600 }}>
              <span>LỢI NHUẬN THẢ NỔI</span>
              {isProfitPositive ? <TrendingUp size={16} style={{ color: '#10B981' }} /> : <TrendingDown size={16} style={{ color: '#EF4444' }} />}
            </div>
            <div className="mono" style={{ 
              fontSize: '26px', fontWeight: 800, marginTop: '8px', 
              color: isProfitPositive ? '#10B981' : '#EF4444' 
            }}>
              {floatingProfit > 0 ? `+${floatingProfit.toFixed(2)}` : floatingProfit.toFixed(2)} USD
            </div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '6px' }}>
              {positions.length} vị thế đang mở
            </div>
          </div>

          {/* Card 4: Free Margin */}
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '12px', fontWeight: 600 }}>
              <span>KÝ QUỸ CÒN DƯ</span>
              <Shield size={16} style={{ color: '#10B981' }} />
            </div>
            <div className="mono" style={{ fontSize: '26px', fontWeight: 800, marginTop: '8px', color: '#F8FAFC' }}>
              ${account ? account.margin_free.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "5,000.00"}
            </div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '6px' }}>
              Margin sử dụng: ${account ? account.margin.toFixed(2) : "0.00"}
            </div>
          </div>

          {/* Card 5: Live Gold Ticker */}
          <div className="glass-panel" style={{ padding: '20px', background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(16, 22, 36, 0.75) 100%)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#F59E0B', fontSize: '12px', fontWeight: 700 }}>
              <span>XAUUSD (VÀNG) M5</span>
              <Activity size={16} />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginTop: '8px' }}>
              <span className="mono" style={{ fontSize: '22px', fontWeight: 800, color: '#F8FAFC' }}>
                {ticker ? ticker.bid.toFixed(2) : "4,580.00"}
              </span>
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>/ {ticker ? ticker.ask.toFixed(2) : "4,580.35"}</span>
            </div>
            <div style={{ fontSize: '11px', color: '#F59E0B', marginTop: '6px', fontWeight: 600 }}>
              Spread: {ticker?.spread || 35} points (${((ticker?.spread || 35) * 0.01).toFixed(2)})
            </div>
          </div>

        </div>

        {/* PREDICTOR & AUTO-ENTRY RADAR (DỰ ĐOÁN THỜI ĐIỂM VÀO LỆNH TIẾP THEO) */}
        <div className="glass-panel" style={{ 
          padding: '22px 26px', 
          marginBottom: '24px',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
          display: 'grid',
          gridTemplateColumns: '1.4fr 1.2fr 1fr',
          gap: '24px',
          alignItems: 'center'
        }}>
          {/* Cột 1: Thời gian ước tính & Đếm ngược nến M5 */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Timer size={18} style={{ color: '#F59E0B' }} />
              <span style={{ fontSize: '13px', fontWeight: 800, letterSpacing: '0.5px', color: '#F59E0B', textTransform: 'uppercase' }}>
                Dự Đoán Thời Điểm Vào Lệnh (Next Trade Predictor)
              </span>
              <span style={{
                background: prediction?.status_level === 'TRIGGER_IMMIMENT' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.15)',
                color: prediction?.status_level === 'TRIGGER_IMMIMENT' ? '#10B981' : '#60A5FA',
                border: `1px solid ${prediction?.status_level === 'TRIGGER_IMMIMENT' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(59, 130, 246, 0.3)'}`,
                padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700
              }}>
                Khung M5 XAUUSD
              </span>
            </div>

            {/* Thời gian dự kiến lớn, nổi bật */}
            <div className="mono" style={{ 
              fontSize: '24px', fontWeight: 800, color: '#F8FAFC',
              display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px'
            }}>
              <span>{prediction?.estimated_time || "Đang tính toán..."}</span>
            </div>

            {/* Mô tả trạng thái chi tiết */}
            <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '6px', lineHeight: '1.4' }}>
              {prediction?.status_text || "Đang theo dõi chu kỳ nén nến và xác suất hội tụ của 4 chiến thuật AI."}
            </p>

            {/* Đồng hồ đếm ngược nến M5 */}
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginTop: '10px', background: 'rgba(255, 255, 255, 0.05)', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <Clock size={13} style={{ color: '#38BDF8' }} />
              <span style={{ fontSize: '11px', color: '#94A3B8' }}>Đóng nến M5 sau:</span>
              <strong className="mono" style={{ fontSize: '12px', color: '#38BDF8' }}>
                {prediction?.bar_countdown || "05:00"}
              </strong>
            </div>
          </div>

          {/* Cột 2: Thanh tiến trình Sẵn Sàng Vào Lệnh & Checklist 4 Điều Kiện */}
          <div style={{ borderLeft: '1px solid rgba(255,255,255,0.08)', borderRight: '1px solid rgba(255,255,255,0.08)', padding: '0 20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#CBD5E1' }}>ĐỘ SẴN SÀNG VÀO LỆNH (READINESS)</span>
              <span className="mono" style={{ 
                fontSize: '16px', fontWeight: 800, 
                color: (prediction?.readiness_pct || 0) >= 80 ? '#10B981' : ((prediction?.readiness_pct || 0) >= 50 ? '#F59E0B' : '#94A3B8') 
              }}>
                {prediction?.readiness_pct ?? 0}%
              </span>
            </div>

            {/* Thanh tiến trình Readiness */}
            <div style={{ height: '10px', background: 'rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${Math.max(prediction?.readiness_pct || 5, 5)}%`,
                background: (prediction?.readiness_pct || 0) >= 80 ? 
                  'linear-gradient(90deg, #10B981 0%, #34D399 100%)' : 
                  'linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)',
                borderRadius: '6px',
                transition: 'width 0.4s ease'
              }} />
            </div>

            {/* Checklist 4 điều kiện cốt lõi */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: prediction?.checklist?.market_open ? '#10B981' : '#EF4444' }}>
                <CheckCircle2 size={13} />
                <span>Thị trường Mở</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: prediction?.checklist?.spread_ok ? '#10B981' : '#94A3B8' }}>
                <CheckCircle2 size={13} />
                <span>Spread an toàn</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: prediction?.checklist?.confluence ? '#10B981' : '#94A3B8' }}>
                <CheckCircle2 size={13} />
                <span>4-Engine Signal</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: prediction?.checklist?.ai_ready ? '#10B981' : '#94A3B8' }}>
                <CheckCircle2 size={13} />
                <span>AI Duyệt (&ge;78%)</span>
              </div>
            </div>
          </div>

          {/* Cột 3: Nút Test Trigger Vào Lệnh Tức Thì */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>
              ⚡ Thử Nghiệm Tự Động (Test Triggers)
            </span>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => handleTestEntry('BUY')}
                disabled={actionLoading}
                style={{
                  flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.4)',
                  background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', fontWeight: 700, fontSize: '12px',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                  transition: 'all 0.2s ease'
                }}
              >
                <TrendingUp size={14} />
                <span>TEST BUY</span>
              </button>
              <button
                onClick={() => handleTestEntry('SELL')}
                disabled={actionLoading}
                style={{
                  flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.4)',
                  background: 'rgba(239, 68, 68, 0.15)', color: '#EF4444', fontWeight: 700, fontSize: '12px',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                  transition: 'all 0.2s ease'
                }}
              >
                <TrendingDown size={14} />
                <span>TEST SELL</span>
              </button>
            </div>
            <span style={{ fontSize: '10px', color: '#64748B' }}>
              * Bấm để mở ngay cụm 3 lệnh (TP1 12p, TP2 22p, TP3 35p) kiểm tra tự động dời SL Breakeven.
            </span>
          </div>
        </div>

        {/* 3. CENTER SPLIT GRID (Active Trades vs AI Analysis) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '20px', marginBottom: '24px' }}>
          
          {/* LEFT: ACTIVE TRADES & MULTI-TIER SCALE-OUT MONITOR */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Layers size={18} style={{ color: '#F59E0B' }} />
                <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Vị Thế Đang Mở & Quản Trị Đa Mục Tiêu</h3>
                <span style={{ 
                  background: 'rgba(255,255,255,0.06)', padding: '2px 8px', 
                  borderRadius: '12px', fontSize: '12px', color: '#94A3B8' 
                }}>{positions.length} Lệnh</span>
              </div>

              {/* 3-Tier Multi-Target Quick Badges */}
              <div style={{ display: 'flex', gap: '6px' }}>
                <span style={{ fontSize: '11px', background: 'rgba(16, 185, 129, 0.1)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '3px 8px', borderRadius: '6px' }}>
                  T1: 12p
                </span>
                <span style={{ fontSize: '11px', background: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6', border: '1px solid rgba(59, 130, 246, 0.25)', padding: '3px 8px', borderRadius: '6px' }}>
                  T2: 22p
                </span>
                <span style={{ fontSize: '11px', background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B', border: '1px solid rgba(245, 158, 11, 0.25)', padding: '3px 8px', borderRadius: '6px' }}>
                  T3: 35p Runner
                </span>
              </div>
            </div>

            {/* Active Trades Table */}
            {positions.length === 0 ? (
              <div style={{ 
                flex: 1, display: 'flex', flexDirection: 'column', 
                alignItems: 'center', justifyContent: 'center', 
                minHeight: '220px', color: '#64748B', gap: '10px' 
              }}>
                <CheckCircle2 size={36} style={{ opacity: 0.4 }} />
                <p style={{ fontSize: '14px' }}>Hiện không có vị thế nào đang mở</p>
                <span style={{ fontSize: '12px', color: '#475569' }}>
                  Bot sẽ tự động mở cụm 3 lệnh khi hội tụ đủ 4 chiến thuật và AI duyệt xác suất thắng &ge; 78%
                </span>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ color: '#64748B', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                      <th style={{ padding: '10px 8px' }}>MÃ LỆNH</th>
                      <th style={{ padding: '10px 8px' }}>LOẠI</th>
                      <th style={{ padding: '10px 8px' }}>LOT</th>
                      <th style={{ padding: '10px 8px' }}>GIÁ VÀO</th>
                      <th style={{ padding: '10px 8px' }}>GIÁ HIỆN TẠI</th>
                      <th style={{ padding: '10px 8px' }}>SL / TP</th>
                      <th style={{ padding: '10px 8px' }}>TRẠNG THÁI</th>
                      <th style={{ padding: '10px 8px', textAlign: 'right' }}>LỢI NHUẬN</th>
                      <th style={{ padding: '10px 8px', textAlign: 'center' }}>XỬ LÝ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((pos) => {
                      const isBuy = pos.type === 'BUY';
                      const isPositive = pos.profit >= 0;
                      return (
                        <tr key={pos.ticket} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <td className="mono" style={{ padding: '12px 8px', color: '#CBD5E1' }}>#{pos.ticket}</td>
                          <td style={{ padding: '12px 8px' }}>
                            <span style={{ 
                              padding: '2px 8px', borderRadius: '4px', fontWeight: 700, fontSize: '11px',
                              background: isBuy ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                              color: isBuy ? '#10B981' : '#EF4444'
                            }}>
                              {pos.type}
                            </span>
                          </td>
                          <td className="mono" style={{ padding: '12px 8px', fontWeight: 600 }}>{pos.volume}</td>
                          <td className="mono" style={{ padding: '12px 8px' }}>{pos.entry_price.toFixed(2)}</td>
                          <td className="mono" style={{ padding: '12px 8px' }}>{pos.current_price.toFixed(2)}</td>
                          <td className="mono" style={{ padding: '12px 8px', fontSize: '11px', color: '#94A3B8' }}>
                            {pos.sl.toFixed(2)} / {pos.tp.toFixed(2)}
                          </td>
                          <td style={{ padding: '12px 8px' }}>
                            {pos.is_breakeven ? (
                              <span style={{ 
                                display: 'inline-flex', alignItems: 'center', gap: '4px',
                                background: 'rgba(16, 185, 129, 0.15)', color: '#10B981',
                                padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 
                              }}>
                                <Shield size={10} /> ĐÃ KHÓA LÃI BE
                              </span>
                            ) : (
                              <span style={{ color: '#64748B', fontSize: '11px' }}>Đang gồng</span>
                            )}
                          </td>
                          <td className="mono" style={{ 
                            padding: '12px 8px', textAlign: 'right', fontWeight: 700,
                            color: isPositive ? '#10B981' : '#EF4444' 
                          }}>
                            {pos.profit > 0 ? `+${pos.profit.toFixed(2)}` : pos.profit.toFixed(2)} USD
                          </td>
                          <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                            <button
                              onClick={() => handleCloseSingle(pos.ticket)}
                              title="Đóng lệnh này"
                              style={{
                                background: 'rgba(239, 68, 68, 0.15)', border: 'none',
                                color: '#EF4444', padding: '4px 8px', borderRadius: '6px',
                                cursor: 'pointer', display: 'inline-flex', alignItems: 'center'
                              }}
                            >
                              <X size={13} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

          </div>

          {/* RIGHT: AI INTELLIGENCE & REAL-TIME STRATEGY CONFLUENCE */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <BarChart2 size={18} style={{ color: '#3B82F6' }} />
                <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Trí Tuệ Nhân Tạo & Đa Chiến Thuật</h3>
              </div>
              <span style={{ fontSize: '11px', color: '#94A3B8' }}>Khung M5 XAUUSD</span>
            </div>

            {/* AI Confidence Gauge */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1' }}>Xác Suất Thắng AI (P-Win)</span>
                <span className="mono" style={{ fontSize: '14px', fontWeight: 800, color: '#F59E0B' }}>
                  {analysis?.prob_buy ? `${(analysis.prob_buy * 100).toFixed(1)}% (BUY)` : 
                   (analysis?.prob_sell ? `${(analysis.prob_sell * 100).toFixed(1)}% (SELL)` : "Đang phân tích...")}
                </span>
              </div>

              {/* Progress bar with threshold mark */}
              <div style={{ position: 'relative', height: '10px', background: 'rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.max((analysis?.prob_buy || analysis?.prob_sell || 0.4) * 100, 10)}%`,
                  background: (analysis?.prob_buy || 0) >= 0.78 || (analysis?.prob_sell || 0) >= 0.78 ?
                    'linear-gradient(90deg, #10B981, #059669)' : 'linear-gradient(90deg, #3B82F6, #F59E0B)',
                  borderRadius: '6px',
                  transition: 'width 0.4s ease'
                }}></div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748B', marginTop: '6px' }}>
                <span>0%</span>
                <span style={{ color: '#F59E0B', fontWeight: 700 }}>Ngưỡng Duyệt Vào Lệnh: &ge; 78%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Technical Confluence Checklist (4 Engines) */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              
              {/* Trend Engine */}
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8' }}>XU HƯỚNG EMA 200</div>
                <div style={{ fontSize: '13px', fontWeight: 700, marginTop: '4px', color: analysis?.trend === 'BULLISH' ? '#10B981' : (analysis?.trend === 'BEARISH' ? '#EF4444' : '#CBD5E1') }}>
                  {analysis?.trend || "NEUTRAL"}
                </div>
              </div>

              {/* RSI Momentum */}
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8' }}>RSI (7 / 14)</div>
                <div className="mono" style={{ fontSize: '13px', fontWeight: 700, marginTop: '4px', color: '#F8FAFC' }}>
                  {analysis?.rsi_7 || "48.2"} / {analysis?.rsi_14 || "51.0"}
                </div>
              </div>

              {/* SMC Liquidity Sweep */}
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8' }}>SMC QUÉT THANH KHOẢN</div>
                <div style={{ fontSize: '13px', fontWeight: 700, marginTop: '4px', color: analysis?.liquidity_sweep_bull || analysis?.liquidity_sweep_bear ? '#10B981' : '#64748B' }}>
                  {analysis?.liquidity_sweep_bull ? "Quét Đáy (Bull Sweep)" : (analysis?.liquidity_sweep_bear ? "Quét Đỉnh (Bear Sweep)" : "Không có")}
                </div>
              </div>

              {/* Squeeze Momentum */}
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8' }}>VOLATILITY SQUEEZE</div>
                <div style={{ fontSize: '13px', fontWeight: 700, marginTop: '4px', color: analysis?.squeeze_on ? '#F59E0B' : '#3B82F6' }}>
                  {analysis?.squeeze_on ? "Đang Nén Chặt (Squeeze)" : "Đang Bung Xung Lực"}
                </div>
              </div>

            </div>

            {/* Model Architecture Info */}
            <div style={{ fontSize: '11px', color: '#64748B', lineHeight: '1.5' }}>
              * Mô hình AI: <strong>Ensemble 2 Cụm (Random Forest + HistGradientBoosting)</strong> hiệu chỉnh xác suất Calibrated, quét 20 đặc trưng nến M5 theo thời gian thực.
            </div>

          </div>

        </div>

        {/* 4. REAL-TIME LOGGING TERMINAL */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} className="pulse-active"></div>
              <h3 style={{ fontSize: '14px', fontWeight: 700 }}>Nhật Ký Thực Thi Thời Gian Thực (Live Terminal)</h3>
            </div>
            <span style={{ fontSize: '11px', color: '#64748B' }}>Tự động đồng bộ mỗi giây</span>
          </div>

          <div 
            ref={logContainerRef}
            style={{ 
              height: '180px', overflowY: 'auto', background: 'rgba(0,0,0,0.3)', 
              borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '6px'
            }}
          >
            {logs.length === 0 ? (
              <div style={{ color: '#475569', fontSize: '12px', fontStyle: 'italic' }}>Chưa có nhật ký ghi nhận...</div>
            ) : (
              logs.map((l, idx) => {
                let badgeColor = '#94A3B8';
                if (l.level === 'TRADE') badgeColor = '#F59E0B';
                if (l.level === 'SUCCESS') badgeColor = '#10B981';
                if (l.level === 'WARNING') badgeColor = '#F59E0B';
                if (l.level === 'ERROR') badgeColor = '#EF4444';

                return (
                  <div key={idx} className="mono" style={{ fontSize: '12px', display: 'flex', gap: '12px', alignItems: 'baseline' }}>
                    <span style={{ color: '#64748B', fontSize: '11px' }}>[{l.time}]</span>
                    <span style={{ 
                      color: badgeColor, fontWeight: 700, fontSize: '10px', 
                      background: 'rgba(255,255,255,0.05)', padding: '1px 6px', borderRadius: '3px' 
                    }}>
                      {l.level}
                    </span>
                    <span style={{ color: '#E2E8F0' }}>{l.message}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
export default App;
