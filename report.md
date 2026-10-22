# Tasked: AI Enabled Task Manager — Gemini migration report

**Date:** 2026-10-22
**Scope:** Replace Amazon Bedrock / Anthropic Claude Haiku 4.5 with the Google
Gemini API while keeping the existing four-service architecture and safety
behaviour.
**Status:** MVP complete and verified in mock and live Gemini modes.

No GitHub remote is configured and nothing was published. The repository
contains no committed provider key.

---

## 1. What was delivered

The application remains split into independently runnable services:

| Service | Responsibility | Local URL |
| --- | --- | --- |
| `frontend` | React + TypeScript UI, nginx reverse proxy | <http://localhost:5173> |
| `task-service` | FastAPI authentication, task rules, CRUD, activity log | <http://localhost:8000> |
| `ai-service` | FastAPI Gemini chat and function-calling orchestration | <http://localhost:8001> |
| `postgres` | Durable task/user/activity storage | `localhost:5432` |

The AI service has no database driver and does not import task-service code. It
forwards the caller's Bearer token to the Core Task API over HTTP. Manual CRUD
never calls the AI service.

### Gemini integration

- Official `google-genai` Python SDK (`>=2.32.0`), async client.
- Model supplied through `GEMINI_MODEL`; default `gemini-3.5-flash-lite`.
- Manual function-calling loop using Gemini `types.Tool` and
  `FunctionDeclaration` schemas. Automatic function calling is disabled; every
  call is validated and executed by our backend.
- Ten functions: create, search, update, complete, reopen, set priority,
  archive, restore, delete, and summary.
- Delete and broad/destructive actions require a user-scoped, short-lived,
  single-use confirmation.
- Ambiguous or missing task matches return a clarification response instead of
  guessing.
- Tool-loop limit: four iterations per user message.
- Provider failures are mapped to safe messages without leaking the key or raw
  provider payloads.
- One retry for transient provider errors, with a 30-second client timeout.
  The nginx `/ai/` proxy timeout is 120 seconds to cover the retry.

### Mock mode

`GEMINI_ENABLED=false` selects `MockGeminiClient`. It uses the same response
shape, validation, tool loop, and confirmation code as live mode. Every mock
reply is labelled `[MOCK MODE]`, and the UI badge says **Mock Mode**.

The repository default is mock mode. No Google credentials are needed to run
the default Docker Compose stack.

---

## 2. Configuration

Environment variables (see `.env.example`):

```dotenv
GEMINI_ENABLED=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT_SECONDS=30
```

- `GEMINI_ENABLED` is explicit. If it is `true` but no key is present, chat
  returns a clear configuration error; the service does not silently pretend to
  be live.
- `GEMINI_API_KEY` is read only by the AI service at runtime.
- `GEMINI_MODEL` is configured, not hardcoded at call sites. The default model
  was verified as visible to the test key with `client.models.list()` (46 models
  returned) and was exercised with live function calling.
- `GEMINI_TIMEOUT_SECONDS` bounds provider calls.

The local `.env` used for live verification is ignored by Git. The committed
`.env.example` has a blank key and `GEMINI_ENABLED=false`.

### Switching modes

```bash
# Mock mode (default, no key)
GEMINI_ENABLED=false
GEMINI_API_KEY=

# Live mode (local .env or shell)
GEMINI_ENABLED=true
GEMINI_API_KEY=<your key>
GEMINI_MODEL=gemini-3.5-flash-lite
```

Rebuild/restart the AI service after changing mode:

```bash
docker compose up -d --build ai-service
```

---

## 3. Removed Bedrock/AWS behaviour

| Removed item | Reason |
| --- | --- |
| `ai-service/app/clients/bedrock.py` | Replaced by `app/clients/gemini.py`. |
| `boto3` dependency in AI service | No AWS runtime dependency remains. |
| Unused `boto3` dependency in task-service | Task service never called Bedrock. |
| Bedrock/AWS settings (`AWS_REGION`, `BEDROCK_MODEL_ID`, `BEDROCK_ENABLED`, etc.) | Replaced by Gemini settings. |
| `/ai/health` field `bedrock` | Replaced by `gemini`. |
| `compose.aws.yaml` overlay | Obsolete provider-specific startup path. |
| AWS/Bedrock startup and deployment instructions | Replaced with Gemini instructions. |
| AWS-specific task-service configuration fields | Never used by the core service. |

