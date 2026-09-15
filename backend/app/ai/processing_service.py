class AIProcessingService:
    """Interface boundary for future parcel/building/road extraction models."""
    def queue(self, job_id: str, project_name: str) -> None:
        # Future implementation: submit imagery to a worker/model pipeline.
        print(f"[mock AI] queued {job_id} for {project_name}")
