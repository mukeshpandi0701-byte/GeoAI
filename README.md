# Urban Parcel Mapping

A beginner-friendly foundation for an urban cadastral mapping application. It demonstrates a public parcel-map experience and an administrator upload workflow while keeping the implementation intentionally small and easy to extend.

## Project structure

- `frontend/` — React + Vite prototype with User and Admin portal views and shared mock map data.
- `backend/` — FastAPI API with SQLite-backed projects and upload metadata, plus local image storage.
- `docs/` — local setup instructions and the planned architecture.

## Current scope and limitations

The frontend map, parcels, and processing metrics are mock data. The Admin Portal connects to the FastAPI API for upload jobs and projects. Uploads may be linked to a project and move through `queued`, `processing`, `review`, and `approved` or `rejected` states. The backend saves validated uploads locally under `backend/storage/uploads/` and persists job/project metadata in SQLite. AI extraction and GIS preparation are separated placeholder services; they do not perform real processing. There is no PostGIS geometry, authentication, authorization, or background job worker yet.

## Local setup

Frontend:

```powershell
cd D:\parcelmap\frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000`. To use another API address, create `frontend/.env.local` with:

```text
VITE_API_URL=http://localhost:8000
```

Run the backend before using Admin Portal uploads, projects, or review actions. If the UI says it cannot reach the backend, verify `VITE_API_URL`, start FastAPI, and restart Vite after changing `.env.local`.

Backend:

```powershell
cd D:\parcelmap\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

SQLite is the default development database. Tables are created automatically when the backend starts, and the default database file is `backend/storage/parcelmap.db`. To use another SQLite file or prepare for a future PostgreSQL deployment, set `DATABASE_URL` before starting the backend:

```powershell
$env:DATABASE_URL = "sqlite:///D:/parcelmap/backend/storage/parcelmap.db"
```

PostgreSQL and PostGIS connection URLs are not configured or required in this phase; the SQLAlchemy session layer is the future integration point.

For backend tests, install the test requirements and run pytest:

```powershell
pip install -r requirements-dev.txt
pytest
```

See [docs/setup.md](docs/setup.md) for details and [docs/architecture.md](docs/architecture.md) for the planned processing flow.
