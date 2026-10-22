#!/usr/bin/env bash
# End-to-end smoke test for Tasked: AI Enabled Task Manager.
# Requires the full stack to be running on http://localhost:5173.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:5173}"
EMAIL="smoke-$(date +%s)@example.com"
PASSWORD="correct-horse-battery"

json() {
  python3 -c "import json,sys; print(json.load(sys.stdin)$1)"
}

echo "1. Registering $EMAIL"
TOKEN=$(curl -fsS -X POST "$BASE_URL/api/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"display_name\":\"Smoke Test\"}" \
  | json "['access_token']")

AUTH="Authorization: Bearer $TOKEN"

echo "2. Creating a task manually"
TASK_ID=$(curl -fsS -X POST "$BASE_URL/api/tasks" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"title":"Smoke test task","priority":"high"}' \
  | json "['id']")
echo "   task: $TASK_ID"

echo "3. Listing tasks"
TOTAL=$(curl -fsS "$BASE_URL/api/tasks" -H "$AUTH" | json "['total']")
[ "$TOTAL" -ge 1 ] || { echo "FAIL: task list is empty"; exit 1; }
echo "   total: $TOTAL"

echo "4. Asking the AI to create a task"
AI_RESPONSE=$(curl -fsS -X POST "$BASE_URL/ai/chat" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"message":"Create a high-priority DBMS assignment due Friday"}')
echo "   $(echo "$AI_RESPONSE" | json "['response']")"
echo "   mock: $(echo "$AI_RESPONSE" | json "['is_mock']")"

echo "5. Asking the AI to delete the smoke task (confirmation flow)"
CONFIRM=$(curl -fsS -X POST "$BASE_URL/ai/chat" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"message":"Delete my Smoke test task"}')
echo "   $(echo "$CONFIRM" | json "['response']")"
CONFIRM_ID=$(echo "$CONFIRM" | json "['confirmation_id']")
[ "$CONFIRM_ID" != "None" ] || { echo "FAIL: no confirmation id"; exit 1; }

echo "6. Confirming deletion"
curl -fsS -X POST "$BASE_URL/ai/actions/$CONFIRM_ID/confirm" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"confirmation_id\":\"$CONFIRM_ID\",\"confirmed\":true}" \
  | json "['message']"

echo "7. Verifying the task is gone"
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/api/tasks/$TASK_ID" -H "$AUTH")
[ "$STATUS" = "404" ] || { echo "FAIL: deleted task still returns $STATUS"; exit 1; }

echo "PASS: manual CRUD and AI function calling flow completed"
