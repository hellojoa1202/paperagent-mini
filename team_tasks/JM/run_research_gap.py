from __future__ import annotations

import argparse
import os
from pathlib import Path

from paperagent.config import load_dotenv
from team_tasks.JM.research_gap_agent import append_next_experiments, run_research_gap_stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="기존 research_report.md 또는 literature review")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--report", dest="full_report", type=Path, help="Next Experiments를 삽입할 보고서")
    parser.add_argument("--output", type=Path, default=Path("team_tasks/JM/outputs/research_report.md"))
    args = parser.parse_args()
    load_dotenv(Path(__file__).with_name(".env"))
    count = int(os.getenv("RESEARCH_GAP_COUNT", "3"))
    result = run_research_gap_stage(args.topic, args.report.read_text(encoding="utf-8"), count)
    if args.full_report:
        output_text = append_next_experiments(
            args.full_report.read_text(encoding="utf-8"),
            result.text,
        )
    else:
        output_text = result.text
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_text, encoding="utf-8")
    print(f"saved: {args.output}")
    print("format issues:", result.issues or "none")
    print("checkpoint:", result.checkpoint_value())


if __name__ == "__main__":
    main()
