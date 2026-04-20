import csv
import os
from typing import Iterator, Set, Tuple

INPUT_COLUMNS = [
    "kvk_number",
    "establishment_number",
    "short_name",
    "street",
    "house_number",
    "postal_code",
    "city",
]

OUTPUT_COLUMNS = INPUT_COLUMNS + ["website", "domain", "notes"]


def row_key(row: dict) -> Tuple[str, str]:
    """Stable identifier for deduplication / resume."""
    return (
        (row.get("kvk_number") or "").strip(),
        (row.get("establishment_number") or "").strip(),
    )


def read_input_rows(path: str) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield {k: (v or "").strip() for k, v in row.items()}


def load_processed_keys(path: str) -> Set[Tuple[str, str]]:
    if not os.path.exists(path):
        return set()
    keys: Set[Tuple[str, str]] = set()
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            keys.add(row_key(row))
    return keys


class OutputWriter:
    """Append rows to the output CSV and flush after every write."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._file = None
        self._writer = None

    def __enter__(self):
        file_exists = os.path.exists(self.path) and os.path.getsize(self.path) > 0
        self._file = open(self.path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=OUTPUT_COLUMNS)
        if not file_exists:
            self._writer.writeheader()
            self._file.flush()
        return self

    def write(self, row: dict) -> None:
        clean = {col: row.get(col, "") for col in OUTPUT_COLUMNS}
        self._writer.writerow(clean)
        self._file.flush()
        os.fsync(self._file.fileno())

    def __exit__(self, exc_type, exc, tb):
        if self._file:
            self._file.close()
