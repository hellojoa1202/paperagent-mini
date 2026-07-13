"""Claude Desktop MCP server for the PaperAgent mini project.

Claude MCP 설정 예시:

{
  "mcpServers": {
    "paperagent-mini": {
      "command": "/path/to/python",
      "args": ["/path/to/Paper Agent/mcp_paperagent_server.py"]
    }
  }
}
"""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(PROJECT_ROOT)

from paperagent.workflow import run_pipeline  # noqa: E402
from paperagent.config import get_settings  # noqa: E402

mcp = FastMCP("paperagent-mini")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
# URI를 버전별로 바꿔 Claude Desktop이 이전 MCP App HTML을 재사용하지 않게 합니다.
APP_RESOURCE_URI = "ui://paperagent-mini/review-v9.html"
APP_DIST_FILE = PROJECT_ROOT / "ui_mockup" / "dist" / "index.html"
APP_CHECKPOINT_FILE = DEFAULT_OUTPUT_DIR / ".paperagent_ui_checkpoint.json"
_APP_JOBS: dict[str, dict[str, object]] = {}
_APP_JOBS_LOCK = threading.Lock()


@mcp.resource(
    APP_RESOURCE_URI,
    name="PaperAgent interactive review",
    title="PaperAgent",
    description="Interactive PaperAgent setup, progress, results, and follow-up UI.",
    mime_type="text/html;profile=mcp-app",
    meta={"ui": {"prefersBorder": True}},
)
def paperagent_app_resource() -> str:
    """Serve the single-file MCP App bundled by Vite."""
    if not APP_DIST_FILE.exists():
        return (
            "<!doctype html><meta charset='utf-8'><p>PaperAgent UI가 아직 빌드되지 "
            "않았습니다. <code>cd ui_mockup && npm install && npm run build</code>를 "
            "실행하세요.</p>"
        )
    return APP_DIST_FILE.read_text(encoding="utf-8")


@mcp.tool(
    title="PaperAgent 열기",
    meta={
        "ui": {
            "resourceUri": APP_RESOURCE_URI,
            "visibility": ["model", "app"],
        },
        # Older MCP Apps hosts still inspect the legacy flat metadata key.
        "ui/resourceUri": APP_RESOURCE_URI,
    },
)
def start_paperagent_review() -> str:
    """Open the PaperAgent form, then end the turn without any assistant text.

    Do not explain that the app opened. Do not suggest topics, keywords, options,
    or next steps. Do not ask a follow-up question. The visible app is the entire
    response, so after this tool call the assistant must produce no chat message.
    """
    # 이 결과는 모델에게만 실행 종료를 알리고, 사용자 입력은 MCP App에서 받습니다.
    return (
        "The PaperAgent app is already visible. End this turn now with no assistant "
        "message, explanation, recommendation, or follow-up question."
    )


@mcp.tool(
    title="PaperAgent UI에서 문헌 조사 실행",
    meta={"ui": {"visibility": ["app"]}},
    structured_output=True,
)
def run_paperagent_app(
    topic: str,
    max_papers: int = 3,
    enable_prototype: bool = False,
    resume: bool = False,
) -> dict[str, object]:
    """Start the workflow in a background thread and return immediately."""
    topic = topic.strip()
    if not topic:
        return {"status": "error", "message": "논문 주제를 입력해주세요."}

    max_papers = max(1, min(int(max_papers), 10))
    signature = (topic, max_papers, enable_prototype, resume)
    with _APP_JOBS_LOCK:
        for existing_id, existing in _APP_JOBS.items():
            if existing.get("status") == "running" and existing.get("signature") == signature:
                return {
                    "status": "running",
                    "job_id": existing_id,
                    "current_step": _read_app_checkpoint().get("current_step", "search"),
                }

        job_id = uuid.uuid4().hex
        _APP_JOBS[job_id] = {
            "status": "running",
            "signature": signature,
            "current_step": "search",
        }

    worker = threading.Thread(
        target=_run_paperagent_job,
        args=(job_id, topic, max_papers, enable_prototype, resume),
        name=f"paperagent-{job_id[:8]}",
        daemon=True,
    )
    worker.start()
    return {"status": "running", "job_id": job_id, "current_step": "search"}


