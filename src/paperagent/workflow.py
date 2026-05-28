"""Merged workflow from GY/SH 1st and 2nd folder assignments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paperagent.agents import (
    MethodExtractionAgent,
    PaperReaderAgent,
    PaperSummary,
    PrototypePlannerAgent,
    PrototypeWriterAgent,
    write_paper_summaries,
)
from paperagent.arxiv_tool import read_arxiv_pdf, search_arxiv
from paperagent.config import get_settings


@dataclass
class PipelineResult:
    topic: str
    output_dir: Path
    paper_count: int
    paper_summaries_path: Path
    final_review_path: Path
    method_extraction_path: Path | None = None
    implementation_plan_path: Path | None = None
    prototype_path: Path | None = None
    prototype_readme_path: Path | None = None


def run_pipeline(
    topic: str,
    max_papers: int | None = None,
    output_dir: str | None = None,
    enable_prototype: bool = True,
) -> PipelineResult:
    settings = get_settings()
    max_papers = max_papers or settings.arxiv_max_results
    out_dir = Path(output_dir or settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    reader = PaperReaderAgent(topic=topic)
    method_agent = MethodExtractionAgent()
    planner_agent = PrototypePlannerAgent()
    writer_agent = PrototypeWriterAgent()

    print(f"[1/7] Searching arXiv for: {topic}")
    papers = search_arxiv(topic, max_results=max_papers)

    summaries: list[PaperSummary] = []
    for index, paper in enumerate(papers, start=1):
        print(f"[2/7] Reading paper {index}/{len(papers)}: {paper.title}")
        full_text = read_arxiv_pdf(paper, out_dir)

        print(f"[3/7] Summarizing paper {index}/{len(papers)}")
        summaries.append(reader.summarize_paper(paper, full_text))

    print("[4/7] Saving paper summaries")
    paper_summaries_path = out_dir / "paper_summaries.md"
    paper_summaries_path.write_text(write_paper_summaries(summaries), encoding="utf-8")

    print("[5/7] Writing final literature review")
    review = reader.write_literature_review(summaries)
    final_review_path = out_dir / "final_literature_review.md"
    final_review_path.write_text(review, encoding="utf-8")

    method_path: Path | None = None
    plan_path: Path | None = None
    prototype_path: Path | None = None
    prototype_readme_path: Path | None = None

    if enable_prototype:
        print("[6/7] Extracting implementable methods")
        method_text = method_agent.extract_implementable_method(topic, summaries)
        method_path = out_dir / "method_extraction.md"
        method_path.write_text(method_text, encoding="utf-8")

        print("[7/7] Writing implementation plan and prototype")
        plan_text = planner_agent.write_implementation_plan(topic, method_text)
        plan_path = out_dir / "implementation_plan.md"
        plan_path.write_text(plan_text, encoding="utf-8")

        code_text = writer_agent.generate_prototype_code(topic, plan_text)
        prototype_path = out_dir / "prototype.py"
        prototype_path.write_text(code_text, encoding="utf-8")

        readme_text = writer_agent.write_prototype_readme(topic, plan_text)
        prototype_readme_path = out_dir / "prototype_readme.md"
        prototype_readme_path.write_text(readme_text, encoding="utf-8")

    return PipelineResult(
        topic=topic,
        output_dir=out_dir,
        paper_count=len(summaries),
        paper_summaries_path=paper_summaries_path,
        final_review_path=final_review_path,
        method_extraction_path=method_path,
        implementation_plan_path=plan_path,
        prototype_path=prototype_path,
        prototype_readme_path=prototype_readme_path,
    )
