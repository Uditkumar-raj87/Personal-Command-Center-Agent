from datetime import datetime

from .contracts import CalendarEvent, CalendarProvider, EmailMessage, EmailProvider


class DisabledCalendarProvider(CalendarProvider):
    def list_events(self, starts_at: datetime, ends_at: datetime) -> list[CalendarEvent]:
        return []

    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        raise RuntimeError("Calendar integration is not configured")


class DisabledEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> None:
        raise RuntimeError("Email integration is not configured")
