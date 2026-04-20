"""Read the prospect CSV and write results in a Google Sheets-friendly format."""

from __future__ import annotations

import csv
import os
from typing import Iterator, Set

INPUT_COLUMNS = ["company_name", "website", "country"]

OUTPUT_COLUMNS = [
    "company_name",
    "website",
    "country",
    "summary",
    "products",
    "fit_score",
    "fit_reason",
    "best_offer",
    "personalization",
    "email_subject",
    "email_body",
    "linkedin_message",
    "contact_form_message",
    "mockup_idea",
    "pages_visited",
    "error",
]


def read_input_rows(path: str) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield {k: (v or "").strip() for k, v in row.items()}


def load_processed_websites(path: str) -> Set[str]:
    if not os.path.exists(path):
        return set()
    done: Set[str] = set()
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            site = (row.get("website") or "").strip().lower()
            if site:
                done.add(site)
    return done


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
