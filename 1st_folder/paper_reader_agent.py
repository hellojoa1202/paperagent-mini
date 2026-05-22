"""
Minimal paper-reading agent.

Goal:
1. Search arXiv for papers related to a topic.
2. Download/read selected paper text.
3. Ask an LLM to summarize each paper.
4. Write a final literature review markdown file.

Run:
    # Edit .env if you want to change the local model.
    python paper_reader_agent.py "LLM agents for scientific discovery"

Install:
    pip install openai arxiv pypdf
"""

from __future__ import annotations

import os
import sys
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import arxiv
from arxiv import HTTPError
from openai import OpenAI
from pypdf import PdfReader


OPENAI_MODEL_NAME = "gpt-4o-mini"
LOCAL_MODEL_NAME = "qwen2.5:7b"
MAX_PAPER_CHARS = 30000
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_LM_STUDIO_URL = "http://localhost:1234/v1"
DEFAULT_FALLBACK_ARXIV_IDS = [
    "2501.04227",  # Agent Laboratory
    "2503.18102",  # AgentRxiv
    "2408.06292",  # The AI Scientist
]


def load_dotenv(dotenv_path: Path = Path(".env")) -> None:
    """Load KEY=VALUE pairs from a local .env file without extra packages."""
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class PaperSummary:
    paper_id: str
    title: str
    abstract: str
    summary: str


