"""Small CLI for the PaperAgent mini project."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="PaperAgent mini literature-review workflow.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the paper-reading workflow")
    run_parser.add_argument("topic", help="Research topic to search on arXiv")
    run_parser.add_argument("--max-papers", "-n", type=int, default=None)
    run_parser.add_argument("--output-dir", default=None)
    run_parser.add_argument("--no-prototype", action="store_true")
    run_parser.add_argument("--no-review", action="store_true")
    run_parser.add_argument("--extra-reviewers", action="store_true")
    run_parser.add_argument("--no-report", action="store_true")
    run_parser.add_argument("--abstract-only", action="store_true")
    run_parser.add_argument("--quick-review", action="store_true")
    run_parser.add_argument("--no-critic", action="store_true")

    args = parser.parse_args()
    if args.command != "run":
        parser.print_help()
        return

    from paperagent.workflow import run_pipeline

    try:
        result = run_pipeline(
            topic=args.topic,
            max_papers=args.max_papers,
            output_dir=args.output_dir,
            enable_prototype=not args.no_prototype,
            enable_review=not args.no_review,
            enable_extra_reviewers=args.extra_reviewers,
            enable_report=not args.no_report,
            read_pdf=not args.abstract_only,
            enable_literature_review=not args.quick_review,
            enable_critic=not args.no_critic,
        )
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("\nDone.")
    print(f"Output dir: {result.output_dir}")
    print(f"Research report: {result.report_path}")
    if result.prototype_path:
        print(f"Prototype: {result.prototype_path}")


if __name__ == "__main__":
    main()
