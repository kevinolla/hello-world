from typing import Iterable, Optional

from .domain import extract_domain, is_excluded


def build_query(short_name: str, city: str, postal_code: str) -> str:
    parts = [p.strip() for p in (short_name, city, postal_code) if p and p.strip()]
    return " ".join(parts)


def _ddg_results(query: str, max_results: int) -> Iterable[dict]:
    from ddgs import DDGS  # imported lazily so the module loads without the dep

    with DDGS() as ddgs:
        yield from ddgs.text(query, max_results=max_results)


def _pick_url(results: Iterable[dict]) -> Optional[str]:
    for result in results:
        url = result.get("href") or result.get("url") or result.get("link")
        if url and not is_excluded(url):
            return url
    return None


def find_website(
    short_name: str,
    city: str,
    postal_code: str,
    max_results: int = 8,
) -> dict:
    """Look up the official website for a single row.

    Returns a dict with keys: website, domain, notes.
    """
    query = build_query(short_name, city, postal_code)
    if not query:
        return {"website": "", "domain": "", "notes": "empty query"}

    try:
        results = list(_ddg_results(query, max_results=max_results))
    except ImportError:
        return {"website": "", "domain": "", "notes": "ddgs package not installed"}
    except Exception as exc:
        return {"website": "", "domain": "", "notes": f"search error: {exc}"}

    if not results:
        return {"website": "", "domain": "", "notes": "no results"}

    url = _pick_url(results)
    if not url:
        return {"website": "", "domain": "", "notes": "no suitable result"}

    return {"website": url, "domain": extract_domain(url), "notes": ""}
