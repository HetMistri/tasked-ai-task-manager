"""Gemini function declarations for the task tools.

Gemini receives only these explicit tools. It never gets SQL, shell,
filesystem or arbitrary HTTP access.
"""

from google.genai import types

TASK_IDENTIFIER = {
    "type": "string",
    "description": "Task ID or title used to identify the task",
}

PRIORITIES = ["low", "medium", "high", "urgent"]


def _declaration(
    name: str,
    description: str,
    properties: dict | None = None,
    required: list[str] | None = None,
) -> types.FunctionDeclaration:
    schema: dict = {"type": "object", "properties": properties or {}}
    if required:
        schema["required"] = required
    return types.FunctionDeclaration(
        name=name,
        description=description,
        parameters_json_schema=schema,
    )


DECLARATIONS = [
    _declaration(
        "create_task",
        "Create a task for the authenticated user.",
        {
            "title": {
                "type": "string",
                "description": "Task title (required, max 255 characters)",
            },
            "description": {
                "type": "string",
                "description": "Optional task description",
            },
            "priority": {
                "type": "string",
                "enum": PRIORITIES,
                "description": "Task priority",
            },
            "due_at": {
                "type": "string",
                "description": "Optional due date in ISO 8601 format",
            },
        },
        ["title"],
    ),
    _declaration(
        "search_tasks",
        "Search the user's tasks by title or description. Use '*' to list all tasks.",
        {
            "query": {
                "type": "string",
                "description": "Search text, or '*' for all tasks",
            }
        },
        ["query"],
    ),
    _declaration(
        "update_task",
        "Update an existing task's details.",
        {
            "task_identifier": TASK_IDENTIFIER,
            "title": {"type": "string", "description": "New title"},
            "description": {"type": "string", "description": "New description"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "New status",
            },
            "priority": {
                "type": "string",
                "enum": PRIORITIES,
                "description": "New priority",
            },
            "due_at": {
                "type": "string",
                "description": "New due date in ISO 8601 format",
            },
            "is_archived": {
                "type": "boolean",
                "description": "Archive state",
            },
        },
        ["task_identifier"],
    ),
    _declaration(
        "complete_task",
        "Mark a task as completed.",
        {"task_identifier": TASK_IDENTIFIER},
        ["task_identifier"],
    ),
    _declaration(
        "reopen_task",
        "Reopen a completed task (mark it pending).",
        {"task_identifier": TASK_IDENTIFIER},
        ["task_identifier"],
    ),
    _declaration(
        "set_task_priority",
        "Change the priority of a task.",
        {
            "task_identifier": TASK_IDENTIFIER,
            "priority": {
                "type": "string",
                "enum": PRIORITIES,
                "description": "New priority",
            },
        },
        ["task_identifier", "priority"],
    ),
    _declaration(
        "archive_task",
        "Archive a task without changing its completion status.",
        {"task_identifier": TASK_IDENTIFIER},
        ["task_identifier"],
    ),
    _declaration(
        "restore_task",
        "Restore an archived task.",
        {"task_identifier": TASK_IDENTIFIER},
        ["task_identifier"],
    ),
    _declaration(
        "delete_task",
        "Permanently delete a task. The backend asks the user to confirm first.",
        {"task_identifier": TASK_IDENTIFIER},
        ["task_identifier"],
    ),
    _declaration(
        "get_task_summary",
        "Get counts of the user's tasks by status, priority and overdue state.",
    ),
]

TOOLS = [types.Tool(function_declarations=DECLARATIONS)]

# Tool name to method name on AIService.
TOOL_HANDLERS = {
    "create_task": "handle_create_task",
    "search_tasks": "handle_search_tasks",
    "update_task": "handle_update_task",
    "complete_task": "handle_complete_task",
    "reopen_task": "handle_reopen_task",
    "set_task_priority": "handle_set_priority",
    "archive_task": "handle_archive_task",
    "restore_task": "handle_restore_task",
    "delete_task": "handle_delete_task",
    "get_task_summary": "handle_get_summary",
}
