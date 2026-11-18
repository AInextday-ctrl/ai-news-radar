#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
The Washington Post Dedicated Crawler & Official MSN Syndication Engine
=============================================================================
Source: The Washington Post (washingtonpost.com)
Scope: Handles all washingtonpost.com article extraction, authentic editorial
       headline resolution, multi-author attribution, Arc XP `__NEXT_DATA__`
       metadata & HD cover photography (`imrs.php?w=1440` localization), and
       strictly URL/entity-verified official MSN Syndication full-text
       penetration (`assets.msn.com/content/view/v2/Detail/en-us/<ar-ID>`).

Architecture & Strategy:
1. Tier 1 — Direct Arc XP `__NEXT_DATA__` Metadata & Lead Extractor:
   - Fetches full URL (preserving `?pwapi_token=...` gift links) via standard
     `curl_cffi` TLS profiles (`safari17_2_ios`, `safari17_0`, `chrome124`).
   - Extracts authentic `headlines.basic`, multi-author `credits.by[].name`,
     `first_publish_date`, lead paragraphs, and `promo_items.basic.url`
     (resized via official `wp-apps/imrs.php?src=...&w=1440` for fast, crisp
     1440px cover localization to `public/images/wapo_<hash>.jpg`).
2. Tier 2 — Official MSN Syndication Full-Text Penetration (Primary Body):
   - Discovers The Washington Post's official syndicated `msn.com/.../ar-<ID>`
     via Bing News search and fetches `assets.msn.com/content/view/v2/Detail`.
   - Enforces a STRICT 2-layer identity gate:
     (a) `provider.name` MUST match `Washington Post`
     (b) EITHER `sourceHref` path exactly equals the target WaPo article path
         OR title/lead significant token overlap >= 55%.
   - Strips trailing WaPo/MSN promo sections (`Most Read From The Washington Post`,
     newsletter signups, etc.) and author avatars/logos.
3. Tier 3 — Clean DOM / Wayback Machine Fallback:
   - Supports injected HTML fixtures in unit tests and Wayback snapshots.

Separation of Concerns:
- Completely isolated from all locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, The New York Times) and Washington Sun.
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


_WAPO_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "wapo_cache.json"
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

WAPO_NOISE_PHRASES = [
    "most read from the washington post",
    "read more from the washington post",
    "sign up for the",
    "subscribe to the washington post",
    "democracy dies in darkness",
    "gift this article",
    "already a subscriber",
    "for unlimited access",
    "thank you for reading the washington post",
    "please enable javascript",
    "contributed to this report. sign up",
    "want more news from the post",
    "follow the washington post",
    "copyright 202",
    "© 202",
]

AVATAR_BAD_TOKENS = (
    "unsplash.com", "placeholder", "icon", "pixel", "avatar",
    "favicon", "og-default", "1x1", "spacer", "wapo-logo", "wp-logo",
    "blurple", "author_profile_images", "headshot", "byline",
    "gravatar", "profile_image", "profile-pic", "-portrait-", "-mug-",
    "staff-", "logo", "aa2024mm", "aa2022fd", "aa201w2u",
)

STOP_WORDS = {
    "the", "and", "for", "that", "with", "from", "this", "have", "were",
    "they", "their", "about", "into", "over", "after", "says", "said",
    "what", "when", "where", "which", "while", "more", "than", "will",
    "could", "would", "should", "been", "being", "washington", "post",
    "sources", "report", "news",
}


def is_wapo_url(url: str) -> bool:
    """Checks whether the given URL belongs to The Washington Post."""
    if not url:
        return False
    low = url.lower()
    return "washingtonpost.com" in low or "wapo.st" in low


def _canonical_wapo_path(url: str) -> str:
    """Normalizes WaPo URL path for exact matching and cache keying."""
    if not url:
        return ""
    p = urlparse(url)
    return p.path.rstrip("/").lower()


def _canonical_wapo_key(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0].split("#")[0].rstrip("/").lower()


def _get_proxies() -> Optional[Dict[str, str]]:
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


def _is_valid_wapo_image(img_url: Optional[str]) -> bool:
    if not img_url or not isinstance(img_url, str):
        return False
    u = img_url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    low = u.lower()
    if any(tok in low for tok in AVATAR_BAD_TOKENS):
        return False
    if low.endswith(".svg") or low.endswith(".ico"):
        return False
    return True


