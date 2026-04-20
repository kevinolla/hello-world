import glob
import os

from .csv_io import OutputWriter, load_processed_keys, read_input_rows, row_key
from .search import find_website

DEFAULT_INPUT = "data/Search email by KVK - Sheet1.csv"
DEFAULT_OUTPUT = "data/output.csv"
INPUT_FALLBACK_GLOB = "data/Search email by KVK - Sheet1*.csv"


def resolve_input_path(path: str) -> str:
    """Return the given path if it exists, otherwise fall back to any
    ``Search email by KVK - Sheet1*.csv`` match under ``data/``."""
    if os.path.exists(path):
        return path
    matches = sorted(glob.glob(INPUT_FALLBACK_GLOB))
    if matches:
        return matches[0]
    return path  # let the caller raise a clear FileNotFoundError


def process_row(row: dict) -> dict:
    result = find_website(
        short_name=row.get("short_name", ""),
        city=row.get("city", ""),
        postal_code=row.get("postal_code", ""),
    )
    return {**row, **result}


def run(input_path: str = DEFAULT_INPUT, output_path: str = DEFAULT_OUTPUT) -> None:
    input_path = resolve_input_path(input_path)
    print(f"Reading {input_path}")

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
