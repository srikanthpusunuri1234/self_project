from temporalio import workflow
from datetime import timedelta


@workflow.defn
class AutoHealWorkflow:

    @workflow.run
    async def run(self, deployment_name: str):

        # STEP 1: CLASSIFY
        action = await workflow.execute_activity(
            "classify_failure",
            deployment_name,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if action == "healthy":
            return "Already healthy"

        # STEP 2: TAKE ACTION (FIXED: SINGLE ARG)
        result = await workflow.execute_activity(
            "take_action",
            (action, deployment_name),   # ✅ tuple
            start_to_close_timeout=timedelta(seconds=20),
        )

        # STEP 3: WAIT
        await workflow.sleep(10)

        # STEP 4: VERIFY
        status = await workflow.execute_activity(
            "verify_health",
            deployment_name,
            start_to_close_timeout=timedelta(seconds=10),
        )

        return f"Action: {action}, Result: {status}"