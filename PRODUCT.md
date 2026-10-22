# Tasked: AI Enabled Task Manager

**Product Requirements and Technical Design Document**

**Project Type:** College Micro-Project  
**Target Demonstration:** Mid-November 2026  
**Architecture:** Independently runnable services (React frontend, Core Task API, AI service, PostgreSQL)  
**AI Provider:** Google Gemini API  
**Selected AI Model:** Gemini 3.5 Flash-Lite  
**Deployment:** Docker and Docker Compose  
**Primary Goal:** Build an intelligent task manager that converts natural-language instructions into secure, validated task operations.

> **Implementation note:** The MVP keeps authentication, task rules and activity history inside the Core Task API instead of splitting them into extra services. See the repository README for the deployed architecture.

---

## 1. Project Overview

### 1.1 Project Name

**Tasked: AI Enabled Task Manager**

### 1.2 Problem Statement

Traditional task management applications require users to navigate forms, menus, filters, and multiple screens to manage everyday tasks. Performing bulk operations or updating several tasks can be tedious.

Tasked: AI Enabled Task Manager addresses this problem by allowing users to manage tasks through natural-language instructions.

For example, users can write:

- "Create a task to complete my DBMS assignment by Friday."
- "Mark my operating systems revision as complete."
- "Make my mini-project submission urgent."
- "Move my networking assignment to next Monday."
- "Archive the tasks I completed last month."
- "Show me everything that is overdue."
- "Find the duplicate SQL revision task and ask me before deleting it."

An AI agent interprets the user's intent and selects appropriate backend tools. Dedicated backend services validate and execute the requested operations.

### 1.3 Project Objectives

1. Build a complete task management application with CRUD operations.
2. Integrate an AI agent using the Google Gemini API and Gemini 3.5 Flash-Lite.
3. Support natural-language task creation, searching, updates, and bulk actions.
4. Implement authentication, authorization, validation, and safe destructive operations.
5. Design the application using independently organized services.
6. Containerize the application using Docker and Docker Compose.
7. Use Git and GitHub for version control and collaborative development.
8. Demonstrate reliability through automated testing, documentation, and a live demonstration.

---

## 2. Core Features

### 2.1 Task Management

Users can create, view, edit, complete, reopen, archive, restore, and delete tasks.

Each task includes a title, optional description, status, priority, optional deadline, and timestamps.

### 2.2 Natural-Language Task Creation

Example:

> Create a high-priority task to finish my DBMS assignment by Friday evening.

The AI extracts the task title, priority, and deadline. The backend validates the extracted information before saving the task.

If the deadline is ambiguous or essential information is missing, the agent asks a clarification question rather than guessing.

### 2.3 Task Updates

Users can update task details conversationally.

Examples:

- "Rename my DBMS task to Database Project Submission."
- "Move my networking assignment to next Monday."
- "Change my mini-project priority to urgent."
- "Mark the completed task as pending again."

### 2.4 Task Status and Priority

Task status:

- `pending`
- `in_progress`
- `completed`

Task priority:

- `low`
- `medium`
- `high`
- `urgent`

Status and priority are independent fields.

### 2.5 Archive, Restore, and Delete

Users can archive tasks without changing their completion status, restore archived tasks, and delete tasks.

Permanent deletion and broad destructive operations require explicit confirmation. Where appropriate, the system can use soft deletion to support recovery and auditing.

### 2.6 Search and Summaries

The application supports:

- Searching by task title and description.
- Filtering by status, priority, and deadline.
- Viewing overdue and upcoming tasks.
- Summarizing completed, pending, and archived tasks.
- Identifying possible duplicate tasks.

Database queries should handle deterministic filtering and sorting rather than asking the language model to calculate everything.

### 2.7 Activity History

The application records important task changes, including the action, timestamp, source of the action, and outcome.

For example, the activity history can distinguish a manual update from an AI-initiated update.

### 2.8 Reminders

The optional reminder feature allows users to schedule notifications for upcoming deadlines.

Reminder delivery, retry behavior, and delivery status are handled by the Reminder Service rather than the AI model.

---

## 3. AI Integration: Google Gemini API

### 3.1 Model Selection

Tasked: AI Enabled Task Manager uses **Gemini 3.5 Flash-Lite** through the Google Gemini API.

