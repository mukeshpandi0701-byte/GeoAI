# Architecture

The prototype separates roles before introducing authentication. The React frontend has an **Admin Portal** for imagery ingestion and project operations, and a read-only **User Portal** for published map and parcel data. `shared/` contains the mock map and sample records reused by both views.

The FastAPI backend exposes `POST /api/uploads/drone-image` and `GET /api/uploads/{job_id}`. It validates recognized image types, stores files locally in `backend/storage/uploads/`, and returns an in-memory queued mock job. `AIProcessingService` and `GISProcessingService` are intentionally small interfaces: model inference, georeferencing, vector cleanup, and publication can be added without changing API route code.

## Future data flow

`Drone upload → project/job record → AI feature extraction → GIS transformation → PostGIS → published map API → User Portal`

No database is required today. Upload job records are lost on application restart, and local uploaded files are development-only. When ready, add PostgreSQL with the PostGIS extension, then place database models/repositories behind `backend/app/models` and the service layer. Store imagery externally (object storage) and retain only a URI plus metadata in the database.
