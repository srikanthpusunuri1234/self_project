import asyncio
from temporalio.client import Client
from workflows import AutoHealWorkflow

async def main():
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        AutoHealWorkflow.run,
        "bad-app",
        id="auto-heal-test",
        task_queue="devops-task-queue",
    )

    print(result)

asyncio.run(main())