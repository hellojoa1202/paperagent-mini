"""Validate a generated prototype and optionally ask one Agent to repair it."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from paperagent.agents import BaseAgent, strip_code_fence


@dataclass(frozen=True)
class PrototypeReview:
    syntax_ok: bool
    execution_ok: bool
    return_code: int | None
    stdout: str
    error: str

    @property
    def passed(self) -> bool:
        return self.syntax_ok and self.execution_ok


class PrototypeReviewerAgent(BaseAgent):
    """Useful new Agent: turn validator errors into one focused code revision."""

    name = "PrototypeReviewerAgent"
    role = "senior Python engineer repairing a small generated prototype"

    def repair(self, code: str, review: PrototypeReview) -> str:
        prompt = f"""
다음 prototype.py는 검증에 실패했습니다.

오류:
{review.error}

기존 코드:
```python
{code}
```

오류만 최소 수정하세요. 표준 라이브러리 또는 NumPy만 사용하고,
외부 데이터 없이 실행 가능해야 합니다. 설명 없이 Python 코드 블록 하나만 반환하세요.
"""
        return strip_code_fence(self.ask(prompt))


def validate_code(code: str, *, execute: bool = False, timeout: int = 10) -> PrototypeReview:
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return PrototypeReview(False, False, None, "", f"SyntaxError: {exc}")

    if not execute:
        # Static-only mode treats a syntax-valid file as passed and never calls the LLM repair step.
        return PrototypeReview(True, True, None, "", "")

    # LLM 생성 코드는 신뢰할 수 없으므로 격리된 실습 환경에서만 execute=True를 사용합니다.
    with tempfile.TemporaryDirectory(prefix="paperagent-prototype-") as temp_dir:
        script = Path(temp_dir) / "prototype.py"
        script.write_text(code, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PATH": os.environ.get("PATH", "")},
                check=False,
            )
        except subprocess.TimeoutExpired:
            return PrototypeReview(True, False, None, "", f"Timeout after {timeout}s")
    return PrototypeReview(
        syntax_ok=True,
        execution_ok=completed.returncode == 0,
        return_code=completed.returncode,
        stdout=completed.stdout[-4000:],
        error=completed.stderr[-4000:],
    )


def review_and_repair(code: str, *, execute: bool, max_repairs: int = 1) -> tuple[str, list[PrototypeReview]]:
    reviews: list[PrototypeReview] = []
    current = code
    reviewer = PrototypeReviewerAgent()
    for attempt in range(max_repairs + 1):
        review = validate_code(current, execute=execute)
        reviews.append(review)
        if review.passed or attempt == max_repairs:
            break
        current = reviewer.repair(current, review)
    return current, reviews
