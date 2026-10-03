"""
Advanced Multi-Model AI Ensemble Gatekeeper 2.0
Combines Calibrated Random Forest + Calibrated Histogram Gradient Boosting
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
import os
import joblib
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from src.core.interfaces import BaseAIModel
from src.core.logger import log
from src.ml.feature_pipeline import DEFAULT_FEATURES, generate_training_labels

class AIGatekeeperModel(BaseAIModel):
    def __init__(self, model_file: str = "ai_scalper_model.joblib", features: List[str] = None):
        self.model_file = model_file
        self.features = features or DEFAULT_FEATURES
        self.buy_rf: Optional[CalibratedClassifierCV] = None
        self.buy_hgb: Optional[CalibratedClassifierCV] = None
        self.sell_rf: Optional[CalibratedClassifierCV] = None
        self.sell_hgb: Optional[CalibratedClassifierCV] = None

    def train(self, df_train: pd.DataFrame) -> None:
        log.info("Bắt đầu huấn luyện Siêu Mô hình AI Ensemble (Random Forest + Gradient Boosting)...")
        labeled_data = generate_training_labels(df_train)
        
        # 1. Huấn luyện cụm mô hình BUY
        buy_samples = labeled_data.dropna(subset=['label_buy'])
        if len(buy_samples) >= 20:
            X_buy = buy_samples[self.features]
            y_buy = buy_samples['label_buy'].astype(int)
            
            # Model 1: Random Forest
            rf_buy = RandomForestClassifier(n_estimators=150, max_depth=7, min_samples_leaf=6, random_state=42)
            self.buy_rf = CalibratedClassifierCV(rf_buy, cv=3)
            self.buy_rf.fit(X_buy, y_buy)
            
            # Model 2: HistGradientBoosting
            hgb_buy = HistGradientBoostingClassifier(max_iter=120, max_depth=5, min_samples_leaf=10, random_state=42)
            self.buy_hgb = CalibratedClassifierCV(hgb_buy, cv=3)
            self.buy_hgb.fit(X_buy, y_buy)
            
            log.info(f"[AI BUY] Đã huấn luyện Ensemble (RF + HGB) với {len(buy_samples)} mẫu. Winrate gốc: {y_buy.mean()*100:.1f}%")
        else:
            log.warning("Cảnh báo: Không đủ mẫu BUY để huấn luyện AI.")
            
        # 2. Huấn luyện cụm mô hình SELL
        sell_samples = labeled_data.dropna(subset=['label_sell'])
        if len(sell_samples) >= 20:
            X_sell = sell_samples[self.features]
            y_sell = sell_samples['label_sell'].astype(int)
            
            # Model 1: Random Forest
            rf_sell = RandomForestClassifier(n_estimators=150, max_depth=7, min_samples_leaf=6, random_state=42)
            self.sell_rf = CalibratedClassifierCV(rf_sell, cv=3)
            self.sell_rf.fit(X_sell, y_sell)
            
            # Model 2: HistGradientBoosting
            hgb_sell = HistGradientBoostingClassifier(max_iter=120, max_depth=5, min_samples_leaf=10, random_state=42)
            self.sell_hgb = CalibratedClassifierCV(hgb_sell, cv=3)
            self.sell_hgb.fit(X_sell, y_sell)
            
            log.info(f"[AI SELL] Đã huấn luyện Ensemble (RF + HGB) với {len(sell_samples)} mẫu. Winrate gốc: {y_sell.mean()*100:.1f}%")
        else:
            log.warning("Cảnh báo: Không đủ mẫu SELL để huấn luyện AI.")
            
        self.save(self.model_file)

    def predict_confidence(self, features_df: pd.DataFrame, signal_type: str) -> np.ndarray:
        """
        Dự đoán xác suất đồng thuận (Weighted Soft Voting Ensemble):
        P(Win) = 0.5 * P(RF) + 0.5 * P(HGB)
        """
        X = features_df[self.features]
        if signal_type == "BUY":
            probs = []
            if self.buy_rf is not None:
                probs.append(self.buy_rf.predict_proba(X)[:, 1])
            if self.buy_hgb is not None:
                probs.append(self.buy_hgb.predict_proba(X)[:, 1])
            if probs:
                return np.mean(probs, axis=0)
                
        elif signal_type == "SELL":
            probs = []
            if self.sell_rf is not None:
                probs.append(self.sell_rf.predict_proba(X)[:, 1])
            if self.sell_hgb is not None:
                probs.append(self.sell_hgb.predict_proba(X)[:, 1])
            if probs:
                return np.mean(probs, axis=0)
                
        return np.zeros(len(features_df))

    def save(self, filepath: str = None) -> None:
        path = filepath or self.model_file
        joblib.dump({
            'buy_rf': self.buy_rf,
            'buy_hgb': self.buy_hgb,
            'sell_rf': self.sell_rf,
            'sell_hgb': self.sell_hgb,
            'features': self.features
        }, path)
        log.info(f"Đã lưu siêu mô hình AI Ensemble vào {path}")

    def load(self, filepath: str = None) -> bool:
        path = filepath or self.model_file
        if os.path.exists(path):
            try:
                saved = joblib.load(path)
                self.buy_rf = saved.get('buy_rf')
                self.buy_hgb = saved.get('buy_hgb')
                self.sell_rf = saved.get('sell_rf')
                self.sell_hgb = saved.get('sell_hgb')
                self.features = saved.get('features', self.features)
                log.info(f"Đã tải thành công siêu mô hình AI Ensemble từ {path}")
                return True
            except Exception as e:
                log.error(f"Lỗi khi tải file mô hình: {e}")
        return False
