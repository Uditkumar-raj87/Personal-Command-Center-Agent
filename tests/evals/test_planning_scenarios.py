import json
from datetime import datetime, timezone
from pathlib import Path

from packages.core.models import Task
from packages.core.priority import calculate_deterministic_plan


def test_fixtures_preserve_tasks_and_reasoning():
    for fixture_path in Path(__file__).parent.joinpath("fixtures").glob("*.json"):
        fixture = json.loads(fixture_path.read_text())
        tasks = [Task(**item) for item in fixture["tasks"]]
        plan = calculate_deterministic_plan(tasks, datetime(2026, 1, 1, 9, tzinfo=timezone.utc), fixture["available_hours"], "medium")
        assert len(plan) == len(tasks)
        assert all(block.reasoning for block in plan)