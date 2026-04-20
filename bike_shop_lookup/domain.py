from urllib.parse import urlparse

EXCLUDED_DOMAINS = {
    "facebook.com",
    "m.facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
    "google.com",
    "google.nl",
    "maps.google.com",
    "wikipedia.org",
    "nl.wikipedia.org",
    "yelp.com",
    "yelp.nl",
    "tripadvisor.com",
    "tripadvisor.nl",
    "kvk.nl",
    "bedrijvenpagina.nl",
    "telefoonboek.nl",
    "detelefoongids.nl",
    "openingstijden.nl",
    "fietsenwinkel.nl",
    "marktplaats.nl",
    "bol.com",
    "amazon.com",
    "amazon.nl",
}


def extract_domain(url: str) -> str:
    """Return the hostname without a leading ``www.`` prefix."""
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_excluded(url: str) -> bool:
    """True if the URL belongs to a directory/social/aggregator site."""
    host = extract_domain(url)
    if not host:
        return True
    if host in EXCLUDED_DOMAINS:
        return True
    parts = host.split(".")
    for i in range(len(parts) - 1):
        if ".".join(parts[i:]) in EXCLUDED_DOMAINS:
            return True
    return False
