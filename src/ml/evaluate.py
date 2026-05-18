from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import xgboost as xgb
from pathlib import Path

def evaluate_model(model, X_test, y_test, label_encoder):
    """
    Evaluates the XGBoost model using accuracy, precision, recall, and F1-score.
    """
    print("\n--- Model Evaluation ---")
    predictions = model.predict(X_test)
    
    # We must inverse transform to get 'LOW', 'MEDIUM', 'HIGH'
    class_names = label_encoder.inverse_transform([0, 1, 2])
    
    # In disaster prediction, accuracy is a bad metric! 
    # If floods happen 1% of the time, a model that always says "No Flood" is 99% accurate but useless.
    # We care deeply about RECALL for the "HIGH" class (we cannot miss a flood).
    acc = accuracy_score(y_test, predictions)
    print(f"Overall Accuracy: {acc * 100:.2f}%")
    
    print("\nClassification Report (Focus on Recall & F1-score):")
    # Wrap in try-except in case some classes are missing in test set
    try:
        print(classification_report(y_test, predictions, target_names=class_names))
    except ValueError:
        print(classification_report(y_test, predictions))
        
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))

def plot_feature_importance(model, features, output_dir: Path):
    """
    Generates and saves a professional feature importance plot.
    This shows which weather signals matter most to the model.
    """
    print("\n--- Feature Importance Analysis ---")
    # Extract importances
    importances = model.feature_importances_
    
    # Sort them
    indices = importances.argsort()[::-1]
    sorted_features = [features[i] for i in indices]
    sorted_importances = importances[indices]
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.title("XGBoost Feature Importance for Flood Prediction")
    plt.bar(range(len(sorted_features)), sorted_importances, align="center")
    plt.xticks(range(len(sorted_features)), sorted_features, rotation=45, ha='right')
    plt.tight_layout()
    
    # Save chart
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "feature_importance.png"
    plt.savefig(chart_path)
    print(f"Saved feature importance chart to: {chart_path}")
    plt.close()
