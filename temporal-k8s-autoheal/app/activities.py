from temporalio import activity
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time


# -------------------------------
# Load Kubernetes config
# -------------------------------
def load_k8s():
    try:
        config.load_kube_config()
    except:
        config.load_incluster_config()


# -------------------------------
# 1. Check Pod Status (REAL CHECK)
# -------------------------------
@activity.defn
async def check_pod_status(deployment_name: str) -> str:
    load_k8s()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace="default")

        found = False

        for pod in pods.items:
            if deployment_name in pod.metadata.name:
                found = True
                print(f"[CHECK] Pod: {pod.metadata.name}")

                # ⚠️ If no container status → something wrong
                if not pod.status.container_statuses:
                    print("[CHECK] No container status found")
                    return "failed"

                for container in pod.status.container_statuses:

                    # 🔥 Check WAITING state (CrashLoopBackOff etc.)
                    if container.state.waiting:
                        reason = container.state.waiting.reason
                        print(f"[CHECK] Waiting reason: {reason}")

                        if reason in [
                            "CrashLoopBackOff",
                            "ImagePullBackOff",
                            "ErrImagePull",
                            "Error"
                        ]:
                            return "failed"

                    # 🔥 Check TERMINATED state
                    if container.state.terminated:
                        print("[CHECK] Container terminated")
                        return "failed"

                    # 🔥 Check restart count
                    if container.restart_count > 3:
                        print(f"[CHECK] High restart count: {container.restart_count}")
                        return "failed"

        if not found:
            print("[CHECK] No matching pods found")
            return "failed"

        return "healthy"

    except ApiException as e:
        print(f"[ERROR] Kubernetes API error: {e}")
        return "failed"


# -------------------------------
# 2. Restart Deployment
# -------------------------------
@activity.defn
async def restart_deployment(deployment_name: str) -> str:
    load_k8s()
    apps = client.AppsV1Api()

    try:
        print(f"[ACTION] Restarting deployment: {deployment_name}")

        apps.patch_namespaced_deployment(
            name=deployment_name,
            namespace="default",
            body={
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                # Force rollout restart
                                "kubectl.kubernetes.io/restartedAt": str(time.time())
                            }
                        }
                    }
                }
            },
        )

        return "restarted"

    except ApiException as e:
        print(f"[ERROR] Failed to restart deployment: {e}")
        return "failed"


# -------------------------------
# 3. Verify Health After Restart
# -------------------------------
@activity.defn
async def verify_health(deployment_name: str) -> str:
    load_k8s()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace="default")

        for pod in pods.items:
            if deployment_name in pod.metadata.name:

                print(f"[VERIFY] Pod: {pod.metadata.name}")

                if not pod.status.container_statuses:
                    return "failed"

                for container in pod.status.container_statuses:

                    if container.state.waiting:
                        return "failed"

                    if container.state.terminated:
                        return "failed"

                    if container.restart_count > 3:
                        return "failed"

                return "healthy"

        return "failed"

    except ApiException as e:
        print(f"[ERROR] Health check failed: {e}")
        return "failed"