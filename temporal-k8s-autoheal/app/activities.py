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
# 1. CLASSIFY FAILURE (CORE LOGIC)
# -------------------------------
@activity.defn
async def classify_failure(deployment_name: str) -> str:
    load_k8s()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace="default")

        for pod in pods.items:
            if deployment_name in pod.metadata.name:

                print(f"[CLASSIFY] Checking pod: {pod.metadata.name}")

                if not pod.status.container_statuses:
                    return "unknown"

                for c in pod.status.container_statuses:

                    # -------------------------------
                    # WAITING STATE (CrashLoop / Image issues)
                    # -------------------------------
                    if c.state.waiting:
                        reason = c.state.waiting.reason
                        print(f"[CLASSIFY] Waiting: {reason}")

                        if reason == "CrashLoopBackOff":
                            return "restart"

                        if reason in ["ImagePullBackOff", "ErrImagePull"]:
                            return "alert"

                    # -------------------------------
                    # 🔥 TERMINATED STATE (YOUR FIX HERE)
                    # -------------------------------
                    if c.state.terminated:
                        reason = c.state.terminated.reason
                        print(f"[CLASSIFY] Terminated: {reason}")

                        if reason == "OOMKilled":
                            return "scale"

                        if reason in ["Error", "Completed"]:
                            return "rollback"

                    # -------------------------------
                    # HIGH RESTART COUNT
                    # -------------------------------
                    if c.restart_count > 5:
                        print("[CLASSIFY] High restart count")
                        return "restart"

        return "healthy"

    except ApiException as e:
        print(f"[ERROR] Classification failed: {e}")
        return "unknown"


# -------------------------------
# 2. TAKE ACTION
# -------------------------------
@activity.defn
async def take_action(action: str, deployment_name: str) -> str:
    load_k8s()
    apps = client.AppsV1Api()

    try:
        if action == "restart":
            print("[ACTION] Restarting deployment")

            apps.patch_namespaced_deployment(
                name=deployment_name,
                namespace="default",
                body={
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": str(time.time())
                                }
                            }
                        }
                    }
                },
            )
            return "restarted"

        elif action == "scale":
            print("[ACTION] Scaling deployment")

            apps.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace="default",
                body={"spec": {"replicas": 2}},
            )
            return "scaled"

        elif action == "rollback":
            print("[ACTION] Rollback required (manual or future automation)")
            return "rollback-needed"

        elif action == "alert":
            print("[ALERT] Manual intervention required")
            return "alerted"

        else:
            print("[INFO] No action needed")
            return "none"

    except ApiException as e:
        print(f"[ERROR] Action failed: {e}")
        return "failed"


# -------------------------------
# 3. VERIFY HEALTH
# -------------------------------
@activity.defn
async def verify_health(deployment_name: str) -> str:
    load_k8s()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace="default")

        for pod in pods.items:
            if deployment_name in pod.metadata.name:

                if not pod.status.container_statuses:
                    return "failed"

                for c in pod.status.container_statuses:

                    if c.state.waiting or c.state.terminated:
                        return "failed"

                    if c.restart_count > 3:
                        return "failed"

                return "healthy"

        return "failed"

    except ApiException as e:
        print(f"[ERROR] Verification failed: {e}")
        return "failed"