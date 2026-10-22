"""Core Task API routes."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_activity_service,
    get_auth_service,
    get_current_user_id,
    get_task_service,
)
from app.db.session import get_db
from app.models.task import TaskPriority, TaskStatus
from app.schemas.activity import ActivityListResponse, ActivityResponse
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPriorityRequest,
    TaskResponse,
    TaskUpdate,
)
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.activity import ActivityService
from app.services.auth import AuthService
from app.services.task import TaskService

router = APIRouter()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


@router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED, tags=["auth"])
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create an account and return a token for the new user."""
    try:
        user = await auth_service.register(user_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    token = auth_service.create_access_token(user.id)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/auth/login", response_model=Token, tags=["auth"])
async def login(credentials: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    """Exchange email and password for a JWT."""
    try:
        return await auth_service.login(credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/auth/me", response_model=UserResponse, tags=["auth"])
async def get_me(
    user_id: UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.get_user_response(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    task_data: TaskCreate,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.create(user_id, task_data)
    return TaskResponse.model_validate(task)


@router.get("/tasks", response_model=TaskListResponse, tags=["tasks"])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[TaskPriority] = None,
    is_archived: Optional[bool] = None,
    search: Optional[str] = Query(None, max_length=255),
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    """List the current user's tasks with filters and pagination."""
    return await task_service.list_tasks(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status_filter,
        priority=priority,
        is_archived=is_archived,
        search=search,
    )


@router.get("/tasks/summary", tags=["tasks"])
async def get_task_summary(
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    """Counts used by the dashboard sidebar."""
    return await task_service.get_summary(user_id)


@router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
async def get_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.get_by_id(user_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.update(user_id, task_id, task_data)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse, tags=["tasks"])
async def complete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.complete(user_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/reopen", response_model=TaskResponse, tags=["tasks"])
async def reopen_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.reopen(user_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/priority", response_model=TaskResponse, tags=["tasks"])
async def set_task_priority(
    task_id: UUID,
    request: TaskPriorityRequest,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.set_priority(user_id, task_id, request.priority)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/archive", response_model=TaskResponse, tags=["tasks"])
async def archive_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.archive(user_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/restore", response_model=TaskResponse, tags=["tasks"])
async def restore_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    task = await task_service.restore(user_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
async def delete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
):
    """Soft delete a task. It disappears from normal lists but stays recoverable."""
    deleted = await task_service.delete(user_id, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


# ---------------------------------------------------------------------------
# Activity history
# ---------------------------------------------------------------------------


@router.get("/activity", response_model=ActivityListResponse, tags=["activity"])
async def list_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_id: Optional[UUID] = None,
    user_id: UUID = Depends(get_current_user_id),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return await activity_service.list_user_activities(user_id, page, page_size, task_id)


@router.get("/activity/tasks/{task_id}", response_model=list[ActivityResponse], tags=["activity"])
async def get_task_activity(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return await activity_service.get_task_activities(user_id, task_id)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", tags=["health"])
async def health():
    """Liveness probe. Deliberately does not check PostgreSQL or the AI provider."""
    return {
        "status": "healthy",
        "service": "task-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", tags=["health"])
async def readiness(session: AsyncSession = Depends(get_db)):
    """Readiness probe: the API can serve traffic only with a working database."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready",
        ) from None
    return {"status": "ready", "database": "ok"}