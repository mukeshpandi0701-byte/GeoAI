class GISProcessingService:
    """Interface boundary for future georeferencing and PostGIS publication."""
    def prepare(self, job_id: str) -> None:
        # Future implementation: transform extracted output to GIS feature layers.
        print(f"[mock GIS] prepared {job_id}")
