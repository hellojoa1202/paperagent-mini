from __future__ import annotations

import argparse
import json
from pathlib import Path

from paperagent.config import load_dotenv
from team_tasks.GY.summary_quality import run_reflection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path, help="title과 abstract가 있는 JSON 파일")
    args = parser.parse_args()
    load_dotenv(Path(__file__).with_name(".env"))
    case = json.loads(args.case.read_text(encoding="utf-8"))
    print(json.dumps(run_reflection(case["title"], case["abstract"]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
