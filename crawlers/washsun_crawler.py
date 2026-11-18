#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
The Washington Sun Dedicated Crawler & Brightspot Penetration Engine
=============================================================================
Source: The Washington Sun (washingtonsun.com)
Scope: Handles all washingtonsun.com article extraction, authentic editorial
       headline resolution, author attribution, Brightspot `.RichTextArticleBody`
       full-text extraction, author mugshot (`-mug-` / `staff-`) rejection, and
       high-resolution 16:9 cover photography localization to
       `public/images/washsun_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from The Washington Post (`wapo_crawler.py`) and all
  locked crawlers (Reuters, Bloomberg, Fortune, WSJ, The Verge, NYT).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from typing import Dict, Any, List, Optional

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


_WASHSUN_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "washsun_cache.json"
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

WASHSUN_NOISE_PHRASES = [
    "sign up for",
    "subscribe to the washington sun",
    "already a subscriber",
    "please enable javascript",
    "follow the washington sun",
    "read more from the washington sun",
    "support independent journalism",
    "have a news tip",
]

AVATAR_BAD_TOKENS = (
    "unsplash.com", "placeholder", "icon", "pixel", "avatar",
    "favicon", "og-default", "1x1", "spacer", "logo",
    "blurple", "author_profile_images", "headshot", "byline",
    "gravatar", "profile_image", "profile-pic", "-portrait-",
    "-mug-", "staff-", "mug-500px",
)


def is_washsun_url(url: str) -> bool:
    if not url:
        return False
    return "washingtonsun.com" in url.lower()


def _canonical_key(url: str) -> str:
    return url.split("?")[0].split("#")[0].rstrip("/").lower() if url else ""


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


def _is_valid_washsun_image(img_url: Optional[str]) -> bool:
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


def _clean_title(raw_title: str) -> str:
    if not raw_title:
        return ""
    t = _clean_text(raw_title)
    t = re.sub(r'\s*[-|—–]\s*The Washington Sun\s*$', '', t, flags=re.I).strip()
    return t


def _is_noise(text: str) -> bool:
    if not text:
        return True
    t = text.strip()
    if len(t) < 20:
        return True
    low = t.lower()
    return any(p in low for p in WASHSUN_NOISE_PHRASES)


def _load_disk_cache() -> None:
    global _WASHSUN_CACHE
    if _WASHSUN_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _WASHSUN_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_WASHSUN_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    if not _is_valid_washsun_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(img_url.encode("utf-8")).hexdigest()[:16]
        fname = f"washsun_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Referer": "https://www.washingtonsun.com/",
            "Accept": "image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(img_url, impersonate="safari17_2_ios", headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.content) > 5000:
                    ct = r.headers.get("content-type", "").lower()
                    if "image/" in ct or r.content[:2] in (b'\xff\xd8', b'\x89P'):
                        content = r.content
            except Exception:
                pass
        if content is None and HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=16)
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
    return img_url


def _parse_washsun_html(html_text: str) -> Dict[str, Any]:
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
    # 1. JSON-LD metadata
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            obj = json.loads(m_ld.group(1).strip())
            if isinstance(obj, list):
                obj = next((x for x in obj if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if not isinstance(obj, dict) or "Article" not in str(obj.get("@type", "")):
                continue
            if obj.get("headline") and not out["title"]:
                out["title"] = _clean_title(obj["headline"])
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
        except Exception:
            continue

    # 2. og:image & og:title
    m_og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og:
        cand = html.unescape(m_og.group(1).strip())
        if _is_valid_washsun_image(cand):
            out["cover_image"] = cand
    if not out["title"]:
        m_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_t:
            out["title"] = _clean_title(m_t.group(1))

    # 3. Brightspot `.RichTextArticleBody`
    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        if not out["title"]:
            h1 = tree.css_first("h1")
            if h1:
                out["title"] = _clean_title(h1.text(strip=True))
        body = (
            tree.css_first(".RichTextArticleBody")
            or tree.css_first(".ArticlePage-articleBody")
            or tree.css_first("article")
            or tree.css_first("main")
        )
        if body:
            for el in body.css("h2, h3, p"):
                tag = (el.tag or "").lower()
                txt = _clean_text(el.html or "")
                if not txt or _is_noise(txt):
                    continue
                if tag in ("h2", "h3") and len(txt) < 180:
                    if txt not in out["subheadings"]:
                        out["subheadings"].append(txt)
                elif tag == "p":
                    if txt not in out["paragraphs"]:
                        out["paragraphs"].append(txt)
            # Clean inline figures (strictly rejecting author mugshots)
            cover_base = (out["cover_image"] or "").split("?")[0]
            seen_u = {cover_base} if cover_base else set()
            for fg in body.css("figure"):
                im = fg.css_first("img")
                if not im:
                    continue
                src = html.unescape(str(im.attributes.get("src") or "").strip())
                if not _is_valid_washsun_image(src):
                    continue
                base = src.split("?")[0]
                if base in seen_u:
                    continue
                seen_u.add(base)
                cap_el = fg.css_first("figcaption")
                cap = _clean_text(cap_el.html or "") if cap_el else _clean_text(im.attributes.get("alt") or "")
                out["inline_images"].append({"url": src, "caption": cap, "alt": cap or out["title"]})

    return out


def _fetch_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Optional[str]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for imp in ("safari17_2_ios", "chrome124", "safari17_0"):
            try:
                r = cffi_requests.get(url, impersonate=imp, headers=headers, proxies=proxies, timeout=18, allow_redirects=True)
                if r.status_code == 200 and len(r.text) > 10000:
                    return r.text
            except Exception:
                continue
    return None


def crawl_washsun(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for The Washington Sun (`washingtonsun.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "washingtonsun.com",
        "source": "The Washington Sun",
        "title": _clean_title(title) if title else "",
        "summary": "",
        "author": "The Washington Sun",
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

    if not url or not is_washsun_url(url):
        return result

    cache_key = _canonical_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _WASHSUN_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if html_text is None else None
    raw_html = html_text if html_text is not None else _fetch_html(url, proxies=proxies)
    if not raw_html:
        return result

    parsed = _parse_washsun_html(raw_html)
    cover = parsed.get("cover_image")
    if cover and localize_cover and html_text is None:
        cover = _localize_image(cover, proxies=proxies)

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

    result["paragraphs"] = paras
    result["paras_count"] = len(paras)
    result["lead_paragraph"] = paras[0] if paras else ""
    result["full_text"] = full_text
    result["article_content"] = full_text
    result["article_content_en"] = full_text
    result["extraction_tier"] = "washsun_brightspot_dom"

    if len(paras) >= 3 and len(full_text) >= 300:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _WASHSUN_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif len(paras) >= 1 and len(full_text) >= 120:
        result["status"] = "partial"
        result["is_substantive"] = True

    return result
