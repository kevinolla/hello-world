"""Row-by-row website lookup orchestration."""
import glob
import os
from typing import Optional

from .csv_io import OutputWriter, load_processed_keys, read_input_rows, row_key
from .search import PlaywrightSearcher

DEFAULT_INPUT = "data/input.csv"
DEFAULT_OUTPUT = "data/output.csv"
INPUT_FALLBACK_GLOBS = (
    "data/*.csv",
)


def resolve_input_path(path: str) -> str:
    """Return ``path`` if it exists; otherwise fall back to any CSV under data/."""
    if os.path.exists(path):
        return path
    for pattern in INPUT_FALLBACK_GLOBS:
        matches = sorted(p for p in glob.glob(pattern) if os.path.basename(p) != "output.csv")
        if matches:
            return matches[0]
    return path


def run(
    input_path: str = DEFAULT_INPUT,
    output_path: str = DEFAULT_OUTPUT,
    limit: Optional[int] = 10,
    headless: bool = True,
) -> None:
    input_path = resolve_input_path(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    print(f"Reading {input_path}")
    processed = load_processed_keys(output_path)
    if processed:
        print(f"Resuming: {len(processed)} row(s) already in {output_path}")

    written = 0
    with OutputWriter(output_path) as writer, PlaywrightSearcher(headless=headless) as searcher:
        for i, row in enumerate(read_input_rows(input_path), start=1):
            if limit is not None and written >= limit:
                print(f"Reached limit of {limit} new rows — stopping.")
                break
            if row_key(row) in processed:
                continue

            result = searcher.find_website(
                business_name=row.get("business_name", ""),
                postal_code=row.get("postal_code", ""),
            )
            enriched = {**row, **result}
            writer.write(enriched)
            written += 1

            label = row.get("business_name") or "?"
            note = enriched.get("notes") or "ok"
            print(f"[{i}] {label}: {enriched.get('domain') or '-'} ({note})")

    print(f"Done. Wrote {written} new row(s) to {output_path}.")
