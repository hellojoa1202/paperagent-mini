from pathlib import Path

import arxiv
from pypdf import PdfReader


MAX_PAPER_CHARS = 30000


def search_arxiv(query: str, max_results: int = 5) -> list[arxiv.Result]:
    client = arxiv.Client()
    search = arxiv.Search(
        query="abs:" + query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    return list(client.results(search))


def read_arxiv_pdf(paper: arxiv.Result, work_dir: Path) -> str:
    work_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = work_dir / f"{paper.get_short_id().replace('/', '_')}.pdf"
    paper.download_pdf(filename=str(pdf_path))

    text_parts = []
    reader = PdfReader(str(pdf_path))
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        text_parts.append(f"\n--- Page {page_index} ---\n{page_text}")

    pdf_path.unlink(missing_ok=True)
    return "\n".join(text_parts)[:MAX_PAPER_CHARS]
