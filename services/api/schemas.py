from datetime import datetime

from pydantic import BaseModel, Field

from packages.core.models import EnergyLevel, PriorityTag, TaskSource, TaskStatus


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None
    deadline: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=1440)
    energy_level: EnergyLevel | None = None
    priority_tag: PriorityTag | None = None
    status: TaskStatus | None = None
    source: TaskSource | None = None