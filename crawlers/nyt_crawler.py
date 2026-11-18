#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
The New York Times Dedicated Crawler & Preloaded GraphQL Penetration Engine
=============================================================================
Source: The New York Times (nytimes.com)
Scope: Handles all nytimes.com article extraction, authentic editorial headline
       resolution, multi-author attribution, `window.__preloadedData` GraphQL
       AST parsing (`sprinkledBody.content` paragraphs, subheadings, quotes,
       lists, inline figures with authentic NYT captions & credits), gift-link
       (`?unlocked_article_code=...`) and regular article penetration, and
       high-resolution 16:9 / 3:2 cover photography localization.

Architecture & Strategy:
1. Multi-Profile Direct Fetcher (Zero CAPTCHA Bypass):
   - Uses standard `curl_cffi` TLS browser profiles (`safari17_2_ios`,
     `safari17_0`, `safari15_5`, `safari15_3`, `chrome124`) while preserving
     NYT `?unlocked_article_code=...` gift tokens.
   - Auto-detects local proxy (7890/7897) or env proxy, and runs cleanly
     without proxy in GitHub Actions cloud runners.
2. Tier 1 — `window.__preloadedData` GraphQL AST Extractor (Primary):
   - Parses `loaderData.data.article.sprinkledBody.content` (replacing JS
     `undefined` literals with JSON `null`), extracting 100% of full-length
     article paragraphs with zero missing inline-link spaces and zero UI
     boilerplate ("Want all of The Times? Subscribe.", Dropzones, etc.).
   - Extracts authentic editorial headline, multi-author byline, ISO publish
     timestamp, section subheadings, and high-res landscape cover + inline
     figures (strictly rejecting author headshots/avatars/NYT logos and
     deduplicating cover media stems).
3. Tier 2 — Clean DOM & JSON-LD Fallback Extractor:
   - Handles direct HTML fixtures and alternate NYT layouts via Lexbor/regex
     with space-preserving inline element text extraction and strict NYT
     subscription/newsletter boilerplate filtering.
4. Tier 3 — Wayback Machine Snapshot Fallback:
   - If direct HTTP profiles return 403/timeout on a cloud datacenter IP,
     gracefully queries `web.archive.org` for an archived snapshot.
5. High-Resolution Master Photography Localization:
   - Downloads authentic `static01.nyt.com` photography and localizes it to
     `public/images/nyt_<hash>.jpg` (`https://ainewsradar.xyz/images/nyt_<hash>.jpg`).

Separation of Concerns:
- Completely isolated from locked Reuters, Bloomberg, Fortune, WSJ, and The Verge crawlers.
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import urlparse, quote
from typing import Dict, Any, List, Optional, Tuple

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    cffi_requests = None
    HAS_CURL_CFFI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    requests = None
    HAS_REQUESTS = False

try:
    from selectolax.lexbor import LexborHTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    LexborHTMLParser = None
    HAS_SELECTOLAX = False


_NYT_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "nyt_cache.json"
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

NYT_NOISE_PHRASES = [
    "want all of the times",
    "thank you for your patience while we verify access",
    "already a subscriber? log in",
    "you have a preview view of this article",
    "please enable js and disable any ad blocker",
    "we are having trouble retrieving the article content",
    "please enable javascript in your browser settings",
    "sign up for the",
    "subscribe to the times",
    "continue reading the main story",
    "a version of this article appears in print",
    "supported by",
    "read more about our",
    "send any friend a story",
    "as a subscriber, you have 10 gift articles",
    "have a tip? reach us at",
    "follow new york times",
]

AVATAR_BAD_TOKENS = (
    "unsplash.com", "placeholder", "icon", "pixel", "avatar",
    "favicon", "og-default", "1x1", "spacer", "nyt_logo", "nyt-logo",
    "times-logo", "blurple", "author_profile_images", "headshot",
    "byline", "gravatar", "profile_image", "profile-pic", "-portrait-",
    "author-page", "thumbstandard", "thumbLarge", "square320", "square640",
    "moth.jpg", "smallsquare",
)


