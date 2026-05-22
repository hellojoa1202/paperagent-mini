from dataclasses import dataclass

import arxiv

from llm import ask_llm


@dataclass
class PaperSummary:
    paper_id: str
    title: str
    abstract: str
    summary: str


class PaperReaderAgent:
    def __init__(self, topic: str):
        self.topic = topic

    def summarize_paper(self, paper: arxiv.Result, full_text: str) -> PaperSummary:
        system_prompt = (
            "You are a careful research assistant. "
            "Read papers for a beginner research group and explain them clearly."
        )
        user_prompt = f"""
Research topic:
{self.topic}

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

    def write_literature_review(self, summaries: list[PaperSummary]) -> str:
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
{self.topic}

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
