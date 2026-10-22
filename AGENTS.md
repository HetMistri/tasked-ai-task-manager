# AGENTS.md — Tasked: AI Enabled Task Manager

> **Purpose:** Give coding agents and contributors the shortest safe path to a working, demonstrable Tasked: AI Enabled Task Manager MVP.
> **Primary constraint:** Finish a coherent end-to-end application in a few hours. Prefer working software over architectural ceremony.
> **Product:** Natural-language task management using Amazon Bedrock and Anthropic Claude Haiku 4.5, with PostgreSQL persistence and Docker Compose.

## 0. Mandatory Execution Order for OpenCode / Nemotron 3 Ultra

**Follow this sequence. Do not begin by implementing isolated features or writing a long plan.**

1. **Inspect the workspace and Git state.** Identify whether this is an empty directory, an existing project, or an existing Git repository. Preserve useful existing work and never overwrite user changes blindly.
2. **Scaffold the complete project structure first.** Create the root files and directories for the frontend, the independently runnable Core Task API, the independently runnable AI service, database/migrations, tests, Docker, and documentation. Keep the service boundaries small and purposeful; do not create extra services beyond those required below.
3. **Create the Docker assets before feature implementation.** Add a Dockerfile and service-specific dependency/configuration setup for the frontend, Core Task API, and AI service; add `.dockerignore` files, `compose.yaml`/`docker-compose.yml`, environment example, PostgreSQL named volume, service networking, health/readiness checks, and startup documentation. Make each service runnable on its own (with dependencies clearly documented) and make the complete stack build/start as early as practical.
4. **Implement the application vertically.** Add database model/migrations, Core Task API CRUD, frontend manual workflows, and then the AI service and Bedrock tool calling. Keep the core manual task workflow runnable without the AI service at every stage.
5. **Verify locally.** Validate Compose configuration, build images, start containers, run migrations, run tests, and perform a CRUD smoke test. Test Bedrock live only if valid AWS credentials and model access are available; otherwise make mock mode explicit.
6. **Prepare for public publication.** Review every tracked file and Git diff. Confirm `.env`, credentials, access tokens, local databases, personal data, generated secrets, and private files are ignored and absent from the commit history being published. Run secret scanning if available. Ensure README and docs contain no private URLs or personal information.
7. **Publish the Git repository as public only after the safety review and build/test checks.** If the GitHub CLI is authenticated, create a public repository or update the intended remote as appropriate, then push the project. Never overwrite an unrelated remote or force-push without explicit approval. If repository creation or authentication is blocked, leave the local repository ready and report the exact command/action the user must complete; never claim publication succeeded when it did not.
8. **Normalize the product name in all documentation.** The canonical display name is exactly **“Tasked: AI Enabled Task Manager”**. Update README, AGENTS.md, architecture/design docs, API docs, UI copy, package metadata where appropriate, Docker Compose project labels/names, and demo instructions. Search for stale `TaskPilot AI` / `TaskPilot` references and replace them unless they occur in historical notes that must be preserved. Do not rename third-party dependencies or technical identifiers unnecessarily.

Use OpenCode with the Nemotron 3 Ultra model as the coding agent, but do not assume it has AWS/GitHub access until tools and credentials are verified. The model choice does not change the repository safety, testing, or publishing requirements.

# 1. Mission and Definition of Done

Build a task manager that supports ordinary CRUD and lets an authenticated user issue natural-language commands. The AI may select tools, but the backend is the authority for permissions, validation, and whether an operation succeeded.

The MVP is done when all of the following are true:

- [ ] A developer can start the app using the documented Docker Compose command.
- [ ] PostgreSQL persists tasks across application/container restarts.
- [ ] A user can create, list, view, update, complete/reopen, archive/restore, and delete tasks through the UI or API.
- [ ] The AI chat can create a task, search for tasks, update a task, change priority, and complete a task using Bedrock tool calling.
- [ ] Ambiguous task references trigger clarification rather than a guessed mutation.
- [ ] Destructive or broad bulk actions require explicit confirmation.
- [ ] Every task query and mutation is scoped to the authenticated user.
- [ ] Manual CRUD continues to work when Bedrock credentials, quota, or service are unavailable.
- [ ] Tests cover core CRUD, user isolation, AI tool execution/validation, and confirmation behavior.
- [ ] `.env.example`, README, and a short demo script are present; no secrets are committed.
- [ ] The full directory structure is scaffolded before feature work, with clear frontend/Core Task API/AI service/database/tests/docs boundaries.
- [ ] Separate Dockerfiles and Compose configuration exist for the frontend, Core Task API, and AI service; each is independently runnable, and the full application starts using the documented workflow.
- [ ] All user-facing and documentation references use the canonical name **Tasked: AI Enabled Task Manager**.
- [ ] The repository has passed a public-release secret/privacy review before any push to a public remote.
- [ ] The public Git repository has been created and pushed successfully, or the exact blocker is reported without claiming success.