def is_nyt_url(url: str) -> bool:
    """Checks whether the given URL belongs to The New York Times."""
    if not url:
        return False
    low = url.lower()
    return "nytimes.com" in low or "nyti.ms" in low


def _canonical_nyt_key(url: str) -> str:
    """Canonical cache key stripping tracking/gift query params."""
    if not url:
        return ""
    return url.split("?")[0].split("#")[0].rstrip("/").lower()


def _get_proxies() -> Optional[Dict[str, str]]:
    """Detects available environment or local proxy (7890/7897)."""
    env_https = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    env_http = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if env_https or env_http:
        return {"http": env_http or env_https, "https": env_https or env_http}
    for p in DEFAULT_PROXIES:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            host, port = p.replace("http://", "").split(":")
            if sock.connect_ex((host, int(port))) == 0:
                sock.close()
                return {"http": p, "https": p}
            sock.close()
        except Exception:
            pass
    return None


def _is_valid_nyt_image(img_url: Optional[str]) -> bool:
    """Validates that an NYT image URL is absolute, high-res, and not an avatar/logo."""
    if not img_url or not isinstance(img_url, str):
        return False
    u = img_url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    low = u.lower()
    if any(tok.lower() in low for tok in AVATAR_BAD_TOKENS):
        return False
    if low.endswith(".svg") or low.endswith(".ico"):
        return False
    return True


def _nyt_media_stem(img_url: Optional[str]) -> str:
    """
    Extracts NYT media directory/slug stem so multiple renditions of the same
    photo (e.g., `-videoSixteenByNineJumbo1600.jpg` vs `-articleLarge.jpg`)
    are cleanly deduplicated.
    """
    if not img_url:
        return ""
    path = urlparse(img_url).path.lower()
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2:
        # e.g. /images/2026/11/17/multimedia/17dc-aibug-zfmc/17dc-aibug-zfmc-articleLarge.jpg
        return parts[-2]
    return path


def _clean_text(raw: str) -> str:
    """Unescapes HTML entities and normalizes Unicode/whitespace cleanly."""
    if not raw:
        return ""
    t = html.unescape(str(raw))
    t = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<script[^>]*>.*?</script>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\xa0]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _clean_nyt_title(raw_title: str) -> str:
    """Cleans NYT headline and removes ' - The New York Times' suffixes."""
    if not raw_title:
        return ""
    t = _clean_text(raw_title)
    t = re.sub(r'\s*[-|—–]\s*The New York Times\s*$', '', t, flags=re.I).strip()
    t = re.sub(r'\s*[-|—–]\s*NYTimes\.com\s*$', '', t, flags=re.I).strip()
    return t


def _is_nyt_noise(text: str) -> bool:
    """Filters NYT paywall prompts, subscription banners, and print-edition footers."""
    if not text:
        return True
    t = text.strip()
    if len(t) < 20:
        return True
    low = t.lower()
    if low in ("advertisement", "supported by", "skip advertisement", "continue reading the main story"):
        return True
    for phrase in NYT_NOISE_PHRASES:
        if phrase in low:
            return True
    # Filter pure image credit lines accidentally leaked into paragraphs
    if re.match(r'^(?:Credit|Image|Photo)\s*[:—-]', t, re.I) and len(t) < 120:
        return True
    return False


