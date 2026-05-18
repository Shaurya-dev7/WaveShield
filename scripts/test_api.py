import requests
import json

# Sample payload
payload = {
    "MonsoonIntensity": 5,
    "TopographyDrainage": 5,
    "RiverManagement": 5,
    "Deforestation": 5,
    "Urbanization": 5,
    "ClimateChange": 5,
    "DamsQuality": 5,
    "Siltation": 5,
    "AgriculturalPractices": 5,
    "Encroachments": 5,
    "IneffectiveDisasterPreparedness": 5,
    "DrainageSystems": 5,
    "CoastalVulnerability": 5,
    "Landslides": 5,
    "Watersheds": 5,
    "DeterioratingInfrastructure": 5,
    "PopulationScore": 5,
    "WetlandLoss": 5,
    "InadequatePlanning": 5,
    "PoliticalFactors": 5
}

url = "http://127.0.0.1:8000/predict"

try:
    print("Testing API /predict endpoint...")
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=4))
except Exception as e:
    print("Error connecting to API:", str(e))
