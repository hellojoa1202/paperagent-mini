"""The reflection loop must keep the best draft, not merely the last draft."""

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
                {
                    "score": next(scores),
                    "feedback": "보강",
                    "strengths": [],
                    "weaknesses": [],
                }
            )
        return next(drafts)

    return _stub


def test_pipeline_keeps_best_draft_when_revisions_regress(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        workflow,
        "search_arxiv",
        lambda topic, max_results: [_FakePaper()],
    )
    monkeypatch.setattr(
        agents,
        "ask_llm",
        _scripted_llm(
            [
                "- DRAFT1 best 한국어로 작성한 첫 번째 요약이며 충분한 근거와 설명을 포함합니다.",
                "- DRAFT2 worse 한국어로 작성한 두 번째 요약이며 충분한 근거와 설명을 포함합니다.",
                "- DRAFT3 worse 한국어로 작성한 세 번째 요약이며 충분한 근거와 설명을 포함합니다.",
            ],
            [5, 3, 4],
        ),
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
    assert "DRAFT1" in adopted
    assert "DRAFT2" not in adopted
    assert "DRAFT3" not in adopted