**Do not claim a feature is complete unless it runs and has been checked.** Keep a short checklist of verified commands and test results.

## 2. How to Work in This Repository

1. Inspect the existing repository, `README.md`, `pyproject.toml`/lockfiles, package manifests, tests, and current Git status before editing.
2. Preserve existing working conventions and useful code. Do not replace the project structure wholesale without a clear need.
3. Treat Git as the source of truth. Do not create parallel implementations in notebooks, temporary directories, or duplicate app folders.
4. Implement the smallest end-to-end slice first: database model → API → UI → test → Docker.
5. Make focused changes, run relevant checks, and fix failures before adding features.
6. Never silently discard user changes. Do not run destructive Git commands, reset branches, or overwrite files without permission.
7. If blocked by unavailable AWS access, implement and test a deterministic mock/provider interface. Clearly label mock mode and never pretend a real Bedrock call occurred.
8. Do not ask for decisions that can be made safely from this document. Choose sensible defaults and document them.

## 3. Scope and Priorities

### P0 — Required MVP

1. Task CRUD backed by PostgreSQL through the Core Task API.
2. Minimal, usable task dashboard with manual task management.
3. A separately runnable AI service supporting natural-language chat with Claude Haiku 4.5 through Amazon Bedrock Converse API and tool calling.
4. Backend validation, ownership checks, clarification, and confirmation for risky actions.
5. Docker Compose startup, service health/readiness checks, and persistent database volume.
6. Tests, `.env.example`, and concise README.
7. Manual task workflows continue to work when the AI service or Bedrock is unavailable.
8. Frontend, Core Task API, and AI service can each be built, started, configured, and tested independently, with dependencies documented.

### P1 — Only after P0 works

- Activity history.
- Overdue/upcoming summaries.
- Archive page polish.
- Better empty/loading/error states.
- Basic reminder scheduling if the core app is stable.

### Explicitly defer unless already mostly implemented

- Kubernetes, Helm, service mesh, message broker, distributed tracing.
- Multiple agents or elaborate agent frameworks.
- Separate database servers per service.
- Complex refresh-token/session infrastructure beyond what the app needs.
- Email/push notifications, calendar sync, embeddings, RAG, vector databases.
- Advanced analytics, elaborate role systems, and premature abstractions.

**Architecture requirement:** The frontend, Core Task API, and AI service must be separate, independently runnable and operable application services. Keep each service small; do not add unnecessary microservices for activity, reminders, or authentication in the MVP. Authentication and task business rules may live inside the Core Task API. PostgreSQL is a separate infrastructure service. Independent operation does not mean a service can perform work without its required dependency; it means it can be started, configured, tested, diagnosed, and failed independently, and failures are surfaced without taking unrelated capabilities down.

## 3A. Service Independence and Failure Isolation (Mandatory)

The application has three independently runnable application services plus PostgreSQL infrastructure:

1. **Frontend service** — React + TypeScript; provides manual task management and the optional AI chat interface.
2. **Core Task API service** — FastAPI; owns authentication/authorization, task validation, task business rules, and all task reads/writes.
3. **AI service** — Python; handles natural-language interpretation, Bedrock Converse/tool-calling orchestration, and invokes the Core Task API through its documented API.
4. **PostgreSQL** — persistent data store used by the Core Task API. It is infrastructure, not a second source of truth.

### Non-negotiable boundaries

