"""Task request and response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Payload for creating a task."""


class TaskUpdate(BaseModel):
    """Patch payload. Only provided fields are applied."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_at: Optional[datetime] = None
    is_archived: Optional[bool] = None


class TaskPriorityRequest(BaseModel):
    priority: TaskPriority


class TaskResponse(TaskBase):
    """Task as returned by the API.

    ``is_overdue`` is read from the ``Task.is_overdue`` property on the ORM
    object, so the overdue rule lives in one place (the model).
    """

    id: UUID
    user_id: UUID
    status: TaskStatus
    is_archived: bool
    archived_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_overdue: bool = False

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int