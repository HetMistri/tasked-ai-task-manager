"""Google Gemini client with a deterministic mock provider.

The rest of the AI service only depends on the small ``generate`` interface
below. That keeps provider details in one place and lets tests (and local
demos without an API key) run without calling Google.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from google import genai
from google.genai import errors, types

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """A safe, user-facing provider error (never contains the API key)."""


@dataclass
class FunctionCall:
    """One function the model asked us to run."""

    name: str
    arguments: dict[str, Any]


@dataclass
class AIResponse:
    """Provider-independent shape returned to the agent loop."""

    text: Optional[str]
    function_calls: list[FunctionCall]
    # The raw model turn is sent back to Gemini on the next request. Mock mode
    # does not need it.
    model_content: Optional[types.Content] = None


class GeminiClient:
    """Thin wrapper around the official google-genai async client."""

    def __init__(self) -> None:
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not settings.gemini_api_key:
                raise ProviderError(
                    "Gemini is enabled but GEMINI_API_KEY is not configured. "
                    "Set the key or run with GEMINI_ENABLED=false."
                )
            self._client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(
                    # Milliseconds, as required by the SDK.
                    timeout=int(settings.gemini_timeout_seconds * 1000),
                    # One retry for transient errors; never loop forever.
                    retry_options=types.HttpRetryOptions(attempts=2),
                ),
            )
        return self._client

    async def generate(
        self,
        system_prompt: str,
        contents: list[types.Content],
        tools: list[types.Tool],
    ) -> AIResponse:
        """Send the conversation and tool definitions to Gemini."""
        client = self._get_client()

        try:
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=tools,
                    temperature=0.1,
                    max_output_tokens=settings.max_output_tokens,
                    # We validate and execute function calls ourselves.
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
        except errors.APIError as exc:
            logger.warning(
                "Gemini API error: code=%s status=%s", exc.code, exc.status
            )
            raise ProviderError(self._friendly_error(exc)) from exc
        except Exception as exc:  # network failure, timeout, SDK error
            logger.error("Gemini request failed: %s", type(exc).__name__)
            raise ProviderError(
                "Could not reach Gemini. Check the network connection and try again."
            ) from exc

        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: types.GenerateContentResponse) -> AIResponse:
        if not response.candidates or response.candidates[0].content is None:
            return AIResponse(text=None, function_calls=[])

        content = response.candidates[0].content
        parts = content.parts or []

        # Thinking models can include internal thought parts. They are kept in
        # model_content (Gemini expects them back) but never shown to the user.
        text = "".join(
            part.text for part in parts if part.text and not part.thought
        )

        calls: list[FunctionCall] = []
        for part in parts:
            call = part.function_call
            if call and call.name:
                calls.append(
                    FunctionCall(
                        name=call.name,
                        arguments=dict(call.args or {}),
                    )
                )

        return AIResponse(
            text=text or None,
            function_calls=calls,
            model_content=content,
        )

    @staticmethod
    def _friendly_error(exc: errors.APIError) -> str:
        """Map provider errors to short messages without leaking details."""
        if exc.code in (400, 401, 403):
            return (
                "Gemini rejected the request. Check that GEMINI_API_KEY is valid "
                "and allowed to use the configured model."
            )
        if exc.code == 404:
            return (
                "The configured Gemini model was not found. Set GEMINI_MODEL to "
                "a model available to your API key."
            )
        if exc.code == 429:
            return "Gemini rate limit reached. Wait a moment and try again."
        if exc.code >= 500:
            return "Gemini is temporarily unavailable. Try again later."
        return f"Gemini request failed (HTTP {exc.code})."


class MockGeminiClient:
    """Keyword-based stand-in used when GEMINI_ENABLED=false.

    It returns the same ``AIResponse`` shape as the real client, so the agent
    loop, validation and confirmation logic are identical in both modes. Every
    reply is clearly labelled as mock mode.
    """

    async def generate(
        self,
        system_prompt: str,
        contents: list[types.Content],
        tools: list[types.Tool],
    ) -> AIResponse:
        last = contents[-1] if contents else None

        # A tool already ran in this turn: summarise its real result instead of
        # asking for another tool call (otherwise the loop would hit its cap).
        if last is not None:
            tool_results = [
                part.function_response.response.get("result", {})
                for part in (last.parts or [])
                if part.function_response and part.function_response.response
            ]
            if tool_results:
                return AIResponse(
                    text="[MOCK MODE] " + self._summarise(tool_results),
                    function_calls=[],
                )

        message = self._last_user_text(contents)
        lower = message.lower()

        if any(word in lower for word in ["create", "add", "new task"]):
            return self._create_task(message)

        if any(word in lower for word in ["delete", "remove"]):
            return self._task_tool("delete_task", message)

        if "restore" in lower:
            return self._task_tool("restore_task", message)

        if "archive" in lower:
            return self._task_tool("archive_task", message)

        if "reopen" in lower:
            return self._task_tool("reopen_task", message)

        if any(word in lower for word in ["complete", "finish", "done with"]):
            return self._task_tool("complete_task", message)

        if any(word in lower for word in ["summary", "overview", "how many"]):
            return AIResponse(
                text=None,
                function_calls=[FunctionCall(name="get_task_summary", arguments={})],
            )

        if any(word in lower for word in ["priority", "update", "change", "rename"]):
            return self._update_task(message)

        if any(word in lower for word in ["show", "list", "find", "search", "my task"]):
            return AIResponse(
                text=None,
                function_calls=[
                    FunctionCall(name="search_tasks", arguments={"query": "*"})
                ],
            )

        return AIResponse(
            text=(
                "[MOCK MODE] I understood: "
                f"'{message}'. In mock mode I can demonstrate creating, searching, "
                "updating, completing, reopening, archiving, restoring, summarising "
                "and deleting tasks."
            ),
            function_calls=[],
        )

    @staticmethod
    def _last_user_text(contents: list[types.Content]) -> str:
        for content in reversed(contents):
            for part in content.parts or []:
                if part.text:
                    return part.text
        return ""

    @staticmethod
    def _tool_call(name: str, arguments: dict[str, Any]) -> AIResponse:
        return AIResponse(
            text=None,
            function_calls=[FunctionCall(name=name, arguments=arguments)],
        )

    @staticmethod
    def _extract_identifier(message: str) -> str:
        """Pull a plausible task title out of 'mark DBMS done'."""
        cleaned = re.sub(
            r"^(please\s+)?(mark|complete|finish|delete|remove|archive|restore|"
            r"reopen|update|change|rename|set)\s+",
            "",
            message.strip(),
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"^(my|the)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.split(
            r"\s+(?:as|to)\s+|\s+(?:done|complete|completed)\b",
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        cleaned = re.sub(
            r"\s+(?:priority|status|due date)$", "", cleaned, flags=re.IGNORECASE
        )
        return cleaned.strip(" .!?") or message.strip()

    def _create_task(self, message: str) -> AIResponse:
        title_match = re.search(
            r"(?:create|add|new task).*?(?:called|named|titled|to|for)\s+([^.!?]+)",
            message,
            re.IGNORECASE,
        )
        if not title_match:
            title_match = re.search(
                r"(?:create|add|new task)\s+(.+)", message, re.IGNORECASE
            )
        title = title_match.group(1).strip() if title_match else "New task from AI"
        title = re.sub(r"^(a|an|the)\s+", "", title, flags=re.IGNORECASE)
        title = re.split(
            r"\s+(?:due|by|before)\s+", title, maxsplit=1, flags=re.IGNORECASE
        )[0]
        title = re.sub(
            r"\b(?:low|medium|high|urgent)[- ]priority\b",
            "",
            title,
            flags=re.IGNORECASE,
        )
        title = re.sub(r"\s+", " ", title).strip(" .") or "New task from AI"

        lower = message.lower()
        priority = "medium"
        if "urgent" in lower:
            priority = "urgent"
        elif "high" in lower:
            priority = "high"
        elif "low" in lower:
            priority = "low"

        due_at = None
        now = datetime.now(timezone.utc)
        if "tomorrow" in lower:
            due_at = (now + timedelta(days=1)).replace(
                hour=23, minute=59, second=0, microsecond=0
            ).isoformat()
        elif "friday" in lower:
            days_ahead = (4 - now.weekday()) % 7 or 7
            due_at = (now + timedelta(days=days_ahead)).replace(
                hour=23, minute=59, second=0, microsecond=0
            ).isoformat()

        arguments: dict[str, Any] = {"title": title, "priority": priority}
        if due_at:
            arguments["due_at"] = due_at
        return self._tool_call("create_task", arguments)

    def _task_tool(self, name: str, message: str) -> AIResponse:
        return self._tool_call(
            name, {"task_identifier": self._extract_identifier(message)}
        )

    def _update_task(self, message: str) -> AIResponse:
        lower = message.lower()
        arguments: dict[str, Any] = {
            "task_identifier": self._extract_identifier(message)
        }
        if "urgent" in lower:
            arguments["priority"] = "urgent"
        elif "high" in lower:
            arguments["priority"] = "high"
        elif "low" in lower:
            arguments["priority"] = "low"
        return self._tool_call("update_task", arguments)

    @staticmethod
    def _summarise(results: list[dict[str, Any]]) -> str:
        lines: list[str] = []

        for payload in results:
            if not isinstance(payload, dict):
                lines.append("Done.")
                continue

            if payload.get("error"):
                lines.append(str(payload["error"]))
                continue

            if "tasks" in payload:
                tasks = payload["tasks"]
                if not tasks:
                    lines.append("You have no matching tasks.")
                else:
                    lines.append(f"You have {len(tasks)} matching task(s):")
                    lines.extend(
                        f"- {task.get('title')} ({task.get('status')}, "
                        f"{task.get('priority')})"
                        for task in tasks
                    )
                continue

            if payload.get("title"):
                detail = (
                    f"status: {payload.get('status', 'unknown')}, "
                    f"priority: {payload.get('priority', 'medium')}"
                )
                if payload.get("completed_at"):
                    detail += ", completed"
                if payload.get("archived_at"):
                    detail += ", archived"
                lines.append(f'Task "{payload["title"]}" ({detail}).')
                continue

            if payload.get("message"):
                lines.append(str(payload["message"]))
                continue

            if payload.get("total") is not None:
                lines.append(
                    "Summary: "
                    + ", ".join(
                        f"{key}={value}" for key, value in payload.items()
                    )
                )
                continue

            if payload.get("status"):
                lines.append(f"Done: task is now {payload['status']}.")
                continue

            lines.append("Done.")

        return "\n".join(lines)


ai_client = MockGeminiClient() if settings.use_mock else GeminiClient()
