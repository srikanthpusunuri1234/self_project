from kubernetes import client, config

def check_pod_status(deployment_name):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod("default")

    for pod in pods.items:
        if deployment_name in pod.metadata.name:
            print(f"Pod: {pod.metadata.name}, Status: {pod.status.phase}")

            if pod.status.phase != "Running":
                return "failed"

    return "healthy"


def restart_deployment(deployment_name):
    config.load_kube_config()
    apps = client.AppsV1Api()

    print(f"Restarting deployment: {deployment_name}")

    apps.patch_namespaced_deployment(
        name=deployment_name,
        namespace="default",
        body={
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": "now"
                        }
                    }
                }
            }
        },
    )

    return "restarted"


def verify_health(deployment_name):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod("default")

    for pod in pods.items:
        if deployment_name in pod.metadata.name:
            if pod.status.phase == "Running":
                return "healthy"

    return "failed"