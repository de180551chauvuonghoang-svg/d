export interface AccountInfo {
  login: number;
  server: string;
  balance: number;
  equity: number;
  floating_profit: number;
  margin: number;
  margin_free: number;
  leverage: number;
}

export interface MarketTicker {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
}

export interface OpenPosition {
  ticket: number;
  type: 'BUY' | 'SELL';
  volume: number;
  entry_price: number;
  entry_time: string;
  sl: number;
  tp: number;
  current_price: number;
  profit: number;
  profit_points: number;
  is_breakeven: boolean;
}

export interface AIAnalysis {
  time?: string;
  rsi_7?: number;
  rsi_14?: number;
  bb_pct_b?: number;
  adx_14?: number;
  trend?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  squeeze_on?: boolean;
  liquidity_sweep_bull?: boolean;
  liquidity_sweep_bear?: boolean;
  prob_buy?: number;
  prob_sell?: number;
  signal_buy?: boolean;
  signal_sell?: boolean;
}

export interface SystemLog {
  time: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS' | 'TRADE';
  message: string;
}

export interface TradePrediction {
  estimated_time: string;
  estimated_bars: number;
  readiness_pct: number;
  bar_countdown: string;
  seconds_remaining: number;
  best_prob: number;
  target_prob: number;
  status_text: string;
  status_level: 'TRIGGER_IMMIMENT' | 'VERY_CLOSE' | 'APPROACHING' | 'WAITING' | 'MONITORING' | 'ACTIVE_TRADE' | 'STANDBY';
  checklist: {
    market_open: boolean;
    spread_ok: boolean;
    confluence: boolean;
    ai_ready: boolean;
  };
}

export interface ClosedTrade {
  ticket: number;
  deal_id?: number;
  symbol: string;
  type: 'BUY' | 'SELL';
  volume: number;
  entry_price?: number;
  price: number;
  profit: number;
  profit_points?: number;
  close_time: string;
  comment: string;
}

export interface WebSocketPayload {
  timestamp: string;
  bot_running: boolean;
  market_open: boolean;
  market_status_message: string;
  account: AccountInfo;
  ticker: MarketTicker;
  positions: OpenPosition[];
  history?: ClosedTrade[];
  analysis: AIAnalysis;
  prediction?: TradePrediction;
  logs: SystemLog[];
}


