"""AI service tests: validation, ambiguity, confirmation, provider errors.

Gemini and the Core Task API are mocked; no Google API key is needed.
"""

import pytest
import pytest_asyncio
from google.genai import errors, types

from app.clients.gemini import (
    AIResponse,
    FunctionCall,
    GeminiClient,
    MockGeminiClient,
    ProviderError,
)
from app.services import ai as ai_module
from app.services.ai import AIService


class FakeGemini:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.contents_seen = []

    async def generate(self, system_prompt, contents, tools):
        self.calls += 1
        self.contents_seen.append(list(contents))
        if not self.responses:
            raise AssertionError("Gemini called more times than expected")
        return self.responses.pop(0)


class FailingGemini:
    def __init__(self, message="Could not reach Gemini."):
        self.message = message

    async def generate(self, system_prompt, contents, tools):
        raise ProviderError(self.message)


def tool_call_response(name: str, arguments: dict):
    return AIResponse(
        text=None,
        function_calls=[FunctionCall(name=name, arguments=arguments)],
    )


def text_response(text: str):
    return AIResponse(text=text, function_calls=[])


class FakeTaskAPI:
    def __init__(self, tasks=None):
        self.tasks = tasks or []
        self.created = []
        self.deleted = []
        self.summary_calls = 0

    async def get_tasks(self, token, search=None, page_size=20, **kwargs):
        return {"tasks": self.tasks, "total": len(self.tasks)}

    async def create_task(self, token, **kwargs):
        self.created.append(kwargs)
        return {"id": "11111111-1111-1111-1111-111111111111", **kwargs}

    async def delete_task(self, token, task_id):
        self.deleted.append(task_id)
        return {"success": True, "id": task_id}

    async def complete_task(self, token, task_id):
        return {"id": task_id, "status": "completed"}

    async def get_summary(self, token):
        self.summary_calls += 1
        return {"total": 3}


@pytest_asyncio.fixture
async def service():
    return AIService()


async def test_invalid_tool_arguments_are_rejected(monkeypatch, service):
    fake_api = FakeTaskAPI()
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)

    result = await service._execute_tool("create_task", {"title": ""}, "token")

    assert result["success"] is False
    assert "Invalid arguments" in result["error"]
    assert fake_api.created == []


async def test_unknown_tool_is_rejected(monkeypatch, service):
    fake_api = FakeTaskAPI()
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)

    result = await service._execute_tool("drop_database", {}, "token")

    assert result["success"] is False
    assert "Unknown tool" in result["error"]


async def test_ambiguous_task_reference_asks_for_clarification(monkeypatch, service):
    fake_api = FakeTaskAPI(
        tasks=[
            {"id": "1", "title": "DBMS assignment"},
            {"id": "2", "title": "DBMS project"},
        ]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)

    result = await service._execute_tool(
        "complete_task", {"task_identifier": "DBMS"}, "token"
    )

    assert result["success"] is False
    assert result["ambiguous"] is True
    assert len(result["matches"]) == 2


async def test_single_match_is_completed(monkeypatch, service):
    fake_api = FakeTaskAPI(tasks=[{"id": "42", "title": "DBMS assignment"}])
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)

    result = await service._execute_tool(
        "complete_task", {"task_identifier": "DBMS"}, "token"
    )

    assert result["status"] == "completed"


