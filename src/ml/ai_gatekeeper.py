"""
AI Ensemble Gatekeeper Model
Implements BaseAIModel using Calibrated Random Forest Ensemble
"""
import pandas as pd
import numpy as np
from typing import List, Optional
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from src.core.interfaces import BaseAIModel
from src.core.logger import log
from src.ml.feature_pipeline import DEFAULT_FEATURES, generate_training_labels

class AIGatekeeperModel(BaseAIModel):
    def __init__(self, model_file: str = "ai_scalper_model.joblib", features: List[str] = None):
        self.model_file = model_file
        self.features = features or DEFAULT_FEATURES
        self.buy_model: Optional[CalibratedClassifierCV] = None
        self.sell_model: Optional[CalibratedClassifierCV] = None

    def train(self, df_train: pd.DataFrame) -> None:
        log.info("Bắt đầu quy trình huấn luyện AI Gatekeeper...")
        labeled_data = generate_training_labels(df_train)
        
        # 1. Huấn luyện mô hình BUY
        buy_samples = labeled_data.dropna(subset=['label_buy'])
        if len(buy_samples) >= 20:
            X_buy = buy_samples[self.features]
            y_buy = buy_samples['label_buy'].astype(int)
            base_rf = RandomForestClassifier(n_estimators=120, max_depth=6, min_samples_leaf=8, random_state=42)
            self.buy_model = CalibratedClassifierCV(base_rf, cv=3)
            self.buy_model.fit(X_buy, y_buy)
            log.info(f"Đã huấn luyện mô hình BUY với {len(buy_samples)} mẫu (Tỷ lệ thắng gốc: {y_buy.mean()*100:.1f}%)")
        else:
            log.warning("Cảnh báo: Không đủ mẫu BUY để huấn luyện AI.")
            
        # 2. Huấn luyện mô hình SELL
        sell_samples = labeled_data.dropna(subset=['label_sell'])
        if len(sell_samples) >= 20:
            X_sell = sell_samples[self.features]
            y_sell = sell_samples['label_sell'].astype(int)
            base_rf = RandomForestClassifier(n_estimators=120, max_depth=6, min_samples_leaf=8, random_state=42)
            self.sell_model = CalibratedClassifierCV(base_rf, cv=3)
            self.sell_model.fit(X_sell, y_sell)
            log.info(f"Đã huấn luyện mô hình SELL với {len(sell_samples)} mẫu (Tỷ lệ thắng gốc: {y_sell.mean()*100:.1f}%)")
        else:
            log.warning("Cảnh báo: Không đủ mẫu SELL để huấn luyện AI.")
            
        self.save(self.model_file)

    def predict_confidence(self, features_df: pd.DataFrame, signal_type: str) -> np.ndarray:
        if signal_type == "BUY" and self.buy_model is not None:
            return self.buy_model.predict_proba(features_df[self.features])[:, 1]
        elif signal_type == "SELL" and self.sell_model is not None:
            return self.sell_model.predict_proba(features_df[self.features])[:, 1]
        return np.zeros(len(features_df))

    def save(self, filepath: str = None) -> None:
        path = filepath or self.model_file
        joblib.dump({
            'buy_model': self.buy_model,
            'sell_model': self.sell_model,
            'features': self.features
        }, path)
        log.info(f"Đã lưu mô hình AI vào {path}")

    def load(self, filepath: str = None) -> bool:
        path = filepath or self.model_file
        if os.path.exists(path):
            try:
                saved = joblib.load(path)
                self.buy_model = saved.get('buy_model')
                self.sell_model = saved.get('sell_model')
                self.features = saved.get('features', self.features)
                log.info(f"Đã tải thành công mô hình AI từ {path}")
                return True
            except Exception as e:
                log.error(f"Lỗi khi tải file mô hình: {e}")
        return False
