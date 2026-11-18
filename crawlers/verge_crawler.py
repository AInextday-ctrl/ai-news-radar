#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
The Verge Dedicated Crawler & Next.js Hydration Penetration Engine
=============================================================================
Source: The Verge (theverge.com)
Scope: Handles all theverge.com article extraction, authentic editorial headline
       resolution, multi-author attribution, Next.js GraphQL hydration block
       parsing (paragraphs, subheadings, quotes, lists, inline figures, YouTube
       embeds), gift-link (?view_token=...) full-text penetration, and high-res
       cover photography localization.

Architecture & Strategy:
1. Tier 1 — Next.js `__NEXT_DATA__` Hydration GraphQL Extractor (Primary):
   - Fetches the full URL (preserving `?view_token=...` gift links for Verge
     subscriber exclusives like Notepad and Command Line).
   - Parses `props.pageProps.hydration.responses[*].data.node` directly so zero
     UI chrome ("Follow topics and authors", "Posts from this topic will be
     added to your daily email digest", recirculation cards) ever leaks into
     article paragraphs.
2. Tier 2 — Clean DOM Fallback Extractor:
   - Handles direct HTML fixtures and legacy layouts with strict Verge UI noise
     filtering and HTML entity decoding (`&#8217;` -> `'`).
3. High-Resolution Master Photography Localization:
   - Extracts authentic `platform.theverge.com` / `cdn.vox-cdn.com` photography
     and localizes it to `public/images/verge_<hash>.jpg`.
4. Substantive Quality Contract:
   - Sets `full_text`, `article_content`, `article_content_en`, `image_url`,
     `cover_image`, `is_substantive = True`, `is_paywalled = False`.
   - Caches verified results in `data/verge_cache.json`.

Separation of Concerns:
- Completely isolated from locked Reuters, Bloomberg, Fortune, and WSJ crawlers.
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


_VERGE_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "verge_cache.json"
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

VERGE_NOISE_PHRASES = [
    "posts from this topic will be added to your daily email digest",
    "follow topics and authors",
    "follow this story to get email or text alerts",
    "sign up for verge deals",
    "subscribe to the verge",
    "verge subscribers get unlimited access",
    "already a subscriber",
    "a version of this story was also published in",
    "vox media, llc. all rights reserved",
    "if you buy something from a verge link",
    "check your inbox for a welcome email",
    "something went wrong. please enter a valid email",
    "by submitting your email, you agree to our terms",
    "want more news from the verge",
    "add the verge as a preferred source",
]


def is_verge_url(url: str) -> bool:
    """Checks whether the given URL belongs to The Verge."""
    if not url:
        return False
    return "theverge.com" in url.lower()


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


def _is_valid_verge_image(img_url: Optional[str]) -> bool:
    """Validates that a Verge image URL is absolute and non-placeholder."""
    if not img_url or not isinstance(img_url, str):
        return False
    u = img_url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    low = u.lower()
    bad_tokens = [
        "unsplash.com", "placeholder", "icon", "pixel", "avatar",
        "favicon", "og-default", "1x1", "spacer", "verge_logo"
    ]
    return not any(b in low for b in bad_tokens)


def _clean_html_fragment(fragment: str) -> str:
    """Strips HTML tags, decodes entities, and normalizes whitespace."""
    if not fragment:
        return ""
    t = html.unescape(str(fragment))
    t = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<script[^>]*>.*?</script>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\xa0]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _clean_verge_title(raw_title: str) -> str:
    """Cleans The Verge headline and removes ' | The Verge' suffixes."""
    if not raw_title:
        return ""
    t = html.unescape(str(raw_title)).strip()
    t = re.sub(r'\s*[\|\-—]\s*The Verge\s*$', '', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _is_verge_noise(text: str) -> bool:
    """Checks if a paragraph is Verge UI chrome, follow prompt, or legal boilerplate."""
    if not text or len(text) < 20:
        return True
    low = text.lower()
    return any(np in low for np in VERGE_NOISE_PHRASES)


def _get_from_disk_cache(canonical_url: str) -> Optional[Dict[str, Any]]:
    if os.path.exists(_DISK_CACHE_FILE):
        try:
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(canonical_url)
        except Exception:
            pass
    return None


def _save_to_disk_cache(canonical_url: str, data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        current = {}
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
        current[canonical_url] = data
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_verge_image(img_url: str, canonical_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads high-res The Verge cover image locally to public/images/verge_<hash>.jpg."""
    if not _is_valid_verge_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url or "platform.theverge.com/sample_" in img_url:
        return img_url
    try:
        img_id = hashlib.md5(canonical_url.encode("utf-8")).hexdigest()[:16]
        ext = ".png" if ".png" in img_url.split("?")[0].lower() else ".jpg"
        filename = f"verge_{img_id}{ext}"
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "public", "images", filename
        )
        cdn_url = f"https://ainewsradar.xyz/images/{filename}"
        if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
            return cdn_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "image/jpeg,image/png,image/webp,*/*;q=0.8",
            "Referer": "https://www.theverge.com/"
        }
        content = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(img_url, impersonate="chrome120", headers=headers, proxies=proxies, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000 and r.headers.get("content-type", "").startswith("image/"):
                    content = r.content
            except Exception:
                pass
        if not content and HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000 and r.headers.get("content-type", "").startswith("image/"):
                    content = r.content
            except Exception:
                pass
        if content:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)
            return cdn_url
    except Exception:
        pass
    return img_url


def _extract_text_from_rich_parts(parts: Any) -> str:
    """Recursively joins text/html from Verge GraphQL rich text arrays."""
    if not parts:
        return ""
    if isinstance(parts, str):
        return _clean_html_fragment(parts)
    if isinstance(parts, dict):
        if "html" in parts:
            return _clean_html_fragment(parts["html"])
        if "plaintext" in parts:
            return _clean_html_fragment(parts["plaintext"])
        if "text" in parts:
            return _clean_html_fragment(parts["text"])
        return ""
    if isinstance(parts, list):
        chunks = [_extract_text_from_rich_parts(p) for p in parts]
        return " ".join(c for c in chunks if c).strip()
    return ""


def _parse_verge_next_data(html_text: str) -> Dict[str, Any]:
    """Extracts structured article payload from The Verge's Next.js `__NEXT_DATA__` hydration JSON."""
    out: Dict[str, Any] = {
        "title": "",
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
    m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I)
    if not m:
        return out
    try:
        nd = json.loads(m.group(1))
    except Exception:
        return out

    responses = nd.get("props", {}).get("pageProps", {}).get("hydration", {}).get("responses", [])
    article_node = None
    for resp in responses:
        node = (resp.get("data") or {}).get("node") if isinstance(resp, dict) else None
        if isinstance(node, dict) and node.get("blocks"):
            article_node = node
            break

    if not article_node:
        return out

    if article_node.get("title"):
        out["title"] = _clean_verge_title(article_node["title"])

    authors = article_node.get("authors") or []
    if isinstance(authors, list):
        names = [str(a.get("name")).strip() for a in authors if isinstance(a, dict) and a.get("name")]
        if names:
            out["author"] = " and ".join(names)

    if article_node.get("publishedAt"):
        out["published_at"] = article_node["publishedAt"]

    # Featured cover image
    fi = article_node.get("featuredImage")
    if isinstance(fi, dict):
        thumbs = fi.get("thumbnails") or {}
        cand = None
        for k in ("horizontal", "large", "original", "square"):
            if isinstance(thumbs.get(k), dict) and thumbs[k].get("url"):
                cand = thumbs[k]["url"]
                break
        if not cand:
            cand = fi.get("url")
        if cand and _is_valid_verge_image(cand):
            out["cover_image"] = cand

    # Traverse structured article blocks
    for blk in article_node.get("blocks") or []:
        if not isinstance(blk, dict):
            continue
        btype = str(blk.get("__typename") or blk.get("type") or "")

        if "Paragraph" in btype:
            txt = _extract_text_from_rich_parts(blk.get("paragraphContents") or blk.get("contents"))
            if txt and not _is_verge_noise(txt) and txt not in out["paragraphs"]:
                out["paragraphs"].append(txt)

        elif "Heading" in btype:
            htxt = _extract_text_from_rich_parts(blk.get("contents") or blk.get("headingContents") or blk.get("text"))
            if htxt and not _is_verge_noise(htxt) and len(htxt) < 160:
                out["subheadings"].append(htxt)

        elif "Quote" in btype or "Pullquote" in btype:
            qtxt = _extract_text_from_rich_parts(blk.get("quoteContents") or blk.get("contents") or blk.get("paragraphs"))
            if qtxt and not _is_verge_noise(qtxt) and qtxt not in out["paragraphs"]:
                out["paragraphs"].append(f'"{qtxt}"' if not qtxt.startswith(('"', '“')) else qtxt)

        elif "List" in btype:
            items = blk.get("items") or blk.get("listItems") or []
            for li in items:
                ltxt = _extract_text_from_rich_parts(li.get("contents") if isinstance(li, dict) else li)
                if ltxt and not _is_verge_noise(ltxt) and ltxt not in out["paragraphs"]:
                    out["paragraphs"].append(ltxt)

        elif "Image" in btype:
            img_obj = blk.get("image") or blk
            i_url = None
            if isinstance(img_obj, dict):
                thumbs = img_obj.get("thumbnails") or {}
                for k in ("horizontal", "large", "original"):
                    if isinstance(thumbs.get(k), dict) and thumbs[k].get("url"):
                        i_url = thumbs[k]["url"]
                        break
                if not i_url:
                    i_url = img_obj.get("url")
            if i_url and _is_valid_verge_image(i_url):
                cap = _extract_text_from_rich_parts(blk.get("caption") or (img_obj.get("caption") if isinstance(img_obj, dict) else ""))
                out["inline_images"].append({"url": i_url, "caption": cap, "alt": cap or out["title"]})

        elif "Embed" in btype or "Video" in btype:
            blk_str = json.dumps(blk)
            m_yt = re.search(r'(?:youtube\.com/embed/|youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})', blk_str)
            if m_yt and not out["video_url"]:
                out["has_video"] = True
                out["video_url"] = f"https://www.youtube.com/embed/{m_yt.group(1)}"
                out["video_provider"] = "iframe"

    return out


def fetch_verge_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Fetches raw The Verge HTML using Chrome 120 TLS impersonation (preserving gift view_token)."""
    if not url:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    if HAS_CURL_CFFI:
        try:
            r = cffi_requests.get(url, impersonate="chrome120", headers=headers, proxies=proxies, timeout=12)
            if r.status_code == 200 and len(r.text) > 2000:
                return r.text
        except Exception:
            pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=12)
            if r.status_code == 200 and len(r.text) > 2000:
                return r.text
        except Exception:
            pass
    return None


def crawl_verge(url: str, html_text: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Dedicated The Verge Crawler.
    Extracts authentic headline, multi-author byline, zero-noise full-text paragraphs,
    subheadings, localized high-res cover photography, inline figures, and YouTube embeds.
    """
    clean_url = url.split("#")[0].split("?")[0].strip() if url else ""
    clean_id = hashlib.md5(clean_url.encode("utf-8")).hexdigest()[:16] if clean_url else ""

    result: Dict[str, Any] = {
        "id": clean_id,
        "url": clean_url,
        "source": "The Verge",
        "domain": "theverge.com",
        "title": "",
        "author": "The Verge",
        "published_at": None,
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "paragraphs": [],
        "subheadings": [],
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "lead_paragraph": "",
        "paras_count": 0,
        "has_video": False,
        "video_url": None,
        "video_provider": None,
        "is_substantive": False,
        "is_paywalled": False,
        "status": "failed"
    }

    if not clean_url:
        return result

    # 1. Check cache
    if not html_text and not force_refresh:
        for cached in (_VERGE_CACHE.get(clean_url), _get_from_disk_cache(clean_url)):
            if cached and cached.get("status") == "success" and cached.get("is_substantive") and cached.get("article_content"):
                _VERGE_CACHE[clean_url] = dict(cached)
                return dict(cached)

    proxies = _get_proxies()
    supplied_html = bool(html_text)
    if not html_text:
        # Preserve original URL (including ?view_token=... gift link) on HTTP fetch!
        html_text = fetch_verge_html(url, proxies=proxies) or ""

    if not html_text:
        return result

    # 2. Tier 1: Structured __NEXT_DATA__ GraphQL hydration extraction
    nd = _parse_verge_next_data(html_text)
    if nd["title"]:
        result["title"] = nd["title"]
    if nd["author"]:
        result["author"] = nd["author"]
    if nd["published_at"]:
        result["published_at"] = nd["published_at"]
    if nd["cover_image"]:
        result["cover_image"] = nd["cover_image"]
    if nd["paragraphs"]:
        result["paragraphs"] = nd["paragraphs"]
    if nd["subheadings"]:
        result["subheadings"] = nd["subheadings"]
    if nd["inline_images"]:
        result["inline_images"] = nd["inline_images"]
    if nd["has_video"]:
        result["has_video"] = True
        result["video_url"] = nd["video_url"]
        result["video_provider"] = nd["video_provider"]

    # 3. Tier 2: Metadata & DOM fallback if any field is missing
    if not result["title"]:
        m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_og_t:
            result["title"] = _clean_verge_title(m_og_t.group(1))
    if not result["cover_image"]:
        m_og_i = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_og_i:
            cand = html.unescape(m_og_i.group(1)).strip()
            if _is_valid_verge_image(cand):
                result["cover_image"] = cand

    if result["author"] == "The Verge":
        for ld_raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
            try:
                ld = json.loads(ld_raw)
                objs = ld if isinstance(ld, list) else [ld]
                for obj in objs:
                    if isinstance(obj, dict) and obj.get("author"):
                        auth = obj["author"]
                        if isinstance(auth, list):
                            names = [a.get("name") for a in auth if isinstance(a, dict) and a.get("name")]
                            if names:
                                result["author"] = " and ".join(names)
                                break
                        elif isinstance(auth, dict) and auth.get("name"):
                            result["author"] = str(auth["name"])
                            break
                        elif isinstance(auth, str):
                            result["author"] = auth
                            break
            except Exception:
                continue

    if not result["paragraphs"]:
        paras = []
        if HAS_SELECTOLAX:
            tree = LexborHTMLParser(html_text)
            for bad in tree.css("style, script, noscript, nav, footer, aside, form"):
                bad.decompose()
            nodes = tree.css(".duet--article--article-body-component p, article p")
            for p in nodes:
                cp = _clean_html_fragment(p.text())
                if cp and len(cp) >= 25 and not _is_verge_noise(cp) and cp not in paras:
                    paras.append(cp)
        else:
            for pm in re.findall(r'<p[^>]*>(.*?)</p>', html_text, re.DOTALL | re.I):
                cp = _clean_html_fragment(pm)
                if cp and len(cp) >= 25 and not _is_verge_noise(cp) and cp not in paras:
                    paras.append(cp)
        result["paragraphs"] = paras

    # Localize high-res cover photography (skip when mock html_text is supplied in unit tests)
    if result["cover_image"]:
        if not supplied_html:
            result["cover_image"] = _localize_verge_image(result["cover_image"], clean_url, proxies=proxies)
        result["image_url"] = result["cover_image"]

    # 4. Final assembly
    if result["paragraphs"]:
        full_body = "\n\n".join(result["paragraphs"])
        result["paras_count"] = len(result["paragraphs"])
        result["lead_paragraph"] = result["paragraphs"][0]
        result["full_text"] = full_body
        result["article_content"] = full_body
        result["article_content_en"] = full_body
        result["is_substantive"] = len(result["paragraphs"]) >= 3 or len(full_body) >= 300
        result["is_paywalled"] = False
        result["status"] = "success"

    if result["is_substantive"] and not supplied_html and "sample-story" not in clean_url:
        _VERGE_CACHE[clean_url] = dict(result)
        _save_to_disk_cache(clean_url, dict(result))

    return result
