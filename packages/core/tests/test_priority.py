from datetime import datetime, timezone

from packages.core.models import EnergyLevel, PriorityTag, Task
from packages.core.priority import calculate_deterministic_plan


def task(title: str, minutes: int = 30, tag: PriorityTag = PriorityTag.ROUTINE) -> Task:
    return Task(title=title, estimated_minutes=minutes, priority_tag=tag, energy_level=EnergyLevel.MEDIUM)


def test_priority_orders_urgent_tasks_first():
    plan = calculate_deterministic_plan(
        [task("routine"), task("urgent", tag=PriorityTag.URGENT_IMPORTANT)],
        datetime(2026, 1, 1, 9, tzinfo=timezone.utc), 2, "medium",
    )
    assert plan[0].task_id != plan[1].task_id
    assert plan[0].reasoning.startswith("Priority urgent_important")


def test_overloaded_tasks_are_flagged_and_explain_budget():
    plan = calculate_deterministic_plan(
        [task("one", 60), task("two", 60)],
        datetime(2026, 1, 1, 9, tzinfo=timezone.utc), 1, "medium",
    )
    assert plan[1].conflict_flag is True
    assert plan[1].reasoning == "Day overloaded: exceeded available time budget"


def test_buffer_is_inserted_between_blocks():
    start = datetime(2026, 1, 1, 9, tzinfo=timezone.utc)
    plan = calculate_deterministic_plan([task("one"), task("two")], start, 2, "medium")
    assert (plan[1].proposed_start - plan[0].proposed_end).total_seconds() == 600