def _load_disk_cache() -> None:
    global _NYT_CACHE
    if _NYT_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _NYT_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_NYT_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_nyt_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """
    Downloads NYT cover image to `public/images/nyt_<hash>.jpg` and returns the
    stable public URL `https://ainewsradar.xyz/images/nyt_<hash>.jpg`.
    """
    if not _is_valid_nyt_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(img_url.split("?")[0].encode("utf-8")).hexdigest()[:16]
        ext = ".png" if ".png" in img_url.split("?")[0].lower() else ".jpg"
        fname = f"nyt_{h}{ext}"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Referer": "https://www.nytimes.com/",
            "Accept": "image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(
                    img_url, impersonate="safari17_2_ios", headers=headers,
                    proxies=proxies, timeout=15
                )
                if r.status_code == 200 and len(r.content) > 5000:
                    ct = r.headers.get("content-type", "").lower()
                    if "image/" in ct or r.content[:2] in (b'\xff\xd8', b'\x89P'):
                        content = r.content
            except Exception:
                pass
        if content is None and HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=15)
                if r.status_code == 200 and len(r.content) > 5000:
                    content = r.content
            except Exception:
                pass

        if content:
            # Optional gentle downsize if image is huge (>1.2MB) and Pillow is available
            if len(content) > 1_200_000:
                try:
                    from io import BytesIO
                    from PIL import Image
                    im = Image.open(BytesIO(content))
                    if im.width > 1600:
                        ratio = 1600 / float(im.width)
                        im = im.resize((1600, max(1, int(im.height * ratio))), Image.LANCZOS)
                    buf = BytesIO()
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    im.save(buf, format="JPEG", quality=86, optimize=True)
                    content = buf.getvalue()
                    fname = f"nyt_{h}.jpg"
                    fpath = os.path.join(img_dir, fname)
                    public_url = f"https://ainewsradar.xyz/images/{fname}"
                except Exception:
                    pass
            with open(fpath, "wb") as f:
                f.write(content)
            return public_url
    except Exception:
        pass
    return img_url


def _pick_best_nyt_rendition(media_obj: Any, prefer_landscape: bool = True) -> Optional[str]:
    """
    Selects the best high-resolution rendition from an NYT GraphQL media object
    (`promotionalMedia`, `promotionalImage`, `ledeMedia`, or `ImageBlock.media`).
    """
    if not isinstance(media_obj, dict):
        return None

    crops = media_obj.get("assetCrops") or media_obj.get("crops") or []
    renditions: List[Dict[str, Any]] = []
    for cr in crops:
        if isinstance(cr, dict):
            for rd in cr.get("renditions") or []:
                if isinstance(rd, dict) and rd.get("url") and _is_valid_nyt_image(rd["url"]):
                    renditions.append(rd)

    if not renditions:
        # Check direct url fallback
        u = media_obj.get("url")
        return u if _is_valid_nyt_image(u) else None

    # Preferred NYT rendition names in optimal resolution/aspect priority
    priority_names = [
        "videoSixteenByNineJumbo1600",
        "videoSixteenByNine1050",
        "threeByTwoLargeAt2X",
        "superJumbo",
        "facebookJumbo",
        "articleLarge",
        "jumbo",
        "videoSixteenByNine3000",
        "threeByTwoMediumAt2X",
    ]
    by_name = {str(r.get("name") or ""): r for r in renditions}
    for pname in priority_names:
        r = by_name.get(pname)
        if not r:
            continue
        w = int(r.get("width") or 0)
        h = int(r.get("height") or 0)
        if prefer_landscape and w > 0 and h > 0 and h > w * 1.15:
            continue
        if w >= 500 or w == 0:
            return r["url"]

    # Fallback: highest landscape width <= 2400px, else highest width overall
    landscape = [
        r for r in renditions
        if (int(r.get("width") or 0) >= 500)
        and (int(r.get("height") or 0) == 0 or int(r.get("width") or 0) >= int(r.get("height") or 0))
    ]
    pool = landscape or renditions
    pool.sort(key=lambda r: (abs(int(r.get("width") or 1200) - 1400)))
    return pool[0]["url"] if pool else None


def _extract_inline_text(node: Any) -> str:
    """Recursively extracts clean text from NYT GraphQL inline content nodes."""
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        parts = []
        if isinstance(node.get("text"), str):
            parts.append(node["text"])
        if isinstance(node.get("content"), list):
            for ch in node["content"]:
                parts.append(_extract_inline_text(ch))
        if isinstance(node.get("children"), list):
            for ch in node["children"]:
                parts.append(_extract_inline_text(ch))
        return "".join(parts)
    if isinstance(node, list):
        return "".join(_extract_inline_text(x) for x in node)
    return ""


