import requests
from time import sleep

FASTAPI_URL = f"http://api.staging.caas.local"

data ={
  "clustering_algorithms": [
    "KMeans",
    "DBSCAN"
  ],
  "clustering_num": [
    1,
    10
  ],
  "columns": [
    {
      "name": "x1",
      "type": "numeric"
    },
    {
      "name": "x2",
      "type": "numeric"
    }
  ],
  "cutoff_time": 45,
  "dataset_name": "test_blobs_8clusters.csv",
  "dim_reduction_algorithms": [
    "PCA"
  ],
  "evaluator_ls": [
    "silhouetteScore",
    "calinskiHarabaszScore"
  ],
  "min_proportion": 0.01,
  "min_relative_proportion": "default",
  "n_evaluations": 20
}

iterations = 500
sleep_time = 0.1
for i in range(iterations):

    print(f"Iteration {i + 1}/{iterations} with algorithm: AutoML")

    res = requests.post(f"{FASTAPI_URL}/automl/job/", json=data)
    if res.status_code == 200:
        print(f"Job submitted successfully: {res.text}")
    else:
        print(f"Failed to submit job: {res.status_code}")
    sleep(sleep_time)
