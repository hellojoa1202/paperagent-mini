import sys

from workflow import run_paper_reader


def main() -> None:
    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        topic = input("Research topic: ").strip()

    out_path = run_paper_reader(topic)
    print(f"Done. Review saved to {out_path}")


if __name__ == "__main__":
    main()
