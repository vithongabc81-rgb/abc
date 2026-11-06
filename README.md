# Cloud Task Manager

A small cloud-computing learning project for managing tasks. The current version uses a FastAPI backend, a Supabase PostgreSQL database, and a static HTML/CSS/JavaScript frontend.

## Architecture

- Frontend: static files in `frontend/`
- Backend: FastAPI in `backend/api.py`
- Database: Supabase PostgreSQL, table `public.tasks`
- Hosting target: Render for the API and static frontend

`backend/lambda_function.py` is an earlier AWS Lambda experiment and is not used by the current application.

## Requirements

- Python 3.10 or newer
- A Supabase project with the `public.tasks` table
- A PostgreSQL connection URI from Supabase

The table must have `id` (UUID primary key), `title`, `description`, `status`, and `created_at` columns. See `docs/architecture.md` for the schema.

## Run locally

Open PowerShell in this directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set `DATABASE_URL` in `backend/.env` to the Supabase connection URI. Replace the password placeholder locally; never commit or share `.env`.

Start the API in the backend directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --port 8001
```

Open a second terminal and serve the frontend:

```powershell
python -m http.server 5500 --directory C:\path\to\project\frontend
```

Visit `http://127.0.0.1:5500`. The API docs are at `http://127.0.0.1:8001/docs`.

The frontend currently targets `http://127.0.0.1:8001`; update its API base URL when deploying the backend.

## API

- `GET /health`
- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

## Deployment

Deployment instructions for Render and Supabase will be added after the local CRUD flow is verified. Configure `DATABASE_URL` as a secret environment variable in the hosting provider; do not put credentials in source code.

## Project documents

- `docs/architecture.md` — current system architecture and database schema
- `docs/report.md` — project report draft
