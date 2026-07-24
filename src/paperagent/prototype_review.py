"""Validation and bounded repair helpers for generated prototype code."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from paperagent.agents import PrototypeReviewerAgent


ALLOWED_IMPORTS = {
    "__future__",
    "collections",
    "dataclasses",
    "functools",
    "itertools",
    "json",
    "math",
    "numpy",
    "random",
    "statistics",
    "time",
    "typing",
}
BLOCKED_CALLS = {"__import__", "compile", "eval", "exec", "open"}
FAKE_METRIC_PATTERN = re.compile(
    r"(?:(?:accuracy|정확도|성능).{0,30}(?:fake|가상|임의|고정)"
    r"|(?:fake|가상|임의|고정).{0,30}(?:accuracy|정확도|성능))",
    flags=re.IGNORECASE,
)


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


@dataclass(frozen=True)
class PrototypeRequirements:
    """Semantic and structural requirements for an ML toy prototype."""

    concept_groups: tuple[tuple[str, ...], ...] = ()
    min_concept_matches: int = 0
    require_numpy: bool = True
    min_functions: int = 4
    min_nonempty_lines: int = 70
    require_baseline_comparison: bool = True
    require_assert: bool = True
    required_entrypoint: str = "run_prototype"


_CONCEPT_VOCABULARY: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("transformer", ("transformer", "attention")),
    ("token", ("token",)),
    ("merge", ("merge", "merged", "merging")),
    ("embedding", ("embedding", "embed")),
    ("classification", ("classification", "classifier", "logit", "predict")),
    ("image", ("image", "patch", "pixel")),
    ("sequence", ("sequence", "temporal", "timestep")),
    ("robot", ("robot", "action", "policy")),
    ("graph", ("graph", "node", "edge")),
    ("retrieval", ("retrieval", "retrieve", "similarity")),
)


def build_prototype_requirements(
    topic: str,
    implementation_plan: str,
) -> PrototypeRequirements:
    """Derive a small, deterministic relevance contract from the requested work."""
    source = f"{topic}\n{implementation_plan}".lower()
    groups = [
        aliases
        for _, aliases in _CONCEPT_VOCABULARY
        if any(alias in source for alias in aliases)
    ][:4]

    if not groups:
        stopwords = {
            "about",
            "based",
            "from",
            "into",
            "paper",
            "prototype",
            "research",
            "using",
            "with",
        }
        topic_terms = tuple(
            dict.fromkeys(
                term
                for term in re.findall(r"[a-z][a-z0-9_-]{3,}", topic.lower())
                if term not in stopwords
            )
        )
        groups = [(term,) for term in topic_terms[:3]]

    return PrototypeRequirements(
        concept_groups=tuple(groups),
        min_concept_matches=min(2, len(groups)),
    )


def validate_code(
    code: str,
    *,
    execute: bool = False,
    timeout: int = 10,
    requirements: PrototypeRequirements | None = None,
) -> PrototypeReview:
    """Check syntax, lightweight safety/quality rules, and optional execution."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return PrototypeReview(False, False, None, "", f"SyntaxError: {exc}")

    policy_issues = _find_policy_issues(tree, code, requirements=requirements)
    if policy_issues:
        return PrototypeReview(
            True,
            False,
            None,
            "",
            "Prototype policy check failed:\n- " + "\n- ".join(policy_issues),
        )

    if not execute:
        return PrototypeReview(True, True, None, "", "")

    with tempfile.TemporaryDirectory(prefix="paperagent-prototype-") as temp_dir:
        script = Path(temp_dir) / "prototype.py"
        script.write_text(code, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=max(1, timeout),
                env={"PATH": os.environ.get("PATH", "")},
                check=False,
            )
        except subprocess.TimeoutExpired:
            return PrototypeReview(
                True,
                False,
                None,
                "",
                f"Timeout after {max(1, timeout)}s",
            )

    return PrototypeReview(
        syntax_ok=True,
        execution_ok=completed.returncode == 0 and bool(completed.stdout.strip()),
        return_code=completed.returncode,
        stdout=completed.stdout[-4000:],
        error=(
            completed.stderr[-4000:]
            if completed.returncode != 0
            else "프로토타입이 실행됐지만 결과를 출력하지 않았습니다."
            if not completed.stdout.strip()
            else ""
        ),
    )


def validate_code_for_storage(code: str) -> PrototypeReview:
    """Allow an unverified draft to be saved only when it is syntactically safe."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return PrototypeReview(False, False, None, "", f"SyntaxError: {exc}")

    imported_roots: set[str] = set()
    blocked_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in BLOCKED_CALLS
        ):
            blocked_calls.add(node.func.id)

    issues: list[str] = []
    forbidden_imports = sorted(imported_roots - ALLOWED_IMPORTS)
    if forbidden_imports:
        issues.append("허용되지 않은 import: " + ", ".join(forbidden_imports))
    if blocked_calls:
        issues.append("허용되지 않은 함수 호출: " + ", ".join(sorted(blocked_calls)))
    if issues:
        return PrototypeReview(
            True,
            False,
            None,
            "",
            "Prototype storage safety check failed:\n- " + "\n- ".join(issues),
        )
    return PrototypeReview(True, True, None, "", "")


def apply_deterministic_repairs(
    code: str,
    *,
    requirements: PrototypeRequirements | None = None,
) -> str:
    """Fix small structural omissions without spending another LLM call."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    has_main_guard = any(
        _is_main_guard(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
    )
    if has_main_guard:
        return code

    functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    preferred_entrypoint = (
        requirements.required_entrypoint
        if requirements is not None
        else "run_prototype"
    )
    entrypoint = (
        preferred_entrypoint
        if preferred_entrypoint in functions
        else "main"
        if "main" in functions
        else ""
    )
    if not entrypoint:
        return code

    suffix = (
        '\n\nif __name__ == "__main__":\n'
        f"    _prototype_result = {entrypoint}()\n"
        "    if _prototype_result is not None:\n"
        "        print(_prototype_result)\n"
    )
    return code.rstrip() + suffix


