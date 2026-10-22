"""Task model."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base, TimestampMixin, SoftDeleteMixin):
    """Task model."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Store enum *values* ("pending", "high") rather than member names, so the
    # database matches the API and the migration defaults.
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    is_archived: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks", lazy="selectin")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="task",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_priority", "user_id", "priority"),
        Index("ix_tasks_user_archived", "user_id", "is_archived"),
        Index("ix_tasks_user_due_at", "user_id", "due_at"),
        Index("ix_tasks_user_deleted", "user_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title!r}, status={self.status})>"

    @property
    def is_overdue(self) -> bool:
        """True when a due date has passed and the task is not completed.

        PostgreSQL returns timezone-aware datetimes; SQLite (used in tests)
        returns naive ones, so treat a missing tzinfo as UTC.
        """
        if self.due_at is None or self.status == TaskStatus.COMPLETED:
            return False
        due_at = self.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        return due_at < datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def mark_reopened(self) -> None:
        """Reopen a completed task."""
        self.status = TaskStatus.PENDING
        self.completed_at = None

    def archive(self) -> None:
        """Archive the task."""
        self.is_archived = True
        self.archived_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore an archived task."""
        self.is_archived = False
        self.archived_at = None