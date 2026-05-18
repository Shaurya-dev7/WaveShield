import joblib
import pandas as pd
from pathlib import Path
import sys

# Ensure backend can import src modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config.settings import BASE_DIR
from src.utils.logger import setup_logger

logger = setup_logger("API_ML_Service")

class MLService:
    """
    Singleton service to keep the XGBoost model loaded in memory across all FastAPI requests.
    Loading a model from disk takes ~100ms. If we get 1,000 requests/sec, loading per request 
    would crash the server. This loads it exactly ONCE at startup.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        models_dir = BASE_DIR / "models"
        try:
            self.model = joblib.load(models_dir / "flood_xgboost_v1.pkl")
            self.label_encoder = joblib.load(models_dir / "label_encoder.pkl")
            self.features = self.model.feature_names_in_.tolist()
            self.is_loaded = True
            logger.info("FastAPI: ML Model successfully loaded into RAM.")
        except FileNotFoundError:
            self.model = None
            self.features = []
            self.is_loaded = False
            logger.error("FastAPI: Model file not found. Ensure src/ml/train.py has run.")

    def predict_risk(self, feature_dict: dict) -> tuple[str, float]:
        if not self.is_loaded:
            return "UNKNOWN", 0.0
            
        df = pd.DataFrame([feature_dict])
        
        # Ensure all required features are present
        for col in self.features:
            if col not in df.columns:
                df[col] = 0.0
                
        # Strict column ordering
        X = df[self.features]
        
        # Inference
        probs = self.model.predict_proba(X)[0]
        class_idx = probs.argmax()
        confidence = float(probs[class_idx])
        risk_level = self.label_encoder.inverse_transform([class_idx])[0]
        
        return risk_level, confidence

ml_engine = MLService()
