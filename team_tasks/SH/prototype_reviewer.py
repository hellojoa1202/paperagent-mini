"""Validate a generated prototype and optionally ask one Agent to repair it."""

from __future__ import annotations

from paperagent.agents import PrototypeReviewerAgent
from paperagent.workflow import PrototypeReview, validate_code


def review_and_repair(code: str, *, execute: bool, max_repairs: int = 1) -> tuple[str, list[PrototypeReview]]:
    reviews: list[PrototypeReview] = []
    current = code
    reviewer = PrototypeReviewerAgent()
    for attempt in range(max_repairs + 1):
        review = validate_code(current, execute=execute)
        reviews.append(review)
        if review.passed or attempt == max_repairs:
            break
        current = reviewer.repair(current, review)
    return current, reviews