The model is selected because the project primarily requires natural-language interpretation, structured function selection, task identification, and concise responses. Gemini 3.5 Flash-Lite is a stable, low-cost model with function-calling support, which fits a student project that needs to stay affordable.

The model must be evaluated against realistic project commands before the final demonstration. `GEMINI_MODEL` is configurable so a different supported model can be selected without changing the agent code.

### 3.2 Integration Approach

Use Google's official `google-genai` Python SDK and the Gemini API function-calling feature.

The model receives the conversation and available function declarations. It can request a function call, but the backend remains responsible for validating arguments and executing the operation through the Core Task API.

The API key is used only by the AI service on the server. It must never be exposed to the frontend, committed to Git, or baked into a Docker image.

### 3.3 Configurable Model Configuration

Configure the provider and model through environment variables rather than hardcoding the model identifier throughout the codebase.

Example configuration:

```dotenv
GEMINI_ENABLED=true
GEMINI_API_KEY=<your-server-side-api-key>
GEMINI_MODEL=gemini-3.5-flash-lite
```

`GEMINI_ENABLED=false` runs the clearly labelled mock provider and needs no key.

This configuration allows the team to change the model without rewriting the Core Task API or AI service.

### 3.4 AI Agent Responsibilities

The AI Agent Service is responsible for:

1. Interpreting natural-language instructions.
2. Identifying the requested operation.
3. Extracting task fields and relevant constraints.
4. Selecting an appropriate backend tool.
5. Requesting clarification when task matching is ambiguous.
6. Requesting confirmation for sensitive or destructive actions.
7. Interpreting actual tool results.
8. Producing a concise, truthful response to the user.

The AI agent must never claim that an operation succeeded unless the backend confirms the result.

### 3.5 Backend Tools

The initial tool set includes:

| Tool | Responsibility |
|---|---|
| `create_task` | Create a validated task |
| `search_tasks` | Find tasks belonging to the authenticated user |
| `update_task` | Update permitted task fields |
| `complete_task` | Mark a task completed |
| `reopen_task` | Reopen a completed task |
| `set_task_priority` | Change task priority |
| `archive_task` | Archive one task |
| `restore_task` | Restore an archived task |
| `delete_task` | Delete a task after explicit confirmation |
| `get_task_summary` | Retrieve task statistics and summaries |

These tools are backend functions, not separate AI agents. Bulk operations are intentionally left out of the MVP until single-task actions are reliable.

### 3.6 Example AI Workflow

User request:

> Mark my DBMS assignment as complete and make my mini-project urgent.

Workflow:

1. The frontend sends the message to the API Gateway.
2. The gateway validates the user's authentication.
3. The AI Agent Service sends the request and function declarations to Gemini.
4. Gemini identifies the two requested operations.
5. The agent requests the necessary task lookups and tool calls.
6. The Task Service verifies task ownership, resolves the targets, and validates the changes.
7. The backend records the successful operations in the activity history.
8. The frontend refreshes the task list using backend data.
9. The agent reports the confirmed results.

If several tasks match "my DBMS assignment," the agent asks the user to identify the correct one before changing it.

### 3.7 AI Safety and Correctness

- AI-generated parameters must be validated using Pydantic and backend business rules.
- The authenticated user ID must come from trusted server-side authentication context.
- Every task lookup and mutation must enforce ownership.
- Destructive operations require confirmation when applicable.
- Bulk operations must have clearly defined scopes and result counts.
- Model output must not be treated as proof of a database mutation.
- Manual CRUD must continue to work if Gemini is unavailable.
- The model must not receive database credentials or direct database write access.

---

## 4. Cost-Conscious AI Strategy

The project should keep model usage small and observable. Gemini API pricing and free-tier limits depend on the selected model and account, so no fixed request count is promised.

### 4.1 Cost-Control Measures

1. Use Gemini 3.5 Flash-Lite rather than a more expensive reasoning model.
2. Keep system prompts concise and function declarations focused.
3. Limit output tokens to an appropriate maximum.
4. Avoid sending the entire task history on every request.
5. Use PostgreSQL for filtering, sorting, and deterministic calculations.
6. Avoid unnecessary model calls for ordinary CRUD operations.
7. Track token usage and request counts during development.
8. Handle throttling and transient failures with bounded retries.
9. Monitor usage in Google AI Studio / Google Cloud billing where available.

### 4.2 Model Evaluation

Create a test set of 30–50 representative commands covering task creation, task updates, ambiguous matches, dates, bulk actions, and destructive operations.

