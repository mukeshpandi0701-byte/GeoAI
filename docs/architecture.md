# Architecture

The prototype separates roles before introducing authentication. The React frontend has an **Admin Portal** for imagery ingestion and project operations, and a read-only **User Portal** for published map and parcel data. `shared/` contains the mock map and sample records reused by both views.

The FastAPI backend exposes upload endpoints plus `POST /api/projects`, `GET /api/projects`, and `GET /api/projects/{project_id}`. The Admin Portal uses these endpoints through a configurable `VITE_API_URL` base URL. SQLAlchemy persists project records and upload metadata to SQLite by default, while image files remain in `backend/storage/uploads/`. The database session layer is ready for a future PostgreSQL/PostGIS URL, but no geometry columns or PostGIS features are present yet. `AIProcessingService` and `GISProcessingService` are intentionally small interfaces: model inference, georeferencing, vector cleanup, and publication can be added without changing API route code.

## Future data flow

`Drone upload → project/job record → AI feature extraction → GIS transformation → PostGIS → published map API → User Portal`

SQLite stores project records and upload metadata today; local uploaded files remain development-only. When ready, configure PostgreSQL with the PostGIS extension, add migrations, then introduce geometry-aware models and repositories behind the existing database session and service layers. Store imagery externally (object storage) and retain only a URI plus metadata in the database.
