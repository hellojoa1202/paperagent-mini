from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from paperagent.config import load_dotenv
from team_tasks.JY.report_quality import check_report, generate_stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--topic", default="paper agent literature review")
    parser.add_argument("--generate", choices=("postdoc", "critic", "professor"))
    args = parser.parse_args()
    load_dotenv(Path(__file__).with_name(".env"))
    text = args.report.read_text(encoding="utf-8")
    result = check_report(text, int(os.getenv("REPORT_MAX_CHARS", "24000")))
    print(json.dumps(asdict(result) | {"passed": result.passed}, ensure_ascii=False, indent=2))
    if args.generate:
        output = Path(f"team_tasks/JY/outputs/{args.generate}_result.md")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(generate_stage(args.generate, args.topic, text), encoding="utf-8")
        print(f"saved: {output}")


if __name__ == "__main__":
    main()
