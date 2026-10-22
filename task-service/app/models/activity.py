"""Activity model."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ActivitySource(str, enum.Enum):
    """Source of the activity."""

    MANUAL = "manual"
    AI = "ai"


class ActivityOutcome(str, enum.Enum):
    """Outcome of the activity."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class Activity(Base, TimestampMixin):
    """Activity event model."""

    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[ActivitySource] = mapped_column(
        Enum(ActivitySource, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=ActivitySource.MANUAL,
        nullable=False,
    )
    before_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outcome: Mapped[ActivityOutcome] = mapped_column(
        Enum(ActivityOutcome, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=ActivityOutcome.SUCCESS,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activities", lazy="selectin")
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="activities", lazy="selectin")

    # Composite indexes
    __table_args__ = (
        Index("ix_activities_user_created", "user_id", "created_at"),
        Index("ix_activities_task_created", "task_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, action={self.action_type}, source={self.source})>"