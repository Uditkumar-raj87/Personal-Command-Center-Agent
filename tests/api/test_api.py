import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

DB_PATH = Path("/tmp") / f"command-center-api-{uuid4()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["LLM_PROVIDER"] = "deterministic"

from fastapi.testclient import TestClient
from services.api.main import app


@pytest.fixture()
def client():
    return TestClient(app)


def create_task(client, title="Integration task"):
    response = client.post("/api/tasks", json={"title": title, "estimated_minutes": 30, "energy_level": "medium", "priority_tag": "important", "source": "web_form"})
    assert response.status_code == 201
    return response.json()


def test_task_crud_and_identity_scope(client):
    task = create_task(client)
    task_id = task["id"]
    assert client.get(f"/api/tasks/{task_id}").status_code == 200
    assert client.patch(f"/api/tasks/{task_id}", json={"title": "Renamed"}).json()["title"] == "Renamed"
    assert client.get("/api/tasks", headers={"X-User-ID": "another-user"}).json() == []
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_plan_lifecycle_edit_approve_and_review(client):
    task = create_task(client, "Finish report")
    plan_response = client.post("/api/plans/generate", json={"date": "2026-10-10", "available_hours": 4, "energy_level": "medium", "task_ids": [task["id"]]})
    assert plan_response.status_code == 200
    plan = plan_response.json()
    plan_id = plan["id"]
    block = plan["proposal"]["planned_blocks"][0]
    edited = {**block, "reasoning": "User reviewed this block"}
    assert client.patch(f"/api/plans/{plan_id}/blocks", json=[edited]).status_code == 200
    assert client.post(f"/api/plans/{plan_id}/review", json=[]).status_code == 409
    approved = client.post(f"/api/plans/{plan_id}/approve")
    assert approved.status_code == 200
    assert client.post(f"/api/plans/{plan_id}/approve").status_code == 200
    reviewed = client.post(f"/api/plans/{plan_id}/review", json=[{"task_id": task["id"], "completed": False, "notes": "Carry to tomorrow"}])
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "COMPLETED"
    assert client.get(f"/api/plans/{plan_id}/audit").json()[-1]["action"] == "reviewed"
    assert client.get(f"/api/tasks/{task['id']}").json()["status"] == "carried_over"


def test_unknown_task_is_rejected(client):
    response = client.post("/api/plans/generate", json={"date": "2026-10-10", "available_hours": 4, "energy_level": "medium", "task_ids": [str(uuid4())]})
    assert response.status_code == 422
