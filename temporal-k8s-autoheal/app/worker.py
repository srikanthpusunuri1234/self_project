import asyncio
from temporalio.worker import Worker
from temporalio.client import Client

from workflows import AutoHealWorkflow
from activities import check_pod_status, restart_deployment, verify_health

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="devops-task-queue",
        workflows=[AutoHealWorkflow],
        activities=[
            check_pod_status,
            restart_deployment,
            verify_health,
        ],
    )

    print("Worker started...")
    await worker.run()

asyncio.run(main())