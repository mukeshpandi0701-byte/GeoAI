# Setup

## Frontend

```powershell
cd D:\parcelmap\frontend
npm install
npm run dev
```

Open the address Vite prints (normally `http://localhost:5173`). The User Portal is the default view; use the header selector to enter the Admin Portal.

## Backend

```powershell
cd D:\parcelmap\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with interactive documentation at `/docs`. `POST /api/uploads/drone-image` accepts JPG, PNG, GIF, WEBP, and TIFF files and stores them locally under `backend/storage/uploads/`. `GET /api/uploads/{job_id}` returns the in-memory status of an upload while the server is running.

## Backend tests

```powershell
cd D:\parcelmap\backend
pip install -r requirements-dev.txt
pytest
```

AI and GIS processing remain mock placeholder calls; no model, GIS system, database, or job worker runs in Phase 1.
