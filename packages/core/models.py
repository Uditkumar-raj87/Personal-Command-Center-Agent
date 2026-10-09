from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EnergyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PriorityTag(StrEnum):
    URGENT_IMPORTANT = "urgent_important"
    IMPORTANT = "important"
    ROUTINE = "routine"
    LOW = "low"


class TaskStatus(StrEnum):
    INBOX = "inbox"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CARRIED_OVER = "carried_over"


class TaskSource(StrEnum):
    MANUAL_NOTE = "manual_note"
    WEB_FORM = "web_form"
    INBOX = "inbox"


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1, max_length=240)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_minutes: int = Field(default=30, ge=1, le=1440)
    energy_level: EnergyLevel = EnergyLevel.MEDIUM
    priority_tag: PriorityTag = PriorityTag.ROUTINE
    status: TaskStatus = TaskStatus.INBOX
    source: TaskSource = TaskSource.MANUAL_NOTE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskScheduleProposal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    proposed_start: datetime
    proposed_end: datetime
    reasoning: str = Field(min_length=1)
    conflict_flag: bool = False
    user_approved: bool = False