@mcp.tool(
    title="PaperAgent UI 작업 상태 확인",
    meta={"ui": {"visibility": ["app"]}},
    structured_output=True,
)
def get_paperagent_job_status(job_id: str) -> dict[str, object]:
    """Return a short status response for a background PaperAgent job."""
    with _APP_JOBS_LOCK:
        job = dict(_APP_JOBS.get(job_id, {}))
    if not job:
        checkpoint = _read_app_checkpoint()
        return {
            "status": "error",
            "message": "작업 연결이 끊겼습니다. 체크포인트에서 다시 실행할 수 있습니다.",
            "failed_step": checkpoint.get("current_step", "search"),
            "can_resume": APP_CHECKPOINT_FILE.exists(),
        }
    if job.get("status") == "running":
        checkpoint = _read_app_checkpoint()
        return {
            "status": "running",
            "job_id": job_id,
            "current_step": checkpoint.get("current_step", "search"),
            "completed": checkpoint.get("completed", []),
        }
    job.pop("signature", None)
    return job


def _run_paperagent_job(
    job_id: str,
    topic: str,
    max_papers: int,
    enable_prototype: bool,
    resume: bool,
) -> None:
    result = _execute_paperagent_app(topic, max_papers, enable_prototype, resume)
    with _APP_JOBS_LOCK:
        signature = _APP_JOBS.get(job_id, {}).get("signature")
        _APP_JOBS[job_id] = {**result, "signature": signature}


def _execute_paperagent_app(
    topic: str,
    max_papers: int,
    enable_prototype: bool,
    resume: bool,
) -> dict[str, object]:
    """Execute the actual long-running pipeline in a worker thread."""
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = run_pipeline(
            topic=topic,
            max_papers=max_papers,
            output_dir=str(DEFAULT_OUTPUT_DIR),
            enable_prototype=enable_prototype,
            enable_review=True,
            enable_extra_reviewers=False,
            enable_report=True,
            read_pdf=False,
            enable_literature_review=True,
            enable_critic=True,
            checkpoint_path=str(APP_CHECKPOINT_FILE),
            resume=resume,
        )
    except Exception as exc:  # UI needs a structured error instead of a broken iframe.
        checkpoint = _read_app_checkpoint()
        return {
            "status": "error",
            "message": str(exc),
            "failed_step": checkpoint.get("current_step", "search"),
            "can_resume": APP_CHECKPOINT_FILE.exists(),
        }

    response = {
        "status": "success",
        "topic": result.topic,
        "paper_count": result.paper_count,
        "report_path": str(result.report_path),
        "prototype_path": str(result.prototype_path) if result.prototype_path else None,
        # UI는 보고서 파일을 다시 읽지 않고, 파이프라인에서 이미 생성한 논문별
        # 한국어 agent summary를 즉시 표로 표시합니다.
        "papers": [
            {
                "date": f"{_format_published_date(str(item.published))} "
                f"({item.venue or 'Preprint'})",
                "title": item.title,
                "abstract": item.abstract,
                "agent_notes": item.summary,
                "paper_link": item.paper_url
                or f"https://arxiv.org/abs/{item.paper_id}",
            }
            for item in result.paper_summaries
        ],
    }
    APP_CHECKPOINT_FILE.unlink(missing_ok=True)
    return response


@mcp.tool()
def check_paperagent_settings() -> str:
    """Check which local PaperAgent settings this MCP server is using."""
    settings = get_settings()
    return (
        "# PaperAgent 설정 확인\n\n"
        f"- project_root: `{PROJECT_ROOT}`\n"
        f"- llm_provider: `{settings.llm_provider}`\n"
        f"- llm_model: `{settings.llm_model}`\n"
        f"- ollama_url: `{settings.ollama_url}`\n"
        f"- output_dir: `{settings.output_dir}`\n\n"
        "`llm_provider`가 `ollama`이면 외부 API 키나 OpenAI quota를 사용하지 않습니다."
    )


