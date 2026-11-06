import os
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlsplit
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from psycopg.rows import dict_row


load_dotenv(Path(__file__).with_name(".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set the DATABASE_URL environment variable before starting the API")

app = FastAPI(title="Cloud Task Manager API")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title is required")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    status: Literal["pending", "in_progress", "done"] | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title cannot be empty")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


def get_connection() -> psycopg.Connection:
    parsed_url = urlsplit(DATABASE_URL)
    if parsed_url.scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("DATABASE_URL must be a PostgreSQL connection URI")

    host = parsed_url.hostname
    username = unquote(parsed_url.username or "")
    password = unquote(parsed_url.password or "")
    database = unquote(parsed_url.path.lstrip("/"))
    try:
        port = parsed_url.port or 5432
    except ValueError as exc:
        raise RuntimeError("DATABASE_URL contains an invalid port") from exc

    if not host or not username or not password or not database:
        raise RuntimeError("DATABASE_URL is missing a required connection component")

    return psycopg.connect(
        host=host,
        port=port,
        dbname=database,
        user=username,
        password=password,
        sslmode="require",
        row_factory=dict_row,
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> dict[str, object]:
    with get_connection() as connection:
        tasks = connection.execute(
            """
            SELECT id, title, description, status, created_at
            FROM public.tasks
            ORDER BY created_at DESC
            """
        ).fetchall()
    return {"tasks": tasks, "count": len(tasks)}


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate) -> dict[str, object]:
    with get_connection() as connection:
        created = connection.execute(
            """
            INSERT INTO public.tasks (title, description)
            VALUES (%s, %s)
            RETURNING id, title, description, status, created_at
            """,
            (task.title, task.description),
        ).fetchone()
    return created


@app.get("/tasks/{task_id}")
def get_task(task_id: UUID) -> dict[str, object]:
    with get_connection() as connection:
        task = connection.execute(
            """
            SELECT id, title, description, status, created_at
            FROM public.tasks
            WHERE id = %s
            """,
            (task_id,),
        ).fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: UUID, update: TaskUpdate) -> dict[str, object]:
    updates = update.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="no fields to update")
    if any(value is None for value in updates.values()):
        raise HTTPException(status_code=400, detail="fields cannot be null")

    set_clauses = [f"{column} = %s" for column in updates]
    values = list(updates.values()) + [task_id]
    with get_connection() as connection:
        task = connection.execute(
            f"""
            UPDATE public.tasks
            SET {", ".join(set_clauses)}
            WHERE id = %s
            RETURNING id, title, description, status, created_at
            """,
            values,
        ).fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: UUID) -> dict[str, str]:
    with get_connection() as connection:
        deleted = connection.execute(
            "DELETE FROM public.tasks WHERE id = %s RETURNING id",
            (task_id,),
        ).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"message": "Task deleted", "id": str(deleted["id"])}
