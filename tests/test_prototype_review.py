from __future__ import annotations

from dataclasses import replace

from paperagent.prototype_review import (
    apply_deterministic_repairs,
    build_prototype_requirements,
    review_and_repair,
    validate_code,
    validate_code_for_storage,
)


class _Repairer:
    def repair(self, code, review, **_context):
        assert "SyntaxError" in review.error
        return (
            "def main():\n"
            "    print('repaired')\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )


def test_validate_code_checks_syntax_without_execution() -> None:
    result = validate_code(
        "def main():\n"
        "    print('not executed')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )

    assert result.passed
    assert result.return_code is None


def test_reviewer_repairs_invalid_code_once() -> None:
    code, reviews = review_and_repair(
        "def broken(:\n",
        max_repairs=1,
        reviewer=_Repairer(),
    )

    assert "print('repaired')" in code
    assert len(reviews) == 2
    assert not reviews[0].passed
    assert reviews[1].passed


def test_optional_execution_detects_runtime_error() -> None:
    result = validate_code(
        "def main():\n"
        "    print('starting')\n"
        "    raise RuntimeError('boom')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        execute=True,
    )

    assert result.syntax_ok
    assert not result.execution_ok
    assert "RuntimeError" in result.error


def test_policy_rejects_unavailable_ml_framework() -> None:
    result = validate_code(
        "import torch\n\n"
        "def main():\n"
        "    print(torch.zeros(1))\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )

    assert not result.passed
    assert "torch" in result.error


def test_policy_rejects_fake_metric_output() -> None:
    result = validate_code(
        "def main():\n"
        "    print('가상 정확도: 85%')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )

    assert not result.passed
    assert "직접 계산" in result.error


def test_numpy_attention_prototype_executes() -> None:
    code = """
import numpy as np

def softmax(values):
    shifted = values - values.max(axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=-1, keepdims=True)

def main():
    rng = np.random.default_rng(7)
    tokens = rng.normal(size=(2, 4, 8))
    scores = tokens @ tokens.transpose(0, 2, 1) / np.sqrt(tokens.shape[-1])
    attended = softmax(scores) @ tokens
    merged = attended.reshape(2, 2, 2, 8).mean(axis=2)
    assert attended.shape == (2, 4, 8)
    assert merged.shape == (2, 2, 8)
    reduction = 1.0 - merged.shape[1] / tokens.shape[1]
    print(f"input_shape={tokens.shape}, output_shape={merged.shape}")
    print(f"token_reduction={reduction:.2f}")

if __name__ == "__main__":
    main()
""".strip()

    result = validate_code(code, execute=True)

    assert result.passed
    assert "token_reduction=0.50" in result.stdout


def test_semantic_contract_rejects_unrelated_trivial_code() -> None:
    requirements = build_prototype_requirements(
        "transformer",
        "NumPy token attention과 learnable token merging을 구현한다.",
    )
    result = validate_code(
        "if __name__ == '__main__':\n"
        "    total = sum(2 * i + 1 for i in range(1, 101))\n"
        "    print(total)\n",
        requirements=requirements,
    )

    assert not result.passed
    assert "관련 없는 코드" in result.error
    assert "NumPy" in result.error


def test_semantic_contract_accepts_structured_transformer_prototype() -> None:
    code = """
import numpy as np

def token_attention(tokens):
    scores = tokens @ tokens.T / np.sqrt(tokens.shape[-1])
    weights = np.exp(scores - scores.max(axis=-1, keepdims=True))
    return (weights / weights.sum(axis=-1, keepdims=True)) @ tokens

def merge_tokens(tokens):
    return tokens.reshape(2, 2, 4).mean(axis=1)

def run_prototype():
    tokens = np.arange(16, dtype=float).reshape(4, 4)
    attended = token_attention(tokens)
    merged = merge_tokens(attended)
    assert attended.shape == (4, 4)
    assert merged.shape == (2, 4)
    print(f"transformer_output_shape={merged.shape}")

if __name__ == "__main__":
    run_prototype()
""".strip()
    requirements = build_prototype_requirements(
        "transformer",
        "token attention과 token merge를 구현한다.",
    )
    requirements = replace(
        requirements,
        min_functions=2,
        min_nonempty_lines=0,
        require_baseline_comparison=False,
    )

    result = validate_code(code, execute=True, requirements=requirements)

    assert result.passed


def test_deterministic_repair_adds_missing_main_guard() -> None:
    code = """
import numpy as np

def token_attention(tokens):
    return tokens @ np.eye(tokens.shape[-1])

def run_prototype():
    tokens = np.ones((2, 4))
    output = token_attention(tokens)
    assert output.shape == tokens.shape
    print(f"transformer_token_shape={output.shape}")
    return output.shape
""".strip()
    requirements = build_prototype_requirements(
        "transformer",
        "token attention prototype",
    )
    requirements = replace(
        requirements,
        min_functions=2,
        min_nonempty_lines=0,
        require_baseline_comparison=False,
    )

    repaired = apply_deterministic_repairs(code, requirements=requirements)
    result = validate_code(
        repaired,
        execute=True,
        requirements=requirements,
    )

    assert 'if __name__ == "__main__":' in repaired
    assert "run_prototype()" in repaired
    assert result.passed


def test_review_flow_repairs_missing_main_guard_without_llm_call() -> None:
    class _MustNotRun:
        def repair(self, *_args, **_kwargs):
            raise AssertionError("deterministic repair should be enough")

    code = """
import numpy as np

def merge_tokens(tokens):
    return tokens.reshape(2, 2, 2).mean(axis=1)

def run_prototype():
    tokens = np.arange(8, dtype=float).reshape(4, 2)
    merged = merge_tokens(tokens)
    assert merged.shape == (2, 2)
    print(f"transformer_token_merge_shape={merged.shape}")
""".strip()
    requirements = build_prototype_requirements(
        "transformer",
        "token merging prototype",
    )
    requirements = replace(
        requirements,
        min_functions=2,
        min_nonempty_lines=0,
        require_baseline_comparison=False,
    )

    repaired, reviews = review_and_repair(
        code,
        execute=True,
        max_repairs=2,
        reviewer=_MustNotRun(),
        requirements=requirements,
    )

    assert 'if __name__ == "__main__":' in repaired
    assert len(reviews) == 1
    assert reviews[0].passed


def test_runtime_failure_keeps_last_repaired_draft() -> None:
    class _StillBroken:
        def repair(self, code, _review, **_context):
            return code

    broken_code = """
import numpy as np

def transformer_attention(tokens):
    return tokens

def merge_tokens(tokens):
    return tokens

def run_prototype():
    tokens = np.ones((4, 8))
    merged_tokens = merge_tokens(transformer_attention(tokens))
    assert merged_tokens.shape[0] < tokens.shape[0]
    print(f"token_merge_shape={merged_tokens.shape}")
""".strip()
    requirements = build_prototype_requirements(
        "transformer",
        "token attention and learnable token merging",
    )
    requirements = replace(
        requirements,
        min_functions=2,
        min_nonempty_lines=0,
        require_baseline_comparison=False,
    )

    repaired, reviews = review_and_repair(
        broken_code,
        execute=True,
        max_repairs=2,
        reviewer=_StillBroken(),
        requirements=requirements,
        topic="transformer",
        implementation_plan="token attention and learnable token merging",
    )

    assert len(reviews) == 3
    assert all(not review.passed for review in reviews)
    assert "assert merged_tokens.shape[0] < tokens.shape[0]" in repaired
    assert 'if __name__ == "__main__":' in repaired
    assert "Verified NumPy fallback" not in repaired


def test_strict_requirements_reject_short_code_without_baseline() -> None:
    requirements = build_prototype_requirements(
        "transformer",
        "token attention and learnable token merging",
    )
    code = """
import numpy as np

def attention(tokens):
    return tokens

def merge_tokens(tokens):
    return tokens

def evaluate(tokens):
    return float(tokens.mean())

def run_prototype():
    tokens = np.ones((2, 4, 8))
    output = merge_tokens(attention(tokens))
    assert output.shape == tokens.shape
    print(evaluate(output))

if __name__ == "__main__":
    run_prototype()
""".strip()

    result = validate_code(code, requirements=requirements)

    assert not result.passed
    assert "지나치게 짧습니다" in result.error
    assert "baseline" in result.error


def test_storage_check_allows_runtime_failure_but_blocks_dangerous_code() -> None:
    runtime_failure = """
import numpy as np

def run_prototype():
    values = np.ones((2, 2))
    assert values.shape == (1, 1)
""".strip()
    dangerous = "import os\n\ndef run_prototype():\n    print(os.getcwd())\n"

    assert validate_code_for_storage(runtime_failure).passed
    assert not validate_code_for_storage(dangerous).passed
