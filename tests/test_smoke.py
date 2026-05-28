from __future__ import annotations


def test_package_importable() -> None:
    import paperagent

    assert paperagent.__version__ == "0.1.0"


def test_assignment_agents_importable() -> None:
    from paperagent.agents import (
        MethodExtractionAgent,
        PaperReaderAgent,
        PrototypePlannerAgent,
        PrototypeWriterAgent,
        strip_code_fence,
    )

    assert PaperReaderAgent("test").topic == "test"
    assert MethodExtractionAgent()
    assert PrototypePlannerAgent()
    assert PrototypeWriterAgent()
    assert strip_code_fence("```python\nprint('ok')\n```") == "print('ok')"


def test_settings_defaults() -> None:
    from paperagent.config import Settings

    settings = Settings()
    assert settings.llm_provider == "ollama"
    assert settings.arxiv_max_results == 3