- Manual task CRUD must never call the AI service, Bedrock, or an AI health endpoint. If the AI service is stopped, users can still create, list, view, edit, complete/reopen, archive/restore, and delete tasks manually.
- The AI service must not connect directly to PostgreSQL, run SQL against it, or maintain a second task store. It uses the Core Task API, which remains the single authority for task data and business rules.
- The Core Task API must not require the AI service to start, become ready, or serve normal task endpoints.
- The frontend must clearly separate manual task workflows from AI chat. An AI error must not block task list loading or manual forms/actions.
- Service-to-service calls must use explicit, documented API contracts, bounded timeouts, safe error handling, and only the minimum required permissions/data.
- Do not share in-process objects or import application internals across service boundaries. Share only stable API contracts/schemas when necessary; avoid creating a shared package unless it materially reduces duplication.
- Each application service must have its own entrypoint, dependency manifest, configuration, Dockerfile, logs, health endpoint, tests, and documented standalone run command.
- A service may have required dependencies. For example, task writes require PostgreSQL, and AI task actions require the Core Task API. Independence means a component can be built, launched, tested, diagnosed, and failed separately; it does not mean dependent operations should falsely succeed when a dependency is unavailable.
- Implement separate **liveness** and **readiness** checks where practical. Liveness should report whether the process is running. Readiness may report a required dependency such as PostgreSQL for the Core Task API. Bedrock being unavailable must not make the Core Task API unready.
- Use bounded connection/request timeouts. Do not add infinite retries, cascading retries, or automatic fallback that silently fabricates task results.
- Keep AI provider failure isolated: return a clear, recoverable AI error while preserving manual CRUD. Show whether AI is live or in mock mode.
- Test the failure boundary explicitly by stopping/disabling the AI service and proving manual CRUD still works.

### Required standalone workflows

Document and verify the equivalent commands using the final Compose service names:

```bash
# Start only the database infrastructure
docker compose up --build postgres

# Start the Core Task API (with its required database)
docker compose up --build postgres task-service

# Start the AI service (and the Core Task API/database it needs for task actions)
docker compose up --build postgres task-service ai-service

# Start the full application
docker compose up --build
```

Also document how to run each application service directly for local development (for example, its own virtual environment/package install and entrypoint). Compose service dependencies must not be configured so that an AI-service failure prevents the frontend or Core Task API from starting. Use actual service names from the final Compose file; adjust these examples if names differ.

### Architecture decision

Do not split authentication, activity history, reminders, or other small modules into extra deployable services for the MVP. Keep authentication and task rules within the Core Task API unless there is a concrete requirement to separate them. This is a deliberate small-service architecture, not a license to collapse the AI service into the Core Task API.

## 4. Required Stack and Configuration

Preferred stack, unless the repository already has an equivalent working choice:

