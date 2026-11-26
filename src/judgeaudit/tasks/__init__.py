"""Task registry. A task is a function (suite_path, reference) -> list[Case].

To add a task (code, summarisation, ...), write a module with a build_cases
function that returns Case objects with known ground truth, and register it here.
"""
from __future__ import annotations

from ..schema import Case
from . import qa

TASKS = {"qa": qa.build_cases}


def load_cases(task: str, suite: str, reference: str = "none") -> list[Case]:
    if task not in TASKS:
        raise ValueError(f"unknown task {task!r}; available: {sorted(TASKS)}")
    return TASKS[task](suite, reference)
