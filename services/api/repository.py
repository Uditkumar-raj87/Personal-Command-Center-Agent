from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from packages.core.db_models import AuditRecord, Base, PlanRecord, ReviewLog, TaskRecord
from packages.core.models import Task


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./command_center.db")


engine = create_engine(_database_url(), connect_args={"check_same_thread": False} if _database_url().startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class Repository:
    def __init__(self, session: Session, owner_id: str):
        self.session = session
        self.owner_id = owner_id

    def tasks(self) -> list[Task]:
        return [Task.model_validate(record, from_attributes=True) for record in self.session.scalars(select(TaskRecord).where(TaskRecord.owner_id == self.owner_id).order_by(TaskRecord.created_at.desc())).all()]

    def get_task(self, task_id: UUID) -> Task | None:
        record = self.session.scalar(select(TaskRecord).where(TaskRecord.id == str(task_id), TaskRecord.owner_id == self.owner_id))
        return Task.model_validate(record, from_attributes=True) if record else None

    def save_task(self, task: Task) -> Task:
        record = self.session.scalar(select(TaskRecord).where(TaskRecord.id == str(task.id), TaskRecord.owner_id == self.owner_id))
        values = task.model_dump()
        values["id"] = str(task.id)
        if record is None:
            self.session.add(TaskRecord(**values, owner_id=self.owner_id))
        else:
            for key, value in values.items():
                setattr(record, key, value)
        self.session.commit()
        return task

    def delete_task(self, task_id: UUID) -> bool:
        record = self.session.scalar(select(TaskRecord).where(TaskRecord.id == str(task_id), TaskRecord.owner_id == self.owner_id))
        if record is None:
            return False
        self.session.delete(record)
        self.session.commit()
        return True

    def save_plan(self, planning_date: datetime, baseline: dict, proposal: dict) -> UUID:
        plan_id = uuid4()
        now = datetime.now(timezone.utc)
        plan_timestamp = planning_date if isinstance(planning_date, datetime) else datetime.combine(planning_date, datetime.min.time(), tzinfo=timezone.utc)
        self.session.add(PlanRecord(id=str(plan_id), owner_id=self.owner_id, planning_date=plan_timestamp, status="GENERATED", baseline_json=json.dumps(baseline), proposal_json=json.dumps(proposal), created_at=now, updated_at=now))
        self.audit(plan_id, "generated", {"provider": proposal.get("provider", "deterministic")})
        self.session.commit()
        return plan_id

    def get_plan(self, plan_id: UUID) -> PlanRecord | None:
        return self.session.scalar(select(PlanRecord).where(PlanRecord.id == str(plan_id), PlanRecord.owner_id == self.owner_id))

    def plans(self) -> list[PlanRecord]:
        return list(self.session.scalars(select(PlanRecord).where(PlanRecord.owner_id == self.owner_id).order_by(PlanRecord.created_at.desc())).all())

    def audit(self, plan_id: UUID | None, action: str, details: dict) -> None:
        self.session.add(AuditRecord(plan_id=str(plan_id) if plan_id else None, owner_id=self.owner_id, action=action, details=json.dumps(details), created_at=datetime.now(timezone.utc)))

    def logs(self, plan_id: UUID) -> list[AuditRecord]:
        return list(self.session.scalars(select(AuditRecord).where(AuditRecord.plan_id == str(plan_id), AuditRecord.owner_id == self.owner_id).order_by(AuditRecord.created_at)).all())

    def review(self, task_id: UUID, completed: bool, notes: str | None, commit: bool = True) -> None:
        task = self.session.scalar(select(TaskRecord).where(TaskRecord.id == str(task_id), TaskRecord.owner_id == self.owner_id))
        if task:
            task.status = "COMPLETED" if completed else "CARRIED_OVER"
            task.updated_at = datetime.now(timezone.utc)
            self.session.add(ReviewLog(task_id=str(task_id), owner_id=self.owner_id, completed=completed, notes=notes, created_at=datetime.now(timezone.utc)))
            if commit:
                self.session.commit()