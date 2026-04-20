from .csv_io import OutputWriter, load_processed_keys, read_input_rows, row_key
from .search import find_website

DEFAULT_INPUT = "data/input.csv"
DEFAULT_OUTPUT = "data/output.csv"


def process_row(row: dict) -> dict:
    result = find_website(
        short_name=row.get("short_name", ""),
        city=row.get("city", ""),
        postal_code=row.get("postal_code", ""),
    )
    return {**row, **result}


def run(input_path: str = DEFAULT_INPUT, output_path: str = DEFAULT_OUTPUT) -> None:
    processed = load_processed_keys(output_path)
    if processed:
        print(f"Resuming: {len(processed)} row(s) already in {output_path}")

    with OutputWriter(output_path) as writer:
        for i, row in enumerate(read_input_rows(input_path), start=1):
            key = row_key(row)
            if key in processed:
                continue

            enriched = process_row(row)
            writer.write(enriched)

            label = row.get("short_name") or "?"
            note = enriched.get("notes") or "ok"
            print(f"[{i}] {label}: {enriched.get('domain') or '-'} ({note})")
