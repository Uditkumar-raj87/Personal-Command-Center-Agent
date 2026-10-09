from datetime import date, datetime, time, timezone
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.agent import generate_agent_plan
from packages.core.models import Task, TaskStatus
from packages.core.priority import calculate_deterministic_plan

app = FastAPI(title="Personal Command Center API", version="0.1.0")
TASKS: dict[UUID, Task] = {}


class PlanRequest(BaseModel):
    date: date
    available_hours: float = Field(gt=0, le=24)
    energy_level: str
    task_ids: list[UUID]


class ReviewItem(BaseModel):
    task_id: UUID
    completed: bool
    notes: str | None = None


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task: Task) -> Task:
    TASKS[task.id] = task
    return task


@app.get("/api/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return list(TASKS.values())


@app.post("/api/plans/generate")
def generate_plan(payload: PlanRequest) -> dict:
    tasks = [TASKS[task_id] for task_id in payload.task_ids if task_id in TASKS]
    start = datetime.combine(payload.date, time(9), tzinfo=timezone.utc)
    baseline = calculate_deterministic_plan(tasks, start, payload.available_hours, payload.energy_level)
    try:
        agent = generate_agent_plan(tasks, {"available_start": start, "available_hours": payload.available_hours, "energy_level": payload.energy_level})
    except Exception as exc:
        raise HTTPException(status_code=422, detail={"message": "Structured plan validation failed", "baseline": [item.model_dump(mode="json") for item in baseline]}) from exc
    return {"baseline": baseline, "agent": agent}


@app.post("/api/plans/review")
def review_plan(items: list[ReviewItem]) -> dict:
    completed = 0
    carried_over = 0
    for item in items:
        task = TASKS.get(item.task_id)
        if task is None:
            continue
        if item.completed:
            task.status = TaskStatus.COMPLETED
            completed += 1
        else:
            task.status = TaskStatus.CARRIED_OVER
            carried_over += 1
    return {"summary": f"Completed {completed}; carried over {carried_over}.", "completed": completed, "carried_over": carried_over}