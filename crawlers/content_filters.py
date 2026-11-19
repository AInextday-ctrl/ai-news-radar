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


# =========================================================================
# Photo Caption, Credit & Newsletter Boilerplate Pure Filters
# =========================================================================

PHOTO_CAPTION_INDICATORS = [
    re.compile(r"^(?:view image in fullscreen|photograph:|photo:|credit:|image:|illustration:|source:|caption:)\s*", re.I),
    re.compile(r"\b(?:photograph|photo|credit|image|illustration):\s*[A-Za-z0-9\s,\./\-]{3,60}$", re.I),
    re.compile(r"\b(?:in a|in this)\s+(?:company\s+)?(?:handout\s+)?(?:portrait|photo(?:graph)?)\s+released by\b", re.I),
    re.compile(r"^(?:file photo|archive photo|handout photo|editorial image|stock photo):?\s*", re.I),
    re.compile(r"^(?:photo\s+by|image\s+courtesy\s+of|courtesy\s+of)\s+[A-Za-z0-9\s,\./\-]{3,60}$", re.I),
    re.compile(r",?\s*in a (?:company\s+)?(?:handout\s+)?portrait released by the company(?:\s+in\s+\d{4})?(?:\.|$)", re.I),
    re.compile(r",?\s*in a (?:company\s+)?(?:handout\s+)?photo(?:graph)?(?:\s+released by\s+.*?)?(?:\.|$)", re.I),
    re.compile(r"^\s*shown (?:here\s+)?(?:in|at|during)\s+.*?(?:\.|$)", re.I),
    # Chinese photo credit / caption indicators
    re.compile(r"(?:公司\d{4}年发布的肖像照|资料照片|资料图片|新华社发|法新社图|视觉中国供图|路透社图|封面配图|正文配图)"),
    re.compile(r"[（\(](?:资料图片|资料照片|供图|视觉中国|新华社发|法新社|路透社|Getty Images)[）\)]\s*$", re.I),
    re.compile(r"^(?:摄影|供图|来源|制图|图源)[：:]\s*"),
    re.compile(r"^(?:图为|图说|配图|照片显示|肖像照|插图)[：:\s]"),
    re.compile(r"^(?:全屏查看图片|全屏查看图像|查看全屏图片)"),
]

NEWSLETTER_PROMO_INDICATORS = [
    re.compile(r"^(?:get the most important|sign up for|subscribe to|read more about|listen to|follow us on).*?(?:inbox|newsletter|podcast|updates)", re.I),
    re.compile(r"\bin your inbox each week\.?$", re.I),
    re.compile(r"^(?:to receive this newsletter in your inbox|delivered directly to your inbox)", re.I),
    re.compile(r"^(?:sign up for the \w+ newsletter|get our newsletter)", re.I),
    re.compile(r"^(?:this article was originally published on|read the original article on)", re.I),
    re.compile(r"^(?:每周在您的收件箱中获取|订阅我们的通讯|点击订阅|更多报道请关注|本文最初发表于|阅读原文请访问)"),
]


def clean_guardian_fullscreen_prefix(text: str) -> str:
    """
    Cleans Guardian-style glued image captions like:
    'View image in fullscreen <Caption text>. Photograph: <Credit><Real sentence...>'
    Returns stripped substantive text or empty string if it was purely a caption.
    """
    if not text:
        return ""
    t = text.strip()
    if re.search(r"^view image in fullscreen", t, re.I):
        cleaned = re.sub(
            r"^view image in fullscreen\s*.*?(?:photograph|photo|credit):\s*[A-Za-z0-9\s,\./\-]+(?:\.|\s*—|\s*-\s*|(?=[A-Z\u4e00-\u9fa5]))",
            "",
            t,
            flags=re.I
        ).strip()
        if len(cleaned) < 30:
            return ""
        return cleaned
    return t


def is_newsletter_or_promo_noise(text: str) -> bool:
    """Detects whether text is an email newsletter signup footer or promo link."""
    if not text:
        return False
    t = text.strip()
    return any(rx.search(t) for rx in NEWSLETTER_PROMO_INDICATORS)


def is_photo_caption_or_credit(
    text: str,
    inline_images: Optional[Iterable[Any]] = None,
    cover_caption: Optional[str] = None,
    is_zh: bool = False
) -> bool:
    """
    Returns True if the text represents an image caption, photo credit,
    or matches an inline/cover image caption or alt text.
    """
    if not text:
        return True
    t = text.strip()
    if len(t) < 5:
        return True

    # 1. Indicator regexes
    for rx in PHOTO_CAPTION_INDICATORS:
        if rx.search(t):
            return True

    # 2. Match against candidate image captions and alt texts
    candidate_captions = []
    if cover_caption:
        candidate_captions.append(str(cover_caption).strip().lower())

    if inline_images:
        for im in inline_images:
            if isinstance(im, dict):
                for k in ("caption", "alt", "caption_zh", "alt_zh"):
                    v = str(im.get(k) or "").strip().lower()
                    if v:
                        candidate_captions.append(v)
            elif isinstance(im, str):
                pass

    t_low = t.lower()
    for cap in candidate_captions:
        if len(cap) < 15:
            continue
        # Exact or substring match
        if t_low == cap or (len(t_low) >= 20 and t_low in cap):
            return True
        if len(cap) >= 20 and cap in t_low and len(t_low) <= len(cap) + 40:
            return True
        # Overlap match
        tw = set(t_low.split())
        cw = set(cap.split())
        if len(tw) >= 5 and len(cw) >= 5:
            overlap = len(tw & cw) / float(min(len(tw), len(cw)))
            if overlap >= 0.85:
                return True

    return False


def clean_article_paragraphs(
    paragraphs: Iterable[Any],
    inline_images: Optional[Iterable[Any]] = None,
    cover_caption: Optional[str] = None,
    is_zh: bool = False
) -> List[str]:
    """
    Cleans paragraph lists by:
    1. Un-gluing and stripping 'View image in fullscreen' prefixes.
    2. Dropping pure image captions and photo credits.
    3. Dropping newsletter signup footers and promotional noise.
    4. Removing empty or trivial fragments.
    """
    if not paragraphs:
        return []

    cleaned = []
    for p in paragraphs:
        p_str = str(p or "").strip()
        if not p_str:
            continue
        # Un-glue Guardian fullscreen prefix
        p_str = clean_guardian_fullscreen_prefix(p_str)
        if not p_str or len(p_str) < 10:
            continue
        # Check newsletter promo
        if is_newsletter_or_promo_noise(p_str):
            continue
        # Check photo caption/credit
        if is_photo_caption_or_credit(p_str, inline_images=inline_images, cover_caption=cover_caption, is_zh=is_zh):
            continue
        cleaned.append(p_str)

    return cleaned

