# Architecture — Tasked: AI Enabled Task Manager

## Services

| Service | Technology | Port | Responsibility |
|---|---|---|---|
| `frontend` | React 19 + TypeScript, nginx | 5173 | Manual task UI and AI chat panel |
| `task-service` | FastAPI, SQLAlchemy, Alembic | 8000 | Auth, task rules, ownership, PostgreSQL |
| `ai-service` | FastAPI, `google-genai` | 8001 | Natural language, Gemini function calling |
| `postgres` | PostgreSQL 16 | 5432 | Durable task, user and activity storage |

The browser only talks to the nginx-served frontend. nginx proxies `/api/*` to
`task-service` (removing the `/api` prefix) and `/ai/*` to `ai-service`.

## Request flows

### Manual CRUD

```
Browser → nginx → Core Task API → PostgreSQL
```

This path never calls the AI service, Gemini, or an AI health endpoint.

### AI chat

```
Browser → nginx → AI service
                     │  Bearer JWT + validated function call
                     ▼
                 Core Task API → PostgreSQL
```

The AI service has no database driver and no database credentials. It forwards
the user's JWT to the Core Task API, which re-checks ownership and business
rules on every request. The AI service never invents a `user_id`.

### Function-calling loop

1. AI service sends the user message, system prompt and ten function
   declarations to Gemini.
2. Gemini returns text and/or function calls.
3. The AI service validates every function name and its arguments with
   Pydantic.
4. Handlers call the Core Task API over HTTP.
5. The real result is sent back to Gemini as a function response.
6. The loop repeats until Gemini returns text, a confirmation is required, or
   the four-iteration cap is reached.

Delete calls are intercepted before execution and stored as pending
confirmations. The user must confirm through a separate endpoint. Confirmations
are token-scoped, single-use, and expire after five minutes.

## Failure isolation

- Core Task API liveness (`/health`) does not depend on the AI service.
- Readiness (`/ready`) depends on PostgreSQL, not Gemini.
- AI service health reports Gemini configuration and Core Task API reachability;
  a Gemini failure does not mark the Core Task API unhealthy.
- AI provider errors are returned as short user-facing messages; manual CRUD
  is unaffected.
- nginx resolves upstream names at request time, so it starts even if the AI
  service is temporarily down.
- Compose starts `ai-service` after `task-service`, but no other service
  depends on the AI service.

## Provider abstraction

`ai-service/app/clients/gemini.py` contains:

- `GeminiClient` — official `google-genai` async client, bounded timeout
  (default 30 s) and one retry for transient errors. API errors are mapped to
  safe messages; raw provider details and keys are never returned or logged.
- `MockGeminiClient` — deterministic keyword-based provider used when
  `GEMINI_ENABLED=false`.

Both return `AIResponse`, so validation, clarification, confirmation and error
handling are identical in mock and live mode.

## Data ownership

PostgreSQL is the only source of truth. Tasks are soft-deletable and always
scoped by `user_id`, which comes from the verified JWT. Activity records are
written by the Core Task API alongside task changes.

The AI service may only see task data returned by the Core Task API after an
authenticated request, and only the fields needed for the response.

## Configuration

AI provider configuration lives only in the AI service:

- `GEMINI_ENABLED`
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (default `gemini-3.5-flash-lite`)
- `GEMINI_TIMEOUT_SECONDS`

The Core Task API has no Gemini configuration and starts without an API key.

## Trade-offs for this MVP

- Pending confirmations are stored in process memory.
- Bulk operations are intentionally not implemented.
- Authentication and activity history stay in the Core Task API rather than
  becoming separate deployable services.
