from temporalio import workflow
from datetime import timedelta


@workflow.defn
class AutoHealWorkflow:

    @workflow.run
    async def run(self, deployment_name: str):

        max_retries = 3

        for attempt in range(max_retries):

            # ---------------- CLASSIFY ----------------
            result = await workflow.execute_activity(
                "classify_failure",
                deployment_name,
                start_to_close_timeout=timedelta(seconds=10),
            )

            action = result.get("action")

            if action == "healthy":
                return "Recovered automatically"

            if action == "alert":
                return "Alert sent - manual fix needed"

            # ---------------- TAKE ACTION ----------------
            await workflow.execute_activity(
                "take_action",
                {
                    "action": action,
                    "deployment": deployment_name
                },
                start_to_close_timeout=timedelta(seconds=20),
            )

            # ---------------- COOLDOWN ----------------
            await workflow.sleep(10)

            # ---------------- VERIFY ----------------
            status = await workflow.execute_activity(
                "verify_health",
                deployment_name,
                start_to_close_timeout=timedelta(seconds=10),
            )

            if status == "healthy":
                return f"Recovered after {attempt+1} attempts"

        return "Failed after retries"