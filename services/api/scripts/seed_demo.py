import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from packages.core.models import EnergyLevel, PriorityTag, Task

api_url = os.getenv("API_URL", "http://localhost:8000")
for index in range(15):
    task = Task(title=f"Demo task {index + 1}", estimated_minutes=30 + (index % 4) * 15, energy_level=EnergyLevel(("low", "medium", "high")[index % 3]), priority_tag=PriorityTag.URGENT_IMPORTANT if index < 2 else PriorityTag.ROUTINE, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    request = Request(f"{api_url}/api/tasks", data=json.dumps(task.model_dump(mode="json")).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request) as response:
        response.read()
print("Seeded 15 synthetic tasks")