from unittest.mock import MagicMock
from team_tasks.SH.prototype_reviewer import validate_code, review_and_repair
from paperagent.agents import PrototypeReviewerAgent


def test_rejects_invalid_syntax() -> None:
    result = validate_code("def broken(:\n    pass")
    assert not result.syntax_ok
    assert "SyntaxError" in result.error


def test_executes_valid_code() -> None:
    result = validate_code("print('ok')", execute=True, timeout=3)
    assert result.passed
    assert "ok" in result.stdout


def test_review_and_repair_with_mock(monkeypatch) -> None:
    mock_repair = MagicMock(return_value="print('repaired')")
    monkeypatch.setattr(PrototypeReviewerAgent, "repair", mock_repair)

    broken_code = "def broken(:\n    pass"
    fixed, reviews = review_and_repair(broken_code, execute=True, max_repairs=1)

    assert fixed == "print('repaired')"
    assert len(reviews) == 2
    assert not reviews[0].passed
    assert reviews[1].passed
    mock_repair.assert_called_once()

