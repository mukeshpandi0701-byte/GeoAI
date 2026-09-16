class AIProcessingService:
    """Queue-facing boundary for the local processing worker.

    Upload requests only create durable queued jobs.  A worker process claims
    them separately, which avoids the former mock status progression.
    """

    def queue(self, job_id: str, project_name: str) -> None:
        # A production queue can be attached here later. The database row is the
        # source of truth for the current lightweight worker foundation.
        return None
