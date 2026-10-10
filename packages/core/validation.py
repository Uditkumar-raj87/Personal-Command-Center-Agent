from datetime import datetime
from typing import Any

from pydantic import ValidationError

from .models import DailyPlanResponse, PlanningConstraints, Task


UNSUPPORTED_ACTIONS = (
    "sent a message",
    "changed the calendar",
    "updated the calendar",
    "completed the task",
    "performed the action",
    "sent an email",
    "created an event",
)


def validate_plan_response(
    response: DailyPlanResponse | dict[str, Any],
    tasks: list[Task],
    constraints: PlanningConstraints,
) -> DailyPlanResponse:
    try:
        plan = response if isinstance(response, DailyPlanResponse) else DailyPlanResponse.model_validate(response)
    except ValidationError as exc:
        raise ValueError("Plan response is not valid structured data") from exc

    task_by_id = {task.id: task for task in tasks}
    input_ids = set(task_by_id)
    block_ids = [block.task_id for block in plan.planned_blocks]
    accounted_ids = block_ids + plan.deferred_tasks + plan.conflicted_tasks
    if len(accounted_ids) != len(set(accounted_ids)):
        raise ValueError("Each task may be accounted for only once")
    if set(accounted_ids) != input_ids:
        raise ValueError("Every submitted task must be planned, deferred, or explicitly conflicted")
    if any(task_id not in input_ids for task_id in accounted_ids):
        raise ValueError("Plan contains an unknown task ID")
    if set(plan.deferred_tasks) & set(plan.conflicted_tasks):
        raise ValueError("A task cannot be both deferred and conflicted")

    previous_end: datetime | None = None
    for block in plan.planned_blocks:
        task = task_by_id[block.task_id]
        if block.proposed_end <= block.proposed_start:
            raise ValueError("Block end must be after block start")
        if previous_end is not None and block.proposed_start < previous_end and not block.conflict_flag:
            raise ValueError("Plan contains a silent overlap")
        if not block.conflict_flag and block.proposed_start < constraints.available_start:
            raise ValueError("Block starts outside the planning window")
        if not block.conflict_flag and block.proposed_end > constraints.available_end:
            raise ValueError("Block ends outside the planning window")
        duration = (block.proposed_end - block.proposed_start).total_seconds() / 60
        if not block.conflict_flag and duration < task.estimated_minutes:
            raise ValueError("A block may not shorten a task estimate")
        if not block.conflict_flag and task.deadline and block.proposed_end > task.deadline:
            raise ValueError("A block may not pass a hard deadline without a conflict")
        if not block.reasoning.strip():
            raise ValueError("Every block requires reasoning")
        previous_end = max(previous_end or block.proposed_end, block.proposed_end)

    combined_text = " ".join((plan.day_summary, plan.trade_off_rationale, plan.overload_warning or "")).lower()
    if any(action in combined_text for action in UNSUPPORTED_ACTIONS):
        raise ValueError("Plan contains an unsupported external action claim")
    if not plan.trade_off_rationale.strip():
        raise ValueError("Trade-off rationale is required")
    return plan