"""Small .env/settings helpers based on the assignment implementations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(dotenv_path: Path = Path(".env"), override: bool = True) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or not os.environ.get(key)):
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "ollama"
    llm_model: str | None = "qwen3:8b"
    output_dir: str = "outputs"
    arxiv_max_results: int = 3
    ollama_url: str = "http://localhost:11434/api/chat"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    exaone_base_url: str = "http://localhost:8000/v1"
    min_review_score: int = 7
    max_revision_rounds: int = 2
    prototype_max_repairs: int = 1
    prototype_execute: bool = True


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "ollama").strip().lower(),
        llm_model=os.getenv("LLM_MODEL") or "qwen3:8b",
        output_dir=os.getenv("OUTPUT_DIR", "outputs"),
        arxiv_max_results=int(os.getenv("ARXIV_MAX_RESULTS", "3")),
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat"),
        lmstudio_base_url=os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
        exaone_base_url=os.getenv("EXAONE_BASE_URL", "http://localhost:8000/v1"),
        min_review_score=int(os.getenv("MIN_REVIEW_SCORE", "7")),
        max_revision_rounds=int(os.getenv("MAX_REVISION_ROUNDS", "2")),
        prototype_max_repairs=int(os.getenv("PROTOTYPE_MAX_REPAIRS", "1")),
        prototype_execute=os.getenv("PROTOTYPE_EXECUTE", "True").strip().lower() in ("true", "1", "yes"),
    )
