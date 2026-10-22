"""Core Task API behaviour tests."""

from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, create_task, register_user


async def test_register_login_and_me(client):
    data = await register_user(client)
    assert data["access_token"]
    assert data["user"]["email"] == "student@example.com"

    login = await client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "correct-horse"},
    )
    assert login.status_code == 200

    me = await client.get("/auth/me", headers=auth_headers(data["access_token"]))
    assert me.status_code == 200
    assert me.json()["display_name"] == "Student"


async def test_duplicate_email_rejected(client):
    await register_user(client)
    response = await client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "another-password",
            "display_name": "Someone",
        },
    )
    assert response.status_code == 409


async def test_create_and_list_task(client):
    user = await register_user(client)
    token = user["access_token"]

    task = await create_task(client, token, description="Chapter 4 exercises")
    assert task["title"] == "DBMS assignment"
    assert task["status"] == "pending"
    assert task["priority"] == "high"
    assert task["is_archived"] is False

    listing = await client.get("/tasks", headers=auth_headers(token))
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1
    assert body["tasks"][0]["id"] == task["id"]


async def test_complete_and_reopen_timestamps(client):
    token = (await register_user(client))["access_token"]
    task = await create_task(client, token)

    completed = await client.post(f"/tasks/{task['id']}/complete", headers=auth_headers(token))
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["completed_at"] is not None

    reopened = await client.post(f"/tasks/{task['id']}/reopen", headers=auth_headers(token))
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "pending"
    assert reopened.json()["completed_at"] is None


async def test_archive_does_not_change_completion(client):
    token = (await register_user(client))["access_token"]
    task = await create_task(client, token)
    await client.post(f"/tasks/{task['id']}/complete", headers=auth_headers(token))

    archived = await client.post(f"/tasks/{task['id']}/archive", headers=auth_headers(token))
    body = archived.json()
    assert body["is_archived"] is True
    assert body["archived_at"] is not None
    assert body["status"] == "completed"

    restored = await client.post(f"/tasks/{task['id']}/restore", headers=auth_headers(token))
    assert restored.json()["is_archived"] is False
    assert restored.json()["archived_at"] is None
    assert restored.json()["status"] == "completed"


async def test_priority_change_via_endpoint(client):
    token = (await register_user(client))["access_token"]
    task = await create_task(client, token)

    response = await client.post(
        f"/tasks/{task['id']}/priority",
        json={"priority": "urgent"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["priority"] == "urgent"


async def test_invalid_input_rejected(client):
    token = (await register_user(client))["access_token"]

    empty_title = await client.post(
        "/tasks", json={"title": ""}, headers=auth_headers(token)
    )
    assert empty_title.status_code == 422

    bad_priority = await client.post(
        "/tasks", json={"title": "Valid", "priority": "extreme"}, headers=auth_headers(token)
    )
    assert bad_priority.status_code == 422

    created = await create_task(client, token, title="Valid")
    bad_status = await client.patch(
        f"/tasks/{created['id']}",
        json={"status": "archived"},
        headers=auth_headers(token),
    )
    assert bad_status.status_code == 422


async def test_user_isolation(client):
    alice = await register_user(client, email="alice@example.com")
    bob = await register_user(client, email="bob@example.com")

    alice_task = await create_task(client, alice["access_token"], title="Alice private task")

    # Bob cannot read, update, complete, archive or delete Alice's task.
    assert (
        await client.get(f"/tasks/{alice_task['id']}", headers=auth_headers(bob["access_token"]))
    ).status_code == 404
    assert (
        await client.patch(
            f"/tasks/{alice_task['id']}",
            json={"title": "hijacked"},
            headers=auth_headers(bob["access_token"]),
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/tasks/{alice_task['id']}/complete", headers=auth_headers(bob["access_token"])
        )
    ).status_code == 404
    assert (
        await client.delete(
            f"/tasks/{alice_task['id']}", headers=auth_headers(bob["access_token"])
        )
    ).status_code == 404

    # Bob's list is still empty.
    bob_listing = await client.get("/tasks", headers=auth_headers(bob["access_token"]))
    assert bob_listing.json()["total"] == 0


async def test_soft_deleted_task_hidden(client):
    token = (await register_user(client))["access_token"]
    task = await create_task(client, token)

    assert (
        await client.delete(f"/tasks/{task['id']}", headers=auth_headers(token))
    ).status_code == 204
    assert (
        await client.get(f"/tasks/{task['id']}", headers=auth_headers(token))
    ).status_code == 404

    listing = await client.get("/tasks", headers=auth_headers(token))
    assert listing.json()["total"] == 0


async def test_filters_and_pagination(client):
    token = (await register_user(client))["access_token"]
    await create_task(client, token, title="Alpha", priority="low")
    await create_task(client, token, title="Beta report", priority="urgent")
    third = await create_task(client, token, title="Gamma")
    await client.post(f"/tasks/{third['id']}/complete", headers=auth_headers(token))

    completed = await client.get(
        "/tasks", params={"status": "completed"}, headers=auth_headers(token)
    )
    assert completed.json()["total"] == 1

    urgent = await client.get(
        "/tasks", params={"priority": "urgent"}, headers=auth_headers(token)
    )
    assert urgent.json()["total"] == 1

    search = await client.get(
        "/tasks", params={"search": "report"}, headers=auth_headers(token)
    )
    assert search.json()["total"] == 1
    assert search.json()["tasks"][0]["title"] == "Beta report"

    paged = await client.get(
        "/tasks", params={"page": 1, "page_size": 2}, headers=auth_headers(token)
    )
    assert len(paged.json()["tasks"]) == 2
    assert paged.json()["total_pages"] == 2


async def test_overdue_flag(client):
    token = (await register_user(client))["access_token"]
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    task = await create_task(client, token, due_at=yesterday.isoformat())
    assert task["is_overdue"] is True


async def test_summary_counts(client):
    token = (await register_user(client))["access_token"]
    await create_task(client, token, title="One")
    second = await create_task(client, token, title="Two")
    await client.post(f"/tasks/{second['id']}/archive", headers=auth_headers(token))

    summary = await client.get("/tasks/summary", headers=auth_headers(token))
    assert summary.status_code == 200
    body = summary.json()
    assert body["total"] == 2
    assert body["archived"] == 1
    assert body["pending"] == 2


async def test_activity_is_recorded(client):
    token = (await register_user(client))["access_token"]
    task = await create_task(client, token)

    activity = await client.get("/activity", headers=auth_headers(token))
    assert activity.status_code == 200
    actions = [item["action_type"] for item in activity.json()["activities"]]
    assert "create_task" in actions

    task_activity = await client.get(
        f"/activity/tasks/{task['id']}", headers=auth_headers(token)
    )
    assert task_activity.status_code == 200
    assert len(task_activity.json()) >= 1


async def test_unauthenticated_requests_rejected(client):
    assert (await client.get("/tasks")).status_code == 401
    assert (await client.get("/tasks", headers={"Authorization": "Bearer nonsense"})).status_code == 401


async def test_health_and_readiness(client):
    assert (await client.get("/health")).json()["status"] == "healthy"
    ready = await client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "ok"