`AGENTS.md` still contains the original assignment text that references Bedrock
and AWS. It is retained as historical project context and has no runtime effect.
No other Bedrock, Anthropic, Claude, or `boto3` references remain in the tracked
application code, Compose files, or current documentation.

---

## 4. Files changed / added / removed

### Added

- `ai-service/app/clients/gemini.py` — real Gemini client, deterministic mock
  client, safe provider error mapping.
- `docs/architecture.md`, `docs/api.md`, `docs/demo.md` — current architecture,
  API contracts, and demo script.
- `scripts/smoke-test.sh` — end-to-end manual CRUD + AI + confirmation flow.
- `report.md` — this report.

### Removed

- `ai-service/app/clients/bedrock.py`
- `compose.aws.yaml`

### Updated

- `ai-service/app/services/ai.py` — Gemini loop, validation before delete
  confirmation, UUID-aware task resolution, bounded iterations, health shape.
- `ai-service/app/services/tools.py` — ten Gemini function declarations and
  handler map.
- `ai-service/app/core/config.py`, `ai-service/pyproject.toml`,
  `ai-service/Dockerfile`, `ai-service/README.md`.
- `ai-service/app/api/routes.py`, `ai-service/app/main.py`.
- `ai-service/tests/test_ai_service.py` — fake provider, validation, ambiguity,
  confirmation ownership/expiry, provider failure, loop cap, mock honesty.
- `compose.yaml`, `.env.example`, `.gitignore`.
- `task-service/app/core/config.py`, `task-service/pyproject.toml`,
  `task-service/README.md` — AWS remnants removed.
- `task-service/app/services/auth.py` and `task-service/app/services/task.py` —
  commit writes before responding.
- `task-service/app/db/session.py` — corrected transaction documentation.
- `client/src/components/AIChat.tsx`, `client/src/types/index.ts`,
  `client/src/App.css` — Gemini health shape and live/mock badge.
- `client/nginx.conf` — runtime DNS resolution, `/ai/` 120-second proxy timeout,
  correct healthcheck host.
- `README.md`, `PRODUCT.md`, architecture/API/demo docs.

### Transaction fix

The Core Task API previously relied on FastAPI's yield-dependency cleanup to
commit. That cleanup runs after the response is sent, which caused an immediate
`401 User no longer exists` after registration and could expose stale reads
after writes. Mutating service methods now commit before returning; the
dependency commit remains only as a safety net.

---

## 5. Commands

### Full application

```bash
cp .env.example .env
# Optional: set JWT_SECRET and Gemini values.
docker compose up --build
```

Open <http://localhost:5173>. Stop with `docker compose down` (keeps data) or
`docker compose down -v` (deletes the local database volume).

### Independent services

```bash
# Database only
docker compose up --build postgres

# Core Task API + database
docker compose up --build postgres task-service

# AI service + Core Task API + database
docker compose up --build postgres task-service ai-service

# Full stack
docker compose up --build
```

### Standalone AI service

```bash
cd ai-service
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

export TASK_API_URL=http://localhost:8000
export GEMINI_ENABLED=false   # or true with GEMINI_API_KEY
uvicorn app.main:app --reload --port 8001
```

The Core Task API must be running for AI task actions. The AI service starts
without it, but `/ai/health` reports the dependency as unhealthy and actions
return a controlled error.

### Tests

```bash
cd task-service && .venv/bin/python -m pytest -q
cd ai-service && .venv/bin/python -m pytest -q
cd client && npm run build
docker compose config -q
./scripts/smoke-test.sh
```

---

## 6. Verification results

### Automated tests

