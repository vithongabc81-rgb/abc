# Mini project report: Cloud Task Manager

## 1. Introduction

Cloud Task Manager is a small web application for creating, viewing, updating, and deleting tasks. It is a learning project for understanding how a web frontend, API service, and managed cloud database work together.

## 2. Objectives

- Build a simple REST API for task management.
- Persist application data in a managed PostgreSQL database.
- Connect a browser-based frontend to the API.
- Practice environment-based configuration and cloud deployment.

## 3. Technology and architecture

- Frontend: HTML, CSS, and JavaScript
- Backend: Python and FastAPI
- Database: Supabase PostgreSQL
- Planned hosting: Render for the API and static frontend
- Database driver: psycopg

The request flow is browser → FastAPI → Supabase PostgreSQL. The earlier AWS Lambda implementation is retained as an experiment but is not part of the current application path.

## 4. Main features

- Create a task with a title and optional description.
- View the task list.
- Update task fields, including status (`pending`, `in_progress`, or `done`).
- Delete a task.
- Display request errors in the frontend.

## 5. Data model

The `public.tasks` table uses a UUID primary key and stores `title`, `description`, `status`, and `created_at`.

## 6. Deployment status

The application is being tested locally before deployment. The API and frontend can be run separately; the API uses `DATABASE_URL` from a local environment file. For deployment, the database URL must be configured as a secret environment variable in the hosting provider rather than committed to the repository.

After deployment, record the public frontend/API URLs, verification steps, screenshots, and provider logs here.

## 7. Benefits and limitations

Managed hosting and a managed database reduce the need to administer servers and database infrastructure. The project is intentionally small and does not yet include user authentication, role-based access, or production-grade operational controls.

## 8. Conclusion

This project demonstrates the basic integration of a browser frontend, an API service, and a cloud-hosted relational database. Deployment and end-to-end verification are the remaining milestones.