def _clean_text(raw: str) -> str:
    if not raw:
        return ""
    t = html.unescape(str(raw))
    t = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<script[^>]*>.*?</script>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\xa0]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _clean_wapo_title(raw_title: str) -> str:
    if not raw_title:
        return ""
    t = _clean_text(raw_title)
    t = re.sub(r'\s*[-|—–]\s*The Washington Post\s*$', '', t, flags=re.I).strip()
    t = re.sub(r'\s*[-|—–]\s*Washington Post\s*$', '', t, flags=re.I).strip()
    return t


def _is_wapo_noise(text: str) -> bool:
    if not text:
        return True
    t = text.strip()
    if len(t) < 20:
        return True
    low = t.lower()
    for phrase in WAPO_NOISE_PHRASES:
        if phrase in low:
            return True
    return False


def _wrap_wapo_imrs(img_url: str) -> str:
    """Wraps huge ArcPublishing master JPEGs with WaPo's fast 1440px imrs resizer."""
    if not img_url:
        return img_url
    if "arcpublishing.com" in img_url and "wp-apps/imrs.php" not in img_url:
        return f"https://www.washingtonpost.com/wp-apps/imrs.php?src={quote(img_url, safe='')}&w=1440"
    if "wp-apps/imrs.php" in img_url and "&w=" not in img_url:
        return f"{img_url}&w=1440"
    return img_url


