# API — Tasked: AI Enabled Task Manager

All task endpoints require:

```
Authorization: Bearer <JWT>
```

Through the frontend nginx proxy, Core Task API paths are prefixed with `/api`
(for example, `POST /api/tasks` → `POST /tasks`). The AI service is available at
`/ai/*`.

## Authentication (Core Task API)

### Register

`POST /auth/register`

```json
{
  "email": "student@example.com",
  "password": "correct-horse-battery",
  "display_name": "Student",
  "timezone": "Asia/Kolkata"
}
```

Returns `201` with:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "email": "student@example.com",
    "display_name": "Student",
    "timezone": "Asia/Kolkata",
    "created_at": "2026-10-22T12:00:00Z"
  }
}
```

`POST /auth/login` accepts `email` and `password` and returns the same shape.
`GET /auth/me` returns the current user.

## Tasks (Core Task API)

### Create

`POST /tasks` → `201`

```json
{
  "title": "DBMS assignment",
  "description": "Normalisation exercises",
  "priority": "high",
  "due_at": "2026-10-23T18:30:00Z"
}
```

Only `title` is required. Priority is `low | medium | high | urgent`.

### List

`GET /tasks?page=1&page_size=20&status=pending&priority=high&is_archived=false&search=DBMS`

```json
{
  "tasks": [
    {
      "id": "<uuid>",
      "user_id": "<uuid>",
      "title": "DBMS assignment",
      "description": "Normalisation exercises",
      "status": "pending",
      "priority": "high",
      "due_at": "2026-10-23T18:30:00Z",
      "is_archived": false,
      "archived_at": null,
      "completed_at": null,
      "created_at": "2026-10-22T12:00:00Z",
      "updated_at": "2026-10-22T12:00:00Z",
      "deleted_at": null,
      "is_overdue": false
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Other task endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/tasks/{id}` | Read one task |
| PATCH | `/tasks/{id}` | Partial update |
| POST | `/tasks/{id}/complete` | Sets `completed_at` |
| POST | `/tasks/{id}/reopen` | Clears `completed_at` |
| POST | `/tasks/{id}/priority` | Body: `{"priority": "urgent"}` |
| POST | `/tasks/{id}/archive` | Does not change completion status |
| POST | `/tasks/{id}/restore` | Clears archive state |
| DELETE | `/tasks/{id}` | Soft delete; returns `204` |
| GET | `/tasks/summary` | Counts by status/priority/overdue |
| GET | `/activity` | Activity history |

Tasks belonging to another user return `404`; ownership is never inferred from
the request body.

## AI service

### Chat

`POST /ai/chat`

```json
{ "message": "Create a high-priority DBMS assignment due Friday" }
```

Normal response:

```json
{
  "response": "Created \"DBMS assignment\" (priority: high).",
  "requires_confirmation": false,
  "confirmation_id": null,
  "confirmation_details": null,
  "is_mock": false
}
```

Delete response:

```json
{
  "response": "Please confirm: delete the task matching 'DBMS assignment'. This action cannot be undone.",
  "requires_confirmation": true,
  "confirmation_id": "<32-char hex>",
  "confirmation_details": {
    "action": "delete_task",
    "task_identifier": "DBMS assignment"
  },
  "is_mock": false
}
```

`is_mock` is `true` whenever the service is using the deterministic mock
provider. The UI shows this explicitly.

### Confirm or cancel

`POST /ai/actions/{confirmation_id}/confirm`

```json
{ "confirmation_id": "<same id>", "confirmed": true }
```

```json
{
  "success": true,
  "message": "Task deleted.",
  "task_id": "<uuid>"
}
```

Confirmations are single-use, expire after five minutes, and only work for the
user who triggered them. Cancelling returns `{"success": true, "message":
"Action cancelled."}`.

### AI health

`GET /ai/health`

```json
{
  "status": "healthy",
  "gemini": {
    "enabled": false,
    "configured": false,
    "model": "gemini-3.5-flash-lite",
    "mock_mode": true
  },
  "task_api": {
    "url": "http://task-service:8000",
    "healthy": true
  }
}
```

Health does not call Gemini, so a bad API key does not make the service
unhealthy. It reports `configured: false` instead.

## Core health

- `GET /health` — liveness only; no database or AI dependency.
- `GET /ready` — checks PostgreSQL; returns `503` when the database is down.

## Error format

FastAPI returns:

```json
{ "detail": "Task not found" }
```

AI provider failures are returned as a normal chat response with a safe message
(no API key or raw provider payload), for example:

```json
{
  "response": "The AI provider is unavailable right now. You can still manage tasks manually. Details: Gemini rate limit reached. Wait a moment and try again.",
  "requires_confirmation": false,
  "is_mock": false
}
```
