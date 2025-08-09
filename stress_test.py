import requests
from time import sleep
import random
from kubernetes import client, config
import datetime
import json

# Connect to the Kubernetes Cluster
config.load_kube_config()
api_client = client.AppsV1Api()

def get_replica_count(api_client, deployment_name: str, namespace: str) -> dict[str, int]:
    core_v1 = client.CoreV1Api()
    try:
        # Get desired number of replicas for deployment
        deployment = api_client.read_namespaced_deployment(deployment_name, namespace)
        desired_replicas = deployment.spec.replicas

        # Count running pods for that deployment
        label_selector = ",".join([f"{k}={v}" for k,v in deployment.spec.selector.match_labels.items()])
        pods = core_v1.list_namespaced_pod(namespace, label_selector=label_selector)
        running_pods = sum(1 for pod in pods.items if pod.status.phase == "Running")

        return {"running": running_pods, "desired": desired_replicas}
    except client.exceptions.ApiException as e:
        print(f"Error fetching replica count for {deployment_name}: {e}")
        return {"running": 0, "desired": 0}

# Set up base information for job requests
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

iterations = 10
sleep_time = 0.1

replicas_clustering = []
replicas_fastapi = []

start_time = int(datetime.datetime.now().timestamp() * 1000)
print(f"Start time: {start_time}")
# Scale up
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

    print(f"Scale up iteration {i + 1}/{iterations} with algorithm: {algorithm}")
    res = requests.post(f"{FASTAPI_URL}/job/", json=data)
    if res.status_code == 200:
        print(f"Job submitted successfully: {res.text}")
    else:
        print(f"Failed to submit job: {res.status_code}")
    

    replicas_clustering.append(get_replica_count(api_client, "clustering-worker", "staging"))
    replicas_fastapi.append(get_replica_count(api_client, "fastapi", "staging"))
    replicas_clustering[-1]['step_time'] = int(datetime.datetime.now().timestamp() * 1000) - start_time
    replicas_fastapi[-1]['step_time'] = int(datetime.datetime.now().timestamp() * 1000) - start_time

    sleep(sleep_time)

# Scale down
for i in range(iterations):
    print(f"Scale down iteration {i + 1}/{iterations}")
    replicas_clustering.append(get_replica_count(api_client, "clustering-worker", "staging"))
    replicas_fastapi.append(get_replica_count(api_client, "fastapi", "staging"))
    replicas_clustering[-1]['step_time'] = int(datetime.datetime.now().timestamp() * 1000) - start_time
    replicas_fastapi[-1]['step_time'] = int(datetime.datetime.now().timestamp() * 1000) - start_time
    sleep(sleep_time)


timestamp = str(datetime.datetime.now()).split(".")[0].replace(" ", "_").replace(":", "-")
with open(f"{timestamp}-replicas_clustering.json", "w") as f:
    json.dump(replicas_clustering, f)

with open(f"{timestamp}-replicas_fastapi.json", "w") as f:
    json.dump(replicas_fastapi, f)
