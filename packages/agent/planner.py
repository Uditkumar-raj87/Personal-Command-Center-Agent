from packages.core.models import DailyPlanResponse, PlanningConstraints, Task
from .provider import generate_plan


def generate_agent_plan(tasks: list[Task], constraints: dict) -> DailyPlanResponse:
    planning_constraints = PlanningConstraints.model_validate(constraints)
    _, proposal = generate_plan(tasks, planning_constraints)
    return proposal