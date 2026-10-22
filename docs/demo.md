# Demo — Tasked: AI Enabled Task Manager

## 1. Start

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:5173>. Register a new account (for example
`demo@example.com`).

Check services:

```bash
docker compose ps
curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready
curl -s http://localhost:8001/ai/health
```

The AI panel shows **Mock Mode** when `GEMINI_ENABLED=false` (the default).

## 2. Manual workflow (no AI)

1. Create “Submit DBMS assignment” with high priority and a due date.
2. Create “Read operating systems notes”.
3. Edit one task, filter by priority, search for a title.
4. Complete a task, reopen it, archive it, then restore it.
5. Delete a task and confirm it disappears from the list.

This is the part that must keep working if the AI service is stopped.

## 3. AI workflow (mock or live)

Open the AI Assistant panel.

1. “Create a high-priority DBMS assignment due Friday.”
2. “Show my tasks.”
3. “Mark my DBMS assignment complete.”
4. “Change the priority of my DBMS assignment to urgent.”
5. “Give me a summary of my tasks.”
6. “Delete my DBMS assignment.” → confirmation appears; click **Cancel**, then
   repeat and click **Confirm** to show the destructive-action guard.
7. “Complete the assignment.” when two tasks match → the assistant asks which
   one instead of guessing (create two similarly named tasks first).

After each AI action the frontend refreshes task data from the Core Task API;
chat text is never treated as the source of truth.

## 4. Persistence

```bash
docker compose restart
```

Reload the page and sign in again if needed. Tasks still exist in the
PostgreSQL volume.

## 5. AI failure isolation

```bash
docker compose stop ai-service
```

- The task list, create/edit/complete/archive/delete actions still work.
- The AI panel shows a controlled error instead of breaking the page.
- `GET /api/health` still returns healthy.
- `GET /ai/health` is unreachable while the service is stopped.

Restart it:

```bash
docker compose start ai-service
```

## 6. Live Gemini (optional)

Requires a Gemini API key and a model available to that key.

```dotenv
GEMINI_ENABLED=true
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

```bash
docker compose up -d --build ai-service
curl -s http://localhost:8001/ai/health
```

The panel should now show **Gemini** instead of **Mock Mode**. Perform one
create and one delete-confirmation flow to demonstrate live function calling.

If no key is available, say clearly that the demo is running in mock mode. Do
not present mock output as a live model response.

## 7. Stop

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the
local database volume.
