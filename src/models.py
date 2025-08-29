# models.py
import uuid
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field


class User(BaseModel):
    """Модель пользователя с хешированным паролем."""

    id: int
    username: Annotated[str, Field(max_length=30)]
    hashed_password: str


class UserInDB(BaseModel):
    """Модель для данных пользователя, хранящихся в базе данных."""

    id: int
    username: Annotated[str, Field(max_length=30)]
    password: str


class Token(BaseModel):
    """Модель для токена доступа, который возвращается пользователю."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Модель для данных, содержащихся в токене."""

    username: str | None = None


class Task(BaseModel):
    uuid: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4)]
    name: Annotated[str, Field(..., max_length=150)]
    description: Annotated[str, Field(..., max_length=250)]
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone.utc))]
    in_work: Annotated[bool, Field(...)]
    is_finished: Annotated[bool, Field(...)]
    owner: int
