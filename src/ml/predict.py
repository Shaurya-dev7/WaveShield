import joblib
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Ensure Python finds the 'src' module when run as a script
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config.settings import BASE_DIR
from src.utils.logger import setup_logger

logger = setup_logger("Live_Prediction")

class DisasterPredictor:
    """
    Loads the trained XGBoost model and LabelEncoder to make real-time predictions.
    """
    def __init__(self):
        models_dir = BASE_DIR / "models"
        try:
            self.model = joblib.load(models_dir / "flood_xgboost_v1.pkl")
            self.label_encoder = joblib.load(models_dir / "label_encoder.pkl")
            self.expected_features = self.model.feature_names_in_
            logger.info("Machine Learning models successfully loaded into memory.")
        except FileNotFoundError:
            logger.error("Model files not found! Please run src/ml/train.py first.")
            self.model = None

    def predict_flood_risk(self, current_weather_data: dict) -> tuple[str, float]:
        """
        Takes live engineered weather data, returns the risk string (LOW, MEDIUM, HIGH)
        and the confidence probability score (0.0 to 1.0).
        """
        if self.model is None:
            return "UNKNOWN", 0.0
            
        # Convert dict to DataFrame for XGBoost
        df = pd.DataFrame([current_weather_data])
        
        # Ensure all expected features are present (handle missing columns gracefully)
        for col in self.expected_features:
            if col not in df.columns:
                df[col] = 0.0 # Default fallback, though feature engineering should provide all
                
        # Filter to only the features the model was trained on, in the exact order
        X = df[self.expected_features]
        
        # Get raw probabilities for each class
        probabilities = self.model.predict_proba(X)[0]
        
        # Get the class index with the highest probability
        predicted_class_index = probabilities.argmax()
        confidence = probabilities[predicted_class_index]
        
        # Decode index back to human-readable label
        risk_level = self.label_encoder.inverse_transform([predicted_class_index])[0]
        
        # Log prediction to PostgreSQL Observability Table
        from src.db.database import SessionLocal
        from src.db.models import PredictionLog
        
        try:
            with SessionLocal() as db:
                log_entry = PredictionLog(
                    timestamp=pd.to_datetime(current_weather_data.get('time', datetime.now().isoformat())),
                    city=current_weather_data.get('city', 'Unknown'),
                    risk_level=risk_level,
                    confidence=confidence,
                    model_version="xgboost_v1"
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to log prediction to PostgreSQL: {e}")
        
        return risk_level, confidence

# Singleton instance to be imported by the alert engine
predictor_instance = DisasterPredictor()
