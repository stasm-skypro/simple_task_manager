# models.py
import uuid
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field


class Tasks(BaseModel):
    uuid: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4)]
    name: Annotated[str, Field(..., max_length=30)]
    description: Annotated[str, Field(..., max_length=150)]
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone.utc))]
    in_work: Annotated[bool, Field(...)]
    is_finished: Annotated[bool, Field(...)]