| Check | Result |
| --- | --- |
| Core Task API tests | **15 passed** |
| AI service tests | **22 passed** |
| Frontend TypeScript + Vite build | **passed** (31 modules) |
| Compose configuration validation | **valid** |
| Default Compose without local `.env` | `GEMINI_ENABLED=false`, blank key, model set |
| Image dependency check | `google-genai 2.32.0`; `boto3` absent in both Python images |

The AI tests cover invalid tool arguments (including invalid delete arguments),
unknown tools, no-match and ambiguous matches, delete confirmation,
confirmation ownership/cancel/expiry, provider failure, loop cap, function
responses sent back to the model, mock-mode honesty, safe error mapping, and
direct UUID lookup.

### Mock-mode end-to-end

`./scripts/smoke-test.sh` passed twice in succession:

1. Register a fresh user.
2. Create a manual task.
3. List tasks.
4. Ask the mock AI to create a task.
5. Ask the mock AI to delete a task and receive confirmation.
6. Confirm deletion.
7. Verify the task is gone.

Mock health reported `enabled: false`, `configured: false`, `mock_mode: true`.

### Live Gemini end-to-end

Live health reported:

```json
{
  "enabled": true,
  "configured": true,
  "model": "gemini-3.5-flash-lite",
  "mock_mode": false
}
```

Verified operations:

- Model visibility: `client.models.list()` returned 46 models including the
  configured model.
- Live create: created a high-priority task due the next day (about 21 seconds).
- Live search: listed the created task.
- Live complete: marked it complete (about 13 seconds on the final run).
- Live delete confirmation: returned a confirmation prompt, then deleted the
  task; a subsequent `GET /tasks/{id}` returned `404`.
- Final live create/delete after the nginx timeout and commit fixes passed.
- One earlier live completion hit a transient Gemini `504`; the single retry
  succeeded. No 504 occurred on the final live flow.

Live tests used a real key in the ignored local `.env`. Automated tests do not
call Gemini.

### Failure isolation and persistence

- Stopped `ai-service`; manual task creation and completion still worked.
- `GET /health` on the Core Task API stayed `healthy`.
- `/ai/chat` returned `502` while the AI service was down (expected).
- Restarted `ai-service`; it became healthy and live mode resumed.
- A task created before a full stack restart was still readable with its
  priority and status intact.

### Security checks

- `.env` is ignored by Git (`git check-ignore` confirms).
- No key-like pattern was found in tracked files or Git history.
- The AI image contains no provider environment values and no `.env` file.
- Database credentials are local-development defaults; they are not production
  secrets.
- The frontend receives no Gemini key and never calls Google directly.
- No GitHub remote is configured; no push was performed.

### Important key-rotation warning

During migration, a live Gemini key was accidentally present in
`compose.yaml` and `.env.example`. It has been removed from both files and moved
to the ignored `.env`. The repository has no remote and the key was never found
in tracked history, but the key did appear in local tool output and files.
**Rotate that key in Google AI Studio** and update the local `.env` before any
future demo or publication.

---

## 7. Remaining limitations

- Pending confirmations are stored in AI-service memory, expire after five
  minutes, and are lost on restart. This is appropriate for the single-process
  MVP but not horizontally scaled deployments.
- Activity history is recorded but not yet displayed in the frontend.
- Mock mode uses keyword heuristics; it demonstrates flow and safety, not real
  natural-language understanding.
- Live model availability, quota, and latency depend on the Google account and
  key. The verified model is not guaranteed for every key or region.
- Live ambiguity clarification was not separately exercised against Gemini;
  the same path is covered by automated tests and is model-independent.
- The local `.env` currently enables live Gemini. Set
  `GEMINI_ENABLED=false` (or remove the key) to return to the safe default.
- `AGENTS.md` retains the original Bedrock/AWS assignment text as historical
  context.

---

## 8. Git state

- Repository: local Git repository with an initial commit plus the migration
  changes and this report committed locally.
- Remote: none.
- Published: no.
- Provider key committed: no.
- `.env` remains untracked and ignored.
