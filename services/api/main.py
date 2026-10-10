from __future__ import annotations

import json
from datetime import date, datetime, time, timezone
from enum import StrEnum
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from packages.agent import generate_plan
from packages.core.models import DailyPlanResponse, EnergyLevel, PlanningConstraints, Task, TaskScheduleProposal
from packages.core.validation import validate_plan_response

from .repository import Repository, SessionLocal
from .identity import current_user_id
from .schemas import TaskUpdate

app = FastAPI(title="Personal Command Center API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


class PlanStatus(StrEnum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    EDITED = "EDITED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class PlanRequest(BaseModel):
    planning_date: date = Field(alias="date")
    available_hours: float = Field(gt=0, le=24)
    energy_level: EnergyLevel
    task_ids: list[UUID]
    model_config = ConfigDict(populate_by_name=True)


class BlockUpdate(BaseModel):
    task_id: UUID
    proposed_start: datetime
    proposed_end: datetime
    reasoning: str = Field(min_length=1)
    conflict_flag: bool = False


class ReviewItem(BaseModel):
    task_id: UUID
    completed: bool
    notes: str | None = None


def repository(user_id: str = Depends(current_user_id)):
    session = SessionLocal()
    try:
        yield Repository(session, user_id)
    finally:
        session.close()


def plan_payload(record) -> dict:
    return {"id": record.id, "planning_date": record.planning_date, "status": record.status, "baseline": json.loads(record.baseline_json), "proposal": json.loads(record.proposal_json), "selected": json.loads(record.selected_json) if record.selected_json else None}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "Personal Command Center API", "docs": "/docs", "web": "http://localhost:3000/capture"}


@app.get("/ready")
def ready(repo: Repository = Depends(repository)) -> dict[str, str]:
    repo.tasks()
    return {"status": "ready"}


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task: Task, repo: Repository = Depends(repository)) -> Task:
    return repo.save_task(task)


@app.get("/api/tasks", response_model=list[Task])
def list_tasks(repo: Repository = Depends(repository)) -> list[Task]:
    return repo.tasks()


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: UUID, repo: Repository = Depends(repository)) -> Task:
    task = repo.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


@app.patch("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: UUID, changes: TaskUpdate, repo: Repository = Depends(repository)) -> Task:
    task = repo.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    try:
        updated = Task.model_validate(task.model_copy(update={**changes.model_dump(exclude_unset=True), "updated_at": datetime.now(timezone.utc)}))
    except ValueError as exc:
        raise HTTPException(422, "Invalid task") from exc
    return repo.save_task(updated)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: UUID, repo: Repository = Depends(repository)) -> Response:
    if not repo.delete_task(task_id):
        raise HTTPException(404, "Task not found")
    return Response(status_code=204)


@app.post("/api/plans/generate")
def generate(payload: PlanRequest, repo: Repository = Depends(repository)) -> dict:
    tasks = []
    for task_id in payload.task_ids:
        task = repo.get_task(task_id)
        if task is None:
            raise HTTPException(422, f"Unknown task ID: {task_id}")
        tasks.append(task)
    start = datetime.combine(payload.planning_date, time(9), tzinfo=timezone.utc)
    constraints = PlanningConstraints(planning_date=payload.planning_date, available_start=start, available_hours=payload.available_hours, energy_level=payload.energy_level)
    baseline, proposal = generate_plan(tasks, constraints)
    plan_id = repo.save_plan(payload.planning_date, baseline.model_dump(mode="json"), proposal.model_dump(mode="json"))
    return {"id": plan_id, "baseline": baseline, "proposal": proposal}


@app.get("/api/plans")
def list_plans(repo: Repository = Depends(repository)) -> list[dict]:
    return [plan_payload(record) for record in repo.plans()]


@app.get("/api/plans/{plan_id}")
def get_plan(plan_id: UUID, repo: Repository = Depends(repository)) -> dict:
    record = repo.get_plan(plan_id)
    if record is None:
        raise HTTPException(404, "Plan not found")
    return plan_payload(record)


