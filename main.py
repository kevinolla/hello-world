import argparse

from bike_shop_lookup.workflow import DEFAULT_INPUT, DEFAULT_OUTPUT, run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Look up bike-shop websites from a CSV.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to input CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to output CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(input_path=args.input, output_path=args.output)


if __name__ == "__main__":
    main()
