from __future__ import annotations

import argparse
import os
from pathlib import Path

from paperagent.config import load_dotenv
from team_tasks.JM.research_gap_agent import ResearchGapAgent, validate_gap_output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="기존 research_report.md 또는 literature review")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--output", type=Path, default=Path("team_tasks/JM/outputs/research_gaps.md"))
    args = parser.parse_args()
    load_dotenv(Path(__file__).with_name(".env"))
    count = int(os.getenv("RESEARCH_GAP_COUNT", "3"))
    result = ResearchGapAgent().propose(args.topic, args.report.read_text(encoding="utf-8"), count)
    issues = validate_gap_output(result, count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"saved: {args.output}")
    print("format issues:", issues or "none")


if __name__ == "__main__":
    main()
