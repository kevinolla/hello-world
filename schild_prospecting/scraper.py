"""Visit a company website with Playwright and grab text from the key pages.

We try the homepage first, then look for links that match typical
"about", "products", "shop", "catalog", and "contact" pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

PAGE_KEYWORDS = {
    "about": ["about", "over-ons", "over ons", "who-we-are", "company", "bedrijf"],
    "products": [
        "product", "shop", "store", "catalog", "catalogue",
        "collection", "webshop", "assortiment", "collectie",
    ],
    "contact": ["contact", "kontakt", "get-in-touch", "reach-us"],
}

MAX_CHARS_PER_PAGE = 4000
NAV_TIMEOUT_MS = 20000


@dataclass
class SiteContent:
    url: str
    homepage_text: str = ""
    about_text: str = ""
    products_text: str = ""
    contact_text: str = ""
    pages_visited: List[str] = field(default_factory=list)
    error: str = ""

    def combined_text(self) -> str:
        parts = [self.homepage_text, self.about_text, self.products_text, self.contact_text]
        return "\n\n".join(p for p in parts if p)


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.split(":")[0].lower().lstrip("www.") == \
           urlparse(b).netloc.split(":")[0].lower().lstrip("www.")


def _pick_link(links: List[dict], keywords: List[str], base_url: str) -> Optional[str]:
    """Return the first link whose href or text matches any keyword."""
    for link in links:
        href = (link.get("href") or "").lower()
        text = (link.get("text") or "").lower()
        if not href:
            continue
        absolute = urljoin(base_url, link["href"])
        if not _same_host(absolute, base_url):
            continue
        for kw in keywords:
            if kw in href or kw in text:
                return absolute
    return None


def _extract_links(page) -> List[dict]:
    return page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => ({href: e.getAttribute('href'), text: (e.innerText || '').trim()}))",
    )


def _visible_text(page) -> str:
    try:
        text = page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:
        text = ""
    return (text or "").strip()[:MAX_CHARS_PER_PAGE]


def _goto(page, url: str) -> bool:
    try:
        page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        return True
    except Exception:
        return False


def scrape_site(website: str) -> SiteContent:
    """Scrape homepage + about / products / contact pages if linked."""
    from playwright.sync_api import sync_playwright

    url = _normalize_url(website)
    content = SiteContent(url=url)
    if not url:
        content.error = "empty url"
        return content

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            if not _goto(page, url):
                content.error = "failed to load homepage"
                return content
            content.homepage_text = _visible_text(page)
            content.pages_visited.append(page.url)

            try:
                links = _extract_links(page)
            except Exception:
                links = []

            targets: Dict[str, Optional[str]] = {
                "about": _pick_link(links, PAGE_KEYWORDS["about"], page.url),
                "products": _pick_link(links, PAGE_KEYWORDS["products"], page.url),
                "contact": _pick_link(links, PAGE_KEYWORDS["contact"], page.url),
            }

            for kind, target in targets.items():
                if not target:
                    continue
                if not _goto(page, target):
                    continue
                text = _visible_text(page)
                setattr(content, f"{kind}_text", text)
                content.pages_visited.append(page.url)
        finally:
            context.close()
            browser.close()

    return content