async def test_delete_requires_confirmation_before_execution(monkeypatch, service):
    fake_api = FakeTaskAPI(tasks=[{"id": "42", "title": "Old task"}])
    fake_gemini = FakeGemini(
        [tool_call_response("delete_task", {"task_identifier": "Old task"})]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    result = await service.process_message("delete my old task", "token-a")

    assert result["requires_confirmation"] is True
    assert result["confirmation_id"]
    # Nothing was deleted yet.
    assert fake_api.deleted == []


async def test_confirmation_executes_delete_for_owner(monkeypatch, service):
    fake_api = FakeTaskAPI(tasks=[{"id": "42", "title": "Old task"}])
    fake_gemini = FakeGemini(
        [tool_call_response("delete_task", {"task_identifier": "Old task"})]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    chat = await service.process_message("delete my old task", "token-a")
    result = await service.confirm_action(chat["confirmation_id"], True, "token-a")

    assert result["success"] is True
    assert fake_api.deleted == ["42"]


async def test_confirmation_is_scoped_to_the_requesting_user(monkeypatch, service):
    fake_api = FakeTaskAPI(tasks=[{"id": "42", "title": "Old task"}])
    fake_gemini = FakeGemini(
        [tool_call_response("delete_task", {"task_identifier": "Old task"})]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    chat = await service.process_message("delete my old task", "token-a")
    result = await service.confirm_action(chat["confirmation_id"], True, "token-b")

    assert result["success"] is False
    assert fake_api.deleted == []


async def test_cancelled_confirmation_does_nothing(monkeypatch, service):
    fake_api = FakeTaskAPI(tasks=[{"id": "42", "title": "Old task"}])
    fake_gemini = FakeGemini(
        [tool_call_response("delete_task", {"task_identifier": "Old task"})]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    chat = await service.process_message("delete my old task", "token-a")
    result = await service.confirm_action(chat["confirmation_id"], False, "token-a")

    assert result["success"] is True
    assert "cancelled" in result["message"].lower()
    assert fake_api.deleted == []


async def test_provider_failure_returns_controlled_error(monkeypatch, service):
    fake_api = FakeTaskAPI()
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(
        ai_module,
        "ai_client",
        FailingGemini("Could not reach Gemini. Check the network connection."),
    )

    result = await service.process_message("create a task", "token")

    assert result["requires_confirmation"] is False
    assert "AI provider is unavailable" in result["response"]
    assert "manage tasks manually" in result["response"]


async def test_tool_loop_is_bounded(monkeypatch):
    monkeypatch.setattr(ai_module.settings, "max_tool_iterations", 3)
    service = AIService()

    fake_api = FakeTaskAPI()
    fake_gemini = FakeGemini(
        [
            tool_call_response("create_task", {"title": f"Task {i}"})
            for i in range(10)
        ]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    await service.process_message("create lots of tasks", "token")

    assert fake_gemini.calls == 3


async def test_create_task_tool_call_round_trip(monkeypatch, service):
    fake_api = FakeTaskAPI()
    fake_gemini = FakeGemini(
        [
            tool_call_response(
                "create_task", {"title": "DBMS assignment", "priority": "high"}
            ),
            text_response("Created DBMS assignment."),
        ]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    result = await service.process_message("create DBMS assignment", "token")

    assert result["response"] == "Created DBMS assignment."
    assert fake_api.created[0]["title"] == "DBMS assignment"
    assert fake_api.created[0]["priority"] == "high"


async def test_tool_result_is_sent_back_to_gemini(monkeypatch, service):
    fake_api = FakeTaskAPI()
    fake_gemini = FakeGemini(
        [
            tool_call_response("create_task", {"title": "DBMS assignment"}),
            text_response("Created."),
        ]
    )
    monkeypatch.setattr(ai_module, "task_api_client", fake_api)
    monkeypatch.setattr(ai_module, "ai_client", fake_gemini)

    await service.process_message("create DBMS assignment", "token")

    second_turn = fake_gemini.contents_seen[1]
    function_response = second_turn[-1].parts[0].function_response
    assert function_response.name == "create_task"
    assert function_response.response["result"]["title"] == "DBMS assignment"


async def test_mock_mode_is_reported(monkeypatch, service):
    monkeypatch.setattr(ai_module.settings, "gemini_enabled", False)

    assert ai_module.settings.use_mock is True
    assert ai_module.settings.gemini_configured is False


async def test_enabled_without_key_is_not_silently_mocked(monkeypatch):
    monkeypatch.setattr(ai_module.settings, "gemini_enabled", True)
    monkeypatch.setattr(ai_module.settings, "gemini_api_key", "")

    assert ai_module.settings.use_mock is False
    assert ai_module.settings.gemini_configured is False


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (400, "GEMINI_API_KEY is valid"),
        (401, "GEMINI_API_KEY is valid"),
        (404, "model was not found"),
        (429, "rate limit"),
        (503, "temporarily unavailable"),
    ],
)
def test_gemini_errors_map_to_safe_messages(code, expected):
    exc = errors.ClientError(
        code,
        {"error": {"message": "provider detail that must not reach the user"}},
        None,
    )

    message = GeminiClient._friendly_error(exc)

    assert expected in message
    assert "provider detail" not in message


async def test_mock_client_returns_valid_create_call():
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="Create a high-priority DBMS assignment due Friday"
                )
            ],
        )
    ]

    response = await MockGeminiClient().generate("", contents, [])

    assert len(response.function_calls) == 1
    call = response.function_calls[0]
    assert call.name == "create_task"
    assert call.arguments["title"] == "DBMS assignment"
    assert call.arguments["priority"] == "high"
    assert call.arguments["due_at"]