@app.patch("/api/plans/{plan_id}/blocks")
def edit_blocks(plan_id: UUID, blocks: list[BlockUpdate], repo: Repository = Depends(repository)) -> dict:
    record = repo.get_plan(plan_id)
    if record is None:
        raise HTTPException(404, "Plan not found")
    if record.status in {PlanStatus.APPROVED, PlanStatus.REJECTED, PlanStatus.COMPLETED}:
        raise HTTPException(409, "Plan can no longer be edited")
    proposal = DailyPlanResponse.model_validate(json.loads(record.proposal_json)).model_copy(update={"planned_blocks": [TaskScheduleProposal.model_validate(block.model_dump()) for block in blocks]})
    proposal_ids = {block.task_id for block in proposal.planned_blocks} | set(proposal.deferred_tasks) | set(proposal.conflicted_tasks)
    tasks = [repo.get_task(task_id) for task_id in proposal_ids]
    tasks = [task for task in tasks if task]
    constraints = PlanningConstraints(planning_date=record.planning_date.date(), available_start=datetime.combine(record.planning_date.date(), time(9), tzinfo=timezone.utc), available_hours=24, energy_level=EnergyLevel.MEDIUM)
    try:
        validate_plan_response(proposal, tasks, constraints)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    record.proposal_json = proposal.model_dump_json()
    record.status = PlanStatus.EDITED
    repo.audit(plan_id, "blocks_edited", {"count": len(blocks)})
    repo.session.commit()
    return plan_payload(record)


@app.post("/api/plans/{plan_id}/approve")
def approve(plan_id: UUID, repo: Repository = Depends(repository)) -> dict:
    record = repo.get_plan(plan_id)
    if record is None:
        raise HTTPException(404, "Plan not found")
    if record.status == PlanStatus.APPROVED:
        return plan_payload(record)
    if record.status not in {PlanStatus.GENERATED, PlanStatus.EDITED}:
        raise HTTPException(409, "Only generated or edited plans can be approved")
    record.selected_json = record.proposal_json
    record.status = PlanStatus.APPROVED
    repo.audit(plan_id, "approved", {})
    repo.session.commit()
    return plan_payload(record)


@app.post("/api/plans/{plan_id}/reject")
def reject(plan_id: UUID, repo: Repository = Depends(repository)) -> dict:
    record = repo.get_plan(plan_id)
    if record is None:
        raise HTTPException(404, "Plan not found")
    if record.status == PlanStatus.APPROVED:
        raise HTTPException(409, "Approved plans cannot be rejected")
    record.status = PlanStatus.REJECTED
    repo.audit(plan_id, "rejected", {})
    repo.session.commit()
    return plan_payload(record)


@app.post("/api/plans/{plan_id}/review")
def review(plan_id: UUID, items: list[ReviewItem], repo: Repository = Depends(repository)) -> dict:
    record = repo.get_plan(plan_id)
    if record is None:
        raise HTTPException(404, "Plan not found")
    if record.status != PlanStatus.APPROVED:
        raise HTTPException(409, "Only approved plans can be reviewed")
    for item in items:
        if repo.get_task(item.task_id) is None:
            raise HTTPException(422, "Unknown task ID")
        repo.review(item.task_id, item.completed, item.notes)
    repo.audit(plan_id, "reviewed", {"items": len(items)})
    record.status = PlanStatus.COMPLETED
    repo.session.commit()
    return {**plan_payload(record), "summary": {"completed": sum(item.completed for item in items), "carried_over": sum(not item.completed for item in items)}}


@app.get("/api/plans/{plan_id}/audit")
def audit(plan_id: UUID, repo: Repository = Depends(repository)) -> list[dict]:
    if repo.get_plan(plan_id) is None:
        raise HTTPException(404, "Plan not found")
    return [{"action": item.action, "details": json.loads(item.details), "created_at": item.created_at} for item in repo.logs(plan_id)]
