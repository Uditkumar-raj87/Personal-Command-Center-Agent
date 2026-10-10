from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from packages.agent.provider import generate_plan
from packages.core.models import PlanningConstraints, Task
from packages.core.validation import validate_plan_response


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "evals" / "fixtures"
REPORTS = ROOT / "reports" / "evaluations"


def build_report(fixture_path: Path) -> dict:
    fixture = json.loads(fixture_path.read_text())
    tasks = [Task.model_validate(item) for item in fixture["tasks"]]
    planning_date = datetime(2026, 1, 1, 9, tzinfo=timezone.utc)
    constraints = PlanningConstraints(
        planning_date=planning_date.date(),
        available_start=planning_date,
        available_hours=fixture["available_hours"],
        energy_level="medium",
    )
    baseline, provider_response = generate_plan(tasks, constraints)
    validation_error = None
    try:
        validate_plan_response(provider_response, tasks, constraints)
        validation = "passed"
    except ValueError as exc:
        validation = "failed"
        validation_error = str(exc)
    approved = provider_response.model_copy(update={"planned_blocks": provider_response.planned_blocks})
    score = len(approved.planned_blocks) / len(tasks) if tasks else 1.0
    return {
        "fixture": fixture_path.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_tasks": [task.model_dump(mode="json") for task in tasks],
        "deterministic_baseline": baseline.model_dump(mode="json"),
        "provider_response": provider_response.model_dump(mode="json"),
        "validation": {"status": validation, "error": validation_error},
        "fallback_reason": provider_response.fallback_reason,
        "final_user_approved_plan": approved.model_dump(mode="json"),
        "evaluation": {"accounted_task_ratio": score, "passed": validation == "passed" and score == 1.0},
    }


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    for fixture_path in sorted(FIXTURES.glob("*.json")):
        report_path = REPORTS / f"{fixture_path.stem}.json"
        report_path.write_text(json.dumps(build_report(fixture_path), indent=2) + "\n")
        print(report_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
