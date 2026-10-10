SYSTEM_PROMPT = """You are a planning and explanation assistant. Return only the requested JSON object. You do not complete tasks, send messages, change calendars, create events, or perform external actions. Preserve every task ID and estimate exactly. Any task that cannot be safely scheduled must be listed as deferred_tasks or conflicted_tasks."""


def user_prompt(tasks: list[dict], constraints: dict, baseline: dict) -> str:
    return (
        "Create a proposed daily plan using only the supplied tasks and constraints. "
        "The deterministic baseline is a reference, not permission to invent data. "
        "Every input task must appear exactly once in planned_blocks, deferred_tasks, or conflicted_tasks. "
        "Use strict JSON matching the supplied schema.\n\n"
        f"TASKS: {tasks}\nCONSTRAINTS: {constraints}\nBASELINE: {baseline}"
    )