- Frontend: React + TypeScript.
- Backend: Python + FastAPI.
- Validation: Pydantic.
- Database: PostgreSQL.
- ORM/migrations: SQLAlchemy + Alembic (or the repository's existing migration system).
- AI: Amazon Bedrock Converse API via `boto3`, using Anthropic Claude Haiku 4.5.
- Tests: Pytest and existing frontend test tooling.
- Runtime: Docker and Docker Compose.
- Version control: Git/GitHub.

Use configuration rather than hardcoding model IDs, credentials, URLs, or secrets.

Suggested `.env.example` (adjust names to match the implementation):

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://tasked:tasked@postgres:5432/tasked
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=
BEDROCK_ENABLED=false
JWT_SECRET=replace-for-local-development
FRONTEND_ORIGIN=http://localhost:5173
```

- `BEDROCK_MODEL_ID` must be the exact model or inference-profile ID verified in the user's AWS account and selected region. Do not guess it or assume access.
- Use `BEDROCK_ENABLED=false` for local mock mode. In mock mode, clearly indicate that AI responses are simulated.
- Use an AWS profile/standard AWS credential chain locally, and a least-privilege IAM role in AWS. Never put AWS keys in the frontend.
- `.env` must be ignored by Git. Commit only `.env.example` with placeholders.
- Do not print credentials, JWTs, or full sensitive request payloads in logs.

## 5. Data Model and Business Rules

### Task

Use a UUID or the repository's existing stable primary key. Minimum fields:

- `id`
- `user_id`
- `title` (required, trimmed, non-empty, length-limited)
- `description` (optional)
- `status`: `pending`, `in_progress`, `completed`
- `priority`: `low`, `medium`, `high`, `urgent`
- `due_at` (optional, timezone-aware)
- `is_archived` (boolean)
- `archived_at` (optional)
- `created_at`, `updated_at`
- `completed_at` (optional)
- `deleted_at` (optional if using soft deletion)

Rules:

- Status, priority, archive state, and deletion state are separate concepts.
- Archiving must not silently change completion status.
- Completing a task sets `completed_at`; reopening clears it.
- All timestamps must be timezone-aware and serialized consistently (prefer UTC in storage).
- Resolve relative dates using an explicit configured/user timezone. If the intended date is unclear, ask.
- Exclude soft-deleted tasks from normal lists and searches.
- Enforce task ownership in the backend on every read and write. Never trust a `user_id` supplied by the model or client.
- Use database constraints/indexes where useful, but avoid speculative schema complexity.

### Authentication

If full authentication is too expensive for the deadline, do not fake secure multi-user authentication. Use the repository's existing auth implementation or implement a minimal, real login/register flow. A clearly labelled single-user local demo mode is acceptable only if the project is explicitly configured as such and never presented as production-secure.

## 6. API and UI Expectations

The Core Task API owns the task endpoints. The AI service exposes its own AI/chat endpoint and calls the Core Task API through the internal service API. Prefer REST endpoints consistent with the current repository. At minimum provide:

- `POST /tasks`
- `GET /tasks` with practical filters
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `POST /tasks/{task_id}/complete`
- `POST /tasks/{task_id}/reopen`
- `POST /tasks/{task_id}/archive`
- `POST /tasks/{task_id}/restore`
- `DELETE /tasks/{task_id}`
- `POST /ai/chat`
- `GET /health` (and a readiness check if straightforward)

Keep API response shapes consistent and use appropriate HTTP status codes. Add pagination if the list can grow; do not load every task into the AI prompt.

The UI should prioritize a complete, understandable demo over visual complexity:

- Task list with title, status, priority, and due date.
- Create/edit task form.
- Search and basic status/priority filters.
- Clear complete, archive, restore, and delete actions.
- AI chat panel with loading, error, clarification, and confirmation states.
- Refresh task data from the backend after mutations; do not treat chat text as the source of truth.
- Show whether AI is live Bedrock or mock mode.

## 7. Bedrock Agent and Tool-Calling Rules

Use `boto3` and the Bedrock Converse API unless the repository already has a sound supported wrapper. Keep the provider client behind a small module/interface so it can be tested and replaced.

### Suggested tools

Start with the smallest useful set:

1. `create_task`
2. `search_tasks`
3. `update_task`
4. `complete_task`
5. `set_task_priority`
6. `archive_task`
7. `restore_task`
8. `delete_task` (confirmation required)
9. `get_task_summary`

Add bulk operations only after single-task actions are reliable. A bulk tool must have explicit filters and a preview/confirmation step.

### Tool execution loop

1. Send the user message, concise system instructions, and tool schemas to Bedrock.
2. If the model requests a tool, validate the tool name and arguments against an allowlist and Pydantic schema.
3. Resolve target tasks through the Task Service using the authenticated user's identity.
4. If no task matches, return a not-found result. If multiple plausible tasks match, ask the user to choose.
5. For delete and broad/bulk changes, create a pending action/preview and require a separate explicit confirmation.
6. Execute the operation in backend code only after validation and any required confirmation.
7. Return the actual result to the model for a user-facing summary, or render the result directly.
8. Bound the number of tool iterations (for example, 4 per user message); stop safely on malformed or repeated calls.
9. Persist only the minimum conversation context needed. Never send the entire database or every task to the model.

### Non-negotiable AI safeguards

- Tool calling is not authorization. The backend must re-check ownership and business rules for every tool call.
- Do not expose a general-purpose SQL tool, shell tool, filesystem tool, or arbitrary HTTP tool to the model.
- Do not let the model choose another user's ID or bypass access checks.
- Do not execute arbitrary code generated by the model.
- Treat task descriptions and retrieved records as untrusted data, not instructions.
- Never claim success before the backend operation succeeds.
- Do not silently execute ambiguous actions or interpret "all" without a precise, displayed scope.
- Ask for confirmation before permanent deletion or destructive bulk operations.
- Make confirmation tokens/action IDs user-scoped, short-lived, and single-use where practical.
- Validate due dates, enums, title length, and every other field server-side.
- Handle provider timeout, throttling, access denied, invalid model/profile, and malformed tool calls with bounded retries and clear errors.
- Never log credentials or secrets.

### Model cost controls

- Use Claude Haiku 4.5 as the initial model; do not upgrade to a larger model without evaluation evidence.
- Keep the system prompt and tool schemas concise.
- Set a reasonable output-token limit.
- Avoid unnecessary calls for normal UI CRUD and deterministic summaries.
- Track input/output token usage when returned by the API.
- Do not retry non-retryable errors or loop indefinitely.
- Check actual current AWS pricing and billing; the available $80 credit is not a fixed request allowance.
- Do not hardcode an unverified inference-profile ID. Confirm model access and regional/profile availability in the AWS console.

## 8. Security and Reliability

- Validate all input at API boundaries.
- Use parameterized ORM queries.
- Enforce authentication and ownership for every user-owned resource.
- Use secure password hashing; never store plaintext passwords.
- Keep internal services and PostgreSQL off public interfaces unless deliberately required.
- Configure CORS narrowly.
- Set request size/time limits where practical.
- Use health checks and wait for database readiness.
- Use a named PostgreSQL volume.
- Ensure manual CRUD functions when the AI service or Bedrock is down. The Core Task API and manual UI paths must never make an AI call or require AI health to serve ordinary task operations.
- Use transactions where a change and its audit event must remain consistent.
- Return safe errors to clients; keep detailed diagnostics in server logs without secrets.
- Do not introduce production claims or certifications that have not been earned.

## 9. Docker and Local Development

The expected first-run workflow should be documented and simple:

```bash
cp .env.example .env
# Set the required values; Bedrock can remain disabled for mock mode.
docker compose up --build
```

Use the repository's actual service names and ports in the README.

Requirements:

- A clean clone can build using documented commands.
- Application containers do not depend on manually installed host packages.
- PostgreSQL data persists in a named volume.
- Health checks are used where straightforward.
- Database migrations run predictably (a documented command or safe startup step).
- The frontend reaches the Core Task API using the correct container/public URLs for its runtime; browser-facing URLs must not use Docker-only hostnames.
- Secrets are injected at runtime, never baked into Docker images.
- The README explains how to stop the app and how to reset local demo data intentionally.

Do not run `docker compose down -v` unless the user explicitly intends to delete the local database volume.

## 10. Testing Requirements

At minimum, add/run tests for:

### Task/API

- Create/list/update/delete task.
- Complete and reopen state timestamps.
- Archive/restore behavior independent of status.
- Invalid status/priority/date/title rejection.
- User A cannot read or mutate User B's task.
- Soft-deleted tasks do not appear in normal results.

### AI

- Tool schemas reject invalid arguments.
- Correct tool results are returned to the model.
- No-match and ambiguous-match behavior.
- Delete/bulk operations require confirmation.
- Model/provider failure returns a useful error and does not break manual CRUD.
- Tool loop stops at its configured maximum.
- Mock mode is clearly identified and does not pretend to call Bedrock.

### Docker/smoke test

- Compose configuration validates.
- Services become healthy.
- API health endpoint responds.
- A task can be created and retrieved.
- Task data survives an application restart.
- With the AI service stopped or disabled, manual task create/list/update/complete flows still pass.
- The AI service reports a useful dependency/provider error when its required service or Bedrock is unavailable, without affecting Core Task API health.

Run existing tests first if feasible. Then run targeted tests after each feature and the full suite before declaring completion. If a check cannot be run, say so explicitly.

## 11. Few-Hour Execution Plan

Work in this order. Do not start optional features until the end-to-end core works.

### Pass 1 — Inspect and scaffold (15–25 minutes)

- Inspect repository and current Git state.
- Create the full folder/file skeleton for frontend, Core Task API, AI service, database/migrations, tests, Docker, and docs before implementing features.
- Add separate Dockerfiles and dependency manifests for frontend, Core Task API, and AI service; add `.dockerignore`, Compose, `.env.example`, PostgreSQL persistence, networking, and health/readiness checks early.
- Verify each service can be built and started independently with its documented dependencies, then verify the complete stack.
- Record the actual startup and test commands. Avoid unnecessary dependency or architecture changes.

### Pass 2 — Working CRUD (45–60 minutes)

- Implement/repair Task model and migrations.
- Implement CRUD and validation in the Core Task API.
- Connect the UI's manual workflows directly to the Core Task API, with no AI dependency.
- Verify persistence and ownership checks while the AI service is stopped.

### Pass 3 — AI integration (45–60 minutes)

- Implement the AI service as a separate runnable application with its own Dockerfile, dependencies, configuration, health checks, and tests.
- Add Bedrock client configuration and health/error handling.
- Have the AI service call the Core Task API over a documented internal API; it must not connect directly to PostgreSQL or duplicate task business rules.
- Implement one reliable tool-calling loop.
- Support create, search, update, complete, and priority change first.
- Add clarification and delete confirmation.
- Test live Bedrock if credentials are available; otherwise test with an explicit mock provider.

### Pass 4 — Docker and tests (30–45 minutes)

- Make the clean startup path work.
- Add persistent volume and health checks.
- Run unit tests and an end-to-end smoke test.
- Fix blocking failures before styling or extras.

### Pass 5 — Demo readiness (20–30 minutes)

- Write `.env.example` and README.
- Verify clean startup and one restart/persistence check.
- Prepare the demo sequence below.
- Record known limitations honestly.

**If time is shorter than expected:** finish CRUD + PostgreSQL + Docker + a working AI tool call before adding auth polish, activity history, reminders, or Kubernetes. Do not sacrifice ownership checks or destructive-action safeguards to save time.

## 12. Suggested Demo Sequence

1. Start the project using the documented Compose command.
2. Create a task manually.
3. Ask the AI: "Create a high-priority DBMS assignment due Friday."
4. Ask: "Show my overdue and upcoming tasks."
5. Ask: "Mark my DBMS assignment as complete."
6. Demonstrate a priority change.
7. Ask to delete a task and show the confirmation step.
8. Demonstrate that ambiguous task names trigger clarification.
9. Restart the application and show that tasks persist.
10. If AWS access is unavailable, clearly disclose mock mode rather than presenting it as a live Bedrock response.

## 13. Product Naming and Public Repository Release

Canonical product name: **Tasked: AI Enabled Task Manager**.

- Use this exact name in the README title, project overview, UI header/title, documentation, architecture diagrams, demo script, and presentation text.
- Use a filesystem-/package-friendly slug such as `tasked-ai-task-manager` where punctuation and spaces are unsuitable; do not use the slug as a replacement for the canonical display name in prose.
- Search the whole repository for `TaskPilot AI`, `TaskPilot`, and stale project names before declaring the rename complete.
- Update package metadata and Compose project naming only where it is safe and supported by the existing stack.
- Do not change dependency names, import paths, or third-party references merely because they contain similar text.
- Before publishing publicly, inspect `git status`, `git diff`, tracked files, `.gitignore`, `.dockerignore`, and recent commits for secrets or private data. Never publish `.env`, AWS credentials, tokens, SSH keys, local database files, private datasets, or personal information.
- Do not rewrite Git history or force-push as a shortcut to remove a secret. If a secret has ever been committed, stop publication, tell the user, and provide a safe remediation path.
- Publish only the intended repository. Verify the remote URL and repository visibility before pushing.
- After push, verify the remote branch and public repository URL. Report the URL only if it was actually returned or verified by GitHub tooling/CLI.

## 13. Git and Documentation

- Use small, descriptive commits.
- Never commit `.env`, AWS credentials, tokens, local databases, or generated secrets.
- Keep `.gitignore` updated.
- Update README when startup commands, environment variables, endpoints, or features change.
- Document which AI mode is active and how to enable live Bedrock.
- Include architecture and data-flow diagrams only after the implementation matches them.
- Report exact test commands and results; do not claim unrun tests passed.

## 14. Agent Response Protocol

At the beginning of work, briefly report:

- What exists in the workspace and Git state.
- The scaffold you will create or preserve.
- The shortest implementation sequence.

Then immediately scaffold the folders and Docker assets, validate the skeleton, and implement rather than merely proposing plans. After each meaningful slice:

- Run relevant checks.
- Fix regressions.
- Summarize changed files and verification results.

At completion, report:

- Features implemented.
- Exact startup commands.
- Required environment variables.
- Tests actually run and their results, including independent service startup and the AI-down/manual-CRUD isolation check.
- Whether Bedrock was tested live or mock mode was used.
- Remaining limitations.

## 15. Final Principle

**Optimize for a secure, working, reproducible demo—not maximum architectural complexity.** Keep the backend authoritative, the AI constrained to explicit tools, the model cost controlled, and the project runnable from a clean checkout.