Measure:

- Correct tool selection.
- Correct extraction of task fields.
- Correct handling of ambiguous tasks.
- Correct confirmation behavior.
- End-to-end operation success.
- Average latency and token usage.

The model should be retained if it meets the application's accuracy and reliability requirements.

### 4.3 Cost Boundary

The available development budget is not a guaranteed number of requests. Actual cost depends on input and output token usage, the selected model, and current Google pricing.

Check the [Gemini API pricing page](https://ai.google.dev/gemini-api/docs/pricing) and the associated Google billing console before substantial testing.

---

## 5. Microservice Architecture

### 5.1 Architecture Overview

The application will use the following logical services:

1. Client Service
2. API Gateway
3. Authentication Service
4. AI Agent Service
5. Task Service
6. Activity Service
7. Reminder Service
8. PostgreSQL infrastructure

The Reminder Service is optional for the initial minimum viable product (MVP).

### 5.2 Client Service

**Technology:** React and TypeScript

Responsibilities:

- Login and registration screens.
- Task dashboard and task forms.
- AI chat interface.
- Task filters and search.
- Archive view and activity history.
- Reminder interface, if implemented.

The frontend communicates through the API Gateway rather than calling internal services directly.

### 5.3 API Gateway

Responsibilities:

- Route requests to appropriate services.
- Validate authentication tokens or coordinate authentication checks.
- Apply rate limits and request-size limits.
- Return consistent error responses.
- Prevent direct public access to internal services.

The gateway can be implemented using a lightweight FastAPI service or an appropriately configured reverse proxy.

### 5.4 Authentication Service

Responsibilities:

- User registration and login.
- Secure password hashing.
- JWT issuance and validation.
- User identity and account management.
- Authentication-related validation.

### 5.5 AI Agent Service

**Technology:** Python, FastAPI, `google-genai`, Google Gemini API

Responsibilities:

- Process natural-language requests.
- Invoke the configured Gemini model.
- Expose and execute approved function declarations.
- Manage clarification and confirmation flows.
- Produce responses based on actual backend results.
- Track model usage and handle provider failures.

The AI Agent Service does not own canonical task records.

### 5.6 Task Service

Responsibilities:

- Create, read, update, and delete tasks.
- Search and filter tasks.
- Manage status, priority, deadlines, and archive state.
- Validate task ownership and permitted changes.
- Return authoritative results to the frontend and AI agent.

The Task Service is the source of truth for task data.

### 5.7 Activity Service

Responsibilities:

- Record task-related activity.
- Track whether an operation originated from the UI or AI agent.
- Record outcomes and relevant before-and-after state.
- Provide activity history to authorized users.

### 5.8 Reminder Service

Optional responsibilities:

- Schedule reminders.
- Track pending, delivered, and failed reminders.
- Process due reminders.
- Handle retry and notification delivery state.

A simple scheduler is sufficient for the first version. A message broker is not required unless the implementation demonstrates a need for one.

### 5.9 PostgreSQL Infrastructure

PostgreSQL stores persistent application data.

For the college project, a single PostgreSQL container is sufficient. Services should have clear ownership of their tables or schemas and should not directly modify another service's data.

Separate logical databases or schemas and restricted credentials can be used where practical. A separate database server per microservice is unnecessary for the MVP.

### 5.10 Service Communication

Use synchronous HTTP APIs for the initial implementation. This keeps the architecture understandable and easy to demonstrate.

Do not introduce Kubernetes, a service mesh, or a message broker solely to make the architecture look more complex.

---

## 6. Database Design

### 6.1 Users

| Field | Description |
|---|---|
| `id` | Primary key |
| `email` | Unique email address |
| `password_hash` | Secure password hash |
| `display_name` | User's display name |
| `timezone` | User's timezone |
| `created_at` | Account creation time |
| `updated_at` | Last account update |

### 6.2 Tasks

| Field | Description |
|---|---|
| `id` | Primary key |
| `user_id` | Owner of the task |
| `title` | Task title |
| `description` | Optional task description |
| `status` | Pending, in progress, or completed |
| `priority` | Low, medium, high, or urgent |
| `due_at` | Optional deadline |
| `is_archived` | Archive state |
| `archived_at` | Optional archive timestamp |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |
| `completed_at` | Optional completion timestamp |
| `deleted_at` | Optional soft-deletion timestamp |

Recommended indexes include `user_id`, `status`, `priority`, `due_at`, and combinations used frequently by the dashboard.

### 6.3 Activity Events

| Field | Description |
|---|---|
| `id` | Primary key |
| `user_id` | User associated with the event |
| `task_id` | Associated task, nullable when appropriate |
| `action_type` | Operation performed |
| `source` | Manual UI or AI |
| `before_state` | Previous state, where applicable |
| `after_state` | New state, where applicable |
| `outcome` | Success, failure, or cancellation |
| `created_at` | Event timestamp |

### 6.4 Reminders

| Field | Description |
|---|---|
| `id` | Primary key |
| `user_id` | Reminder owner |
| `task_id` | Associated task |
| `scheduled_at` | Reminder time |
| `status` | Pending, delivered, cancelled, or failed |
| `delivered_at` | Optional delivery timestamp |
| `created_at` | Creation timestamp |

Use SQLAlchemy for ORM access and migrations for controlled schema changes.

---

## 7. API Design

### 7.1 Authentication APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register an account |
| POST | `/auth/login` | Authenticate a user |
| POST | `/auth/logout` | Log out or invalidate a session where supported |
| GET | `/auth/me` | Retrieve the current user |

### 7.2 Task APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/tasks` | Create a task |
| GET | `/tasks` | List and filter tasks |
| GET | `/tasks/{task_id}` | Retrieve a task |
| PATCH | `/tasks/{task_id}` | Update task fields |
| POST | `/tasks/{task_id}/complete` | Complete a task |
| POST | `/tasks/{task_id}/reopen` | Reopen a task |
| POST | `/tasks/{task_id}/archive` | Archive a task |
| POST | `/tasks/{task_id}/restore` | Restore a task |
| DELETE | `/tasks/{task_id}` | Delete a task |

### 7.3 AI APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ai/chat` | Submit a natural-language instruction |
| POST | `/ai/actions/{action_id}/confirm` | Confirm a pending action |
| POST | `/ai/actions/{action_id}/cancel` | Cancel a pending action |

Confirmation records should be scoped to the authenticated user and expire after a defined period.

### 7.4 Activity APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/activity` | Retrieve activity history |
| GET | `/activity/tasks/{task_id}` | Retrieve history for a task |

### 7.5 Reminder APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/reminders` | List reminders |
| POST | `/reminders` | Create a reminder |
| PATCH | `/reminders/{reminder_id}` | Update a reminder |
| DELETE | `/reminders/{reminder_id}` | Delete a reminder |

FastAPI's generated OpenAPI documentation will make the APIs easier to test and demonstrate.

---

## 8. Docker and Deployment

### 8.1 Containerization

Each independently deployed application service will have its own Dockerfile where appropriate.

Docker Compose will coordinate:

- Frontend
- API Gateway
- Authentication Service
- AI Agent Service
- Task Service
- Activity Service
- Optional Reminder Service
- PostgreSQL

### 8.2 Local Startup

The intended development command is:

```bash
docker compose up --build
```

The exact service list and configuration will be finalized in the repository.

### 8.3 Docker Requirements

- Use an internal Docker network for backend communication.
- Keep PostgreSQL inaccessible from the public internet.
- Use a named volume for database persistence.
- Add service health checks and appropriate startup dependencies.
- Keep secrets out of images, source code, and Git history.
- Configure environment-specific values through environment variables.
- Verify that application data survives container restarts.
- Document backup and restore procedures.

### 8.4 Google Gemini API Access

The AI Agent Service calls the Gemini API using a server-side API key supplied through the environment (for example, `GEMINI_API_KEY` in a local `.env` file or a secret manager in deployment).

Never put the API key in frontend code, a Docker image, a response payload, or a committed `.env` file. Set `GEMINI_ENABLED=false` to run the deterministic mock provider without a key.

### 8.5 Kubernetes

Kubernetes is an optional extension after the Docker Compose MVP is stable.

The priority is a working, tested, demonstrable application rather than introducing additional orchestration complexity before the deadline.

---

## 9. Security and Reliability

1. Hash passwords using an appropriate password-hashing algorithm.
2. Enforce authorization on every user-owned resource.
3. Validate all API inputs and AI tool parameters.
4. Use parameterized queries through the ORM.
5. Require confirmation for destructive actions when applicable.
6. Avoid logging passwords, tokens, credentials, or unnecessary sensitive content.
7. Keep the Gemini API key server-side and restrict it to the Gemini API.
8. Keep database credentials and model configuration outside source code.
9. Add bounded retries and useful error messages for transient Gemini failures.
10. Ensure task CRUD works when the AI provider is unavailable.
11. Record relevant activity without trusting model-generated success claims.
12. Use database transactions for operations that must succeed or fail together.

---

## 10. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript |
| Backend APIs | Python, FastAPI |
| AI model | Gemini 3.5 Flash-Lite (configurable) |
| AI platform | Google Gemini API |
| Model integration | `google-genai`, function calling |
| Validation | Pydantic |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy and Alembic |
| Authentication | JWT and secure password hashing |
| Containerization | Docker |
| Local orchestration | Docker Compose |
| Version control | Git and GitHub |
| Backend testing | Pytest |
| Frontend testing | Appropriate React testing tools |
| API documentation | FastAPI OpenAPI |
| Optional deployment extension | Kubernetes |

---

## 11. Implementation Roadmap

### Phase 1: Foundation

- Create the repository and define service boundaries.
- Implement the React dashboard.
- Implement PostgreSQL models and migrations.
- Build task CRUD and filtering.
- Implement authentication and user ownership.
- Verify that manual operations work end to end.

### Phase 2: AI Integration

- Configure the Google Gemini API key.
- Integrate Gemini 3.5 Flash-Lite through the `google-genai` SDK.
- Implement typed function declarations.
- Add natural-language task creation and search.
- Add task updates, completion, priority changes, and archive/restore.
- Implement clarification and confirmation flows.
- Add error handling and usage tracking.

### Phase 3: Supporting Features

- Add activity history.
- Implement overdue and upcoming summaries.
- Add reminders if time permits.
- Verify that the application remains usable during Gemini outages.

### Phase 4: Docker

- Write Dockerfiles.
- Configure Docker Compose and service networking.
- Add PostgreSQL persistence.
- Add health checks and environment configuration.
- Verify clean startup and persistence across restarts.

### Phase 5: Testing and Demonstration

- Run backend and frontend tests.
- Test AI tool selection and task matching.
- Test authorization and destructive-operation confirmations.
- Measure Gemini usage and latency.
- Prepare the architecture diagram, database diagram, README, and demonstration workflow.

---

## 12. Testing Strategy

The test plan must cover both deterministic application behavior and AI-assisted behavior.

### 12.1 Functional Tests

- Create, read, update, complete, reopen, archive, restore, and delete tasks.
- Verify filtering by status, priority, and deadline.
- Verify database persistence after container restarts.
- Verify that different users cannot access each other's tasks.

### 12.2 AI Tests

- Correctly interpret task creation instructions.
- Extract dates, titles, and priorities.
- Select the correct tools for updates and completion.
- Ask for clarification when multiple tasks match.
- Require confirmation for destructive or broad actions.
- Report actual backend outcomes rather than invented successes.

### 12.3 Reliability Tests

- Gemini request failure or throttling.
- Invalid tool arguments.
- Expired authentication tokens.
- Database unavailability.
- Duplicate requests and safe retry behavior.
- Activity logging for successful and failed operations.

### 12.4 Cost Tests

- Record input and output token usage.
- Measure typical request latency.
- Compare model usage across simple and multi-step commands.
- Check actual costs against the available credit.
- Ensure unnecessary model calls are avoided for deterministic operations.

---

## 13. Expected Outcome

At completion, Tasked: AI Enabled Task Manager will provide:

- A working web-based task management application.
- Secure, persistent CRUD functionality.
- Natural-language task management through Gemini 3.5 Flash-Lite on the Google Gemini API.
- A backend-controlled tool-calling workflow.
- Authentication and user-level authorization.
- Activity history and optional reminders.
- Docker-based deployment with PostgreSQL persistence.
- Automated tests and technical documentation.
- A live demonstration suitable for the college micro-project.

The project prioritizes practical engineering, controlled AI usage, security, explainability, and reliable execution over unnecessary model or infrastructure complexity.

---

## Final Project Definition

**Tasked: AI Enabled Task Manager is a Docker-deployed, service-based task management system that uses the Google Gemini API to translate natural-language instructions into secure, validated CRUD operations, with PostgreSQL as the source of truth and FastAPI services enforcing authorization and business rules.**