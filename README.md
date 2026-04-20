# hello-world

This repo has two small workflows:

1. **bike_shop_lookup** — find a website for each shop in a KVK CSV (DuckDuckGo search).
2. **schild_prospecting** — for each prospect website, visit it with Playwright,
   figure out what they sell, score the fit with Schild Inc, and generate outreach drafts.

---

## Schild Inc prospecting workflow

### What it does

Given a CSV of prospects with columns `company_name,website,country`, the script:

1. Opens each website with Playwright (headless Chrome).
2. Reads the homepage, then tries to follow links to the about, products, and contact pages.
3. Extracts a short business summary and a guess at what they sell.
4. Scores fit for Schild Inc (1–5), picks the best offer, and writes:
   - email subject + email draft
   - LinkedIn message
   - short contact-form message
   - mockup idea
5. Writes everything to a single CSV you can import into Google Sheets.

### Setup (one time)

```bash
pip install -r requirements.txt
playwright install chromium
```

### Run

1. Make a CSV with this header:

   ```csv
   company_name,website,country
   ```

   See `data/prospects_sample.csv` for an example.

2. Run:

   ```bash
   python prospect.py --input data/prospects_sample.csv --output data/prospects_output.csv
   ```

   Defaults if you omit the flags:
   - input: `data/prospects.csv`
   - output: `data/prospects_output.csv`

3. Open `data/prospects_output.csv` in Google Sheets (File → Import → Upload).

### Output columns

`company_name, website, country, summary, products, fit_score, fit_reason,
best_offer, personalization, email_subject, email_body, linkedin_message,
contact_form_message, mockup_idea, pages_visited, error`

### Notes

- The script is resumable — re-running with the same output file will skip rows already written.
- All drafts are generated from keyword heuristics and templates in
  `schild_prospecting/analyze.py`. Edit that file to tune the offers,
  keywords, or wording.
- If a site fails to load, the row is still written with the `error` column
  filled in so you can review it later.

---

## Bike shop lookup workflow

See `main.py` and `bike_shop_lookup/` — unchanged from before.
