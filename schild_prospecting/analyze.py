"""Turn scraped text into a summary, fit decision, and outreach drafts.

Pure heuristics — no API keys, no network. Keeps the script easy to run.
Anyone can edit the keyword lists and templates below.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

# --- What Schild Inc actually sells --------------------------------------
#
# Schild Inc makes custom metal labels, nameplates, and bike accessories
# (head badges, frame plates, chainring guards, etc.). We score fit by
# asking: does this company sell bikes, metal products, or branded goods
# where a custom metal label or bike accessory would add value?

BIKE_KEYWORDS = [
    "bike", "bicycle", "bicycles", "cycling", "cyclist",
    "fiets", "fietsen", "rijwiel", "tweewieler",
    "e-bike", "ebike", "frame", "frames",
    "componenten", "onderdelen",
]

METAL_KEYWORDS = [
    "metal", "brass", "aluminum", "aluminium", "steel", "stainless",
    "engraving", "engraved", "nameplate", "name plate", "plaque",
    "badge", "emblem", "signage", "sign", "label", "tag",
]

BRAND_KEYWORDS = [
    "custom", "bespoke", "handmade", "handcrafted", "artisan",
    "premium", "luxury", "heritage", "boutique", "limited edition",
    "branded", "merchandise", "gift",
]

RETAIL_KEYWORDS = [
    "shop", "store", "webshop", "catalog", "collection", "product",
    "winkel", "assortiment", "collectie",
]

# (offer_name, keywords that trigger this offer)
OFFERS: List[Tuple[str, List[str]]] = [
    ("Custom metal head badges for bike frames",
     BIKE_KEYWORDS + ["frame", "custom"]),
    ("Branded chainring guards & frame plates",
     BIKE_KEYWORDS + ["accessor", "component"]),
    ("Custom engraved nameplates & plaques",
     ["nameplate", "plaque", "engraving", "engraved", "award"]),
    ("Metal product labels & branded tags",
     METAL_KEYWORDS + BRAND_KEYWORDS),
    ("Custom bike accessories (bells, plates, bottle cages)",
     BIKE_KEYWORDS + RETAIL_KEYWORDS),
]

DEFAULT_OFFER = "Custom metal labels for branded products"


@dataclass
class Analysis:
    summary: str = ""
    products: str = ""
    fit_score: int = 1
    fit_reason: str = ""
    best_offer: str = ""
    personalization: str = ""
    email_subject: str = ""
    email_body: str = ""
    linkedin_message: str = ""
    contact_form_message: str = ""
    mockup_idea: str = ""
    signals: List[str] = field(default_factory=list)


# --- helpers -------------------------------------------------------------

def _lc(text: str) -> str:
    return (text or "").lower()


def _count_hits(text_lc: str, keywords: List[str]) -> int:
    return sum(1 for kw in keywords if kw in text_lc)


def _first_sentences(text: str, max_chars: int = 240) -> str:
    """Pick the first meaningful line(s) from the page text."""
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) < 30 or len(line) > 400:
            continue
        lower = line.lower()
        if any(skip in lower for skip in ("cookie", "privacy", "javascript", "menu")):
            continue
        return line[:max_chars]
    cleaned = " ".join(text.split())
    return cleaned[:max_chars]


def _detect_products(text_lc: str) -> str:
    """Return a short, human-readable list of likely product categories."""
    buckets = [
        ("bicycles", BIKE_KEYWORDS),
        ("metal goods / signage", METAL_KEYWORDS),
        ("retail / webshop", RETAIL_KEYWORDS),
        ("custom / branded goods", BRAND_KEYWORDS),
    ]
    found = [name for name, kws in buckets if _count_hits(text_lc, kws) >= 2]
    return ", ".join(found) if found else "unclear from site"


def _pick_offer(text_lc: str) -> str:
    best_name, best_hits = DEFAULT_OFFER, 0
    for name, kws in OFFERS:
        hits = _count_hits(text_lc, kws)
        if hits > best_hits:
            best_name, best_hits = name, hits
    return best_name


def _score_fit(text_lc: str) -> Tuple[int, str, List[str]]:
    bike = _count_hits(text_lc, BIKE_KEYWORDS)
    metal = _count_hits(text_lc, METAL_KEYWORDS)
    brand = _count_hits(text_lc, BRAND_KEYWORDS)
    retail = _count_hits(text_lc, RETAIL_KEYWORDS)

    signals = []
    if bike:
        signals.append(f"bike signals x{bike}")
    if metal:
        signals.append(f"metal signals x{metal}")
    if brand:
        signals.append(f"branding signals x{brand}")
    if retail:
        signals.append(f"retail signals x{retail}")

    if bike >= 3 and (brand + retail) >= 2:
        return 5, "Strong bike-industry fit with retail/branding signals.", signals
    if bike >= 2:
        return 4, "Bike-industry company — direct fit for bike accessories.", signals
    if metal >= 2 and brand >= 1:
        return 4, "Sells branded or custom metal goods — direct label fit.", signals
    if metal >= 1 or brand >= 2:
        return 3, "Some signals for custom metal labels.", signals
    if retail >= 2:
        return 2, "Retailer, but unclear whether custom labels fit.", signals
    return 1, "No clear signals that Schild Inc products would fit.", signals


def _pick_personalization(text: str, company: str) -> str:
    """Grab a line from the site we can reference in outreach."""
    snippet = _first_sentences(text, max_chars=160)
    if snippet:
        return f"Noticed on {company}'s site: \"{snippet}\""
    return f"Came across {company} while looking at your industry."


# --- draft templates -----------------------------------------------------

def _email_subject(company: str, offer: str) -> str:
    short_offer = offer.split("—")[0].strip()
    return f"Idea for {company}: {short_offer}"


def _email_body(company: str, country: str, offer: str,
                personalization: str, products: str) -> str:
    country_line = f" in {country}" if country else ""
    return (
        f"Hi {company} team,\n\n"
        f"{personalization}\n\n"
        f"I'm reaching out from Schild Inc. We make custom metal labels, "
        f"nameplates, and bike accessories for brands that care about how "
        f"their products look and feel. Based on what you're doing{country_line} "
        f"({products}), I think a good starting point would be:\n\n"
        f"    {offer}\n\n"
        f"Happy to send over a quick mockup with your logo so you can see "
        f"how it would look on one of your products. No cost, no obligation.\n\n"
        f"Would next week work for a short call?\n\n"
        f"Thanks,\n"
        f"Schild Inc"
    )


def _linkedin_message(company: str, offer: str) -> str:
    return (
        f"Hi — I came across {company} and liked what you're doing. "
        f"I run outreach at Schild Inc (custom metal labels & bike accessories). "
        f"I think {offer.lower()} could be a nice fit for you. "
        f"Open to a short chat? Happy to send a free mockup first."
    )


def _contact_form_message(company: str, offer: str) -> str:
    return (
        f"Hi {company} — Schild Inc here. We make custom metal labels and "
        f"bike accessories. I'd love to send you a free mockup of "
        f"{offer.lower()} branded with your logo. What's the best email to "
        f"reach you on?"
    )


def _mockup_idea(company: str, offer: str, products: str) -> str:
    return (
        f"Render a branded mockup of {offer.lower()} featuring {company}'s "
        f"logo, applied to a representative {products.split(',')[0].strip() or 'product'}. "
        f"Show two finish options (brushed stainless + matte black)."
    )


# --- public API ----------------------------------------------------------

def analyze(company_name: str, country: str, text: str) -> Analysis:
    """Run the full analysis for one scraped site."""
    text_lc = _lc(text)
    company = company_name or "there"

    summary = _first_sentences(text) or "No readable content found on the site."
    products = _detect_products(text_lc)
    fit_score, fit_reason, signals = _score_fit(text_lc)
    offer = _pick_offer(text_lc)
    personalization = _pick_personalization(text, company)

    return Analysis(
        summary=summary,
        products=products,
        fit_score=fit_score,
        fit_reason=fit_reason,
        best_offer=offer,
        personalization=personalization,
        email_subject=_email_subject(company, offer),
        email_body=_email_body(company, country, offer, personalization, products),
        linkedin_message=_linkedin_message(company, offer),
        contact_form_message=_contact_form_message(company, offer),
        mockup_idea=_mockup_idea(company, offer, products),
        signals=signals,
    )
