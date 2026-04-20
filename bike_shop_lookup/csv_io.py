import csv
import os
import re
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

# Map normalised header -> canonical column name. Covers the common
# Dutch/English variants exported from KVK-style sheets.
HEADER_ALIASES = {
    "kvknumber": "kvk_number",
    "kvk": "kvk_number",
    "kvknummer": "kvk_number",
    "kvk_nummer": "kvk_number",
    "establishmentnumber": "establishment_number",
    "vestigingsnummer": "establishment_number",
    "vestiging": "establishment_number",
    "shortname": "short_name",
    "handelsnaam": "short_name",
    "name": "short_name",
    "businessname": "short_name",
    "bedrijfsnaam": "short_name",
    "tradename": "short_name",
    "street": "street",
    "straat": "street",
    "straatnaam": "street",
    "address": "street",
    "adres": "street",
    "housenumber": "house_number",
    "huisnummer": "house_number",
    "nummer": "house_number",
    "postalcode": "postal_code",
    "postcode": "postal_code",
    "zip": "postal_code",
    "zipcode": "postal_code",
    "city": "city",
    "plaats": "city",
    "stad": "city",
    "vestigingsplaats": "city",
    "woonplaats": "city",
}


def _normalise_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (header or "").lower())


def _canonical_column(header: str) -> str:
    key = _normalise_header(header)
    if key in HEADER_ALIASES:
        return HEADER_ALIASES[key]
    return header  # keep original if unknown


# "1234 AB Amsterdam" -> ("1234 AB", "Amsterdam")
_POSTAL_CITY_RE = re.compile(r"^\s*(\d{4}\s?[A-Za-z]{2})\s+(.+?)\s*$")
# "Harinxmastrjitte 6", "Westeinde 1A", "Fricoweg 1e" -> (street, house_number)
_STREET_HOUSE_RE = re.compile(r"^\s*(.+?)\s+(\d+[A-Za-z]?(?:[-/]\d+[A-Za-z]?)?)\s*$")


def _split_postal_city(value: str) -> Tuple[str, str]:
    match = _POSTAL_CITY_RE.match(value or "")
    if not match:
        return value, ""
    return match.group(1).upper().replace("  ", " "), match.group(2)


def _split_street_housenumber(value: str) -> Tuple[str, str]:
    match = _STREET_HOUSE_RE.match(value or "")
    if not match:
        return value, ""
    return match.group(1), match.group(2)


def _enrich_combined_fields(row: dict) -> dict:
    """Split combined postal/city and street/house-number fields when the
    source sheet puts them into a single column."""
    if not row.get("city") and row.get("postal_code"):
        postal, city = _split_postal_city(row["postal_code"])
        row["postal_code"], row["city"] = postal, city or row.get("city", "")
    if not row.get("house_number") and row.get("street"):
        street, house = _split_street_housenumber(row["street"])
        row["street"], row["house_number"] = street, house or row.get("house_number", "")
    return row


def row_key(row: dict) -> Tuple[str, str]:
    """Stable identifier for deduplication / resume."""
    return (
        (row.get("kvk_number") or "").strip(),
        (row.get("establishment_number") or "").strip(),
    )


def read_input_rows(path: str) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        field_map = {h: _canonical_column(h) for h in (reader.fieldnames or [])}
        for row in reader:
            mapped = {
                field_map[k]: (v or "").strip()
                for k, v in row.items()
                if k is not None
            }
            yield _enrich_combined_fields(mapped)


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
