from kubernetes import client, config, watch
import asyncio
from temporalio.client import Client
from workflows import AutoHealWorkflow


def load_k8s():
    try:
        config.load_kube_config()
    except:
        config.load_incluster_config()


def get_deployment_name(pod_name):
    return "-".join(pod_name.split("-")[:-2])


def is_unhealthy(pod):
    if not pod.status.container_statuses:
        return False

    for c in pod.status.container_statuses:

        if c.state.waiting:
            if c.state.waiting.reason in [
                "CrashLoopBackOff",
                "ImagePullBackOff",
                "ErrImagePull"
            ]:
                return True

        if c.state.terminated:
            return True

        if c.restart_count > 5:
            return True

    return False


async def trigger_workflow(deployment_name):
    client = await Client.connect("localhost:7233")

    workflow_id = f"autoheal-{deployment_name}"

    try:
        await client.start_workflow(
            AutoHealWorkflow.run,   # ✅ FIXED
            deployment_name,
            id=workflow_id,
            task_queue="devops-task-queue",
        )
        print(f"[TRIGGER] Workflow started for {deployment_name}")

    except Exception as e:
        print(f"[INFO] Workflow already running or error: {e}")


async def watch_pods():
    load_k8s()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    print("👀 Watching Kubernetes pods...")

    for event in w.stream(v1.list_namespaced_pod, namespace="default"):

        pod = event["object"]
        pod_name = pod.metadata.name

        if is_unhealthy(pod):
            deployment_name = get_deployment_name(pod_name)

            print(f"[DETECTED] Unhealthy pod: {pod_name}")

            await trigger_workflow(deployment_name)


if __name__ == "__main__":
    asyncio.run(watch_pods())