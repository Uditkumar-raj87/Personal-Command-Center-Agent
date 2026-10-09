from uuid import UUID

from pydantic import BaseModel, Field

from packages.core.models import Task, TaskScheduleProposal
from packages.core.priority import calculate_deterministic_plan


class DailyPlanResponse(BaseModel):
    day_summary: str
    planned_blocks: list[TaskScheduleProposal]
    overload_warning: str | None = None
    deferred_tasks: list[UUID] = Field(default_factory=list)
    trade_off_rationale: str


def generate_agent_plan(tasks: list[Task], constraints: dict) -> DailyPlanResponse:
    """Provider-neutral structured planner fallback; an SDK adapter can replace this body."""
    baseline = calculate_deterministic_plan(
        tasks,
        constraints["available_start"],
        constraints["available_hours"],
        constraints.get("energy_level", "medium"),
    )
    deferred = [block.task_id for block in baseline if block.conflict_flag]
    return DailyPlanResponse(
        day_summary=f"Proposed {len(tasks) - len(deferred)} of {len(tasks)} tasks with explicit conflicts.",
        planned_blocks=baseline,
        overload_warning="Some tasks exceed the available budget." if deferred else None,
        deferred_tasks=deferred,
        trade_off_rationale="The structured planner preserves every task and exposes baseline conflicts for human review.",
    )