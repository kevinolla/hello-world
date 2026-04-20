"""Entry point for the Schild Inc prospecting workflow.

Usage:
    python prospect.py
    python prospect.py --input my_list.csv --output results.csv
"""

import argparse

from schild_prospecting.workflow import DEFAULT_INPUT, DEFAULT_OUTPUT, run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visit prospect websites and generate outreach drafts for Schild Inc."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT,
                        help=f"Input CSV path (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help=f"Output CSV path (default: {DEFAULT_OUTPUT})")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(input_path=args.input, output_path=args.output)


if __name__ == "__main__":
    main()
