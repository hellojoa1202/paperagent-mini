"""PaperAgent workflow with one consolidated report and an optional prototype."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paperagent.agents import (
    CriticAgent,
    ExperimentReviewerAgent,
    ImpactReviewerAgent,
    MethodExtractionAgent,
    NoveltyReviewerAgent,
    PaperReaderAgent,
    PaperSummary,
    PostdocAgent,
    ProfessorAgent,
    PrototypePlannerAgent,
    PrototypeWriterAgent,
    ReviewerAgent,
    ReviewVerdict,
    write_paper_summaries,
    write_quick_literature_review,
    write_reviewer_feedback,
)
from paperagent.arxiv_tool import read_arxiv_pdf, search_arxiv
from paperagent.config import get_settings


@dataclass(frozen=True)
class PipelineResult:
    topic: str
    output_dir: Path
    paper_count: int
    report_path: Path
    paper_summaries: tuple[PaperSummary, ...] = ()
    prototype_path: Path | None = None


@dataclass(frozen=True)
class _CachedPaper:
    """Minimal arXiv result representation used by UI checkpoint resume."""

    paper_id: str
    title: str
    summary: str
    published: str = ""
    abs_url: str = ""
    journal_ref: str = ""
    comment: str = ""

    def get_short_id(self) -> str:
        return self.paper_id


def run_pipeline(
    topic: str,
    max_papers: int | None = None,
    output_dir: str | None = None,
    enable_prototype: bool = True,
    enable_review: bool = True,
    enable_extra_reviewers: bool = False,
    enable_report: bool = True,
    read_pdf: bool = True,
    enable_literature_review: bool = True,
    enable_critic: bool = True,
    checkpoint_path: str | None = None,
    resume: bool = False,
) -> PipelineResult:
    settings = get_settings()
    max_papers = max_papers or settings.arxiv_max_results
    out_dir = Path(output_dir or settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = Path(checkpoint_path) if checkpoint_path else None
    signature = {
        "topic": topic,
        "max_papers": max_papers,
        "enable_prototype": enable_prototype,
        "enable_review": enable_review,
        "enable_extra_reviewers": enable_extra_reviewers,
        "enable_report": enable_report,
        "read_pdf": read_pdf,
        "enable_literature_review": enable_literature_review,
        "enable_critic": enable_critic,
    }
    state = _load_checkpoint(checkpoint, signature) if resume else None
    if state is None:
        state = {
            "version": 1,
            "signature": signature,
            "completed": [],
            "current_step": "search",
            "papers": [],
            "summaries": [],
            "reviewer_feedbacks": [],
            "pending_summary": None,
        }
        _save_checkpoint(checkpoint, state)

    completed = set(state.get("completed", []))

    reader = PaperReaderAgent(topic=topic)
    reviewer = ReviewerAgent()

    if "search" in completed:
        papers = [_CachedPaper(**paper) for paper in state.get("papers", [])]
        print(f"[1] Resuming with {len(papers)} cached arXiv results")
    else:
        _checkpoint_step(checkpoint, state, "search")
        print(f"[1] Searching arXiv directly for: {topic}")
        papers = search_arxiv(topic, max_results=max_papers)
        state["papers"] = [_paper_to_checkpoint(paper) for paper in papers]
        _complete_checkpoint_step(checkpoint, state, "search")
        completed.add("search")

    summaries = [_summary_from_checkpoint(item) for item in state.get("summaries", [])]
    reviewer_feedbacks = [
        (_summary_from_checkpoint(item["summary"]), _verdict_from_checkpoint(item["verdict"]))
        for item in state.get("reviewer_feedbacks", [])
    ]

    if "paper_review" not in completed:
        for zero_index in range(len(summaries), len(papers)):
            paper = papers[zero_index]
            index = zero_index + 1
            if read_pdf:
                _checkpoint_step(checkpoint, state, "paper_reader")
                print(f"[2] Reading paper {index}/{len(papers)}: {paper.title}")
                full_text = read_arxiv_pdf(paper, out_dir)
            else:
                full_text = f"arXiv abstract only:\n{paper.summary}"
                print(f"[2] Using arXiv abstract for paper {index}/{len(papers)}: {paper.title}")

            pending = state.get("pending_summary")
            if pending and pending.get("paper_id") == paper.get_short_id():
                summary = _summary_from_checkpoint(pending)
                print(f"[3] Resuming cached PaperReaderAgent summary {index}/{len(papers)}")
            else:
                _checkpoint_step(checkpoint, state, "paper_reader")
                print(f"[3] PaperReaderAgent summarizing paper {index}/{len(papers)}")
                summary = reader.summarize_paper(paper, full_text)
                state["pending_summary"] = _summary_to_checkpoint(summary)
                _save_checkpoint(checkpoint, state)

            if enable_review:
                _checkpoint_step(checkpoint, state, "reviewer")
                print(f"[4] ReviewerAgent checking summary {index}/{len(papers)}")
                verdict = reviewer.review_summary(summary, full_text)
                rounds_used = summary.revision_round
                while (
                    verdict.score < settings.min_review_score
                    and rounds_used < settings.max_revision_rounds
                ):
                    rounds_used += 1
                    print(
                        f"[4] score {verdict.score} < {settings.min_review_score}; "
                        f"revising {rounds_used}/{settings.max_revision_rounds}"
                    )
                    _checkpoint_step(checkpoint, state, "paper_reader")
                    summary = reader.summarize_paper(
                        paper,
                        full_text,
                        revision_round=rounds_used,
                        reviewer_feedback=verdict.feedback,
                    )
                    state["pending_summary"] = _summary_to_checkpoint(summary)
                    _save_checkpoint(checkpoint, state)
                    _checkpoint_step(checkpoint, state, "reviewer")
                    verdict = reviewer.review_summary(summary, full_text)
                reviewer_feedbacks.append((summary, verdict))

            summaries.append(summary)
            state["summaries"] = [_summary_to_checkpoint(item) for item in summaries]
            state["reviewer_feedbacks"] = [
                {
                    "summary": _summary_to_checkpoint(item),
                    "verdict": _verdict_to_checkpoint(verdict),
                }
                for item, verdict in reviewer_feedbacks
            ]
            state["pending_summary"] = None
            _save_checkpoint(checkpoint, state)

        _complete_checkpoint_step(checkpoint, state, "paper_review")
        completed.add("paper_review")

    reviewer_feedback_text = (
        write_reviewer_feedback(reviewer_feedbacks) if reviewer_feedbacks else ""
    )
    if "literature_review" in completed:
        literature_review = str(state.get("literature_review", ""))
    else:
        _checkpoint_step(checkpoint, state, "postdoc_critic")
        print("[5] PostdocAgent writing literature review")
        if enable_literature_review:
            literature_review = PostdocAgent().write_literature_review(
                topic=topic,
                summaries=summaries,
                reviewer_feedback=reviewer_feedback_text,
            )
        else:
            literature_review = write_quick_literature_review(topic, summaries)
        state["literature_review"] = literature_review
        _complete_checkpoint_step(checkpoint, state, "literature_review")
        completed.add("literature_review")

    critic_text = str(state.get("critic_text", ""))
    if "critic" not in completed:
        if enable_critic and enable_literature_review:
            _checkpoint_step(checkpoint, state, "postdoc_critic")
            print("[6] CriticAgent reviewing blind spots")
            critic_text = CriticAgent().critique(topic, literature_review)
        state["critic_text"] = critic_text
        _complete_checkpoint_step(checkpoint, state, "critic")
        completed.add("critic")

    extra_reviews = [tuple(item) for item in state.get("extra_reviews", [])]
    if "extra_reviews" not in completed:
        if enable_extra_reviewers:
            _checkpoint_step(checkpoint, state, "postdoc_critic")
            print("[7] Running Experiment/Novelty/Impact reviewers")
            extra_reviews = [
                ("Experiment Review", ExperimentReviewerAgent().review(topic, literature_review)),
                ("Novelty Review", NoveltyReviewerAgent().review(topic, literature_review)),
                ("Impact Review", ImpactReviewerAgent().review(topic, literature_review)),
            ]
        state["extra_reviews"] = extra_reviews
        _complete_checkpoint_step(checkpoint, state, "extra_reviews")
        completed.add("extra_reviews")

    method_text = ""
    plan_text = ""
    prototype_guide = ""
    prototype_path: Path | None = None
    if enable_prototype and "prototype" not in completed:
        _checkpoint_step(checkpoint, state, "prototype")
        print("[8] Extracting methods and planning implementation")
        method_text = MethodExtractionAgent().extract_implementable_method(topic, summaries)
        plan_text = PrototypePlannerAgent().write_implementation_plan(topic, method_text)

        print("[9] PrototypeWriterAgent writing prototype.py")
        writer = PrototypeWriterAgent()
        prototype_path = out_dir / "prototype.py"
        prototype_path.write_text(
            writer.generate_prototype_code(topic, plan_text),
            encoding="utf-8",
        )
        prototype_guide = writer.write_prototype_readme(topic, plan_text)
        state.update(
            method_text=method_text,
            plan_text=plan_text,
            prototype_guide=prototype_guide,
            prototype_path=str(prototype_path),
        )
        _complete_checkpoint_step(checkpoint, state, "prototype")
        completed.add("prototype")
    elif enable_prototype:
        method_text = str(state.get("method_text", ""))
        plan_text = str(state.get("plan_text", ""))
        prototype_guide = str(state.get("prototype_guide", ""))
        saved_path = state.get("prototype_path")
        prototype_path = Path(str(saved_path)) if saved_path else None

    professor_text = str(state.get("professor_text", ""))
    if enable_report and "professor" not in completed:
        _checkpoint_step(checkpoint, state, "report")
        print("[10] ProfessorAgent writing final synthesis")
        professor_text = ProfessorAgent().write_project_report(
            topic=topic,
            literature_review=literature_review,
            method_text=method_text,
            implementation_plan=plan_text,
            extra_reviews="\n\n".join(text for _, text in extra_reviews),
        )
        state["professor_text"] = professor_text
        _complete_checkpoint_step(checkpoint, state, "professor")
        completed.add("professor")

    _checkpoint_step(checkpoint, state, "report")
    report_text = _build_research_report(
        topic=topic,
        summaries=summaries,
        reviewer_feedback=reviewer_feedback_text,
        literature_review=literature_review,
        critic_review=critic_text,
        extra_reviews=extra_reviews,
        method_text=method_text,
        plan_text=plan_text,
        prototype_guide=prototype_guide,
        professor_text=professor_text,
        prototype_path=prototype_path,
    )
    report_path = out_dir / "research_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    _complete_checkpoint_step(checkpoint, state, "complete")

    return PipelineResult(
        topic=topic,
        output_dir=out_dir,
        paper_count=len(summaries),
        report_path=report_path,
        paper_summaries=tuple(summaries),
        prototype_path=prototype_path,
    )


def _paper_to_checkpoint(paper: Any) -> dict[str, str]:
    return {
        "paper_id": paper.get_short_id(),
        "title": str(paper.title),
        "summary": str(paper.summary),
        "published": str(getattr(paper, "published", "")),
        "abs_url": str(getattr(paper, "abs_url", "")),
        "journal_ref": str(getattr(paper, "journal_ref", "") or ""),
        "comment": str(getattr(paper, "comment", "") or ""),
    }


def _summary_to_checkpoint(summary: PaperSummary) -> dict[str, Any]:
    return {
        "paper_id": summary.paper_id,
        "title": summary.title,
        "abstract": summary.abstract,
        "summary": summary.summary,
        "published": str(summary.published),
        "paper_url": summary.paper_url,
        "venue": summary.venue,
        "revision_round": summary.revision_round,
    }


def _summary_from_checkpoint(data: dict[str, Any]) -> PaperSummary:
    return PaperSummary(**data)


def _verdict_to_checkpoint(verdict: ReviewVerdict) -> dict[str, Any]:
    return {
        "score": verdict.score,
        "feedback": verdict.feedback,
        "strengths": list(verdict.strengths),
        "weaknesses": list(verdict.weaknesses),
    }


def _verdict_from_checkpoint(data: dict[str, Any]) -> ReviewVerdict:
    return ReviewVerdict(
        score=int(data["score"]),
        feedback=str(data["feedback"]),
        strengths=tuple(data.get("strengths", [])),
        weaknesses=tuple(data.get("weaknesses", [])),
    )


def _load_checkpoint(path: Path | None, signature: dict[str, Any]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return state if state.get("signature") == signature else None


def _save_checkpoint(path: Path | None, state: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _checkpoint_step(path: Path | None, state: dict[str, Any], step: str) -> None:
    state["current_step"] = step
    _save_checkpoint(path, state)


def _complete_checkpoint_step(path: Path | None, state: dict[str, Any], step: str) -> None:
    completed = state.setdefault("completed", [])
    if step not in completed:
        completed.append(step)
    state["current_step"] = step
    _save_checkpoint(path, state)


def _build_research_report(
    *,
    topic: str,
    summaries: list[PaperSummary],
    reviewer_feedback: str,
    literature_review: str,
    critic_review: str,
    extra_reviews: list[tuple[str, str]],
    method_text: str,
    plan_text: str,
    prototype_guide: str,
    professor_text: str,
    prototype_path: Path | None,
) -> str:
    sections = [
        "# PaperAgent Research Report",
        f"- **Research topic**: {topic}",
        f"- **Paper count**: {len(summaries)}",
        "## 1. Paper Summaries",
        write_paper_summaries(summaries),
    ]

    if reviewer_feedback:
        sections.extend(["## 2. Summary Quality Review", reviewer_feedback])

    sections.extend(["## 3. Literature Review", literature_review])

    if critic_review:
        sections.extend(["## 4. Critical Review", critic_review])

    if extra_reviews:
        sections.append("## 5. Specialized Reviews")
        for title, text in extra_reviews:
            sections.extend([f"### {title}", text])

    if method_text or plan_text:
        sections.append("## 6. Implementation")
        if method_text:
            sections.extend(["### Extracted Methods", method_text])
        if plan_text:
            sections.extend(["### Implementation Plan", plan_text])
        if prototype_guide:
            sections.extend(["### Prototype Guide", prototype_guide])
        if prototype_path:
            sections.append(f"- Generated code: `{prototype_path.name}`")

    if professor_text:
        sections.extend(["## 7. Final Synthesis", professor_text])

    return "\n\n".join(section.strip() for section in sections if section.strip()) + "\n"
