"""Claude Desktop MCP server for the merged PaperAgent project.

Claude MCP 설정 예시:

{
  "mcpServers": {
    "paperagent-merged": {
      "command": "/path/to/python",
      "args": ["/home/joa/Desktop/PM/paperagent-merged/mcp_paperagent_server.py"]
    }
  }
}
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(PROJECT_ROOT)

from paperagent.workflow import run_pipeline  # noqa: E402

mcp = FastMCP("paperagent-merged")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"


@mcp.tool()
def start_paperagent_review() -> str:
    """Start an interactive paper-agent run by asking the user for missing inputs."""
    return (
        "paperagent-merged MCP 실행을 시작합니다.\n\n"
        "Claude는 사용자에게 아래 정보를 한 단계씩 물어본 뒤 "
        "`run_paper_literature_review` tool을 호출하세요.\n\n"
        "1. 찾아볼 논문 주제(topic)를 물어보세요.\n"
        "2. 읽을 논문 개수(max_papers)를 물어보세요. 사용자가 모르겠다고 하면 3개를 사용하세요.\n"
        "3. prototype.py까지 만들지(enable_prototype)를 물어보세요. 사용자가 모르겠다고 하면 true를 사용하세요.\n"
        "4. 세 답변을 모아 `run_paper_literature_review(topic, max_papers, enable_prototype)`를 실행하세요."
    )


@mcp.tool()
def run_paper_literature_review(
    topic: str,
    max_papers: int = 3,
    enable_prototype: bool = True,
) -> str:
    """Search arXiv using the user's topic, read papers, run agents, and save outputs.

    If the user only says "mcp 실행해줘" or does not provide a topic, ask for:
    topic, max_papers, and enable_prototype before calling this tool.
    """
    topic = topic.strip()
    if not topic:
        return (
            "topic이 비어 있습니다. 사용자에게 찾아볼 논문 주제를 먼저 물어본 뒤 "
            "다시 `run_paper_literature_review`를 호출하세요."
        )

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_pipeline(
        topic=topic,
        max_papers=max_papers,
        output_dir=str(DEFAULT_OUTPUT_DIR),
        enable_prototype=enable_prototype,
    )
    return _render_mcp_response(result)


def _render_mcp_response(result) -> str:
    paper_titles = _extract_paper_titles(result.paper_summaries_path)
    review_preview = _read_markdown_preview(result.final_review_path, max_chars=1800)

    optional_paths = [
        ("구현 가능 방법 추출", result.method_extraction_path),
        ("구현 계획", result.implementation_plan_path),
        ("프로토타입 코드", result.prototype_path),
        ("프로토타입 README", result.prototype_readme_path),
    ]
    optional_lines = [
        f"- {label}: `{path}`" for label, path in optional_paths if path is not None
    ]

    return (
        "# PaperAgent 실행 완료\n\n"
        f"- 주제: **{result.topic}**\n"
        f"- 읽은 논문 수: **{result.paper_count}개**\n"
        f"- 출력 폴더: `{result.output_dir}`\n\n"
        "## 읽은 논문\n\n"
        f"{paper_titles}\n\n"
        "## 최종 문헌 리뷰 간단 미리보기\n\n"
        f"{review_preview}\n\n"
        "## 저장된 파일\n\n"
        f"- 논문별 요약: `{result.paper_summaries_path}`\n"
        f"- 최종 문헌 리뷰: `{result.final_review_path}`\n"
        f"{chr(10).join(optional_lines)}\n\n"
        "전체 내용은 위 파일들에서 확인하면 됩니다."
    )


def _extract_paper_titles(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    titles = re.findall(r"^##\s+\d+\.\s+(.+)$", text, flags=re.MULTILINE)
    if not titles:
        return "- 논문 제목을 자동 추출하지 못했습니다. `paper_summaries.md`를 확인하세요."
    return "\n".join(f"{index}. {title}" for index, title in enumerate(titles, start=1))


def _read_markdown_preview(path: Path, max_chars: int) -> str:
    text = path.read_text(encoding="utf-8").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit("\n", 1)[0].strip()
    return f"{cut}\n\n...(미리보기 생략: 전체 내용은 `{path}`에서 확인)"


if __name__ == "__main__":
    mcp.run(transport="stdio")
