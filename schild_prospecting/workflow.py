"""Run the full prospecting flow: CSV in, scrape each site, analyze, CSV out."""

from __future__ import annotations

from dataclasses import asdict

from .analyze import analyze
from .csv_io import OutputWriter, load_processed_websites, read_input_rows
from .scraper import scrape_site

DEFAULT_INPUT = "data/prospects.csv"
DEFAULT_OUTPUT = "data/prospects_output.csv"


def process_row(row: dict) -> dict:
    company = row.get("company_name", "")
    website = row.get("website", "")
    country = row.get("country", "")

    site = scrape_site(website)
    analysis = analyze(company, country, site.combined_text())

    return {
        "company_name": company,
        "website": website,
        "country": country,
        **{k: v for k, v in asdict(analysis).items() if k != "signals"},
        "pages_visited": " | ".join(site.pages_visited),
        "error": site.error,
    }


def run(input_path: str = DEFAULT_INPUT, output_path: str = DEFAULT_OUTPUT) -> None:
    processed = load_processed_websites(output_path)
    if processed:
        print(f"Resuming: {len(processed)} row(s) already in {output_path}")

    with OutputWriter(output_path) as writer:
        for i, row in enumerate(read_input_rows(input_path), start=1):
            website_key = (row.get("website") or "").strip().lower()
            if website_key and website_key in processed:
                continue

            company = row.get("company_name") or "?"
            print(f"[{i}] {company} ({row.get('website') or '-'}) ...")
            try:
                result = process_row(row)
            except Exception as exc:
                result = {
                    "company_name": company,
                    "website": row.get("website", ""),
                    "country": row.get("country", ""),
                    "error": f"unexpected error: {exc}",
                    "fit_score": 1,
                }

            writer.write(result)
            note = result.get("error") or f"fit {result.get('fit_score')}/5"
            print(f"    -> {note}")
