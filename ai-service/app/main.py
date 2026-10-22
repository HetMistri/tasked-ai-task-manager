"""AI Service main entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as ai_router
from app.clients.task_api import task_api_client
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting AI Service...")
    yield
    logger.info("Shutting down AI Service...")
    await task_api_client.close()


app = FastAPI(
    title="Tasked AI Service",
    description="Natural language task management with Google Gemini",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)


@app.get("/")
async def root():
    return {
        "service": "Tasked AI Service",
        "version": "0.1.0",
        "gemini_enabled": settings.gemini_enabled,
        "gemini_model": settings.gemini_model,
        "mock_mode": settings.use_mock,
    }