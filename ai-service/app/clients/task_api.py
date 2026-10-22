"""Client for communicating with the Core Task API."""

import logging
from typing import Any, Optional
from uuid import UUID

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskAPIClient:
    """HTTP client for the Core Task API."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.task_api_url
        self.timeout = settings.task_api_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    # Task operations
    async def create_task(
        self, token: str, title: str, description: Optional[str] = None, priority: str = "medium", due_at: Optional[str] = None
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            "/tasks",
            json={"title": title, "description": description, "priority": priority, "due_at": due_at},
            headers=self._auth_headers(token),
        )
        response.raise_for_status()
        return response.json()

    async def get_tasks(
        self,
        token: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        is_archived: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if is_archived is not None:
            params["is_archived"] = is_archived
        if search:
            params["search"] = search

        response = await client.get("/tasks", params=params, headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def get_task(self, token: str, task_id: UUID) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/tasks/{task_id}", headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def update_task(
        self,
        token: str,
        task_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_at: Optional[str] = None,
        is_archived: Optional[bool] = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        data = {}
        if title is not None:
            data["title"] = title
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if priority is not None:
            data["priority"] = priority
        if due_at is not None:
            data["due_at"] = due_at
        if is_archived is not None:
            data["is_archived"] = is_archived

        response = await client.patch(f"/tasks/{task_id}", json=data, headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def complete_task(self, token: str, task_id: UUID) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(f"/tasks/{task_id}/complete", headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def reopen_task(self, token: str, task_id: UUID) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(f"/tasks/{task_id}/reopen", headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def set_priority(self, token: str, task_id: UUID, priority: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(f"/tasks/{task_id}/priority", json={"priority": priority}, headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def archive_task(self, token: str, task_id: UUID) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(f"/tasks/{task_id}/archive", headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def restore_task(self, token: str, task_id: UUID) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(f"/tasks/{task_id}/restore", headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    async def delete_task(self, token: str, task_id: UUID) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.delete(f"/tasks/{task_id}", headers=self._auth_headers(token))
        response.raise_for_status()
        # The Core Task API returns 204 No Content after a successful delete.
        return {"success": True, "id": str(task_id)}

    async def get_summary(self, token: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get("/tasks/summary", headers=self._auth_headers(token))
        response.raise_for_status()
        return response.json()

    # Health check
    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


task_api_client = TaskAPIClient()