def _parse_nyt_preloaded_data(html_text: str) -> Dict[str, Any]:
    """
    Tier 1: Parses NYT's `window.__preloadedData` GraphQL hydration payload.
    Returns authentic headline, authors, published_at, summary, full paragraphs,
    subheadings, hero cover_image, and inline_images with captions.
    """
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "",
        "published_at": None,
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
        "inline_images": [],
        "has_video": False,
        "video_url": None,
        "video_provider": None,
    }

    if "window.__preloadedData" not in html_text:
        return out

    m = re.search(r'window\.__preloadedData\s*=\s*(\{.*?\});\s*</script>', html_text, re.DOTALL | re.I)
    if not m:
        return out

    raw = m.group(1).rstrip('; \r\n')
    # Convert JS `undefined` literals into valid JSON `null`
    fixed = re.sub(r':\s*undefined\b', ':null', raw)
    fixed = re.sub(r'\[\s*undefined\b', '[null', fixed)
    fixed = re.sub(r',\s*undefined\b', ',null', fixed)

    try:
        pd = json.loads(fixed)
    except Exception:
        return out

    ld = (pd.get("loaderData") or {}).get("data") or {}
    article = ld.get("article") or ld.get("workOrLocation") or ld.get("interactive")
    if not isinstance(article, dict):
        return out

    # 1. Headline & summary & published_at
    hl = article.get("headline")
    if isinstance(hl, dict):
        raw_hl = hl.get("default") or hl.get("seo") or hl.get("kicker") or ""
        out["title"] = _clean_nyt_title(raw_hl)
    elif isinstance(hl, str):
        out["title"] = _clean_nyt_title(hl)

    if isinstance(article.get("summary"), str):
        out["summary"] = _clean_text(article["summary"])

    if article.get("firstPublished"):
        out["published_at"] = article["firstPublished"]

    # 2. Multi-author byline extraction
    bylines = article.get("bylines") or []
    author_names: List[str] = []
    if isinstance(bylines, list):
        for bl in bylines:
            if not isinstance(bl, dict):
                continue
            creators = bl.get("creators") or []
            for cr in creators:
                if isinstance(cr, dict):
                    nm = str(cr.get("displayName") or "").strip()
                    if nm and nm not in author_names:
                        author_names.append(nm)
            if not author_names and bl.get("renderedRepresentation"):
                rep = re.sub(r'^By\s+', '', str(bl["renderedRepresentation"]).strip(), flags=re.I)
                if rep:
                    author_names.append(rep)
    if author_names:
        if len(author_names) == 1:
            out["author"] = author_names[0]
        elif len(author_names) == 2:
            out["author"] = f"{author_names[0]} and {author_names[1]}"
        else:
            out["author"] = ", ".join(author_names[:-1]) + f", and {author_names[-1]}"

    # 3. Hero Cover Image (promotionalMedia -> promotionalImage -> HeaderBasicBlock.ledeMedia)
    hero_candidates = [
        article.get("promotionalMedia"),
        article.get("promotionalImage"),
    ]
    body_obj = article.get("sprinkledBody") or article.get("body") or {}
    blocks = body_obj.get("content") if isinstance(body_obj, dict) else []
    if not isinstance(blocks, list):
        blocks = []

    for blk in blocks:
        if isinstance(blk, dict) and blk.get("__typename") in ("HeaderBasicBlock", "HeaderFullBleedHorizontalBlock", "HeaderFullBleedVerticalBlock"):
            lede = blk.get("ledeMedia")
            if isinstance(lede, dict):
                hero_candidates.insert(0, lede)
            break

    for cand_media in hero_candidates:
        u = _pick_best_nyt_rendition(cand_media, prefer_landscape=True)
        if u:
            out["cover_image"] = u
            break

    cover_stem = _nyt_media_stem(out["cover_image"])
    seen_stems = {cover_stem} if cover_stem else set()

    # 4. Traverse `sprinkledBody.content` AST blocks in exact editorial order
    for blk in blocks:
        if not isinstance(blk, dict):
            continue
        btype = str(blk.get("__typename") or "")

        if btype == "ParagraphBlock":
            txt = _clean_text(_extract_inline_text(blk.get("content")))
            if txt and not _is_nyt_noise(txt) and txt not in out["paragraphs"]:
                out["paragraphs"].append(txt)

        elif btype in ("Heading1Block", "Heading2Block", "Heading3Block", "Heading4Block", "SubheadBlock"):
            htxt = _clean_text(_extract_inline_text(blk.get("content")))
            if htxt and len(htxt) < 180 and not _is_nyt_noise(htxt):
                if htxt not in out["subheadings"]:
                    out["subheadings"].append(htxt)

        elif btype in ("BlockquoteBlock", "PullquoteBlock"):
            qtxt = _clean_text(_extract_inline_text(blk.get("content") or blk.get("quote")))
            if qtxt and not _is_nyt_noise(qtxt) and qtxt not in out["paragraphs"]:
                out["paragraphs"].append(f'“{qtxt}”' if not qtxt.startswith(('"', '“')) else qtxt)

        elif btype == "ListBlock":
            for li in blk.get("content") or []:
                ltxt = _clean_text(_extract_inline_text(li))
                if ltxt and not _is_nyt_noise(ltxt) and ltxt not in out["paragraphs"]:
                    out["paragraphs"].append(ltxt)

        elif btype in ("ImageBlock", "MediaBlock", "PhotoBlock"):
            media = blk.get("media") or blk
            i_url = _pick_best_nyt_rendition(media, prefer_landscape=False)
            if not i_url:
                continue
            stem = _nyt_media_stem(i_url)
            if stem and stem in seen_stems:
                continue
            if stem:
                seen_stems.add(stem)
            cap_obj = media.get("caption")
            cap = ""
            if isinstance(cap_obj, dict):
                cap = _clean_text(cap_obj.get("text") or _extract_inline_text(cap_obj))
            elif isinstance(cap_obj, str):
                cap = _clean_text(cap_obj)
            credit = _clean_text(media.get("credit") or "")
            full_cap = f"{cap} ({credit})" if (cap and credit and credit.lower() not in cap.lower()) else (cap or credit)
            out["inline_images"].append({
                "url": i_url,
                "caption": full_cap,
                "alt": cap or out["title"],
            })

        elif btype in ("VideoBlock", "EmbeddedVideoBlock"):
            media = blk.get("media") or blk
            if isinstance(media, dict):
                renditions = media.get("renditions") or []
                for rd in renditions:
                    if isinstance(rd, dict) and str(rd.get("url") or "").endswith(".mp4"):
                        out["has_video"] = True
                        out["video_url"] = rd["url"]
                        out["video_provider"] = "direct"
                        break

    return out


