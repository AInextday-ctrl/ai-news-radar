#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Fortune Dedicated Crawler & Video/Full-Text Wire Penetration Engine
=============================================================================
Source: Fortune (财富杂志 / fortune.com)
Scope: Handles all fortune.com article extraction, authentic headline resolution,
       multi-author attribution, 100% full-text reporting, subheadings,
       high-resolution master photography, and embedded video resolution (STN Video/Minute Media/YouTube).

Architecture & Penetration Strategy:
1. Native Fortune DOM Extractor:
   - Direct extraction of article metadata, og:image, author, and paragraph nodes.
   - Extracts initial lead paragraphs from `article.article-content > p` as well as
     the full body paragraphs enclosed inside `.paywall` containers.
   - Filters out publisher copyright disclaimers (© Fortune Media IP Limited...), newsletter
     solicitations, and editorial callout links.
2. High-Resolution Master Photography:
   - Identifies original WP upload assets (`https://fortune.com/img-assets/wp-content/uploads/...`).
   - Strips downscaling query parameters (`?resize=1200,600`) to access pristine 1.5MB+ master assets.
   - Downloads and hosts image locally at `public/images/fortune_<id>.jpg` so links never break.
3. Embedded Video Stream & Metadata Resolver:
   - Penetrates Next.js React component tree to extract STN Video / Minute Media `relatedVideoId`
     (e.g., `SM900242588-900242588-14497`).
   - Parses `stnMeta` video franchise tags and anchors.
   - Extracts embedded YouTube, Brightcove, Vimeo, and HTML5 MP4 player streams.
   - Sets `has_video = True`, `video_url`, `video_id`, and `video_provider` = "stn".
4. Substantive Quality Contract:
   - Sets `is_substantive = True`, `is_paywalled = False`, `status = "success"` whenever >= 3 paragraphs
     or >= 300 characters of reporting are extracted.
   - Saves successful crawls to `data/fortune_cache.json` for fast local and CI reproduction.

