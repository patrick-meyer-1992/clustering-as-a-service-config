import requests
from time import sleep
import random

FASTAPI_URL = f"http://api.staging.caas.local"

algorithms = requests.get(f"{FASTAPI_URL}/algorithms/").json()

data = {
    "clustering_algorithm": "",
    "clustering_params": "",
    "columns": [
        {"name": "x1", "type": "numeric"},
        {"name": "x2", "type": "numeric"},
    ],
    "dataset_name": "test_blobs_8clusters.csv",
    "preprocess": "true",
    "preprocessing_params": {
        "feature_selection": "low_variance",
        "imputation_strategy": "mean",
        "normalization_type": "l2",
        "outlier_removal": "zscore",
        "outlier_threshold": 3,
        "pca_components": 10,
        "scaler": "auto",
        "transform_type": "quantile",
        "use_normalization": "false",
        "use_pca": "false",
        "variance_threshold": 0,
    },
}

iterations = 500
sleep_time = 0.1
for i in range(iterations):
    algorithm = random.choice(algorithms)
    response = requests.get(f"{FASTAPI_URL}/parameters/{algorithm}/")
    if response.status_code == 200:
        clustering_params = response.json()["clustering_params"]
    else: 
        print(f"Error fetching parameters for {algorithm}: {response.text}")
        continue

    if "n_clusters" in clustering_params:
        clustering_params["n_clusters"] = 8
    data["clustering_algorithm"] = algorithm
    data["clustering_params"] = clustering_params

    print(f"Iteration {i + 1}/{iterations} with algorithm: {algorithm}")

    res = requests.post(f"{FASTAPI_URL}/job/", json=data)
    if res.status_code == 200:
        print(f"Job submitted successfully: {res.text}")
    else:
        print(f"Failed to submit job: {res.status_code}")
    sleep(sleep_time)
