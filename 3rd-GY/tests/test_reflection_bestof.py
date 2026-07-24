"""Offline test: the reflection loop adopts the best-scoring draft, not the last one."""

from __future__ import annotations

import json

import paperagent.agents as agents
import paperagent.workflow as workflow


class _FakePaper:
    title = "Best-of reflection paper"
    summary = "Abstract of the fake paper."
    published = "2024-01-01"
    abs_url = "https://arxiv.org/abs/0000.00000"
    journal_ref = ""
    comment = ""

    def get_short_id(self) -> str:
        return "0000.00000"


def _scripted_llm(reader_drafts, reviewer_scores):
    drafts = iter(reader_drafts)
    scores = iter(reviewer_scores)

    def _stub(system: str, user: str) -> str:
        if "ReviewerAgent" in system:
            return json.dumps(
                {"score": next(scores), "feedback": "보강", "strengths": [], "weaknesses": []}
            )
        return next(drafts)

    return _stub


def test_pipeline_keeps_best_draft_when_revisions_regress(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(workflow, "search_arxiv", lambda topic, max_results: [_FakePaper()])
    # First draft scores best (5); both revisions regress (3, 4). min_score=7 forces 2 revisions.
    monkeypatch.setattr(
        agents,
        "ask_llm",
        _scripted_llm(["- DRAFT1 best", "- DRAFT2 worse", "- DRAFT3 worse"], [5, 3, 4]),
    )

    result = workflow.run_pipeline(
        topic="reflection test",
        max_papers=1,
        output_dir=str(tmp_path),
        enable_prototype=False,
        enable_report=False,
        enable_literature_review=False,
        enable_critic=False,
        read_pdf=False,
    )

    adopted = result.paper_summaries[0].summary
    assert "DRAFT1" in adopted           # best-of kept the first, highest-scoring draft
    assert "DRAFT2" not in adopted
    assert "DRAFT3" not in adopted