def _load_disk_cache() -> None:
    global _WAPO_CACHE
    if _WAPO_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _WAPO_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_WAPO_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_wapo_image(img_url: str, fallback_url: Optional[str] = None, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads WaPo cover photo (via imrs 1440px or MSN CDN) to `public/images/wapo_<hash>.jpg`."""
    candidates = []
    if img_url and _is_valid_wapo_image(img_url):
        candidates.append(_wrap_wapo_imrs(img_url))
    if fallback_url and _is_valid_wapo_image(fallback_url):
        fb = fallback_url
        if "akamaized.net" in fb and "?w=" not in fb:
            fb = f"{fb}?w=1280&m=6"
        candidates.append(fb)

    if not candidates:
        return img_url

    if "ainewsradar.xyz/images/" in candidates[0]:
        return candidates[0]

    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(candidates[0].encode("utf-8")).hexdigest()[:16]
        fname = f"wapo_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Referer": "https://www.washingtonpost.com/",
            "Accept": "image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5",
        }
        for cand in candidates:
            content = None
            if HAS_CURL_CFFI:
                try:
                    r = cffi_requests.get(cand, impersonate="safari17_2_ios", headers=headers, proxies=proxies, timeout=16)
                    if r.status_code == 200 and len(r.content) > 5000:
                        ct = r.headers.get("content-type", "").lower()
                        if "image/" in ct or r.content[:2] in (b'\xff\xd8', b'\x89P'):
                            content = r.content
                except Exception:
                    pass
            if content is None and HAS_REQUESTS:
                try:
                    r = requests.get(cand, headers=headers, proxies=proxies, timeout=16)
                    if r.status_code == 200 and len(r.content) > 5000:
                        content = r.content
                except Exception:
                    pass
            if content:
                with open(fpath, "wb") as f:
                    f.write(content)
                return public_url
    except Exception:
        pass
    return candidates[0]


def _parse_wapo_next_data(html_text: str) -> Dict[str, Any]:
    """Tier 1: Extracts Arc XP `__NEXT_DATA__` metadata, lead paragraphs, and cover image."""
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
    m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I)
    if not m:
        return out
    try:
        nd = json.loads(m.group(1))
    except Exception:
        return out

    gc = nd.get("props", {}).get("pageProps", {}).get("globalContent") or {}
    if not isinstance(gc, dict) or not gc:
        return out

    hl = gc.get("headlines") or {}
    if isinstance(hl, dict):
        out["title"] = _clean_wapo_title(hl.get("basic") or hl.get("meta_title") or "")
    desc = gc.get("description") or {}
    if isinstance(desc, dict) and desc.get("basic"):
        out["summary"] = _clean_text(desc["basic"])

    out["published_at"] = gc.get("first_publish_date") or gc.get("publish_date")

    credits = (gc.get("credits") or {}).get("by") or []
    names = []
    for c in credits:
        if isinstance(c, dict) and c.get("name"):
            nm = str(c["name"]).strip()
            if nm and nm not in names:
                names.append(nm)
    if names:
        if len(names) == 1:
            out["author"] = names[0]
        elif len(names) == 2:
            out["author"] = f"{names[0]} and {names[1]}"
        else:
            out["author"] = ", ".join(names[:-1]) + f", and {names[-1]}"

    promo = (gc.get("promo_items") or {}).get("basic") or {}
    if isinstance(promo, dict):
        p_url = promo.get("url")
        if not p_url and isinstance(promo.get("promo_image"), dict):
            p_url = promo["promo_image"].get("url")
        if _is_valid_wapo_image(p_url):
            out["cover_image"] = p_url

    for el in gc.get("content_elements") or []:
        if not isinstance(el, dict):
            continue
        etype = str(el.get("type") or "")
        if etype == "text":
            txt = _clean_text(el.get("content") or "")
            if txt and not _is_wapo_noise(txt) and txt not in out["paragraphs"]:
                out["paragraphs"].append(txt)
        elif etype == "header":
            htxt = _clean_text(el.get("content") or "")
            if htxt and len(htxt) < 180 and not _is_wapo_noise(htxt) and htxt not in out["subheadings"]:
                out["subheadings"].append(htxt)
        elif etype == "quote":
            for qel in el.get("content_elements") or []:
                if isinstance(qel, dict) and qel.get("content"):
                    qt = _clean_text(qel["content"])
                    if qt and not _is_wapo_noise(qt) and qt not in out["paragraphs"]:
                        out["paragraphs"].append(f'“{qt}”')
        elif etype == "image":
            iu = el.get("url")
            if _is_valid_wapo_image(iu) and iu != out["cover_image"]:
                out["inline_images"].append({
                    "url": _wrap_wapo_imrs(iu),
                    "caption": _clean_text(el.get("caption") or ""),
                    "alt": _clean_text(el.get("caption") or out["title"]),
                })

    return out


def _significant_tokens(text: str) -> set:
    words = re.findall(r"[a-z0-9]{3,}", (text or "").lower())
    return {w for w in words if w not in STOP_WORDS}


def _fetch_wapo_via_msn_syndication(
    target_url: str,
    title_hint: str,
    lead_hint: str = "",
    proxies: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Tier 2: Discovers and verifies The Washington Post's official MSN syndication
    payload via `assets.msn.com/content/view/v2/Detail/en-us/<ar-ID>`.
    Strictly validates provider == Washington Post AND (exact `sourceHref` match
    OR >= 55% title/lead token similarity).
    """
    if not HAS_REQUESTS or not title_hint:
        return None

    target_path = _canonical_wapo_path(target_url)
    # Build clean search queries from title and URL slug
    clean_q = re.sub(r'\s*\([^)]*washington post[^)]*\)\s*$', '', title_hint, flags=re.I).strip()
    slug_words = " ".join(w for w in re.split(r'[-_/]', target_path.split("/")[-1]) if len(w) > 2)
    queries = [f"{clean_q} Washington Post"]
    if slug_words and slug_words.lower() not in clean_q.lower():
        queries.append(f"{slug_words} Washington Post")

    target_tokens = _significant_tokens(clean_q + " " + slug_words)
    seen_ids = set()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for q in queries:
        try:
            r = requests.get(
                "https://www.bing.com/news/search",
                params={"q": q},
                proxies=proxies,
                timeout=12,
                headers=headers,
            )
            if r.status_code != 200:
                continue
            ar_ids = list(dict.fromkeys(re.findall(r'https://www\.msn\.com/en-us/[^"\'<>]+/ar-([A-Za-z0-9]+)', r.text)))
            for ar_id in ar_ids[:5]:
                if ar_id in seen_ids:
                    continue
                seen_ids.add(ar_id)
                api_r = requests.get(
                    f"https://assets.msn.com/content/view/v2/Detail/en-us/{ar_id}",
                    proxies=proxies,
                    timeout=12,
                    headers=headers,
                )
                if api_r.status_code != 200:
                    continue
                data = api_r.json()
                prov_name = str((data.get("provider") or {}).get("name") or "").lower()
                if "washington post" not in prov_name:
                    continue

                # Strict identity check
                src_href = str(data.get("sourceHref") or "")
                exact_path_match = bool(target_path and src_href and _canonical_wapo_path(src_href) == target_path)
                msn_title = _clean_wapo_title(data.get("title") or "")
                msn_tokens = _significant_tokens(msn_title)
                overlap = (
                    len(target_tokens & msn_tokens) / float(max(1, min(len(target_tokens), len(msn_tokens))))
                    if target_tokens and msn_tokens else 0.0
                )
                body_html = str(data.get("body") or "")
                lead_match = bool(lead_hint and len(lead_hint) >= 40 and lead_hint[:50].lower() in _clean_text(body_html[:1500]).lower())

                if not (exact_path_match or lead_match or overlap >= 0.55):
                    continue

                # Truncate trailing "Most Read From The Washington Post" promo section
                cut_idx = body_html.lower().find("most read from the washington post")
                if cut_idx != -1:
                    body_html = body_html[:cut_idx]

                paras: List[str] = []
                subheadings: List[str] = []
                if HAS_SELECTOLAX and LexborHTMLParser is not None:
                    tree = LexborHTMLParser(body_html)
                    for el in tree.css("h2, h3, p"):
                        tag = (el.tag or "").lower()
                        txt = _clean_text(el.html or "")
                        if not txt or _is_wapo_noise(txt):
                            continue
                        if tag in ("h2", "h3") and len(txt) < 180:
                            if txt not in subheadings:
                                subheadings.append(txt)
                        elif tag == "p":
                            if txt not in paras:
                                paras.append(txt)
                else:
                    for m_p in re.finditer(r'<p[^>]*>(.*?)</p>', body_html, re.DOTALL | re.I):
                        txt = _clean_text(m_p.group(1))
                        if txt and not _is_wapo_noise(txt) and txt not in paras:
                            paras.append(txt)

                if len(paras) < 3:
                    continue

                # Extract MSN imageResources (hero + clean inline images, excluding logos)
                msn_cover = None
                msn_inlines: List[Dict[str, str]] = []
                for idx, im in enumerate(data.get("imageResources") or []):
                    if not isinstance(im, dict):
                        continue
                    iu = str(im.get("url") or "").strip()
                    w = int(im.get("width") or 0)
                    h = int(im.get("height") or 0)
                    if not _is_valid_wapo_image(iu) or (w > 0 and w < 400):
                        continue
                    if w > 0 and h > 0 and h > w * 1.15:
                        continue
                    sized_u = f"{iu}?w=1280&m=6" if ("akamaized.net" in iu and "?" not in iu) else iu
                    if msn_cover is None:
                        msn_cover = sized_u
                    else:
                        cap = _clean_text(im.get("caption") or "")
                        msn_inlines.append({"url": sized_u, "caption": cap, "alt": cap or msn_title})

                authors = []
                for a in data.get("authors") or []:
                    if isinstance(a, dict) and a.get("name"):
                        authors.append(str(a["name"]).strip())

                return {
                    "title": msn_title,
                    "author": ", ".join(authors) if authors else "",
                    "published_at": data.get("publishedDateTime"),
                    "cover_image": msn_cover,
                    "paragraphs": paras,
                    "subheadings": subheadings,
                    "inline_images": msn_inlines,
                    "msn_id": ar_id,
                }
        except Exception:
            continue
    return None


def _parse_wapo_dom_fallback(html_text: str) -> Dict[str, Any]:
    """Tier 3: Clean DOM + JSON-LD fallback for injected HTML fixtures or Wayback pages."""
    out: Dict[str, Any] = {
        "title": "",
        "author": "",
        "published_at": None,
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
    }
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            obj = json.loads(m_ld.group(1).strip())
            if isinstance(obj, list):
                obj = next((x for x in obj if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if not isinstance(obj, dict) or "Article" not in str(obj.get("@type", "")):
                continue
            if obj.get("headline") and not out["title"]:
                out["title"] = _clean_wapo_title(obj["headline"])
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
        except Exception:
            continue

    if not out["title"]:
        m_og = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_og:
            out["title"] = _clean_wapo_title(m_og.group(1))
    if not out["cover_image"]:
        m_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_img and _is_valid_wapo_image(m_img.group(1)):
            out["cover_image"] = html.unescape(m_img.group(1).strip())

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        body = tree.css_first('div[data-qa="article-body"]') or tree.css_first("article") or tree.css_first("main")
        if body:
            for p in body.css("p"):
                txt = _clean_text(p.html or "")
                if txt and not _is_wapo_noise(txt) and txt not in out["paragraphs"]:
                    out["paragraphs"].append(txt)
    return out


def _fetch_wapo_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Optional[str]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for imp in ("safari17_2_ios", "safari17_0", "chrome124"):
            try:
                r = cffi_requests.get(url, impersonate=imp, headers=headers, proxies=proxies, timeout=18, allow_redirects=True)
                if r.status_code == 200 and len(r.text) > 15000:
                    return r.text
            except Exception:
                continue
    return None


def crawl_wapo(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Main isolated entrypoint for The Washington Post (`washingtonpost.com`).
    """
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "washingtonpost.com",
        "source": "The Washington Post",
        "title": _clean_wapo_title(title) if title else "",
        "summary": "",
        "author": "The Washington Post",
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
        "extraction_tier": "failed",
    }

    if not url or not is_wapo_url(url):
        return result

    cache_key = _canonical_wapo_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _WAPO_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if html_text is None else None
    raw_html = html_text if html_text is not None else _fetch_wapo_html(url, proxies=proxies)

    direct = _parse_wapo_next_data(raw_html) if raw_html else {}
    if raw_html and (not direct.get("title") or len(direct.get("paragraphs") or []) < 2):
        dom_fb = _parse_wapo_dom_fallback(raw_html)
        for k in ("title", "author", "published_at", "cover_image"):
            if not direct.get(k) and dom_fb.get(k):
                direct[k] = dom_fb[k]
        if len(dom_fb.get("paragraphs") or []) > len(direct.get("paragraphs") or []):
            direct["paragraphs"] = dom_fb["paragraphs"]

    best_title = direct.get("title") or result["title"]
    lead_hint = (direct.get("paragraphs") or [""])[0]
    direct_paras = direct.get("paragraphs") or []
    tier = "wapo_direct_nextdata"

    # Tier 2: Official MSN Syndication when direct SSR only exposes lead 1-3 paragraphs
    msn_data = None
    if html_text is None and (len(direct_paras) < 5 or sum(len(p) for p in direct_paras) < 1200):
        msn_data = _fetch_wapo_via_msn_syndication(url, best_title or title, lead_hint=lead_hint, proxies=proxies)
        if msn_data and len(msn_data.get("paragraphs") or []) > len(direct_paras):
            direct_paras = msn_data["paragraphs"]
            if msn_data.get("subheadings"):
                direct["subheadings"] = msn_data["subheadings"]
            if msn_data.get("inline_images"):
                direct["inline_images"] = msn_data["inline_images"]
            if not direct.get("title") and msn_data.get("title"):
                best_title = msn_data["title"]
            if not direct.get("author") and msn_data.get("author"):
                direct["author"] = msn_data["author"]
            if not direct.get("published_at") and msn_data.get("published_at"):
                direct["published_at"] = msn_data["published_at"]
            tier = f"wapo_msn_syndication_{msn_data.get('msn_id', '')}"

    cover = direct.get("cover_image")
    msn_cover = msn_data.get("cover_image") if isinstance(msn_data, dict) else None
    if localize_cover and html_text is None and (cover or msn_cover):
        cover = _localize_wapo_image(cover or msn_cover, fallback_url=msn_cover, proxies=proxies)
    elif not cover and msn_cover:
        cover = msn_cover

    full_text = "\n\n".join(direct_paras).strip()

    if best_title:
        result["title"] = best_title
    if direct.get("summary"):
        result["summary"] = direct["summary"]
    if direct.get("author"):
        result["author"] = direct["author"]
    if direct.get("published_at"):
        result["published_at"] = direct["published_at"]
    if cover:
        result["cover_image"] = cover
        result["image_url"] = cover
    if direct.get("inline_images"):
        result["inline_images"] = direct["inline_images"]
    if direct.get("subheadings"):
        result["subheadings"] = direct["subheadings"]

    result["paragraphs"] = direct_paras
    result["paras_count"] = len(direct_paras)
    result["lead_paragraph"] = direct_paras[0] if direct_paras else ""
    result["full_text"] = full_text
    result["article_content"] = full_text
    result["article_content_en"] = full_text
    result["extraction_tier"] = tier

    if len(direct_paras) >= 3 and len(full_text) >= 400:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _WAPO_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif len(direct_paras) >= 1 and len(full_text) >= 120:
        result["status"] = "partial"
        result["is_substantive"] = True

    return result
