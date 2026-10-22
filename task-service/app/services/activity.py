"""Activity service."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import Activity
from app.schemas.activity import ActivityListResponse


class ActivityService:
    """Activity service for retrieving activity history."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_user_activities(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        task_id: Optional[UUID] = None,
    ) -> ActivityListResponse:
        """List activities for a user, optionally filtered by task."""
        query = select(Activity).where(Activity.user_id == user_id)

        if task_id:
            query = query.where(Activity.task_id == task_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Activity.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.options(selectinload(Activity.task))

        result = await self.session.execute(query)
        activities = result.scalars().all()

        return ActivityListResponse(
            activities=[a for a in activities],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_task_activities(self, user_id: UUID, task_id: UUID) -> list[Activity]:
        """Get activities for a specific task."""
        result = await self.session.execute(
            select(Activity)
            .where(Activity.user_id == user_id, Activity.task_id == task_id)
            .order_by(Activity.created_at.desc())
        )
        return list(result.scalars().all())


async def get_activity_service(session: AsyncSession) -> ActivityService:
    """Dependency injection for ActivityService."""
    return ActivityService(session)