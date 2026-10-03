"""
Module Mô hình Trí tuệ nhân tạo (AI Ensemble Filter)
Lọc tín hiệu vào lệnh xác suất cao để đạt Winrate > 80% và DD < 10%
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
import joblib
import os
from config import config

FEATURES = [
    'bb_pct_b', 'bb_width',
    'rsi_7', 'rsi_14',
    'dist_ema_50', 'dist_ema_200',
    'stoch_k', 'stoch_d',
    'atr_ratio',
    'body_ratio', 'upper_wick_ratio', 'lower_wick_ratio',
    'hour', 'day_of_week'
]

def generate_labels(df: pd.DataFrame, tp_points: int = None, sl_points: int = None, breakeven_trigger: int = None) -> pd.DataFrame:
    """
    Tạo nhãn thực tế cho từng nến (Labeling):
    1 = Lệnh thành công (đạt TP hoặc được dời SL hòa vốn có lãi)
    0 = Lệnh thất bại (dính SL)
    """
    tp_pts = tp_points or config.TP_POINTS
    sl_pts = sl_points or config.SL_POINTS
    be_trigger = breakeven_trigger or config.BREAKEVEN_TRIGGER_POINTS
    
    # 1 point trên XAUUSD = 0.01 USD
    tp_val = tp_pts * 0.01
    sl_val = sl_pts * 0.01
    be_val = be_trigger * 0.01
    
    data = df.copy()
    data['label_buy'] = np.nan
    data['label_sell'] = np.nan
    
    close_vals = data['close'].values
    high_vals = data['high'].values
    low_vals = data['low'].values
    n = len(data)
    
    # Duyệt kiểm tra kết quả cho các nến có tín hiệu
    max_holding_bars = 48  # Giới hạn giữ lệnh tối đa 48 nến M5 (4 tiếng) cho scalping
    
    for i in range(n - max_holding_bars):
        entry_price = close_vals[i]
        
        # Kiểm tra kịch bản BUY
        if data['raw_signal_buy'].iloc[i]:
            hit_tp = False
            hit_sl = False
            hit_be = False
            
            for j in range(i + 1, min(i + max_holding_bars, n)):
                curr_high = high_vals[j]
                curr_low = low_vals[j]
                
                # Kiểm tra chạm Breakeven
                if curr_high >= entry_price + be_val:
                    hit_be = True
                    
                # Kiểm tra chạm TP
                if curr_high >= entry_price + tp_val:
                    hit_tp = True
                    break
                    
                # Kiểm tra chạm SL (nếu đã kích hoạt Breakeven thì điểm cắt lỗ là Entry + chút lời)
                curr_sl = entry_price if hit_be else (entry_price - sl_val)
                if curr_low <= curr_sl:
                    if hit_be:
                        hit_tp = True  # Coi như lệnh hòa vốn có lãi dương
                    else:
                        hit_sl = True
                    break
                    
            if hit_tp:
                data.at[i, 'label_buy'] = 1
            elif hit_sl:
                data.at[i, 'label_buy'] = 0
                
        # Kiểm tra kịch bản SELL
        if data['raw_signal_sell'].iloc[i]:
            hit_tp = False
            hit_sl = False
            hit_be = False
            
            for j in range(i + 1, min(i + max_holding_bars, n)):
                curr_high = high_vals[j]
                curr_low = low_vals[j]
                
                # Kiểm tra chạm Breakeven
                if curr_low <= entry_price - be_val:
                    hit_be = True
                    
                # Kiểm tra chạm TP
                if curr_low <= entry_price - tp_val:
                    hit_tp = True
                    break
                    
                # Kiểm tra chạm SL
                curr_sl = entry_price if hit_be else (entry_price + sl_val)
                if curr_high >= curr_sl:
                    if hit_be:
                        hit_tp = True
                    else:
                        hit_sl = True
                    break
                    
            if hit_tp:
                data.at[i, 'label_sell'] = 1
            elif hit_sl:
                data.at[i, 'label_sell'] = 0
                
    return data

class AIScalperModel:
    def __init__(self, model_file="ai_scalper_model.joblib"):
        self.model_file = model_file
        self.buy_model = None
        self.sell_model = None
        
    def train(self, df_train: pd.DataFrame):
        """
        Huấn luyện mô hình AI trên dữ liệu Giai đoạn 1 (In-Sample)
        Sử dụng Random Forest hiệu chỉnh xác suất (CalibratedClassifier)
        """
        print("[AI] Bắt đầu gán nhãn dữ liệu huấn luyện...")
        labeled_data = generate_labels(df_train)
        
        # Huấn luyện mô hình BUY
        buy_samples = labeled_data.dropna(subset=['label_buy'])
        if len(buy_samples) > 20:
            X_buy = buy_samples[FEATURES]
            y_buy = buy_samples['label_buy'].astype(int)
            base_rf_buy = RandomForestClassifier(n_estimators=120, max_depth=6, min_samples_leaf=8, random_state=42)
            self.buy_model = CalibratedClassifierCV(base_rf_buy, cv=3)
            self.buy_model.fit(X_buy, y_buy)
            print(f"[AI] Huấn luyện xong mô hình BUY với {len(buy_samples)} mẫu. Winrate mẫu gốc: {y_buy.mean()*100:.1f}%")
        else:
            print("[AI] Cảnh báo: Quá ít mẫu BUY để huấn luyện.")
            
        # Huấn luyện mô hình SELL
        sell_samples = labeled_data.dropna(subset=['label_sell'])
        if len(sell_samples) > 20:
            X_sell = sell_samples[FEATURES]
            y_sell = sell_samples['label_sell'].astype(int)
            base_rf_sell = RandomForestClassifier(n_estimators=120, max_depth=6, min_samples_leaf=8, random_state=42)
            self.sell_model = CalibratedClassifierCV(base_rf_sell, cv=3)
            self.sell_model.fit(X_sell, y_sell)
            print(f"[AI] Huấn luyện xong mô hình SELL với {len(sell_samples)} mẫu. Winrate mẫu gốc: {y_sell.mean()*100:.1f}%")
        else:
            print("[AI] Cảnh báo: Quá ít mẫu SELL để huấn luyện.")
            
        # Lưu file mô hình
        joblib.dump({'buy_model': self.buy_model, 'sell_model': self.sell_model}, self.model_file)
        print(f"[AI] Đã lưu mô hình AI vào {self.model_file}")

    def load(self):
        """Tải mô hình AI đã huấn luyện từ ổ đĩa"""
        if os.path.exists(self.model_file):
            saved = joblib.load(self.model_file)
            self.buy_model = saved.get('buy_model')
            self.sell_model = saved.get('sell_model')
            return True
        return False
        
    def predict_confidence(self, features_df: pd.DataFrame, signal_type: str) -> np.ndarray:
        """
        Dự đoán xác suất thắng P(Win) của tín hiệu vào lệnh
        """
        if signal_type == "BUY" and self.buy_model is not None:
            probs = self.buy_model.predict_proba(features_df[FEATURES])
            return probs[:, 1]
        elif signal_type == "SELL" and self.sell_model is not None:
            probs = self.sell_model.predict_proba(features_df[FEATURES])
            return probs[:, 1]
        return np.zeros(len(features_df))
