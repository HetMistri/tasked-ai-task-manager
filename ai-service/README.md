# Tasked: AI Enabled Task Manager — AI Service

Separate FastAPI service that turns natural-language requests into Core Task API
calls using the **Google Gemini API** (`google-genai` SDK) with function calling.

It has no database driver and no database credentials. It calls the Core Task
API over HTTP using the caller's JWT, so ownership and business rules remain in
one place.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/ai/chat` | Send a message; returns text or a confirmation request |
| POST | `/ai/actions/{id}/confirm` | Confirm/cancel a pending destructive action |
| GET | `/ai/health` | Liveness + dependency status |

Requires `Authorization: Bearer <jwt>` for chat and confirm.

## Environment

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_ENABLED` | `false` | `true` to call the Gemini API |
| `GEMINI_API_KEY` | empty | Server-side key; never exposed to the browser |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Any Gemini model available to your key that supports function calling |
| `GEMINI_TIMEOUT_SECONDS` | `30` | Bounded request timeout |
| `TASK_API_URL` | `http://task-service:8000` | Core Task API base URL |
| `TASK_API_TIMEOUT` | `10.0` | Bounded timeout for Core Task API calls |
| `APP_ENV` | `development` | |
| `LOG_LEVEL` | `INFO` | |

The default model is **Gemini 3.5 Flash-Lite**: a stable, cost-effective model
with function-calling support. Confirm availability for your API key with
`client.models.list()` or the Gemini API docs, then override `GEMINI_MODEL` if
needed.

## Mock mode (default)

With `GEMINI_ENABLED=false` the service uses a deterministic in-process mock
provider. It exercises the same validation, ambiguity and confirmation code as
live mode. Responses are labelled `[MOCK MODE]` and the UI shows a **Mock Mode**
badge.

Mock mode is a simulation. It is never presented as a live Gemini response.

Enabling Gemini without a key is **not** silently converted to mock mode:
`/ai/chat` returns a configuration error instead, and `/ai/health` reports
`configured: false`.

## Live mode

Create a `.env` file in the repository root (already ignored by Git):

```dotenv
GEMINI_ENABLED=true
GEMINI_API_KEY=your-key-from-google-ai-studio
GEMINI_MODEL=gemini-3.5-flash-lite
```

Then rebuild/start the AI service:

```bash
docker compose up -d --build ai-service
```

The key is injected as a runtime environment variable. It is not copied into
the image, written to logs, or returned by any endpoint.

Get a key from <https://aistudio.google.com/apikey>. Do not commit it.

## Run standalone

```bash
cd ai-service
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

export TASK_API_URL=http://localhost:8000
export GEMINI_ENABLED=false   # or true with GEMINI_API_KEY set
uvicorn app.main:app --reload --port 8001
```

The Core Task API must be reachable for task actions. If it is not, `/ai/chat`
returns a controlled error; manual task management is unaffected.

## Verification status\n\n- Automated tests mock Gemini and the Core Task API; no key or network needed.\n- Live function calling was verified manually on 2026-10-22 with\n  `gemini-3.5-flash-lite`: task creation, search, completion and the\n  delete-confirmation flow all succeeded through the Core Task API.\n- One transient Gemini `504` was retried successfully. The service retries once\n  with a bounded timeout, and the frontend proxy allows 120 seconds.\n- Model availability is account-specific. The configured model was present in\n  `client.models.list()` for the verification key, but this is not a guarantee\n  for every key or region.\n\n## Safety rules implemented here

- Gemini may only call the ten declarations in `app/services/tools.py`; the
  backend rejects unknown names.
- Arguments are validated with Pydantic before any Core Task API call.
- The model never receives SQL, shell, filesystem or arbitrary HTTP tools.
- Task titles/descriptions are treated as untrusted data, not instructions.
- Ambiguous task matches return a clarification list instead of guessing.
- Delete requires an explicit confirmation, scoped to the requesting user and
  expiring after 5 minutes.
- The function-calling loop is capped at 4 iterations per message.
- Provider errors are mapped to short, safe messages. API keys and raw provider
  payloads are never returned or logged.
- Nothing is reported as successful until the Core Task API confirms it.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Gemini rejected the request` | Invalid/restricted API key, or the key cannot use the model |
| `configured Gemini model was not found` | `GEMINI_MODEL` is wrong or unavailable for the key |
| `Gemini rate limit reached` | Free-tier or per-minute quota; retry later |
| `Gemini is temporarily unavailable` | Provider 5xx; retry later |
| `AI provider is unavailable` | AI service cannot reach the provider; manual CRUD still works |

## Tests

```bash
cd ai-service
uv pip install -e ".[dev]"
pytest -q
```

Tests mock Gemini and the Core Task API client; no Google API key is required.
They cover argument validation, unknown tools, ambiguity, delete confirmation,
confirmation ownership/cancellation, provider failures, the iteration cap,
function-response round trips and safe provider error mapping.
