from temporalio import workflow
from datetime import timedelta

@workflow.defn
class AutoHealWorkflow:

    @workflow.run
    async def run(self, deployment_name: str):

        status = await workflow.execute_activity(
            "check_pod_status",
            deployment_name,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if status == "healthy":
            return "Already healthy"

        for i in range(3):
            await workflow.execute_activity(
                "restart_deployment",
                deployment_name,
                start_to_close_timeout=timedelta(seconds=20),
            )

            await workflow.sleep(10)

            result = await workflow.execute_activity(
                "verify_health",
                deployment_name,
                start_to_close_timeout=timedelta(seconds=10),
            )

            if result == "healthy":
                return f"Recovered in {i+1} attempts"

        return "Failed after retries"