from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    starts_at: datetime
    ends_at: datetime
    description: str | None = None


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    body: str


class CalendarProvider(Protocol):
    def list_events(self, starts_at: datetime, ends_at: datetime) -> list[CalendarEvent]: ...

    def create_event(self, event: CalendarEvent) -> CalendarEvent: ...


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> None: ...
