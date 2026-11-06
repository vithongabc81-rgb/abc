# Cloud Task Manager architecture

## Overview

The current application uses a small three-part cloud architecture:

- Static frontend files (`index.html`, `style.css`, and `app.js`)
- A Python FastAPI service that exposes the task API
- Supabase PostgreSQL for persistent task storage

Render is the planned hosting provider for the API and frontend. Until deployment is complete, the app can be run locally with the frontend on port 5500 and the API on port 8001.

The earlier `backend/lambda_function.py` file is an AWS Lambda exercise. It is not called by the current FastAPI application.

## Request flow

1. A user opens the frontend.
2. The frontend calls the FastAPI endpoints using `fetch()`.
3. FastAPI validates the request and executes parameterized SQL with psycopg.
4. Supabase PostgreSQL reads or updates `public.tasks`.
5. FastAPI returns JSON to the frontend.

## Database schema

Table: `public.tasks`

| Column | Type | Purpose |
|---|---|---|
| `id` | `uuid` primary key | Unique task identifier; defaults to `gen_random_uuid()` |
| `title` | `text` | Required task title, 1–200 characters |
| `description` | `text` | Optional task description, up to 1000 characters |
| `status` | `text` | `pending`, `in_progress`, or `done` |
| `created_at` | `timestamptz` | Creation time, defaults to `now()` |

If the existing table is missing `description`, add it in the Supabase SQL Editor:

```sql
ALTER TABLE public.tasks
ADD COLUMN IF NOT EXISTS description text NOT NULL DEFAULT '';
```

## API routes

- `GET /health`: API health check
- `GET /tasks`: list tasks
- `POST /tasks`: create a task
- `GET /tasks/{task_id}`: retrieve one task
- `PUT /tasks/{task_id}`: update task fields
- `DELETE /tasks/{task_id}`: delete a task

## Configuration and security

- `DATABASE_URL` is stored locally in the ignored `backend/.env` file.
- In a hosted environment, configure `DATABASE_URL` using the provider's secret environment-variable settings.
- Never commit `.env`, passwords, or database connection strings.
- CORS is configured with `CORS_ORIGINS`; set it to the deployed frontend origin when hosting.
- Database queries use parameters for user-supplied values.

## Monitoring

Use the hosting provider's application logs to inspect API errors. Supabase provides database monitoring through its dashboard.