def _extract_dom_text_with_spaces(node) -> str:
    """Safely extracts text from a Lexbor HTML node preserving spaces across inline links."""
    if node is None:
        return ""
    raw_html = node.html or ""
    # Preserve spaces around inline tags while not breaking punctuation
    raw_html = re.sub(r'<(?:br|BR)\s*/?>', ' ', raw_html)
    # Strip tags cleanly
    txt = html.unescape(re.sub(r'<[^>]+>', '', raw_html))
    txt = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\xa0]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt


def _parse_nyt_dom_fallback(html_text: str) -> Dict[str, Any]:
    """
    Tier 2: Clean DOM & JSON-LD fallback extractor for NYT HTML fixtures or
    layouts without `window.__preloadedData`.
    """
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "",
        "published_at": None,
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
        "inline_images": [],
    }

    # 1. JSON-LD NewsArticle metadata
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            obj = json.loads(m_ld.group(1).strip())
            if isinstance(obj, list):
                obj = next((x for x in obj if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if not isinstance(obj, dict) or "Article" not in str(obj.get("@type", "")):
                continue
            if obj.get("headline") and not out["title"]:
                out["title"] = _clean_nyt_title(obj["headline"])
            if obj.get("description") and not out["summary"]:
                out["summary"] = _clean_text(obj["description"])
            if obj.get("datePublished") and not out["published_at"]:
                out["published_at"] = obj["datePublished"]
            auth = obj.get("author")
            if auth and not out["author"]:
                if isinstance(auth, list):
                    names = [str(a.get("name")).strip() for a in auth if isinstance(a, dict) and a.get("name")]
                    if names:
                        out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"
                elif isinstance(auth, dict) and auth.get("name"):
                    out["author"] = str(auth["name"]).strip()
            img = obj.get("image")
            if img and not out["cover_image"]:
                if isinstance(img, list) and img:
                    cand = img[0].get("url") if isinstance(img[0], dict) else str(img[0])
                elif isinstance(img, dict):
                    cand = img.get("url")
                else:
                    cand = str(img)
                if _is_valid_nyt_image(cand):
                    out["cover_image"] = cand
        except Exception:
            continue

    # 2. Meta tags fallback (og:title, og:image)
    if not out["title"]:
        m_og = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if not m_og:
            m_og = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.DOTALL | re.I)
        if m_og:
            out["title"] = _clean_nyt_title(m_og.group(1))

    if not out["cover_image"]:
        m_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_img and _is_valid_nyt_image(m_img.group(1)):
            out["cover_image"] = html.unescape(m_img.group(1).strip())

    # 3. DOM paragraphs from <section name="articleBody">
    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        try:
            tree = LexborHTMLParser(html_text)
            if not out["title"]:
                h1 = tree.css_first('h1[data-testid="headline"]') or tree.css_first("h1")
                if h1:
                    out["title"] = _clean_nyt_title(h1.text(strip=True))
            body_sec = tree.css_first('section[name="articleBody"]') or tree.css_first("article")
            if body_sec:
                for el in body_sec.css("h2, h3, p"):
                    tag = (el.tag or "").lower()
                    txt = _extract_dom_text_with_spaces(el)
                    if not txt or _is_nyt_noise(txt):
                        continue
                    if tag in ("h2", "h3") and len(txt) < 180:
                        if txt not in out["subheadings"]:
                            out["subheadings"].append(txt)
                    elif tag == "p":
                        if txt not in out["paragraphs"]:
                            out["paragraphs"].append(txt)
        except Exception:
            pass
    else:
        m_sec = re.search(r'<section[^>]+name=["\']articleBody["\'][^>]*>(.*?)</section>', html_text, re.DOTALL | re.I)
        scope = m_sec.group(1) if m_sec else html_text
        for m_p in re.finditer(r'<p[^>]*>(.*?)</p>', scope, re.DOTALL | re.I):
            txt = _clean_text(m_p.group(1))
            if txt and not _is_nyt_noise(txt) and txt not in out["paragraphs"]:
                out["paragraphs"].append(txt)

    return out


def _fetch_nyt_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    """
    Fetches NYT article HTML using standard browser TLS profiles (preserving
    `?unlocked_article_code=...` tokens) with graceful Wayback Machine fallback.
    Never attempts to solve or bypass CAPTCHAs.
    """
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    }

    if HAS_CURL_CFFI:
        for profile in ("safari17_2_ios", "safari17_0", "safari15_5", "safari15_3", "chrome124"):
            try:
                r = cffi_requests.get(
                    url,
                    impersonate=profile,
                    headers=headers,
                    proxies=proxies,
                    timeout=18,
                    allow_redirects=True,
                )
                if r.status_code == 200 and len(r.text) > 15000:
                    low = r.text[:4000].lower()
                    if "captcha-delivery" not in low and ("__preloadeddata" in r.text.lower() or 'name="articlebody"' in r.text.lower()):
                        return r.text, f"nyt_direct_{profile}"
            except Exception:
                continue

    # Fallback: Wayback Machine archived snapshot (standard public archive)
    if HAS_REQUESTS:
        clean_u = url.split("?")[0]
        try:
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={quote(clean_u, safe='')}&output=json&limit=3&filter=statuscode:200&collapse=digest"
            cr = requests.get(cdx_url, proxies=proxies, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if cr.status_code == 200:
                rows = cr.json()
                if isinstance(rows, list) and len(rows) > 1:
                    ts = rows[-1][1]
                    orig = rows[-1][2]
                    wb_url = f"https://web.archive.org/web/{ts}id_/{orig}"
                    wr = requests.get(wb_url, proxies=proxies, timeout=18, headers={"User-Agent": "Mozilla/5.0"})
                    if wr.status_code == 200 and len(wr.text) > 15000:
                        return wr.text, "nyt_wayback"
        except Exception:
            pass

    return None, "failed"


def crawl_nyt(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Main isolated entrypoint for The New York Times (`nytimes.com`).
    Returns the standardized crawler payload compatible with ArticleExtractor,
    processor.py, main.py, and tool_news_publisher.py.
    """
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "nytimes.com",
        "source": "The New York Times",
        "title": _clean_nyt_title(title) if title else "",
        "summary": "",
        "author": "The New York Times",
        "published_at": None,
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "lead_paragraph": "",
        "paragraphs": [],
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "subheadings": [],
        "key_metrics": [],
        "quotes": [],
        "paras_count": 0,
        "is_substantive": False,
        "is_paywalled": False,
        "has_video": False,
        "video_url": None,
        "video_provider": None,
        "extraction_tier": "failed",
    }

    if not url or not is_nyt_url(url):
        return result

    cache_key = _canonical_nyt_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _NYT_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if html_text is None else None
    tier = "nyt_injected_html"
    raw_html = html_text
    if raw_html is None:
        raw_html, tier = _fetch_nyt_html(url, proxies=proxies)

    if not raw_html:
        return result

    # Tier 1: Parse `window.__preloadedData` GraphQL AST
    parsed = _parse_nyt_preloaded_data(raw_html)
    used_tier = f"{tier}_preloaded"

    # Tier 2: Supplement or fallback via clean DOM + JSON-LD
    if len(parsed.get("paragraphs", [])) < 3 or not parsed.get("title") or not parsed.get("cover_image"):
        dom_parsed = _parse_nyt_dom_fallback(raw_html)
        if not parsed.get("title") and dom_parsed.get("title"):
            parsed["title"] = dom_parsed["title"]
        if not parsed.get("summary") and dom_parsed.get("summary"):
            parsed["summary"] = dom_parsed["summary"]
        if not parsed.get("author") and dom_parsed.get("author"):
            parsed["author"] = dom_parsed["author"]
        if not parsed.get("published_at") and dom_parsed.get("published_at"):
            parsed["published_at"] = dom_parsed["published_at"]
        if not parsed.get("cover_image") and dom_parsed.get("cover_image"):
            parsed["cover_image"] = dom_parsed["cover_image"]
        if len(dom_parsed.get("paragraphs", [])) > len(parsed.get("paragraphs", [])):
            parsed["paragraphs"] = dom_parsed["paragraphs"]
            used_tier = f"{tier}_dom"
        if not parsed.get("subheadings") and dom_parsed.get("subheadings"):
            parsed["subheadings"] = dom_parsed["subheadings"]

    # Localize hero cover image to public/images/nyt_<hash>.jpg
    cover = parsed.get("cover_image")
    if cover and localize_cover and html_text is None:
        cover = _localize_nyt_image(cover, proxies=proxies)

    paras = parsed.get("paragraphs") or []
    full_text = "\n\n".join(paras).strip()

    if parsed.get("title"):
        result["title"] = parsed["title"]
    if parsed.get("summary"):
        result["summary"] = parsed["summary"]
    if parsed.get("author"):
        result["author"] = parsed["author"]
    if parsed.get("published_at"):
        result["published_at"] = parsed["published_at"]
    if cover:
        result["cover_image"] = cover
        result["image_url"] = cover
    if parsed.get("inline_images"):
        result["inline_images"] = parsed["inline_images"]
    if parsed.get("subheadings"):
        result["subheadings"] = parsed["subheadings"]
    if parsed.get("has_video") and parsed.get("video_url"):
        result["has_video"] = True
        result["video_url"] = parsed["video_url"]
        result["video_provider"] = parsed.get("video_provider") or "direct"

    result["paragraphs"] = paras
    result["paras_count"] = len(paras)
    result["lead_paragraph"] = paras[0] if paras else ""
    result["full_text"] = full_text
    result["article_content"] = full_text
    result["article_content_en"] = full_text
    result["extraction_tier"] = used_tier

    if len(paras) >= 3 and len(full_text) >= 300:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _NYT_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif len(paras) >= 1 and len(full_text) >= 120:
        result["status"] = "partial"
        result["is_substantive"] = True

    return result
