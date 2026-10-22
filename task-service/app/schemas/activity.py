"""Activity schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.activity import ActivityOutcome, ActivitySource


class ActivityResponse(BaseModel):
    """Activity event response."""

    id: UUID
    user_id: UUID
    task_id: Optional[UUID] = None
    action_type: str
    source: ActivitySource
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    outcome: ActivityOutcome
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    """Paginated activity list response."""

    activities: list[ActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int