"""Authentication service."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token


class AuthService:
    """Authentication service for user management and JWT handling."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def hash_password(self, password: str) -> str:
        """Hash a password with bcrypt (the schema caps input at 72 bytes)."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False

    def create_access_token(self, user_id: UUID) -> str:
        """Create JWT access token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        to_encode = {"sub": str(user_id), "exp": expire}
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def decode_token(self, token: str) -> Optional[UUID]:
        """Decode JWT token and return user ID."""
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id_str = payload.get("sub")
            if user_id_str:
                return UUID(user_id_str)
        except Exception:
            pass
        return None

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user."""
        # Check if email already exists
        existing = await self.session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=user_data.email,
            password_hash=self.hash_password(user_data.password),
            display_name=user_data.display_name,
            timezone=user_data.timezone,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def login(self, credentials: UserLogin) -> Token:
        """Authenticate user and return token."""
        result = await self.session.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid email or password")

        token = self.create_access_token(user.id)
        return Token(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_response(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user response by ID."""
        user = await self.get_user(user_id)
        if user:
            return UserResponse.model_validate(user)
        return None


async def get_auth_service(session: AsyncSession) -> AuthService:
    """Dependency injection for AuthService."""
    return AuthService(session)