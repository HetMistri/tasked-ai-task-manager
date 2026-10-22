"""Task service."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.activity import Activity, ActivitySource, ActivityOutcome
from app.schemas.task import TaskCreate, TaskUpdate, TaskListResponse


class TaskService:
    """Task service for CRUD operations and business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, task_data: TaskCreate, source: ActivitySource = ActivitySource.MANUAL) -> Task:
        """Create a new task."""
        task = Task(
            user_id=user_id,
            title=task_data.title.strip(),
            description=task_data.description.strip() if task_data.description else None,
            priority=task_data.priority,
            due_at=task_data.due_at,
        )
        self.session.add(task)
        await self.session.flush()

        # Log activity
        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="create_task",
            source=source,
            after_state={"title": task.title, "priority": task.priority.value},
        )

        return task

    async def get_by_id(self, user_id: UUID, task_id: UUID) -> Optional[Task]:
        """Get task by ID, ensuring ownership."""
        result = await self.session.execute(
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id, Task.deleted_at.is_(None))
            .options(selectinload(Task.activities))
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        is_archived: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> TaskListResponse:
        """List tasks with filters and pagination."""
        query = select(Task).where(Task.user_id == user_id, Task.deleted_at.is_(None))

        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if is_archived is not None:
            query = query.where(Task.is_archived == is_archived)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Task.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        tasks = result.scalars().all()

        return TaskListResponse(
            tasks=[t for t in tasks],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def update(self, user_id: UUID, task_id: UUID, task_data: TaskUpdate, source: ActivitySource = ActivitySource.MANUAL) -> Optional[Task]:
        """Update a task."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return None

        before_state = {
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "is_archived": task.is_archived,
        }

        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "title" and value is not None:
                value = value.strip()
            if field == "description" and value is not None:
                value = value.strip() if value else None
            setattr(task, field, value)

        await self.session.flush()

        after_state = {
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "is_archived": task.is_archived,
        }

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="update_task",
            source=source,
            before_state=before_state,
            after_state=after_state,
        )

        return task

    async def complete(self, user_id: UUID, task_id: UUID, source: ActivitySource = ActivitySource.MANUAL) -> Optional[Task]:
        """Mark a task as completed."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return None

        before_state = {"status": task.status.value, "completed_at": None}
        task.mark_completed()
        await self.session.flush()

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="complete_task",
            source=source,
            before_state=before_state,
            after_state={"status": task.status.value, "completed_at": task.completed_at.isoformat() if task.completed_at else None},
        )

        return task

    async def reopen(self, user_id: UUID, task_id: UUID, source: ActivitySource = ActivitySource.MANUAL) -> Optional[Task]:
        """Reopen a completed task."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return None

        before_state = {"status": task.status.value, "completed_at": task.completed_at.isoformat() if task.completed_at else None}
        task.mark_reopened()
        await self.session.flush()

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="reopen_task",
            source=source,
            before_state=before_state,
            after_state={"status": task.status.value, "completed_at": None},
        )

        return task

    async def set_priority(self, user_id: UUID, task_id: UUID, priority: TaskPriority, source: ActivitySource = ActivitySource.MANUAL) -> Optional[Task]:
        """Change task priority."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return None

        before_state = {"priority": task.priority.value}
        task.priority = priority
        await self.session.flush()

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="set_task_priority",
            source=source,
            before_state=before_state,
            after_state={"priority": task.priority.value},
        )

        return task

    async def archive(self, user_id: UUID, task_id: UUID, source: ActivitySource = ActivitySource.MANUAL) -> Optional[Task]:
        """Archive a task."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return None

        before_state = {"is_archived": task.is_archived, "archived_at": task.archived_at.isoformat() if task.archived_at else None}
        task.archive()
        await self.session.flush()

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="archive_task",
            source=source,
            before_state=before_state,
            after_state={"is_archived": task.is_archived, "archived_at": task.archived_at.isoformat() if task.archived_at else None},
        )

        return task

    async def restore(self, user_id: UUID, task_id: UUID, source: ActivitySource = ActivitySource.MANUAL) -> Optional[Task]:
        """Restore an archived task."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return None

        before_state = {"is_archived": task.is_archived, "archived_at": task.archived_at.isoformat() if task.archived_at else None}
        task.restore()
        await self.session.flush()

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="restore_task",
            source=source,
            before_state=before_state,
            after_state={"is_archived": task.is_archived, "archived_at": None},
        )

        return task

    async def delete(self, user_id: UUID, task_id: UUID, source: ActivitySource = ActivitySource.MANUAL) -> bool:
        """Soft delete a task."""
        task = await self.get_by_id(user_id, task_id)
        if not task:
            return False

        before_state = {"deleted_at": None}
        task.soft_delete()
        await self.session.flush()

        await self._log_activity(
            user_id=user_id,
            task_id=task.id,
            action_type="delete_task",
            source=source,
            before_state=before_state,
            after_state={"deleted_at": task.deleted_at.isoformat() if task.deleted_at else None},
        )

        return True

    async def search_tasks(self, user_id: UUID, query: str, limit: int = 10) -> list[Task]:
        """Search tasks by title/description."""
        search_term = f"%{query}%"
        result = await self.session.execute(
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.deleted_at.is_(None),
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                ),
            )
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_summary(self, user_id: UUID) -> dict:
        """Get task summary statistics."""
        from sqlalchemy import case

        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(
                func.count(Task.id).label("total"),
                func.count(case((Task.status == TaskStatus.COMPLETED, 1))).label("completed"),
                func.count(case((Task.status == TaskStatus.PENDING, 1))).label("pending"),
                func.count(case((Task.status == TaskStatus.IN_PROGRESS, 1))).label("in_progress"),
                func.count(case((Task.is_archived.is_(True), 1))).label("archived"),
                func.count(
                    case(
                        (
                            and_(
                                Task.due_at.is_not(None),
                                Task.due_at < now,
                                Task.status != TaskStatus.COMPLETED,
                            ),
                            1,
                        )
                    )
                ).label("overdue"),
            )
            .where(Task.user_id == user_id, Task.deleted_at.is_(None))
        )
        row = result.one()
        return {
            "total": row.total,
            "completed": row.completed,
            "pending": row.pending,
            "in_progress": row.in_progress,
            "archived": row.archived,
            "overdue": row.overdue,
        }

    async def _log_activity(
        self,
        user_id: UUID,
        task_id: UUID,
        action_type: str,
        source: ActivitySource,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        outcome: ActivityOutcome = ActivityOutcome.SUCCESS,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an activity event."""
        activity = Activity(
            user_id=user_id,
            task_id=task_id,
            action_type=action_type,
            source=source,
            before_state=before_state,
            after_state=after_state,
            outcome=outcome,
            error_message=error_message,
        )
        self.session.add(activity)


async def get_task_service(session: AsyncSession) -> TaskService:
    """Dependency injection for TaskService."""
    return TaskService(session)