def _find_policy_issues(
    tree: ast.AST,
    code: str,
    *,
    requirements: PrototypeRequirements | None = None,
) -> list[str]:
    issues: list[str] = []
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    forbidden_imports = sorted(imported_roots - ALLOWED_IMPORTS)
    if forbidden_imports:
        issues.append(
            "허용되지 않은 import: "
            + ", ".join(forbidden_imports)
            + ". 표준 안전 모듈과 NumPy만 사용하세요."
        )

    if any(isinstance(node, ast.Pass) for node in ast.walk(tree)):
        issues.append("구현되지 않은 pass 문이 있습니다.")
    if any(
        isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id == "NotImplementedError"
        for node in ast.walk(tree)
    ):
        issues.append("NotImplementedError로 남겨둔 기능이 있습니다.")

    blocked = sorted(
        {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in BLOCKED_CALLS
        }
    )
    if blocked:
        issues.append("허용되지 않은 함수 호출: " + ", ".join(blocked))

    if not any(_is_main_guard(node) for node in ast.walk(tree) if isinstance(node, ast.If)):
        issues.append('`if __name__ == "__main__":` 실행 블록이 없습니다.')
    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        for node in ast.walk(tree)
    ):
        issues.append("실행 결과를 확인할 print 출력이 없습니다.")
    if FAKE_METRIC_PATTERN.search(code):
        issues.append("가상·고정 성능 수치를 출력하지 말고 실행 결과에서 직접 계산하세요.")
    if requirements is not None:
        issues.extend(_find_requirement_issues(tree, code, requirements))
    return issues


def _find_requirement_issues(
    tree: ast.AST,
    code: str,
    requirements: PrototypeRequirements,
) -> list[str]:
    issues: list[str] = []
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    if requirements.require_numpy and "numpy" not in imported_roots:
        issues.append("ML 프로토타입은 mock tensor 계산에 NumPy를 사용해야 합니다.")
    if len(functions) < requirements.min_functions:
        issues.append(
            "데이터 생성, baseline, 제안 방법, 평가를 나눈 함수가 "
            f"최소 {requirements.min_functions}개 필요합니다."
        )
    nonempty_lines = [
        line
        for line in code.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(nonempty_lines) < requirements.min_nonempty_lines:
        issues.append(
            "prototype이 지나치게 짧습니다. 주석으로 분량을 채우지 말고 "
            f"실행 코드 기준 최소 {requirements.min_nonempty_lines}줄로 구현하세요."
        )
    if requirements.require_baseline_comparison and "baseline" not in code.lower():
        issues.append(
            "같은 mock data에서 baseline과 제안 방법을 비교하는 계산이 필요합니다."
        )
    if (
        requirements.required_entrypoint
        and requirements.required_entrypoint not in functions
    ):
        issues.append(
            f"`{requirements.required_entrypoint}()` 함수에서 전체 프로토타입을 실행하세요."
        )
    if requirements.require_assert and not any(
        isinstance(node, ast.Assert) for node in ast.walk(tree)
    ):
        issues.append("입력·중간 결과·출력 shape를 확인하는 assert가 필요합니다.")

    lowered = code.lower()
    matched = sum(
        any(alias in lowered for alias in aliases)
        for aliases in requirements.concept_groups
    )
    if matched < requirements.min_concept_matches:
        readable_groups = [
            "/".join(aliases) for aliases in requirements.concept_groups
        ]
        issues.append(
            "연구 주제와 관련 없는 코드입니다. 다음 핵심 개념 중 "
            f"{requirements.min_concept_matches}개 이상을 실제 구현에 반영하세요: "
            + ", ".join(readable_groups)
        )
    return issues


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    return any(
        isinstance(comparator, ast.Constant) and comparator.value == "__main__"
        for comparator in test.comparators
    )


def review_and_repair(
    code: str,
    *,
    execute: bool = False,
    max_repairs: int = 1,
    timeout: int = 10,
    reviewer: PrototypeReviewerAgent | None = None,
    requirements: PrototypeRequirements | None = None,
    topic: str = "",
    implementation_plan: str = "",
) -> tuple[str, tuple[PrototypeReview, ...]]:
    """Validate code and ask PrototypeReviewerAgent to repair it at most N times."""
    current = apply_deterministic_repairs(code, requirements=requirements)
    reviews: list[PrototypeReview] = []
    repair_agent = reviewer or PrototypeReviewerAgent()

    for attempt in range(max(0, max_repairs) + 1):
        review = validate_code(
            current,
            execute=execute,
            timeout=timeout,
            requirements=requirements,
        )
        reviews.append(review)
        if review.passed or attempt >= max_repairs:
            break
        current = apply_deterministic_repairs(
            repair_agent.repair(
                current,
                review,
                topic=topic,
                implementation_plan=implementation_plan,
            ),
            requirements=requirements,
        )

    return current, tuple(reviews)
