# Setup

## Frontend

```powershell
cd D:\parcelmap\frontend
npm install
npm run dev
```

Open the address Vite prints (normally `http://localhost:5173`). The User Portal is the default view; use the header selector to enter the Admin Portal. The Admin Portal uses `VITE_API_URL` for the backend base URL and defaults to `http://localhost:8000`. To override it, add `frontend/.env.local` containing `VITE_API_URL=http://localhost:8000` before starting Vite.

Start the backend before using Admin Portal uploads, project creation, or the review queue. The UI validates empty project names, missing image files, and unsupported image extensions before sending a request. Server validation errors are displayed in the form.

## Backend

```powershell
cd D:\parcelmap\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with interactive documentation at `/docs`. `POST /api/uploads/drone-image` accepts JPG, PNG, GIF, WEBP, and TIFF files and stores them locally under `backend/storage/uploads/`. `GET /api/uploads/{job_id}` reads persisted upload metadata. `POST /api/projects`, `GET /api/projects`, and `GET /api/projects/{project_id}` use the same database.

## Database

The backend uses SQLite by default, creating `backend/storage/parcelmap.db` and its tables automatically on startup. No separate database server or migration command is needed for local development.

Set `DATABASE_URL` before starting Uvicorn to override the default location:

```powershell
$env:DATABASE_URL = "sqlite:///D:/parcelmap/backend/storage/parcelmap.db"
uvicorn app.main:app --reload
```

The SQLAlchemy configuration can use a future PostgreSQL URL, but PostGIS extensions, geometry columns, and migrations are intentionally not part of Phase 3.

## Backend tests

```powershell
cd D:\parcelmap\backend
pip install -r requirements-dev.txt
pytest
```

AI and GIS processing remain mock placeholder calls. Queued uploads remain queued until a future worker updates them. SQLite is intended only for local development; database files are not committed. There is still no model, GIS system, PostGIS geometry, authentication, or job worker.

## Frontend troubleshooting

- **“Could not reach the backend”**: Start the backend from `D:\parcelmap\backend`, then verify that `VITE_API_URL` matches its host and port. Restart Vite after changing `.env.local`.
- **Upload validation message**: Choose a JPG, PNG, GIF, WEBP, or TIFF file and enter a project name before submitting.
- **No projects or review items appear**: Confirm the backend is running and that the frontend points at the same `DATABASE_URL`-backed backend instance.
