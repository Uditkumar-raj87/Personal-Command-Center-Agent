from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .models import EnergyLevel, PriorityTag, TaskSource, TaskStatus


class Base(DeclarativeBase):
    pass


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), nullable=False, default="development-user")
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    energy_level: Mapped[EnergyLevel] = mapped_column(Enum(EnergyLevel), nullable=False)
    priority_tag: Mapped[PriorityTag] = mapped_column(Enum(PriorityTag), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False)
    source: Mapped[TaskSource] = mapped_column(Enum(TaskSource), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[UUID] = mapped_column(String(36), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PlanRecord(Base):
    __tablename__ = "plans"

    id: Mapped[UUID] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), nullable=False, default="development-user")
    planning_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    baseline_json: Mapped[str] = mapped_column(Text, nullable=False)
    proposal_json: Mapped[str] = mapped_column(Text, nullable=False)
    selected_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[UUID | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)