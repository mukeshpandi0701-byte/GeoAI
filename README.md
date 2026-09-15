# Urban Parcel Mapping

A beginner-friendly foundation for an urban cadastral mapping application. It demonstrates a public parcel-map experience and an administrator upload workflow while keeping the implementation intentionally small and easy to extend.

## Project structure

- `frontend/` — React + Vite prototype with User and Admin portal views and shared mock map data.
- `backend/` — FastAPI API for health checks and safely storing image uploads with in-memory job status records.
- `docs/` — local setup instructions and the planned architecture.

## Current scope and limitations

The frontend map, parcels, projects, and processing metrics are mock data. The backend saves validated uploads locally under `backend/storage/uploads/` and keeps job metadata only in memory, so job records disappear when the server restarts. AI extraction and GIS preparation are separated placeholder services; they do not perform real processing. There is no database, PostGIS, authentication, authorization, or background job worker yet.

## Local setup

Frontend:

```powershell
cd D:\parcelmap\frontend
npm install
npm run dev
```

Backend:

```powershell
cd D:\parcelmap\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For backend tests, install the test requirements and run pytest:

```powershell
pip install -r requirements-dev.txt
pytest
```

See [docs/setup.md](docs/setup.md) for details and [docs/architecture.md](docs/architecture.md) for the planned processing flow.