@mcp.tool()
def run_paper_literature_review(
    topic: str,
    max_papers: int = 3,
    enable_prototype: bool = False,
    enable_review: bool = True,
    enable_extra_reviewers: bool = False,
    enable_report: bool = True,
    read_pdf: bool = False,
    enable_literature_review: bool = True,
    enable_critic: bool = True,
) -> str:
    """Search arXiv using the user's topic, read papers, run agents, and save outputs.

    After the user answers the three setup questions, call this tool immediately.
    Passing only topic, max_papers, and enable_prototype runs the standard full review.
    """
    topic = topic.strip()
    if not topic:
        return (
            "topic이 비어 있습니다. 사용자에게 찾아볼 논문 주제를 먼저 물어본 뒤 "
            "다시 `run_paper_literature_review`를 호출하세요."
        )

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = run_pipeline(
            topic=topic,
            max_papers=max_papers,
            output_dir=str(DEFAULT_OUTPUT_DIR),
            enable_prototype=enable_prototype,
            enable_review=enable_review,
            enable_extra_reviewers=enable_extra_reviewers,
            enable_report=enable_report,
            read_pdf=read_pdf,
            enable_literature_review=enable_literature_review,
            enable_critic=enable_critic,
        )
    except RuntimeError as exc:
        return f"# PaperAgent 실행 실패\n\n{exc}"
    return _render_mcp_response(result)


def _render_mcp_response(result) -> str:
    prototype_line = (
        f"- 프로토타입 코드: `{result.prototype_path}`"
        if result.prototype_path
        else "- 프로토타입 코드: 생성하지 않음"
    )

    paper_sources = [
        {
            "date": f"{_format_published_date(item.published)} ({item.venue or 'Preprint'})",
            "title": item.title,
            "abstract": item.abstract,
            "agent_summary": item.summary,
            "paper_link": item.paper_url
            or f"https://arxiv.org/abs/{item.paper_id}",
        }
        for item in result.paper_summaries
    ]

    return (
        "# PaperAgent 실행 완료\n\n"
        f"- 주제: **{result.topic}**\n"
        f"- 읽은 논문 수: **{result.paper_count}개**\n"
        f"- `research_report.md` 생성 완료: `{result.report_path}`\n"
        f"{prototype_line}\n\n"
        "## Claude 최종 응답 지침\n\n"
        "아래 SOURCE를 사용자에게 그대로 노출하거나 파일을 다시 읽지 마세요. "
        "Claude 자체 지식 정리 능력으로 SOURCE를 요약하여, 위 생성 완료 안내 바로 아래에 "
        "Markdown 표 하나를 작성하세요.\n\n"
        "표의 열은 정확히 `DATE | 제목 | 배경 | 제시 | 성과 | 문제 | Paper Link`입니다.\n"
        "`분야` 열은 만들지 마세요. 배경·제시·성과·문제는 줄글 대신 각각 2~4개의 "
        "짧은 불릿으로 구조화하세요. Markdown 표 셀 안에서는 `<br>• `로 불릿을 구분하세요. "
        "SOURCE의 핵심 내용은 임의로 생략하거나 말줄임표로 자르지 마세요.\n"
        "DATE는 `YYYY.MM (학회명)` 형식이며 학회가 없으면 `Preprint`로 표시하고, "
        "링크는 `[Paper](URL)` 형식을 사용하세요.\n\n"
        "<PAPER_TABLE_SOURCE>\n"
        f"{json.dumps(paper_sources, ensure_ascii=False)}\n"
        "</PAPER_TABLE_SOURCE>"
    )


def _format_published_date(value: str) -> str:
    """Convert an arXiv timestamp such as 2026-07-13T... to YYYY.MM."""
    if len(value) >= 7 and value[4] == "-":
        return value[:7].replace("-", ".")
    return value[:7] or "-"


def _read_app_checkpoint() -> dict:
    if not APP_CHECKPOINT_FILE.exists():
        return {}
    try:
        return json.loads(APP_CHECKPOINT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


if __name__ == "__main__":
    mcp.run(transport="stdio")
