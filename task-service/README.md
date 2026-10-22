# Tasked - Core Task API

FastAPI service that owns authentication, task business rules and all
PostgreSQL reads/writes. The AI service talks to this API; it never touches the
database directly.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account, returns JWT |
| POST | `/auth/login` | Email + password -> JWT |
| GET | `/auth/me` | Current user |
| POST | `/tasks` | Create task |
| GET | `/tasks` | List/filter tasks (pagination) |
| GET | `/tasks/summary` | Dashboard counts |
| GET | `/tasks/{id}` | Read one task |
| PATCH | `/tasks/{id}` | Update fields |
| POST | `/tasks/{id}/complete` | Complete task |
| POST | `/tasks/{id}/reopen` | Reopen task |
| POST | `/tasks/{id}/priority` | Change priority |
| POST | `/tasks/{id}/archive` | Archive task |
| POST | `/tasks/{id}/restore` | Restore archived task |
| DELETE | `/tasks/{id}` | Soft delete |
| GET | `/activity` | Activity history |
| GET | `/activity/tasks/{id}` | History for one task |
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness (checks PostgreSQL) |

Interactive docs: http://localhost:8000/docs

## Environment

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://tasked:tasked@postgres:5432/tasked` | PostgreSQL DSN |
| `JWT_SECRET` | dev placeholder | **Change outside local development** |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_MINUTES` | `10080` | 7 days |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allow-list |
| `APP_ENV` | `development` | |

This service does not need AI provider credentials.

## Run standalone (without Docker)

Requires a reachable PostgreSQL database.

```bash
cd task-service
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://tasked:tasked@localhost:5432/tasked
export JWT_SECRET=local-dev-secret
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Database migrations

```bash
cd task-service
alembic upgrade head       # apply
alembic downgrade -1       # roll back one revision
alembic revision --autogenerate -m "message"
```

The Docker image runs `alembic upgrade head` before starting Uvicorn, so the
schema is ready before the container is healthy.

## Tests

```bash
cd task-service
pip install -e ".[dev]"
pytest -q
```

Tests use an in-memory SQLite database and never call Gemini.
