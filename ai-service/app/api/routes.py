"""AI Service API routes."""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from app.services.ai import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    response: str
    requires_confirmation: bool = False
    confirmation_id: str | None = None
    confirmation_details: dict | None = None
    is_mock: bool = False


class ConfirmRequest(BaseModel):
    confirmation_id: str
    confirmed: bool


class ConfirmResponse(BaseModel):
    success: bool
    message: str
    task_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    gemini: dict
    task_api: dict


async def get_auth_token(authorization: str = Header(...)) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return authorization[7:]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, token: str = Depends(get_auth_token)):
    """Process a natural language task request."""
    result = await ai_service.process_message(request.message, token)
    return ChatResponse(**result)


@router.post("/actions/{confirmation_id}/confirm", response_model=ConfirmResponse)
async def confirm_action(confirmation_id: str, request: ConfirmRequest, token: str = Depends(get_auth_token)):
    """Confirm or cancel a pending AI action."""
    if confirmation_id != request.confirmation_id:
        raise HTTPException(status_code=400, detail="Confirmation ID mismatch")
    result = await ai_service.confirm_action(confirmation_id, request.confirmed, token)
    return ConfirmResponse(**result)


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return await ai_service.health_check()