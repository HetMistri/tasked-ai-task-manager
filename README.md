# Tasked: AI Enabled Task Manager

A task manager with a normal CRUD interface plus an optional natural-language
assistant. The assistant uses **Google Gemini** function calling, but the
backend remains the authority for authentication, validation, ownership and
every task change.

The project is deliberately split into independently runnable services:

```
Browser
  │
  ▼
React frontend (nginx :5173)
  │  /api/*           /ai/*
  ▼                    ▼
Core Task API       AI service
(FastAPI :8000)     (FastAPI :8001)
  │                    │
  ▼                    │  HTTP + user's JWT
PostgreSQL             └──► Core Task API
```

- **Frontend** — React + TypeScript. Manual task management and the AI chat panel.
- **Core Task API** — FastAPI. Authentication, task rules, ownership checks and PostgreSQL.
- **AI service** — FastAPI. Gemini function-calling loop. No database access.
- **PostgreSQL** — persistent task storage.

Manual task CRUD never calls the AI service or Gemini. You can stop the AI
service and keep using the task dashboard normally.

## Quick start (Docker Compose)

```bash
cp .env.example .env
# Optional: set a real JWT_SECRET. Leave GEMINI_ENABLED=false for mock mode.
docker compose up --build
```

Open <http://localhost:5173>, register an account, and create a task.

To stop:

```bash
docker compose down          # keeps the PostgreSQL volume
docker compose down -v       # also deletes local demo data (destructive)
```

## AI modes

The default is **mock mode**, which needs no API key and is clearly labelled in
the UI. It exercises the same validation and confirmation paths as live mode.

Live Gemini mode:

```dotenv
# .env (ignored by Git)
GEMINI_ENABLED=true
GEMINI_API_KEY=your-key-from-google-ai-studio
GEMINI_MODEL=gemini-3.5-flash-lite
```

```bash
docker compose up -d --build ai-service
```

`GEMINI_MODEL` must be a model available to your key that supports function
calling. The default is `gemini-3.5-flash-lite`, a stable, cost-effective
choice. Get a key at <https://aistudio.google.com/apikey>. Never commit it.

If Gemini is unavailable, `/ai/chat` returns a controlled error and manual task
management continues to work.

## Manual task features

- Create, view, edit, complete, reopen, archive, restore and delete tasks.
- Status (`pending`, `in_progress`, `completed`) and priority (`low`, `medium`,
  `high`, `urgent`).
- Optional due dates, search and filters.
- JWT authentication and per-user task ownership.
- Activity history recorded by the Core Task API.

## AI-supported actions

The AI service exposes only these backend functions to Gemini:

| Function | Purpose |
|---|---|
| `create_task` | Create a task |
| `search_tasks` | Search/list the user's tasks |
| `update_task` | Update task fields |
| `complete_task` | Mark completed |
| `reopen_task` | Reopen a completed task |
| `set_task_priority` | Change priority |
| `archive_task` | Archive a task |
| `restore_task` | Restore an archived task |
| `delete_task` | Delete after explicit confirmation |
| `get_task_summary` | Task counts and overdue summary |

Safety behaviour:

- Function names and arguments are validated before execution.
- Every read and write goes through the Core Task API with the user's JWT.
- Ambiguous task names trigger a clarification question.
- Deletion always requires a separate confirmation.
- The function-calling loop is capped at 4 iterations.

## Environment variables

| Variable | Default | Used by |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://tasked:tasked@postgres:5432/tasked` | Core Task API |
| `JWT_SECRET` | dev placeholder | Core Task API |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Core Task API CORS |
| `GEMINI_ENABLED` | `false` | AI service |
| `GEMINI_API_KEY` | empty | AI service |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | AI service |
| `GEMINI_TIMEOUT_SECONDS` | `30` | AI service |
| `TASK_API_URL` | `http://task-service:8000` | AI service |
| `TASK_API_TIMEOUT` | `10.0` | AI service |

Copy `.env.example` to `.env`. Only `.env.example` is committed.

## Run services individually

### Database only

```bash
docker compose up --build postgres
```

### Core Task API (with PostgreSQL)

```bash
docker compose up --build postgres task-service
```

The API is at <http://localhost:8000>, docs at <http://localhost:8000/docs>.

Standalone (requires a reachable PostgreSQL):

```bash
cd task-service
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://tasked:tasked@localhost:5432/tasked
export JWT_SECRET=local-dev-secret
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### AI service (with the Core Task API and database)

```bash
docker compose up --build postgres task-service ai-service
```

Standalone:

```bash
cd ai-service
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
export TASK_API_URL=http://localhost:8000
export GEMINI_ENABLED=false
uvicorn app.main:app --reload --port 8001
```

Health: <http://localhost:8001/ai/health>

### Full stack

```bash
docker compose up --build
```

### Frontend only

```bash
cd client
npm install
npm run dev
```

Vite proxies `/api` and `/ai` to the running backend containers.

## API overview

Core Task API:

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET|POST /tasks`, `GET|PATCH|DELETE /tasks/{id}`
- `POST /tasks/{id}/complete`, `/reopen`, `/priority`, `/archive`, `/restore`
- `GET /tasks/summary`, `GET /activity`
- `GET /health` (liveness), `GET /ready` (PostgreSQL readiness)

AI service:

- `POST /ai/chat`
- `POST /ai/actions/{confirmation_id}/confirm`
- `GET /ai/health`

Full examples are in [`docs/api.md`](docs/api.md).

## Tests

```bash
cd task-service && .venv/bin/python -m pytest -q
cd ai-service && .venv/bin/python -m pytest -q
cd client && npm run build
```

Or with fresh environments, follow the standalone setup and run `pytest -q`.

Task tests use in-memory SQLite. AI tests mock Gemini and the Core Task API, so
no API key or network access is required.

## Demo flow

1. Start the full stack.
2. Register and create a task manually.
3. Ask: “Create a high-priority DBMS assignment due Friday.”
4. Ask: “Show my tasks.”
5. Ask: “Mark my DBMS assignment complete.”
6. Ask: “Change the priority of my DBMS assignment to urgent.”
7. Ask to delete a task and use the confirmation buttons.
8. Restart the stack and show that tasks persist.
9. Stop the AI service and show that manual CRUD still works.

More detail: [`docs/demo.md`](docs/demo.md).

## Repository layout

```
task-service/   Core Task API (FastAPI, SQLAlchemy, Alembic, JWT)
ai-service/     AI service (FastAPI, google-genai, Gemini function calling)
client/         React + TypeScript frontend, served by nginx
docs/           Architecture, API and demo notes
scripts/        Smoke-test helper
compose.yaml    Full stack
.env.example    Environment template
```

## Known limitations

- The AI service keeps pending confirmations in memory; they expire after five
  minutes and are lost on restart. This is acceptable for the single-process
  MVP.
- Activity history is not yet displayed in the frontend.
- Mock mode uses simple keyword heuristics; it demonstrates the flow and safety
  checks, not a real language model.
- Live Gemini behaviour depends on the key, quota and model availability. Mock
  tests do not prove a live provider call.

## Security notes

- Passwords are hashed with bcrypt.
- JWTs are required for task and AI endpoints.
- Every task query is scoped to the authenticated user.
- The Gemini API key stays on the server and is injected at runtime.
- `.env`, virtual environments and local databases are ignored by Git.
