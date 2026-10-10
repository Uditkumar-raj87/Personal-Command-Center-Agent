from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from packages.agent.provider import DeterministicProvider, ProviderSettings, create_provider
from packages.core.models import DailyPlanResponse, EnergyLevel, PlanningConstraints, Task, TaskScheduleProposal
from packages.core.validation import validate_plan_response


def context():
    task = Task(id=uuid4(), title="Write brief", estimated_minutes=30)
    constraints = PlanningConstraints(planning_date=date(2026, 1, 1), available_start=datetime(2026, 1, 1, 9, tzinfo=timezone.utc), available_hours=2, energy_level=EnergyLevel.MEDIUM)
    return task, constraints


def test_factory_defaults_to_deterministic():
    assert isinstance(create_provider(ProviderSettings()), DeterministicProvider)


def test_validator_rejects_unknown_task():
    task, constraints = context()
    response = DailyPlanResponse(day_summary="x", planned_blocks=[TaskScheduleProposal(task_id=uuid4(), proposed_start=constraints.available_start, proposed_end=constraints.available_start.replace(hour=9, minute=30), reasoning="x")], trade_off_rationale="x")
    with pytest.raises(ValueError, match="Every submitted task"):
        validate_plan_response(response, [task], constraints)


def test_validator_rejects_shortened_estimate():
    task, constraints = context()
    response = DailyPlanResponse(day_summary="x", planned_blocks=[TaskScheduleProposal(task_id=task.id, proposed_start=constraints.available_start, proposed_end=constraints.available_start.replace(hour=9, minute=15), reasoning="x")], trade_off_rationale="x")
    with pytest.raises(ValueError, match="shorten"):
        validate_plan_response(response, [task], constraints)
