#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
MIT Technology Review Dedicated Crawler & WordPress REST Penetration Engine
=============================================================================
Source: MIT Technology Review (technologyreview.com)
Scope: Handles all technologyreview.com article extraction, authentic editorial
       headline resolution, real journalist byline extraction (WP `_embedded`
       + HTML `a[href*="/author/"]`), full-text extraction via official
       WordPress REST API (`/wp-json/wp/v2/posts/{id}?_embed=1` & `?slug=...`)
       with HTML `#content--body` fallback, newsletter/subscription/related
       noise stripping, WP-size-suffix-aware image deduplication, Vimeo/YouTube
       video extraction (excluding audio-only Simplecast/Spotify podcasts) with
       oEmbed aspect-ratio resolution, and cover image localization to
       `public/images/mittr_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 10 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import quote, urlparse
from typing import Dict, Any, List, Optional, Tuple
from .content_filters import detect_low_value_roundup_or_promo

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


_MITTR_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "mittr_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

MITTR_NOISE_PHRASES = [
    "only available to mit technology review subscribers",
    "subscribe to mit technology review",
    "already a subscriber",
    "become a subscriber",
    "unlock unlimited access",
    "give the gift of",
    "sign up for the download",
    "sign up for our",
    "sign up for",
    "delivered to your inbox",
    "you can unsubscribe at any time",
    "by signing up you agree",
    "related stories:",
    "related story",
    "read more:",
    "read next:",
    "read the full story",
    "got any ideas? drop me a line",
    "drop me a line",
    "follow us on",
    "listen to the session or watch below",
    "this content was produced by",
    "it was not written by mit technology review",
    "mit technology review insights",
    "copyright ©",
    "all rights reserved",
    "advertisement",
    "sponsored content",
    "get the latest",
    "stay up to date",
]

AUDIO_ONLY_IFRAME_DOMAINS = (
    "simplecast.com",
    "open.spotify.com",
    "megaphone.fm",
    "omny.fm",
    "podcasts.apple.com",
    "soundcloud.com",
    "art19.com",
    "libsyn.com",
    "podbean.com",
    "transistor.fm",
    "acast.com",
)

BAD_IMAGE_TOKENS = (
    "avatar",
    "headshot",
    "author",
    "profile",
    "logo",
    "icon",
    "badge",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "doubleclick",
    "googlesyndication",
    "unsplash.com",
    "placeholder",
    "newsletter",
    "subscribe",
    "podcast-badge",
    "app-store",
    "google-play",
    "1x1",
)


def is_mittr_url(url: str) -> bool:
    """Returns True if URL belongs to MIT Technology Review."""
    if not url or not isinstance(url, str):
        return False
    low = url.lower()
    return "technologyreview.com" in low


def _canonical_mittr_key(url: str) -> str:
    clean = (url or "").split("?")[0].split("#")[0].strip().rstrip("/").lower()
    return clean


def _extract_mittr_post_id(url: str) -> Optional[str]:
    """Extracts numeric WP post ID from `/YYYY/MM/DD/<id>/<slug>/`."""
    m = re.search(r"/20\d{2}/\d{2}/\d{2}/(\d{5,9})(?:/|$)", url or "")
    return m.group(1) if m else None


def _extract_mittr_slug(url: str) -> Optional[str]:
    path = urlparse(url or "").path.strip("/")
    if not path:
        return None
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    last = parts[-1]
    if last.isdigit() and len(parts) >= 2:
        return parts[-2]
    return last


def _get_proxies() -> Optional[Dict[str, str]]:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return None
    for env_key in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        val = os.environ.get(env_key)
        if val:
            return {"http": val, "https": val}
    if HAS_REQUESTS:
        import socket
        for p in DEFAULT_PROXIES:
            try:
                host_port = p.replace("http://", "").replace("https://", "")
                host, port_s = host_port.split(":")
                s = socket.create_connection((host, int(port_s)), timeout=0.4)
                s.close()
                return {"http": p, "https": p}
            except Exception:
                continue
    return None


def _clean_text(text: str) -> str:
    if not text:
        return ""
    t = html.unescape(str(text))
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _clean_mittr_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*MIT Technology Review\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*\(MIT Technology Review\)\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_mittr_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"archive\s+page", "", t, flags=re.I)
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("mit technology review", "mit tech review", "staff", "editors"):
        return ""
    return t


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 22:
        return True
    low = t.lower()
    if any(phrase in low for phrase in MITTR_NOISE_PHRASES):
        return True
    if re.match(r"^(recorded on|speakers?:|related|explore how|read more|watch now)\b", low) and len(t) < 130:
        return True
    if re.match(r"^[+•\-\s]+$", t):
        return True
    return False


def _mittr_media_stem(url: str) -> str:
    """
    Canonicalizes WordPress image URLs so resized variants
    (`foo-1024x576.jpg?resize=1200,600` vs `foo.jpg`) deduplicate cleanly.
    """
    if not url:
        return ""
    base = url.split("?")[0].split("#")[0].strip().lower()
    base = re.sub(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    return base


def _is_valid_mittr_image(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    if low.endswith((".svg", ".ico")):
        return False
    return True


def _clean_wp_image_url(url: str) -> str:
    """Strips tiny WordPress crop params like `?resize=300,200` to obtain high-res source."""
    if not url:
        return ""
    u = html.unescape(url.strip())
    if "wp.technologyreview.com/wp-content/uploads/" in u.lower():
        base = u.split("?")[0]
        return base
    return u


def _load_disk_cache() -> None:
    if _MITTR_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _MITTR_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_MITTR_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_mittr_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads MIT Technology Review hero cover photo to `public/images/mittr_<hash>.jpg`."""
    if not _is_valid_mittr_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        clean_u = _clean_wp_image_url(img_url)
        h = hashlib.md5(_mittr_media_stem(clean_u).encode("utf-8")).hexdigest()[:16]
        fname = f"mittr_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.technologyreview.com/",
            "Accept": "image/jpeg,image/png,image/webp,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        for cand_u in (clean_u, img_url):
            if content:
                break
            if HAS_REQUESTS:
                try:
                    r = requests.get(cand_u, headers=headers, proxies=proxies, timeout=16)
                    if r.status_code == 200 and len(r.content) > 5000:
                        ct = r.headers.get("content-type", "").lower()
                        if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P"):
                            content = r.content
                            break
                except Exception:
                    pass
            if content is None and HAS_CURL_CFFI:
                try:
                    r = cffi_requests.get(cand_u, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
                    if r.status_code == 200 and len(r.content) > 5000:
                        content = r.content
                        break
                except Exception:
                    pass
        if content:
            try:
                from io import BytesIO
                from PIL import Image
                im = Image.open(BytesIO(content))
                need_convert = (
                    len(content) > 1_200_000
                    or im.width > 1600
                    or (im.format or "").upper() not in ("JPEG", "JPG")
                )
                if need_convert:
                    if im.width > 1600:
                        ratio = 1600 / float(im.width)
                        im = im.resize((1600, max(1, int(im.height * ratio))), Image.LANCZOS)
                    if im.mode in ("RGBA", "P", "LA"):
                        im = im.convert("RGB")
                    buf = BytesIO()
                    im.save(buf, format="JPEG", quality=86, optimize=True)
                    content = buf.getvalue()
            except Exception:
                pass
            with open(fpath, "wb") as f:
                f.write(content)
            return public_url
    except Exception:
        pass
    return img_url


def _resolve_vimeo_oembed(vimeo_url: str, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Resolves official Vimeo oEmbed metadata for exact aspect ratio, poster, and title."""
    meta: Dict[str, Any] = {"video_aspect": "16x9", "video_poster": None, "video_title": ""}
    m_id = re.search(r"vimeo\.com/(?:video/)?(\d+)", vimeo_url or "")
    if not m_id or not HAS_REQUESTS:
        return meta
    vid_id = m_id.group(1)
    try:
        oembed_url = f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{vid_id}"
        r = requests.get(oembed_url, proxies=proxies, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json()
            w = int(data.get("width") or 0)
            h = int(data.get("height") or 0)
            if w > 0 and h > 0:
                ratio = w / float(h)
                if ratio < 0.8:
                    meta["video_aspect"] = "9x16"
                elif ratio <= 1.15:
                    meta["video_aspect"] = "1x1"
                else:
                    meta["video_aspect"] = f"{w}x{h}"
            if data.get("thumbnail_url"):
                meta["video_poster"] = str(data["thumbnail_url"]).strip()
            if data.get("title"):
                meta["video_title"] = _clean_text(data["title"])
    except Exception:
        pass
    return meta


def _extract_video_from_html(fragment: str, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Extracts genuine embedded video players (Vimeo, YouTube, native MP4/WebM)
    while explicitly ignoring audio-only podcast players (Simplecast, Spotify, etc.).
    """
    out: Dict[str, Any] = {
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
    }
    if not fragment:
        return out

    # 1. Native <video> / <source src="...mp4">
    m_mp4 = re.search(r'<source[^>]+src=["\']([^"\']+\.(?:mp4|webm)(?:\?[^"\']*)?)["\']', fragment, re.I)
    if not m_mp4:
        m_mp4 = re.search(r'<video[^>]+src=["\']([^"\']+\.(?:mp4|webm)(?:\?[^"\']*)?)["\']', fragment, re.I)
    if m_mp4:
        out["has_video"] = True
        out["video_url"] = html.unescape(m_mp4.group(1).strip())
        out["video_provider"] = "mp4"
        return out

    # 2. <iframe> video embeds (Vimeo / YouTube / Brightcove / JWPlayer)
    for m_ifr in re.finditer(r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]*>', fragment, re.I):
        src = html.unescape(m_ifr.group(1).strip())
        low = src.lower()
        if any(aud in low for aud in AUDIO_ONLY_IFRAME_DOMAINS):
            continue
        if "player.vimeo.com/video/" in low:
            m_vid = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
            out["has_video"] = True
            out["video_url"] = src
            out["video_id"] = m_vid.group(1) if m_vid else None
            out["video_provider"] = "iframe"
            if proxies is not None or HAS_REQUESTS:
                vmeta = _resolve_vimeo_oembed(src, proxies=proxies)
                out.update({k: v for k, v in vmeta.items() if v})
            return out
        if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
            m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
            out["has_video"] = True
            out["video_url"] = src
            out["video_id"] = m_yt.group(1) if m_yt else None
            out["video_provider"] = "iframe"
            out["video_aspect"] = "16x9"
            return out

    return out


def _parse_content_fragment(
    content_html: str,
    cover_image: Optional[str] = None,
) -> Tuple[List[str], List[str], List[str]]:
    """Parses clean paragraphs, subheadings, and deduplicated inline images from HTML."""
    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[str] = []
    seen_p = set()
    seen_img_stems = set()
    if cover_image:
        seen_img_stems.add(_mittr_media_stem(cover_image))

    if not content_html:
        return paragraphs, subheadings, inline_images

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(content_html)
        # Strip non-editorial widgets, scripts, styles, forms, newsletter signups
        for sel in (
            "script", "style", "noscript", "form", "svg",
            "[class*='newsletter']", "[class*='subscribe']", "[class*='promo']",
            "[class*='related']", "[class*='advert']", "[class*='sponsor']",
            "[class*='paywall']", ".screen-reader-text",
        ):
            for n in tree.css(sel):
                n.decompose()

        for node in tree.css("h2, h3, p, blockquote, li, figure img, img"):
            tag = (node.tag or "").lower()
            if tag == "img":
                src = node.attributes.get("data-src") or node.attributes.get("src") or ""
                src = _clean_wp_image_url(src)
                if _is_valid_mittr_image(src):
                    stem = _mittr_media_stem(src)
                    if stem and stem not in seen_img_stems:
                        seen_img_stems.add(stem)
                        inline_images.append(src)
                continue

            txt = _clean_text(node.text(separator=" "))
            if not txt:
                continue
            if tag in ("h2", "h3"):
                if 4 <= len(txt) <= 140 and not _is_noise_paragraph(txt):
                    if txt.lower() not in ("related stories", "related stories:", "read more"):
                        subheadings.append(txt)
                continue

            if tag == "li" and len(txt) < 40:
                continue
            if _is_noise_paragraph(txt):
                continue
            key = txt.lower()[:120]
            if key not in seen_p:
                seen_p.add(key)
                paragraphs.append(txt)
    else:
        for m in re.finditer(r"<p[^>]*>(.*?)</p>", content_html, re.S | re.I):
            txt = _clean_text(re.sub(r"<[^>]+>", " ", m.group(1)))
            if not _is_noise_paragraph(txt):
                key = txt.lower()[:120]
                if key not in seen_p:
                    seen_p.add(key)
                    paragraphs.append(txt)
        for m_img in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', content_html, re.I):
            src = _clean_wp_image_url(m_img.group(1))
            if _is_valid_mittr_image(src):
                stem = _mittr_media_stem(src)
                if stem and stem not in seen_img_stems:
                    seen_img_stems.add(stem)
                    inline_images.append(src)

    return paragraphs, subheadings, inline_images[:6]


def _parse_mittr_html(html_text: str, resolve_oembed: bool = False, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Parses MIT Technology Review full HTML page (fallback + og:image/byline enrichment)."""
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
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
    }
    if not html_text:
        return out

    # og:title / og:description / og:image / article:published_time
    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t:
        out["title"] = _clean_mittr_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d:
        out["summary"] = _clean_text(m_og_d.group(1))
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i:
        cand = _clean_wp_image_url(m_og_i.group(1))
        if _is_valid_mittr_image(cand):
            out["cover_image"] = cand
    m_pub = re.search(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_pub:
        out["published_at"] = m_pub.group(1).strip()

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        if not out["title"]:
            h1 = tree.css_first("h1")
            if h1:
                out["title"] = _clean_mittr_title(h1.text(separator=" "))

        # Real journalist bylines scoped strictly to the article header/byline (never sidebar/related stories)
        authors: List[str] = []
        byline_container = (
            tree.css_first('[class*="byline"]')
            or tree.css_first('[class*="Byline"]')
            or tree.css_first('[class*="contentHeader"]')
            or tree.css_first("header")
        )
        author_links = byline_container.css('a[href*="/author/"]') if byline_container else tree.css('a[href*="/author/"]')[:2]
        for a in author_links:
            txt = _clean_mittr_author(a.text(separator=" "))
            if txt and txt not in authors:
                authors.append(txt)
        if authors:
            out["author"] = " and ".join(authors) if len(authors) <= 2 else ", ".join(authors[:-1]) + f", and {authors[-1]}"

        body_node = tree.css_first("#content--body") or tree.css_first("[class*='contentBody']") or tree.css_first("article")
        if body_node:
            frag = body_node.html or ""
            paras, subs, inls = _parse_content_fragment(frag, cover_image=out["cover_image"])
            out["paragraphs"] = paras
            out["subheadings"] = subs
            out["inline_images"] = inls
            vmeta = _extract_video_from_html(frag, proxies=proxies if resolve_oembed else None)
            if vmeta.get("has_video"):
                out.update(vmeta)

    return out


def _fetch_mittr_wp_post(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
    """Fetches canonical MIT Technology Review post via official WordPress REST API."""
    post_id = _extract_mittr_post_id(url)
    slug = _extract_mittr_slug(url)
    endpoints: List[Tuple[str, str]] = []
    if post_id:
        endpoints.append((f"https://www.technologyreview.com/wp-json/wp/v2/posts/{post_id}?_embed=1", "mittr_wp_id"))
    if slug:
        endpoints.append((f"https://www.technologyreview.com/wp-json/wp/v2/posts?slug={quote(slug)}&_embed=1", "mittr_wp_slug"))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }

    for api_url, tier in endpoints:
        data = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(api_url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=15)
                if r.status_code == 200:
                    data = r.json()
            except Exception:
                pass
        if data is None and HAS_REQUESTS:
            try:
                r = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
                if r.status_code == 200:
                    data = r.json()
            except Exception:
                pass
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0], tier
        if isinstance(data, dict) and data.get("id") and data.get("content"):
            return data, tier
    return None, "failed"


def _fetch_mittr_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    """Fetches MIT Technology Review HTML page with Chrome TLS fingerprint + Wayback fallback."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        try:
            r = cffi_requests.get(url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "mittr_html_cffi"
        except Exception:
            pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "mittr_html_requests"
        except Exception:
            pass
        # Wayback Machine fallback
        try:
            cdx = f"https://web.archive.org/cdx/search/cdx?url={quote(url, safe='')}&output=json&filter=statuscode:200&limit=1"
            cr = requests.get(cdx, proxies=proxies, timeout=12)
            if cr.status_code == 200:
                rows = cr.json()
                if isinstance(rows, list) and len(rows) > 1:
                    ts, orig = rows[-1][1], rows[-1][2]
                    wr = requests.get(f"https://web.archive.org/web/{ts}id_/{orig}", proxies=proxies, timeout=18, headers={"User-Agent": "Mozilla/5.0"})
                    if wr.status_code == 200 and len(wr.text) > 10000:
                        return wr.text, "mittr_wayback"
        except Exception:
            pass
    return None, "failed"


def _parse_mittr_wp_post(post: Dict[str, Any], resolve_oembed: bool = False, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Parses a WordPress REST API post object into structured editorial fields."""
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "",
        "published_at": post.get("date_gmt") or post.get("date"),
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
        "inline_images": [],
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
        "class_list": post.get("class_list") if isinstance(post.get("class_list"), list) else [],
        "raw_content_text": "",
    }
    raw_title = (post.get("title") or {}).get("rendered") if isinstance(post.get("title"), dict) else post.get("title")
    if raw_title:
        out["title"] = _clean_mittr_title(str(raw_title))

    raw_excerpt = (post.get("excerpt") or {}).get("rendered") if isinstance(post.get("excerpt"), dict) else ""
    if raw_excerpt:
        out["summary"] = _clean_text(re.sub(r"<[^>]+>", " ", raw_excerpt))

    emb = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    # Authors
    authors: List[str] = []
    for a in (emb.get("author") or []):
        if isinstance(a, dict) and a.get("name"):
            cleaned = _clean_mittr_author(str(a["name"]))
            if cleaned and cleaned not in authors:
                authors.append(cleaned)
    if authors:
        out["author"] = " and ".join(authors) if len(authors) <= 2 else ", ".join(authors[:-1]) + f", and {authors[-1]}"

    # Cover image from Jetpack / _embedded wp:featuredmedia
    cand_cover = post.get("jetpack_featured_media_url") or ""
    if not cand_cover and emb.get("wp:featuredmedia"):
        fm = emb["wp:featuredmedia"][0]
        if isinstance(fm, dict):
            cand_cover = fm.get("source_url") or ""
    if cand_cover:
        cand_cover = _clean_wp_image_url(str(cand_cover))
        if _is_valid_mittr_image(cand_cover):
            out["cover_image"] = cand_cover

    # Body HTML
    content_html = (post.get("content") or {}).get("rendered") if isinstance(post.get("content"), dict) else ""
    out["raw_content_text"] = _clean_text(re.sub(r"<[^>]+>", " ", content_html))
    paras, subs, inls = _parse_content_fragment(content_html, cover_image=out["cover_image"])
    out["paragraphs"] = paras
    out["subheadings"] = subs
    out["inline_images"] = inls

    # Video embed (Vimeo / YouTube / MP4; ignores audio-only podcasts)
    vmeta = _extract_video_from_html(content_html, proxies=proxies if resolve_oembed else None)
    if vmeta.get("has_video"):
        out.update(vmeta)

    return out


def crawl_mittr(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    wp_post: Optional[Dict[str, Any]] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for MIT Technology Review (`technologyreview.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "technologyreview.com",
        "source": "MIT Technology Review",
        "title": _clean_mittr_title(title) if title else "",
        "summary": "",
        "author": "MIT Technology Review",
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
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
        "is_filtered_out": False,
        "filter_reason": "",
        "extraction_tier": "failed",
    }

    if not url or not is_mittr_url(url):
        return result

    # Early fast-reject for obvious link-roundups ("The Download"), event promos ("Roundtables"), and hub pages ("Research Reports")
    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_mittr_key(url)
    if use_cache and html_text is None and wp_post is None:
        _load_disk_cache()
        cached = _MITTR_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_filtered_out"):
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if (html_text is None and wp_post is None) else None
    parsed: Dict[str, Any] = {}
    tier = "failed"

    # 1. WordPress REST API (gold-standard fulltext without paywall truncation)
    if wp_post is not None:
        parsed = _parse_mittr_wp_post(wp_post, resolve_oembed=False, proxies=None)
        tier = "mittr_injected_wp"
    elif html_text is None:
        post_obj, wp_tier = _fetch_mittr_wp_post(url, proxies=proxies)
        if post_obj:
            parsed = _parse_mittr_wp_post(post_obj, resolve_oembed=True, proxies=proxies)
            tier = wp_tier

    # Post-WP taxonomy & raw-body check (catches `tag-sponsored`, `category-download-newsletter`, `tag-roundtables`, brand-studio advertorials)
    if parsed:
        post_flagged, post_reason = detect_low_value_roundup_or_promo(
            title=parsed.get("title") or title,
            url=url,
            body=parsed.get("raw_content_text") or "\n\n".join(parsed.get("paragraphs") or []),
            summary=parsed.get("summary") or "",
            classes=parsed.get("class_list"),
        )
        if post_flagged:
            result["status"] = "filtered_promo_or_roundup"
            result["is_filtered_out"] = True
            result["filter_reason"] = post_reason
            if use_cache and html_text is None and wp_post is None:
                _load_disk_cache()
                _MITTR_CACHE[cache_key] = dict(result)
                _save_disk_cache()
            return result

    # 2. HTML enrichment / fallback (when injected, or missing cover/author/body)
    need_html = (
        html_text is not None
        or not parsed
        or not parsed.get("cover_image")
        or not parsed.get("author")
        or len("\n\n".join(parsed.get("paragraphs") or [])) < 400
    )
    if need_html:
        raw_html = html_text
        html_tier = "mittr_injected_html"
        if raw_html is None:
            raw_html, html_tier = _fetch_mittr_html(url, proxies=proxies)
        if raw_html:
            hp = _parse_mittr_html(raw_html, resolve_oembed=(html_text is None), proxies=proxies)
            if not parsed:
                parsed = hp
                tier = html_tier
            else:
                if not parsed.get("title") and hp.get("title"):
                    parsed["title"] = hp["title"]
                if not parsed.get("summary") and hp.get("summary"):
                    parsed["summary"] = hp["summary"]
                if not parsed.get("author") and hp.get("author"):
                    parsed["author"] = hp["author"]
                if not parsed.get("cover_image") and hp.get("cover_image"):
                    parsed["cover_image"] = hp["cover_image"]
                if not parsed.get("published_at") and hp.get("published_at"):
                    parsed["published_at"] = hp["published_at"]
                if not parsed.get("has_video") and hp.get("has_video"):
                    for vk in ("has_video", "video_url", "video_id", "video_provider", "video_aspect", "video_poster", "video_title"):
                        if hp.get(vk):
                            parsed[vk] = hp[vk]
                # Only replace WP paragraphs if HTML body is clearly richer and non-stub
                wp_len = len("\n\n".join(parsed.get("paragraphs") or []))
                hp_len = len("\n\n".join(hp.get("paragraphs") or []))
                if wp_len < 400 and hp_len > wp_len:
                    parsed["paragraphs"] = hp["paragraphs"]
                    parsed["subheadings"] = hp.get("subheadings") or parsed.get("subheadings") or []
                    tier = f"{tier}+{html_tier}"

    if not parsed:
        return result

    # Cover image fallback to first valid inline image, then re-deduplicate inline_images
    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if not cover and inlines:
        cover = inlines.pop(0)
    if cover:
        cover_stem = _mittr_media_stem(cover)
        inlines = [u for u in inlines if _mittr_media_stem(u) != cover_stem]
        if localize_cover and html_text is None and wp_post is None:
            cover = _localize_mittr_image(cover, proxies=proxies)

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
    result["inline_images"] = inlines
    if parsed.get("subheadings"):
        result["subheadings"] = parsed["subheadings"]
    if parsed.get("has_video") and parsed.get("video_url"):
        result["has_video"] = True
        result["video_url"] = parsed["video_url"]
        result["video_id"] = parsed.get("video_id")
        result["video_provider"] = parsed.get("video_provider") or "iframe"
        if parsed.get("video_aspect"):
            result["video_aspect"] = parsed["video_aspect"]
        if parsed.get("video_poster"):
            result["video_poster"] = parsed["video_poster"]
        if parsed.get("video_title"):
            result["video_title"] = parsed["video_title"]

    result["paragraphs"] = paras
    result["paras_count"] = len(paras)
    result["lead_paragraph"] = paras[0] if paras else ""
    result["full_text"] = full_text
    result["article_content"] = full_text
    result["article_content_en"] = full_text
    result["extraction_tier"] = tier

    if (len(paras) >= 3 and len(full_text) >= 400) or (result["has_video"] and len(full_text) >= 250):
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None and wp_post is None:
            _load_disk_cache()
            _MITTR_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
