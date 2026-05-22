from pathlib import Path

from agent import PaperReaderAgent
from arxiv_tool import read_arxiv_pdf, search_arxiv


def run_paper_reader(topic: str, max_papers: int = 5, output_dir: str = "outputs") -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(exist_ok=True)

    agent = PaperReaderAgent(topic=topic)

    print(f"[1/4] Searching arXiv for: {topic}")
    papers = search_arxiv(topic, max_results=max_papers)

    summaries = []
    for index, paper in enumerate(papers, start=1):
        print(f"[2/4] Reading paper {index}/{len(papers)}: {paper.title}")
        full_text = read_arxiv_pdf(paper, out_dir)

        print(f"[3/4] Summarizing paper {index}/{len(papers)}")
        summaries.append(agent.summarize_paper(paper, full_text))

    print("[4/4] Writing final literature review")
    review = agent.write_literature_review(summaries)

    out_path = out_dir / "final_literature_review.md"
    out_path.write_text(review, encoding="utf-8")
    return out_path
