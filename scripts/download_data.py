import kagglehub
import os

# Download dataset
path = kagglehub.dataset_download("naiyakhalid/flood-prediction-dataset")

# Show dataset location
print("Dataset downloaded successfully")
print("Path:", path)

# Show files inside dataset folder
print("\nFiles in dataset:")
print(os.listdir(path))