@dataclass
class ArxivPaper:
    paper_id: str
    title: str
    summary: str
    pdf_url: str

    def get_short_id(self) -> str:
        return self.paper_id

    def download_pdf(self, filename: str) -> None:
        request = urllib.request.Request(
            self.pdf_url,
            headers={"User-Agent": "PaperReviewAgent/0.1 contact: local-study-project"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            Path(filename).write_bytes(response.read())


def ask_llm(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    """Small LLM wrapper supporting OpenAI, Ollama, and LM Studio."""
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if model is None:
        model = OPENAI_MODEL_NAME if provider == "openai" else LOCAL_MODEL_NAME
    model = os.getenv("LLM_MODEL", model).strip()

    if provider == "ollama":
        return ask_ollama(system_prompt, user_prompt, model)
    if provider == "lmstudio":
        return ask_openai_compatible(
            system_prompt,
            user_prompt,
            model=model,
            base_url=os.getenv("LM_STUDIO_BASE_URL", DEFAULT_LM_STUDIO_URL),
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
        )
    if provider == "openai":
        return ask_openai_compatible(
            system_prompt,
            user_prompt,
            model=model,
            base_url=None,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    raise ValueError("LLM_PROVIDER must be one of: openai, ollama, lmstudio")


def ask_openai_compatible(
    system_prompt: str,
    user_prompt: str,
    model: str,
    base_url: str | None,
    api_key: str | None,
) -> str:
    """Call OpenAI or an OpenAI-compatible local server such as LM Studio."""
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if base_url:
        client = OpenAI(base_url=base_url, api_key=api_key)
    else:
        client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def ask_ollama(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call a local Ollama model, for example qwen2.5:7b or llama3.1:8b."""
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.2},
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Start it with `ollama serve` "
            "and make sure your model is pulled."
        ) from exc

    return result.get("message", {}).get("content", "")


def search_arxiv(query: str, max_results: int = 5) -> list[arxiv.Result | ArxivPaper]:
    """Search arXiv and return metadata objects."""
    if os.getenv("USE_FALLBACK_PAPERS", "false").strip().lower() == "true":
        print("Using fallback paper IDs from .env.")
        return load_fallback_papers(max_results=max_results)

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

    for attempt in range(5):
        try:
            return list(client.results(search))
        except HTTPError as exc:
            if "429" not in str(exc) or attempt == 4:
                print("arXiv search API is still rate-limiting us. Using fallback paper IDs.")
                return load_fallback_papers(max_results=max_results)
            wait_seconds = int(os.getenv("ARXIV_RETRY_WAIT_SECONDS", "5")) * (attempt + 1)
            print(f"arXiv is rate-limiting us. Waiting {wait_seconds}s and retrying...")
            time.sleep(wait_seconds)

    return []


def load_fallback_papers(max_results: int = 3) -> list[ArxivPaper]:
    """Use known arXiv IDs when the search API is temporarily rate-limited."""
    configured_ids = os.getenv("FALLBACK_ARXIV_IDS", "").strip()
    if configured_ids:
        paper_ids = [item.strip() for item in configured_ids.split(",") if item.strip()]
    else:
        paper_ids = DEFAULT_FALLBACK_ARXIV_IDS

    papers = []
    for paper_id in paper_ids[:max_results]:
        papers.append(fetch_arxiv_metadata_by_id(paper_id))
        time.sleep(2)
    return papers


def fetch_arxiv_metadata_by_id(paper_id: str) -> ArxivPaper:
    """Fetch lightweight metadata with urllib so we can set a User-Agent."""
    url = f"https://export.arxiv.org/api/query?id_list={paper_id}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PaperReviewAgent/0.1 contact: local-study-project"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            xml_text = response.read().decode("utf-8")
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            raise RuntimeError("No arXiv entry found")
        title = (entry.findtext("atom:title", default=paper_id, namespaces=ns) or paper_id).strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
    except Exception:
        title = f"arXiv paper {paper_id}"
        summary = "Metadata could not be fetched because arXiv is temporarily unavailable."

    return ArxivPaper(
        paper_id=paper_id,
        title=" ".join(title.split()),
        summary=" ".join(summary.split()),
        pdf_url=f"https://arxiv.org/pdf/{paper_id}.pdf",
    )


def read_arxiv_pdf(paper: arxiv.Result | ArxivPaper, work_dir: Path) -> str:
    """Download a PDF, extract text, then remove the temporary file."""
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


def summarize_paper(topic: str, paper: arxiv.Result, full_text: str) -> PaperSummary:
    """Ask the LLM to produce a structured summary for one paper."""
    system_prompt = (
        "You are a careful research assistant. "
        "Read papers for a beginner research group and explain them clearly."
    )
    user_prompt = f"""
Research topic:
{topic}

Paper title:
{paper.title}

Paper abstract:
{paper.summary}

Paper text:
{full_text}

Write a concise Korean summary with these sections:
- Problem
- Key idea
- Method
- Experiments or evidence
- Limitations
- Why this matters for our project
"""
    summary = ask_llm(system_prompt, user_prompt)
    return PaperSummary(
        paper_id=paper.get_short_id(),
        title=paper.title,
        abstract=paper.summary,
        summary=summary,
    )


def write_literature_review(topic: str, summaries: list[PaperSummary]) -> str:
    """Synthesize all paper summaries into one review."""
    joined = "\n\n".join(
        f"## {item.title}\nID: {item.paper_id}\n\n{item.summary}"
        for item in summaries
    )
    system_prompt = (
        "You are a research mentor. "
        "Synthesize papers into a literature review for a student team."
    )
    user_prompt = f"""
Research topic:
{topic}

Paper summaries:
{joined}

Create a Korean literature review in markdown.
Include:
1. Overall research trend
2. Paper comparison table
3. Common methods
4. Open problems
5. Project ideas our team could build next
"""
    return ask_llm(system_prompt, user_prompt)


def main() -> None:
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please put OPENAI_API_KEY=your-key in .env before running.")

    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        topic = input("Research topic: ").strip()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    print(f"[1/4] Searching arXiv for: {topic}")
    papers = search_arxiv(topic, max_results=5)

    summaries = []
    for index, paper in enumerate(papers, start=1):
        print(f"[2/4] Reading paper {index}/{len(papers)}: {paper.title}")
        full_text = read_arxiv_pdf(paper, output_dir)

        print(f"[3/4] Summarizing paper {index}/{len(papers)}")
        summaries.append(summarize_paper(topic, paper, full_text))

    print("[4/4] Writing final literature review")
    review = write_literature_review(topic, summaries)

    out_path = output_dir / "final_literature_review.md"
    out_path.write_text(review, encoding="utf-8")
    print(f"Done. Review saved to {out_path}")


if __name__ == "__main__":
    main()