Separation of Concerns:
- Completely isolated from Reuters, Bloomberg, and generic fallback scrapers.
=============================================================================
"""

import os
import re
import html
import json
import hashlib
import urllib.parse
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


# Module-level memory & disk cache
_FORTUNE_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "fortune_cache.json"
)

# Known proxies for network resilience
DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]


def _get_proxies() -> Optional[Dict[str, str]]:
    """Detects available local or environment proxy."""
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


def _get_from_disk_cache(url: str) -> Optional[Dict[str, Any]]:
    """Loads cached Fortune crawl result from disk."""
    if os.path.exists(_DISK_CACHE_FILE):
        try:
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(url)
        except Exception:
            pass
    return None


def _save_to_disk_cache(url: str, data: Dict[str, Any]) -> None:
    """Saves Fortune crawl result to disk cache."""
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        current = {}
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
        current[url] = data
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_fortune_url(url: str) -> bool:
    """Checks whether the given URL belongs to Fortune."""
    if not url:
        return False
    u = url.lower()
    return "fortune.com" in u or "fortune.net" in u


def fetch_fortune_html(url: str) -> Optional[str]:
    """
    Fetches raw Fortune article HTML using curl_cffi Chrome 120 impersonation,
    bypassing Cloudflare/Next.js protection.
    """
    if not url:
        return None

    proxies = _get_proxies()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    if HAS_CURL_CFFI:
        try:
            r = cffi_requests.get(
                url,
                headers=headers,
                proxies=proxies,
                impersonate="chrome120",
                timeout=18
            )
            if r.status_code == 200 and len(r.text) > 1000:
                return r.text
        except Exception:
            pass

    if HAS_REQUESTS:
        try:
            r = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=18
            )
            if r.status_code == 200 and len(r.text) > 1000:
                return r.text
        except Exception:
            pass

    return None


def download_and_host_image(image_url: str, article_id: str) -> Optional[str]:
    """
    Downloads high-resolution Fortune image locally to public/images/fortune_<id>.jpg (or png)
    so links never 404 or expire.
    """
    if not image_url or not image_url.startswith("http"):
        return None

    # Clean query parameters to fetch pristine master asset
    clean_download_url = image_url.split("?")[0]
    ext = ".png" if clean_download_url.lower().endswith(".png") else ".jpg"
    filename = f"fortune_{article_id}{ext}"
    local_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "public", "images", filename
    )

    cdn_url = f"https://ainewsradar.xyz/images/{filename}"

    if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
        return cdn_url

    proxies = _get_proxies()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://fortune.com/"
    }

    try:
        content = None
        if HAS_CURL_CFFI:
            r = cffi_requests.get(clean_download_url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=15)
            if r.status_code == 200 and len(r.content) > 3000:
                content = r.content
        if not content and HAS_REQUESTS:
            r = requests.get(clean_download_url, headers=headers, proxies=proxies, timeout=15)
            if r.status_code == 200 and len(r.content) > 3000:
                content = r.content

        if content:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)
            return cdn_url
    except Exception:
        pass

    # Fallback to pristine remote image if download fails
    return clean_download_url


def crawl_fortune(url: str, html_text: str = "", force_refresh: bool = False) -> Dict[str, Any]:
    """
    Comprehensive Fortune crawler:
    Extracts authentic headline, author, full 100% paragraphs, subheadings,
    master cover photography, and playable STN/iframe/MP4 video embeds.
    """
    clean_url = url.split("#")[0].split("?")[0].strip() if url else ""

    # 1. Check memory & disk cache (only when fresh HTML is not explicitly supplied)
    if not html_text and not force_refresh and clean_url:
        for cached in (_FORTUNE_CACHE.get(clean_url), _get_from_disk_cache(clean_url)):
            if cached and (cached.get("is_substantive") or cached.get("paras_count", 0) >= 3):
                # Reject legacy cache entries that still carry 404 .3.1.1.php video URL or missing article_content
                v_old = str(cached.get("video_url") or "")
                if "embedcode.3.1.1.php" not in v_old and cached.get("article_content") and cached.get("image_url"):
                    _FORTUNE_CACHE[clean_url] = dict(cached)
                    return dict(cached)

    clean_id = hashlib.md5(clean_url.encode("utf-8")).hexdigest()[:16]
    result: Dict[str, Any] = {
        "id": clean_id,
        "url": clean_url,
        "title": "",
        "author": "Fortune",
        "published_at": None,
        "cover_image": None,
        "image_url": None,
        "original_image_url": None,
        "inline_images": [],
        "paragraphs": [],
        "subheadings": [],
        "paras_count": 0,
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "lead_paragraph": "",
        "is_substantive": False,
        "is_paywalled": False,
        "has_video": False,
        "video_url": None,
        "video_embed_script": None,
        "video_id": None,
        "video_provider": None,
        "video_direct_url": None,
        "status": "failed",
        "domain": "fortune.com"
    }

    # 2. Obtain HTML
    if not html_text:
        html_text = fetch_fortune_html(clean_url) or ""

    if not html_text:
        return result

    # 3. Parse Metadata & JSON-LD
    json_ld_article: Dict[str, Any] = {}
    json_ld_matches = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.IGNORECASE)
    for ld_raw in json_ld_matches:
        try:
            ld = json.loads(ld_raw)
            if isinstance(ld, dict):
                t = ld.get("@type", "")
                if t in ["NewsArticle", "Article"] or (isinstance(t, list) and any(x in ["NewsArticle", "Article"] for x in t)):
                    json_ld_article = ld
                    break
            elif isinstance(ld, list):
                for item in ld:
                    if isinstance(item, dict) and item.get("@type") in ["NewsArticle", "Article"]:
                        json_ld_article = item
                        break
        except Exception:
            continue

    # Title Resolution
    raw_title = ""
    if json_ld_article.get("headline"):
        raw_title = str(json_ld_article["headline"]).strip()
    if not raw_title:
        m_og = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_og:
            raw_title = html.unescape(m_og.group(1)).strip()
    if not raw_title:
        m_title = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.I | re.DOTALL)
        if m_title:
            raw_title = html.unescape(m_title.group(1)).strip()

    # Clean title suffix (e.g. " | Fortune", " - Fortune")
    raw_title = re.sub(r'\s*\|\s*Fortune.*$', '', raw_title, flags=re.I)
    raw_title = re.sub(r'\s*-\s*Fortune.*$', '', raw_title, flags=re.I)
    raw_title = re.sub(r'^Trendingnow\s*', '', raw_title, flags=re.I).strip()
    result["title"] = raw_title

    # Author Resolution
    author_str = ""
    if json_ld_article.get("author"):
        auth_data = json_ld_article["author"]
        if isinstance(auth_data, list):
            names = [a.get("name") for a in auth_data if isinstance(a, dict) and a.get("name")]
            if names:
                author_str = " and ".join(names)
        elif isinstance(auth_data, dict) and auth_data.get("name"):
            author_str = str(auth_data["name"])
        elif isinstance(auth_data, str):
            author_str = auth_data

    if not author_str:
        m_auth = re.search(r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_auth:
            author_str = html.unescape(m_auth.group(1)).strip()

    if author_str:
        result["author"] = author_str

    # Date Published
    if json_ld_article.get("datePublished"):
        result["published_at"] = json_ld_article["datePublished"]
    else:
        m_date = re.search(r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|datePublished)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_date:
            result["published_at"] = m_date.group(1).strip()

    # Master Photography Resolution
    candidate_img = None
    if json_ld_article.get("image"):
        img_val = json_ld_article["image"]
        if isinstance(img_val, str):
            candidate_img = img_val
        elif isinstance(img_val, dict) and img_val.get("url"):
            candidate_img = img_val["url"]
        elif isinstance(img_val, list) and img_val:
            candidate_img = img_val[0]

    if not candidate_img:
        m_og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_og_img:
            candidate_img = html.unescape(m_og_img.group(1)).strip()

    if candidate_img:
        # Strip downscaling resize parameters to access master resolution
        clean_remote_img = candidate_img.split("?")[0]
        result["original_image_url"] = clean_remote_img
        # Localize image
        hosted_url = download_and_host_image(clean_remote_img, clean_id)
        result["cover_image"] = hosted_url or clean_remote_img
        result["image_url"] = result["cover_image"]

    # 4. Embedded Video Stream & Metadata Resolution
    # Fortune uses STN Video (SendtoNews / Minute Media Voltax) embedded via Next.js components
    related_video_id = None
    # Pattern 1: Next.js component props with possible escaped quotes: {\"relatedVideoId\":\"SM900242588-900242588-14497\"}
    m_vid_id = re.search(r'relatedVideoId["\\]*:\s*\\*["\']([^"\'\\]+)', html_text)
    if m_vid_id:
        related_video_id = m_vid_id.group(1).strip()

    # Pattern 2: Regex for STN share code format: SM\d+-\d+-\d+
    if not related_video_id:
        m_sc = re.search(r'(?:relatedVideoId|data-fk|data-sc|SC=).*?([A-Z0-9]+-\d+-\d+)', html_text)
        if m_sc:
            related_video_id = m_sc.group(1).strip()

    # Pattern 3: data-video-id or data-fk attributes
    if not related_video_id:
        m_fk = re.search(r'data-(?:video-id|fk|sc)=["\']([^"\']+)["\']', html_text)
        if m_fk:
            related_video_id = m_fk.group(1).strip()

    # Check for STN Video (official HTTP 200 Voltax/STN embed script; no-ads variant -16481 also supported)
    if related_video_id:
        stn_embed_url = f"https://embed.sendtonews.com/player3/embedcode.js?SC={related_video_id}"
        result["has_video"] = True
        result["video_id"] = related_video_id
        result["video_provider"] = "stn"
        result["video_url"] = stn_embed_url
        result["video_embed_script"] = stn_embed_url
        result["video_direct_url"] = f"{clean_url}#related-video"

    # Check for stnMeta franchise tags in JSON-LD
    if json_ld_article.get("stnMeta"):
        stn_meta = json_ld_article["stnMeta"]
        if isinstance(stn_meta, dict):
            video_tags = stn_meta.get("video", [])
            if video_tags:
                result["has_video"] = True
                if not result.get("video_provider"):
                    result["video_provider"] = "stn"
                result["video_tags"] = video_tags

    # Pattern 3: Standard embedded iframes (YouTube, Brightcove, Vimeo, MP4)
    if not result.get("video_url"):
        m_iframe = re.search(r'<iframe[^>]+src=["\']([^"\']+(?:youtube\.com/embed|player\.vimeo\.com|players\.brightcove\.net)[^"\']*)["\']', html_text, re.I)
        if m_iframe:
            result["has_video"] = True
            result["video_url"] = html.unescape(m_iframe.group(1)).strip()
            result["video_provider"] = "iframe"
        else:
            m_mp4 = re.search(r'<video[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']', html_text, re.I)
            if m_mp4:
                result["has_video"] = True
                result["video_url"] = html.unescape(m_mp4.group(1)).strip()
                result["video_provider"] = "mp4"

    # 5. Extract Full Body Paragraphs & Subheadings
    substantive_paras: List[str] = []
    subheadings: List[str] = []
    inline_figures: List[Dict[str, str]] = []

    # Noise patterns to strictly discard
    NOISE_PATTERNS = [
        r'©\s*\d{4}\s*Fortune Media IP Limited',
        r'All Rights Reserved',
        r'Use of this site constitutes acceptance of',
        r'Sign up for the\b',
        r'Subscribe to Fortune',
        r'Get the latest.*delivered to your inbox',
        r'Read Next:',
        r'Recommended Video',
        r'Sponsored Content',
        r'Advertisement\b',
        r'Fortune is a registered trademark',
        r'Quotes displayed in real-time',
        r'Terms and Conditions',
        r'Privacy Policy',
        r'Do Not Sell My Personal Information'
    ]

    def is_noise(text: str) -> bool:
        if len(text) < 25:
            return True
        for pat in NOISE_PATTERNS:
            if re.search(pat, text, re.I):
                return True
        return False

    if HAS_SELECTOLAX:
        tree = LexborHTMLParser(html_text)

        # 5.1 Inline Figures & Diagrams
        for fig in tree.css('figure'):
            img_el = fig.css_first('img')
            src = img_el.attributes.get('src') if img_el else None
            if src and not any(bad in src.lower() for bad in ["pixel", "spacer", "tracking", "icon", "logo", "avatar"]):
                clean_src = src.split("?")[0]
                cap_el = fig.css_first('figcaption')
                caption = cap_el.text().strip() if cap_el else ""
                inline_figures.append({"url": clean_src, "caption": caption})

        # 5.2 Article Content Container
        # Fortune structure: `article.article-content` contains lead <p> and `<div class="paywall">` body
        content_root = tree.css_first('article.article-content') or tree.css_first('article') or tree.css_first('.article-page-wrapper')

        if content_root:
            for child in content_root.css('h2, h3, p'):
                tag = child.tag
                txt = child.text().strip()
                if not txt:
                    continue
                if tag in ['h2', 'h3']:
                    if not is_noise(txt) and len(txt) < 150:
                        subheadings.append(txt)
                elif tag == 'p':
                    # Check parent classes
                    parent = child.parent
                    parent_cls = parent.attributes.get('class', '') if parent else ''
                    if 'description-parser' in parent_cls or 'footer' in parent_cls:
                        continue
                    if not is_noise(txt):
                        # Avoid duplicates
                        if txt not in substantive_paras:
                            substantive_paras.append(txt)

    # Fallback to regex extraction if selectolax was unavailable or yielded nothing
    if not substantive_paras:
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', html_text, flags=re.DOTALL | re.IGNORECASE)
        for p_raw in p_matches:
            clean_p = re.sub(r'<[^>]+>', '', p_raw).strip()
            clean_p = html.unescape(clean_p)
            clean_p = re.sub(r'\s+', ' ', clean_p).strip()
            if not is_noise(clean_p) and clean_p not in substantive_paras:
                substantive_paras.append(clean_p)

    # 6. Assembly & Quality Assurance
    if substantive_paras:
        result["paragraphs"] = substantive_paras
        result["paras_count"] = len(substantive_paras)
        result["lead_paragraph"] = substantive_paras[0]
        result["subheadings"] = subheadings
        result["inline_images"] = inline_figures

        # Format full text and populate all canonical text fields for downstream pipeline parity
        full_body = "\n\n".join(substantive_paras)
        result["full_text"] = full_body
        result["article_content"] = full_body
        result["article_content_en"] = full_body
        result["is_substantive"] = len(substantive_paras) >= 3 or len(full_body) >= 300
        result["is_paywalled"] = False
        result["status"] = "success"

    # Save to disk and memory cache (avoid caching unit-test mock URLs)
    if result["is_substantive"] and clean_url and "test-story" not in clean_url:
        _FORTUNE_CACHE[clean_url] = dict(result)
        _save_to_disk_cache(clean_url, dict(result))

    return result
