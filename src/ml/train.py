import xgboost as xgb
import joblib
from pathlib import Path
import sys

# Ensure Python finds the 'src' module when run as a script
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config.settings import ENGINEERED_DIR, BASE_DIR
from src.ml.preprocessing import load_and_clean_data, generate_training_labels, prepare_features_and_target, time_series_split
from src.ml.evaluate import evaluate_model, plot_feature_importance

def train_flood_model():
    """
    Complete ML pipeline to train an XGBoost model for Flood Risk Prediction.
    """
    dataset_path = ENGINEERED_DIR / "engineered_master.csv"
    models_dir = BASE_DIR / "models"
    
    print("1. Loading and cleaning data...")
    df = load_and_clean_data(dataset_path)
    
    print("2. Generating heuristic training labels...")
    df = generate_training_labels(df)
    
    print("3. Preparing features and encoding target...")
    X, y, features, label_encoder = prepare_features_and_target(df, models_dir)
    
    print("4. Splitting Time-Series data (80% Train, 20% Test)...")
    X_train, X_test, y_train, y_test = time_series_split(X, y, train_ratio=0.8)
    print(f"   Train samples: {len(X_train)} | Test samples: {len(X_test)}")
    
    print("5. Training XGBoost Classifier...")
    # XGBoost is excellent for tabular data. It handles non-linear relationships
    # and correlations between weather features much better than linear models.
    # It builds trees sequentially, correcting the errors of previous trees (Boosting).
    model = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=6, 
        learning_rate=0.1, 
        random_state=42,
        eval_metric='mlogloss',
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train)
    
    print("6. Saving trained model...")
    model_path = models_dir / "flood_xgboost_v1.pkl"
    joblib.dump(model, model_path)
    print(f"   Model saved to {model_path}")
    
    print("7. Evaluating Model Performance...")
    evaluate_model(model, X_test, y_test, label_encoder)
    
    print("8. Generating Feature Importance Analysis...")
    plot_feature_importance(model, features, models_dir)
    
    print("\n--- Training Pipeline Complete ---")

if __name__ == "__main__":
    train_flood_model()
