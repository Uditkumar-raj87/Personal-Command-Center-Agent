from datetime import datetime, timedelta

from .models import EnergyLevel, PriorityTag, Task, TaskScheduleProposal


_PRIORITY_WEIGHT = {
    PriorityTag.URGENT_IMPORTANT: 100,
    PriorityTag.IMPORTANT: 70,
    PriorityTag.ROUTINE: 35,
    PriorityTag.LOW: 10,
}


def _score(task: Task, available_start: datetime, focus_energy: str) -> float:
    score = float(_PRIORITY_WEIGHT[task.priority_tag])
    if task.energy_level.value == focus_energy:
        score += 20
    elif task.energy_level == EnergyLevel.HIGH and focus_energy == EnergyLevel.LOW.value:
        score -= 10
    if task.deadline:
        hours_until_due = (task.deadline - available_start).total_seconds() / 3600
        score += max(0, 48 - hours_until_due) * 1.5
    return score


def calculate_deterministic_plan(
    tasks: list[Task],
    available_start: datetime,
    available_hours: float,
    focus_energy: str,
) -> list[TaskScheduleProposal]:
    """Rank and block tasks using only explicit, reproducible rules."""
    ordered = sorted(tasks, key=lambda task: _score(task, available_start, focus_energy), reverse=True)
    cursor = available_start
    budget_end = available_start + timedelta(hours=max(0, available_hours))
    proposals: list[TaskScheduleProposal] = []
    for task in ordered:
        end = cursor + timedelta(minutes=task.estimated_minutes)
        overloaded = end > budget_end
        deadline_conflict = task.deadline is not None and end > task.deadline
        conflict = overloaded or deadline_conflict
        if overloaded:
            reason = "Day overloaded: exceeded available time budget"
        elif deadline_conflict:
            reason = "Scheduled block exceeds the task deadline"
        else:
            reason = f"Priority {task.priority_tag.value}; energy match: {task.energy_level.value == focus_energy}"
        proposals.append(TaskScheduleProposal(
            task_id=task.id,
            proposed_start=cursor,
            proposed_end=end,
            reasoning=reason,
            conflict_flag=conflict,
        ))
        if not conflict:
            cursor = end + timedelta(minutes=10)
    return proposals