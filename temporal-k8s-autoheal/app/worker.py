import asyncio
from temporalio.worker import Worker
from temporalio.client import Client

from workflows import AutoHealWorkflow
from activities import classify_failure, take_action, verify_health


async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="devops-task-queue",
        workflows=[AutoHealWorkflow],
        activities=[
            classify_failure,
            take_action,
            verify_health,
        ],
    )

    print("Worker started...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())