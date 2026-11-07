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

The frontend currently targets the deployed Render API at `https://cloud-task-manager-api-f5hz.onrender.com`. For local development, change this value in `frontend/app.js` to `http://127.0.0.1:8001`.

## API

- `GET /health`
- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

## Deploy the backend to Render

The root `render.yaml` configures a Python web service with `backend/` as its root directory. To deploy:

1. Push the repository to GitHub.
2. In Render, choose **New → Blueprint**, connect the repository, and apply `render.yaml`.
3. Enter the Supabase PostgreSQL connection URI when Render prompts for `DATABASE_URL`. Keep credentials out of GitHub.
4. Wait for the deploy and open the service URL followed by `/health`; it should return `{"status":"ok"}`.
5. After deploying the frontend, update the service's `CORS_ORIGINS` environment variable to include the frontend's exact origin, then redeploy.

The existing Supabase table must include all columns listed above. If `description` is missing, run the `ALTER TABLE` statement in `docs/architecture.md` before testing task endpoints.

## Deploy the frontend as a Render Static Site

1. Push the latest project changes to the GitHub `main` branch.
2. In Render, choose **New → Static Site** and connect the same GitHub repository and `main` branch.
3. Set **Root Directory** to `frontend`.
4. Leave the build command empty if Render allows it; otherwise use `echo "No build step"`.
5. Set **Publish Directory** to `.` and create the site.
6. Wait for Render to show the static site's public `onrender.com` URL.
7. In the backend web service settings, set `CORS_ORIGINS` to the exact frontend origin (scheme and hostname only, with no trailing slash), for example `https://your-site.onrender.com`, then save and redeploy the backend.
8. Open the frontend URL and test it. Task actions also require a working Supabase connection and the complete table schema.

## Project documents

- `docs/architecture.md` — current system architecture and database schema
- `docs/report.md` — project report draft
