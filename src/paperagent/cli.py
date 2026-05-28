"""Small CLI for the merged assignment project."""

from __future__ import annotations

import argparse

from paperagent.workflow import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Merged GY/SH paper-reading agent.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the paper-reading workflow")
    run_parser.add_argument("topic", help="Research topic to search on arXiv")
    run_parser.add_argument("--max-papers", "-n", type=int, default=None)
    run_parser.add_argument("--output-dir", default=None)
    run_parser.add_argument("--no-prototype", action="store_true")

    args = parser.parse_args()
    if args.command != "run":
        parser.print_help()
        return

    result = run_pipeline(
        topic=args.topic,
        max_papers=args.max_papers,
        output_dir=args.output_dir,
        enable_prototype=not args.no_prototype,
    )
    print("\nDone.")
    print(f"Output dir: {result.output_dir}")
    print(f"Paper summaries: {result.paper_summaries_path}")
    print(f"Final review: {result.final_review_path}")
    if result.method_extraction_path:
        print(f"Method extraction: {result.method_extraction_path}")
    if result.implementation_plan_path:
        print(f"Implementation plan: {result.implementation_plan_path}")
    if result.prototype_path:
        print(f"Prototype: {result.prototype_path}")


if __name__ == "__main__":
    main()
