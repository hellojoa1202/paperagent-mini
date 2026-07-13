from __future__ import annotations

import argparse
import os
from pathlib import Path

from paperagent.config import load_dotenv
from team_tasks.SH.prototype_reviewer import review_and_repair


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("code", type=Path, help="검증할 prototype.py")
    parser.add_argument("--execute", action="store_true", help="신뢰 가능한 격리 환경에서만 사용")
    parser.add_argument("--output", type=Path, default=Path("team_tasks/SH/outputs/prototype_fixed.py"))
    args = parser.parse_args()
    load_dotenv(Path(__file__).with_name(".env"))
    max_repairs = int(os.getenv("PROTOTYPE_MAX_REPAIRS", "1"))
    fixed, reviews = review_and_repair(
        args.code.read_text(encoding="utf-8"),
        execute=args.execute,
        max_repairs=max_repairs,
    )
    for index, review in enumerate(reviews, start=1):
        print(f"review {index}: passed={review.passed}, error={review.error}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(fixed, encoding="utf-8")
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
