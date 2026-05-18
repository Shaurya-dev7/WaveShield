import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('data/train.csv')

# 1. Dataset shape
print("--- 1. Dataset Shape ---")
print(df.shape)

# 2. Column names
print("\n--- 2. Column Names ---")
print(df.columns.tolist())

# 3. Dataframe info
print("\n--- 3. Dataframe Info ---")
df.info()

# 4. First 5 rows
print("\n--- 4. First 5 Rows ---")
print(df.head())

# 5. Statistical summary
print("\n--- 5. Statistical Summary ---")
print(df.describe())

# 6. Missing values
print("\n--- 6. Missing Values ---")
print(df.isnull().sum())

# 7. Duplicate rows
print("\n--- 7. Duplicate Rows ---")
print("Duplicates:", df.duplicated().sum())

# 8. Identify target and features
target = 'FloodProbability'
features = [col for col in df.columns if col not in [target, 'id']]
print("\n--- 8. Identified Target and Features ---")
print(f"Target: {target}")
print(f"Features: {features}")

# 9. Analysis
print("\n--- 9. Analysis ---")
print(f"Problem Type: {'Regression' if df[target].dtype in [np.float64, np.float32] else 'Classification'}")
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
print(f"Categorical Columns: {categorical_cols}")
missing_count = df.isnull().sum().sum()
print(f"Total Missing Values: {missing_count}")

# Check for scaling
# Most environmental features have different scales or distributions
print("Scaling Recommendation: Most features are integer-based counts/intensities, scaling is recommended for models sensitive to scale (e.g., Linear Regression, SVM, NN).")

# Check for outliers (simple check using 3 std deviations)
outlier_candidates = []
for col in features:
    mean = df[col].mean()
    std = df[col].std()
    outliers = df[(df[col] > mean + 3*std) | (df[col] < mean - 3*std)]
    if not outliers.empty:
        outlier_candidates.append(col)
print(f"Features with potential outliers (>3 std devs): {outlier_candidates[:10]}...")
