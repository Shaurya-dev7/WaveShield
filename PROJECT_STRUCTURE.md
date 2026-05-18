# 📁 Project Structure

This document explains the architectural layout of the Flood Prediction AI System. The repository follows best practices for a decoupled Machine Learning project, separating the data science experimentation, the backend serving API, and the frontend user interface.

```text
flood-prediction-ai/
│
├── api/                        # Backend Microservice
│   └── main.py                 # FastAPI application. Loads the XGBoost model into memory and exposes the /predict REST endpoint.
│
├── data/                       # Dataset Storage
│   └── .keep                   # Placeholder to keep the folder in version control (data files are ignored via .gitignore).
│
├── frontend/                   # User Interface
│   └── app.py                  # Streamlit dashboard. Consumes the FastAPI backend to visualize risk predictions and collect user inputs.
│
├── models/                     # Persisted AI Models
│   ├── xgboost_flood_model.pkl # The serialized XGBoost model generated after training.
│   └── .keep                   # Placeholder to ensure folder existence.
│
├── notebooks/                  # Data Science & Experimentation
│   └── flood_prediction.ipynb  # Jupyter notebook containing EDA, feature engineering, model training, and performance evaluation.
│
├── scripts/                    # Automation & Utility Scripts
│   ├── analyze_data.py         # Utility script for quick data analysis without starting Jupyter.
│   ├── download_data.py        # Script to fetch the Kaggle dataset.
│   ├── setup_api_model.py      # Script to automate training and saving the model to the models/ directory.
│   └── test_api.py             # Script to run an automated integration test against the running FastAPI server.
│
├── .gitignore                  # Instructs Git to ignore cache files, datasets, and the virtual environment.
├── LICENSE                     # MIT License.
├── README.md                   # The main project landing page containing setup instructions and architecture details.
├── PROJECT_STRUCTURE.md        # This file, explaining the purpose of each directory.
└── requirements.txt            # Python dependencies needed to reproduce this environment.
```

## Why this Structure?

1.  **Modularity**: By separating the `api/` from the `frontend/`, the backend can be consumed by other services (like a mobile app) without touching the Streamlit code.
2.  **Scalability**: The `api/` can be containerized and deployed to AWS or Render independently of the UI.
3.  **Reproducibility**: The `notebooks/` and `scripts/` ensure that any data scientist can retrain the model and reproduce the `.pkl` file.
