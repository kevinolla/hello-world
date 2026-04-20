"""CSV read/write for the 3-column bike-shop sheet.

Input columns : Business Name, Address, Postal code
Output columns: business_name, address, postal_code, website, domain, notes
"""
import csv
import os
import re
from typing import Iterator, Set, Tuple

INPUT_COLUMNS = ["business_name", "address", "postal_code"]
OUTPUT_COLUMNS = INPUT_COLUMNS + ["website", "domain", "notes"]

HEADER_ALIASES = {
    "businessname": "business_name",
    "business": "business_name",
    "name": "business_name",
    "shortname": "business_name",
    "handelsnaam": "business_name",
    "address": "address",
    "adres": "address",
    "street": "address",
    "postalcode": "postal_code",
    "postcode": "postal_code",
    "zip": "postal_code",
    "zipcode": "postal_code",
}


def _normalise_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (header or "").lower())


def _canonical_column(header: str) -> str:
    key = _normalise_header(header)
    return HEADER_ALIASES.get(key, header)


def row_key(row: dict) -> Tuple[str, str]:
    """Resume identifier: business name + postal code."""
    return (
        (row.get("business_name") or "").strip().lower(),
        (row.get("postal_code") or "").strip().lower(),
    )


def read_input_rows(path: str) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        field_map = {h: _canonical_column(h) for h in (reader.fieldnames or [])}
        for row in reader:
            yield {
                field_map[k]: (v or "").strip()
                for k, v in row.items()
                if k is not None
            }


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
