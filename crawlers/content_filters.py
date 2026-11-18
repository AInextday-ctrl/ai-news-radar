#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Site-wide Editorial Purity Filter
=================================
Rejects low-value link-roundup newsletters (e.g. MIT Tech Review's
"The Download"), subscriber promo hubs ("Research Reports", "Roundtables"),
paid sponsored advertorials ("tag-sponsored", "produced by ... not written by"),
and shopping/cyber-sale deal listicles so only authentic, original reporting
enters or remains in the AI News Radar pipeline.
"""

import re
from typing import Iterable, Optional, Tuple

ROUNDUP_TITLE_RES = [
    re.compile(r"^\s*the\s+download\s*:", re.I),
    re.compile(r"^\s*roundtables?\s*:", re.I),
    re.compile(r"^\s*research\s+reports?\s*$", re.I),
    re.compile(r"^\s*(?:morning|evening|daily|weekly)\s+(?:briefing|digest|roundup|wrap|links)\s*:", re.I),
    re.compile(r"\b(?:daily|weekly|weekend)\s+(?:link\s+)?(?:roundup|digest|briefing|wrap-?up)\b", re.I),
    re.compile(r"\b(?:what\s+we['’]re\s+reading|the\s+must-?reads|links?\s+we\s+love)\b", re.I),
    re.compile(r"^\s*(?:sponsored|partner\s+content|paid\s+post|advertorial|webinar|live\s+event)\s*:", re.I),
    re.compile(r"\b(?:cyber\s+(?:monday|sale)|black\s+friday|prime\s+day)\b.*\b(?:deal|deals|sale|save|off|discount)\b", re.I),
    re.compile(r"^\s*best\s+.{0,60}\bdeals?\b", re.I),
]

ROUNDUP_URL_RES = [
    re.compile(r"/the-download-", re.I),
    re.compile(r"/roundtables?-", re.I),
    re.compile(r"/research-reports/?$", re.I),
    re.compile(r"/(?:sponsored|partner-content|brand-studio|paid-post|advertorial|webinars?|deals)/", re.I),
    re.compile(r"technologyreview\.com/2026/11/16/(?:1148565|1146070)/", re.I),
]

ROUNDUP_BODY_RES = [
    re.compile(r"this\s+is\s+today['’]s\s+edition\s+of\s+the\s+download", re.I),
    re.compile(r"i['’]ve\s+combed\s+the\s+internet\s+to\s+find\s+you", re.I),
    re.compile(r"this\s+content\s+was\s+produced\s+by\b.{0,160}\bnot\s+written\s+by\b", re.I | re.S),
    re.compile(r"\bnot\s+written\s+by\s+.{0,60}editorial\s+staff\b", re.I),
    re.compile(r"only\s+available\s+to\s+mit\s+technology\s+review\s+subscribers\.\s*$", re.I),
    re.compile(r"\b(?:sponsored\s+content|paid\s+post|partner\s+content)\b.{0,80}\b(?:produced\s+by|advertiser|brand\s+studio)\b", re.I),
]

BLOCKED_TAXONOMY_CLASSES = {
    "category-download-newsletter",
    "tag-sponsored",
    "category-sponsored",
    "category-partner-content",
    "category-brand-studio",
    "tag-roundtables",
    "tag-subscriber-only",
}

# Strict link-roundup citation marker (e.g. "(Bloomberg $)", "(Reuters $)", "(Wired $)") used by aggregator newsletters
PAYWALL_DOLLAR_CITE_RE = re.compile(
    r"\((AP|Reuters|Bloomberg|CNBC|Verge|The Verge|Wired|NYT|New York Times|WSJ|FT|Financial Times|Guardian|The Guardian|Nature|TechCrunch|MIT Technology Review|Axios|BBC|CNN)\s+\$\)"
)

MULTI_OUTLET_BULLET_RE = re.compile(
    r"(?:^|\n|\+)\s*[^\n]{15,240}\((AP|Reuters|Bloomberg|CNBC|Verge|The Verge|Wired|NYT|New York Times|WSJ|FT|Financial Times|Guardian|The Guardian|Nature|TechCrunch|MIT Technology Review|Axios|BBC|CNN)(?:\s+\$)?\)"
)


def detect_low_value_roundup_or_promo(
    title: str = "",
    url: str = "",
    body: str = "",
    summary: str = "",
    classes: Optional[Iterable[str]] = None,
) -> Tuple[bool, str]:
    """
    Returns (True, reason) if the article is a link-roundup digest,
    subscriber promo hub, event teaser, deals listicle, or sponsored advertorial.
    """
    t = (title or "").strip()
    u = (url or "").strip()
    b = (body or "").strip()
    s = (summary or "").strip()

    if classes:
        cls_low = {str(c).strip().lower() for c in classes if c}
        hit_cls = cls_low.intersection(BLOCKED_TAXONOMY_CLASSES)
        if hit_cls:
            return True, f"taxonomy:{sorted(hit_cls)[0]}"

    for rx in ROUNDUP_TITLE_RES:
        if t and rx.search(t):
            return True, f"title:{rx.pattern}"

    for rx in ROUNDUP_URL_RES:
        if u and rx.search(u):
            return True, f"url:{rx.pattern}"

    combined_text = f"{s}\n{b}"
    for rx in ROUNDUP_BODY_RES:
        if combined_text and rx.search(combined_text):
            return True, f"body:{rx.pattern}"

    # Multi-outlet link-aggregation bullet check: >=3 DISTINCT news outlets cited in newsletter bullet/paywall-dollar style
    # (Never triggers on a single-publisher investigative article URL unless it has >=2 paywall-dollar roundup markers like `(Bloomberg $)` `(Reuters $)`)
    if b:
        dollar_outlets = {m.group(1).lower() for m in PAYWALL_DOLLAR_CITE_RE.finditer(b)}
        if len(dollar_outlets) >= 2:
            return True, f"multi_outlet_dollar_roundup:{len(dollar_outlets)}"
        bullet_outlets = {m.group(1).lower() for m in MULTI_OUTLET_BULLET_RE.finditer(b)}
        if len(bullet_outlets) >= 4 and not re.search(r"/(?:news/)?articles/", u, re.I):
            return True, f"multi_outlet_roundup:{len(bullet_outlets)}"

    return False, ""


def is_low_value_roundup_or_promo(
    title: str = "",
    url: str = "",
    body: str = "",
    summary: str = "",
    classes: Optional[Iterable[str]] = None,
) -> bool:
    flagged, _ = detect_low_value_roundup_or_promo(
        title=title, url=url, body=body, summary=summary, classes=classes
    )
    return flagged
