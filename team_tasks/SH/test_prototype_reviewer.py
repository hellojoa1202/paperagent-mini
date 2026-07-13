from team_tasks.SH.prototype_reviewer import validate_code


def test_rejects_invalid_syntax() -> None:
    result = validate_code("def broken(:\n    pass")
    assert not result.syntax_ok
    assert "SyntaxError" in result.error


def test_executes_valid_code() -> None:
    result = validate_code("print('ok')", execute=True, timeout=3)
    assert result.passed
    assert "ok" in result.stdout
