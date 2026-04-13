from temporalio import activity
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import subprocess
import time

# -------------------------------
# K8s Config
# -------------------------------
def load_k8s():
    try:
        config.load_kube_config()
    except:
        config.load_incluster_config()


# -------------------------------
# CLASSIFY FAILURE
# -------------------------------
@activity.defn
async def classify_failure(deployment_name: str) -> dict:
    load_k8s()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace="default")

        for pod in pods.items:
            if deployment_name in pod.metadata.name:

                if not pod.status.container_statuses:
                    return {"status": "unknown"}

                for c in pod.status.container_statuses:

                    # WAITING
                    if c.state.waiting:
                        reason = c.state.waiting.reason

                        if reason == "CrashLoopBackOff":
                            return {"action": "restart"}

                        if reason in ["ImagePullBackOff", "ErrImagePull"]:
                            return {"action": "alert"}

                    # TERMINATED
                    if c.state.terminated:
                        reason = c.state.terminated.reason

                        if reason == "OOMKilled":
                            return {"action": "scale"}

                        if reason in ["Error", "Completed"]:
                            return {"action": "rollback"}

                    # RESTART COUNT
                    if c.restart_count > 5:
                        return {"action": "restart"}

        return {"action": "healthy"}

    except Exception as e:
        return {"action": "unknown", "error": str(e)}


# -------------------------------
# TAKE ACTION (SMART)
# -------------------------------
@activity.defn
async def take_action(input_data: dict) -> str:
    action = input_data["action"]
    deployment_name = input_data["deployment"]

    load_k8s()
    apps = client.AppsV1Api()

    try:
        # ------------------ RESTART ------------------
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
                                    "restartedAt": str(time.time())
                                }
                            }
                        }
                    }
                },
            )
            return "restarted"

        # ------------------ SCALE ------------------
        elif action == "scale":
            print("[ACTION] Scaling deployment")

            apps.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace="default",
                body={"spec": {"replicas": 2}},
            )
            return "scaled"

        # ------------------ ROLLBACK ------------------
        elif action == "rollback":
            print("[ACTION] Rolling back deployment")

            subprocess.run([
                "kubectl",
                "rollout",
                "undo",
                f"deployment/{deployment_name}"
            ])

            return "rolled-back"

        # ------------------ ALERT ------------------
        elif action == "alert":
            print("[ALERT] Manual intervention required")
            return "alerted"

        return "none"

    except Exception as e:
        print(f"[ERROR] {e}")
        return "failed"


# -------------------------------
# VERIFY HEALTH
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

    except Exception:
        return "failed"