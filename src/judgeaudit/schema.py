"""Data shapes shared by every task, judge and metric."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Case:
    """One thing the judge is asked to grade.

    A case is derived from a base item (one question with a known answer) by
    changing exactly one property, so that any change in the judge's verdict
    between two cases of the same item can be attributed to that property.
    """

    case_id: str
    item_id: str
    task: str
    mode: str  # "pointwise" (grade one answer) | "pairwise" (pick A or B)
    variant: str  # e.g. "correct_terse", "wrong_fluent", "pair_cw_AB"
    split: str  # "dev" (tune on this) | "heldout" (report on this)
    question: str
    answer: str = ""
    answer_a: str = ""
    answer_b: str = ""
    reference: str = ""
    # pointwise: "correct" | "incorrect"; pairwise: "A" | "B" | "" (no ground truth)
    expected: str = ""
    meta: dict = field(default_factory=dict)
