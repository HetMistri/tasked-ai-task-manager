"""Pydantic validation for tool arguments.

The model proposes tool arguments, but the backend decides whether they are
acceptable. Invalid arguments are rejected before any Core Task API call.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Priority = Literal["low", "medium", "high", "urgent"]
Status = Literal["pending", "in_progress", "completed"]


class CreateTaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Priority = "medium"
    due_at: Optional[datetime] = None


class SearchTasksInput(BaseModel):
    query: str = Field(min_length=1, max_length=255)


class TaskIdentifierInput(BaseModel):
    task_identifier: str = Field(min_length=1, max_length=255)


class UpdateTaskInput(BaseModel):
    task_identifier: str = Field(min_length=1, max_length=255)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    due_at: Optional[datetime] = None
    is_archived: Optional[bool] = None


class SetPriorityInput(BaseModel):
    task_identifier: str = Field(min_length=1, max_length=255)
    priority: Priority


TOOL_INPUT_SCHEMAS = {
    "create_task": CreateTaskInput,
    "search_tasks": SearchTasksInput,
    "update_task": UpdateTaskInput,
    "complete_task": TaskIdentifierInput,
    "reopen_task": TaskIdentifierInput,
    "set_task_priority": SetPriorityInput,
    "archive_task": TaskIdentifierInput,
    "restore_task": TaskIdentifierInput,
    "delete_task": TaskIdentifierInput,
    "get_task_summary": BaseModel,
}