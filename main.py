"""CLI entry: python main.py [--input ...] [--output ...] [--limit N] [--no-headless]"""
import argparse

from bike_shop_lookup.workflow import DEFAULT_INPUT, DEFAULT_OUTPUT, run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find the official website for each bike-shop row in a CSV."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to input CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to output CSV")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max new rows to process this run (default: 10). Use 0 for no limit.",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show the browser window (useful for debugging).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        input_path=args.input,
        output_path=args.output,
        limit=None if args.limit == 0 else args.limit,
        headless=not args.no_headless,
    )


if __name__ == "__main__":
    main()
