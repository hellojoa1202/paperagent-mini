from __future__ import annotations


def test_package_importable() -> None:
    import paperagent

    assert paperagent.__version__ == "0.3.0"


def test_assignment_agents_importable() -> None:
    from paperagent.agents import (
        BaseAgent,
        CriticAgent,
        ExperimentReviewerAgent,
        ImpactReviewerAgent,
        MethodExtractionAgent,
        NoveltyReviewerAgent,
        PaperReaderAgent,
        PostdocAgent,
        ProfessorAgent,
        PrototypePlannerAgent,
        PrototypeWriterAgent,
        ReviewerAgent,
        parse_review_verdict,
        strip_code_fence,
    )

    assert BaseAgent()
    assert PaperReaderAgent("test").topic == "test"
    assert ReviewerAgent()
    assert CriticAgent()
    assert PostdocAgent()
    assert ProfessorAgent()
    assert MethodExtractionAgent()
    assert PrototypePlannerAgent()
    assert PrototypeWriterAgent()
    assert ExperimentReviewerAgent()
    assert NoveltyReviewerAgent()
    assert ImpactReviewerAgent()
    assert strip_code_fence("```python\nprint('ok')\n```") == "print('ok')"
    verdict = parse_review_verdict(
        '```json\n{"score": 8, "strengths": ["clear"], '
        '"weaknesses": [], "feedback": "keep it"}\n```'
    )
    assert verdict.score == 8
    assert verdict.feedback == "keep it"


def test_settings_defaults() -> None:
    from paperagent.config import Settings

    settings = Settings()
    assert settings.llm_provider == "ollama"
    assert settings.llm_model == "qwen3:8b"
    assert settings.arxiv_max_results == 3
    assert settings.min_review_score == 7
    assert settings.max_revision_rounds == 2
