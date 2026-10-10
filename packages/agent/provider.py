from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packages.core.models import DailyPlanResponse, PlanningConstraints, Task
from packages.core.priority import calculate_deterministic_plan
from packages.core.validation import validate_plan_response

from .prompts import SYSTEM_PROMPT, user_prompt

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    pass


class PlanProvider(Protocol):
    name: str
    model: str | None

    def propose(self, tasks: list[Task], constraints: PlanningConstraints, baseline: DailyPlanResponse) -> DailyPlanResponse: ...


@dataclass(frozen=True)
class ProviderSettings:
    provider: str = "deterministic"
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    timeout_seconds: float = 30
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "ProviderSettings":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "deterministic"),
            api_key=os.getenv("LLM_API_KEY") or None,
            model=os.getenv("LLM_MODEL") or None,
            base_url=os.getenv("LLM_BASE_URL") or None,
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        )


class DeterministicProvider:
    name = "deterministic"
    model = None

    def propose(self, tasks: list[Task], constraints: PlanningConstraints, baseline: DailyPlanResponse) -> DailyPlanResponse:
        return baseline.model_copy(update={"provider": self.name, "fallback_reason": None})


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, settings: ProviderSettings):
        if not settings.api_key or not settings.model or not settings.base_url:
            raise ProviderError("OpenAI-compatible provider requires API key, model, and base URL")
        self.settings = settings
        self.model = settings.model

    def propose(self, tasks: list[Task], constraints: PlanningConstraints, baseline: DailyPlanResponse) -> DailyPlanResponse:
        payload = {
            "model": self.settings.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt([task.model_dump(mode="json") for task in tasks], constraints.model_dump(mode="json"), baseline.model_dump(mode="json"))},
            ],
            "response_format": {"type": "json_object"},
        }
        request = Request(
            self.settings.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            started = time.perf_counter()
            try:
                with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                    body: dict[str, Any] = json.loads(response.read())
                content = body["choices"][0]["message"]["content"]
                result = DailyPlanResponse.model_validate(json.loads(content))
                result = validate_plan_response(result, tasks, constraints)
                logger.info("llm_plan provider=%s model=%s latency_ms=%d fallback=false", self.name, self.model, int((time.perf_counter() - started) * 1000))
                return result.model_copy(update={"provider": self.name, "model": self.model})
            except (HTTPError, URLError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.settings.max_retries:
                    continue
        logger.warning("llm_plan provider=%s model=%s fallback=true reason=%s", self.name, self.model, type(last_error).__name__)
        raise ProviderError("LLM provider failed or returned an invalid plan") from last_error


def create_provider(settings: ProviderSettings | None = None) -> PlanProvider:
    selected = settings or ProviderSettings.from_env()
    if selected.provider.lower() in {"openai", "openai-compatible"}:
        return OpenAICompatibleProvider(selected)
    return DeterministicProvider()


def generate_plan(tasks: list[Task], constraints: PlanningConstraints) -> tuple[DailyPlanResponse, DailyPlanResponse]:
    baseline_blocks = calculate_deterministic_plan(tasks, constraints.available_start, constraints.available_hours, constraints.energy_level.value)
    conflicted = [block.task_id for block in baseline_blocks if block.conflict_flag]
    baseline = DailyPlanResponse(
        day_summary=f"Proposed {len(tasks) - len(conflicted)} of {len(tasks)} tasks.",
        planned_blocks=baseline_blocks,
        deferred_tasks=[],
        conflicted_tasks=[],
        overload_warning="Some tasks need review." if conflicted else None,
        trade_off_rationale="The deterministic baseline preserves estimates and exposes deadline or capacity conflicts.",
    )
    validate_plan_response(baseline, tasks, constraints)
    provider = create_provider()
    try:
        proposal = provider.propose(tasks, constraints, baseline)
    except ProviderError as exc:
        proposal = baseline.model_copy(update={"fallback_reason": str(exc), "provider": "deterministic"})
    return baseline, proposal
