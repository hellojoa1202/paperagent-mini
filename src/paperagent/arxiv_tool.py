"""arXiv search and PDF reading based on the assignment implementations."""

from __future__ import annotations

import os
import time
import urllib.request
from pathlib import Path

import arxiv
from arxiv import HTTPError
from pypdf import PdfReader

MAX_PAPER_CHARS = 30_000


def search_arxiv(query: str, max_results: int = 5) -> list[arxiv.Result]:
    """Search arXiv directly without fallback papers."""
    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=5.0,
        num_retries=5,
    )
    search = arxiv.Search(
        query="abs:" + query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    max_attempts = 5
    base_wait = int(os.getenv("ARXIV_RETRY_WAIT_SECONDS", "5"))

    for attempt in range(1, max_attempts + 1):
        try:
            results = list(client.results(search))
            if not results:
                raise RuntimeError(f"arXiv 검색 결과가 0개입니다: {query}")
            return results
        except HTTPError as exc:
            is_rate_limit = "429" in str(exc)
            if not is_rate_limit or attempt == max_attempts:
                raise RuntimeError(f"arXiv 검색 실패: {exc}") from exc
            wait_seconds = base_wait * (2 ** (attempt - 1))
            print(f"[arxiv retry] 429 rate-limit. {wait_seconds}s 후 재시도...")
            time.sleep(wait_seconds)

    raise RuntimeError("arXiv 검색이 모든 재시도 후에도 실패했습니다.")


def read_arxiv_pdf(paper: arxiv.Result, work_dir: Path) -> str:
    work_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = work_dir / f"{paper.get_short_id().replace('/', '_')}.pdf"

    request = urllib.request.Request(
        paper.pdf_url,
        headers={"User-Agent": "PaperReviewAgent/0.1 contact: local-study-project"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        pdf_path.write_bytes(response.read())

    text_parts = []
    reader = PdfReader(str(pdf_path))
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        text_parts.append(f"\n--- Page {page_index} ---\n{page_text}")

    pdf_path.unlink(missing_ok=True)
    return "\n".join(text_parts)[:MAX_PAPER_CHARS]
