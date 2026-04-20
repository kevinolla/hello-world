"""Playwright-backed website lookup.

Uses a real headless browser so the search works against DuckDuckGo's
JavaScript-rendered results page. A single browser context is reused
across rows for speed.
"""
from typing import List
from urllib.parse import parse_qs, quote_plus, urlparse

from .domain import extract_domain, is_excluded

SEARCH_URL = "https://duckduckgo.com/?q={query}"
RESULT_SELECTORS = (
    "a[data-testid='result-title-a']",
    "a.result__a",
    "article a[href^='http']",
)


def _unwrap_ddg_redirect(url: str) -> str:
    """DuckDuckGo sometimes wraps results in /l/?uddg=<real-url>."""
    if "duckduckgo.com/l/" not in url:
        return url
    try:
        qs = parse_qs(urlparse(url).query)
        real = qs.get("uddg", [""])[0]
        return real or url
    except Exception:
        return url


def _build_query(business_name: str, postal_code: str) -> str:
    return " ".join(p.strip() for p in (business_name, postal_code) if p and p.strip())


class PlaywrightSearcher:
    """Context manager that owns a browser session for multiple queries."""

    def __init__(self, headless: bool = True, timeout_ms: int = 15000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "PlaywrightSearcher":
        from playwright.sync_api import sync_playwright  # lazy import

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="nl-NL",
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()

    def _collect_links(self, page) -> List[str]:
        links: List[str] = []
        for selector in RESULT_SELECTORS:
            try:
                found = page.eval_on_selector_all(
                    selector, "els => els.map(e => e.href)"
                )
            except Exception:
                found = []
            for url in found:
                if url and url not in links:
                    links.append(_unwrap_ddg_redirect(url))
            if links:
                break
        return links

    def find_website(self, business_name: str, postal_code: str) -> dict:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout

        query = _build_query(business_name, postal_code)
        if not query:
            return {"website": "", "domain": "", "notes": "empty query"}

        page = self._context.new_page()
        try:
            page.goto(
                SEARCH_URL.format(query=quote_plus(query)),
                timeout=self.timeout_ms,
                wait_until="domcontentloaded",
            )
            try:
                page.wait_for_selector(
                    ", ".join(RESULT_SELECTORS), timeout=self.timeout_ms
                )
            except PlaywrightTimeout:
                pass
            links = self._collect_links(page)
        except PlaywrightTimeout:
            return {"website": "", "domain": "", "notes": "timeout"}
        except Exception as exc:
            return {"website": "", "domain": "", "notes": f"search error: {exc}"}
        finally:
            page.close()

        if not links:
            return {"website": "", "domain": "", "notes": "no results"}

        for url in links:
            if url and not is_excluded(url):
                return {"website": url, "domain": extract_domain(url), "notes": ""}
        return {"website": "", "domain": "", "notes": "no suitable result"}
