#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
IGN Dedicated Crawler (`ign.com`)
=============================================================================
Source: IGN (`ign.com` / `www.ign.com`)
Scope: Handles all ign.com news, reviews, and feature articles:
       - Pure-Python LZ-String UTF-16 decompression of IGN's Next.js
         `<script id="__NEXT_DATA__">` `props.apolloState` GraphQL cache.
       - Authentic headline resolution (`ModernContent.title` / `<h1>` /
         JSON-LD `NewsArticle`/`Article`), multi-author byline resolution via
         `contributorsOrBylines` -> `Contributor:*` (e.g., "Luke Reilly and
         Simon Cardy"), and exact ISO `publishDate`.
       - Single-pass `article.processedHtml` (with DOM `section.article-page`
         fallback) walk:
         * Hard-stops at `data-transform="divider"` / `author-sign-off` so
           editorial bios, related widgets, and comment widgets never leak.
         * Strips `<aside>` editorial promo boxes, `mobile-ad-break`, `poll`,
           commerce/newsletter widgets, and `"For more ..., check out our "`
           cross-promo tail lines.
         * Resolves inline `<section data-transform="slideshow">` galleries
           directly from Apollo `ROOT_QUERY.slideshow(...)` HD `Image:*`
           entries (capped to 4 representative HD frames per gallery, with
           authentic captions) at exact `after_para` + `dom_order`.
         * Resolves hero videos (`article.heroVideoContentId` -> `ModernVideo`
           720p MP4 + poster at `after_para=-1`) and inline IGN videos
           (`<section data-transform="ignvideo" data-slug="...">` -> 720p MP4
           + poster at exact `after_para` + `dom_order`).
         * Formats `<h2>` as `### ` subheadings, avoids stacked duplicate
           bars when `<h3>` immediately follows `<h2>`, and preserves `<ul>`/
           `<ol>` list items as clean `• ` bullet paragraphs.
       - Hero cover localization to `public/images/ign_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 26 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC, THE DECODER, OpenAI,
  SiliconANGLE, Semafor, CoinDesk, CBS News, iFixit News, 9to5Mac, Tom's
  Hardware, BBC News, New York Post, Tech Funding News).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import urlparse
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


_IGN_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "ign_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

MAX_SLIDESHOW_IMAGES_PER_GALLERY = 4
MAX_TOTAL_INLINE_IMAGES = 10
MAX_INLINE_VIDEO_FETCHES = 2

IGN_SKIP_TRANSFORMS = {
    "mobile-ad-break",
    "ad-break",
    "poll",
    "commerce",
    "commerce-widget",
    "commerce-deal",
    "newsletter",
    "recirc",
    "related-articles",
    "wiki-callout",
    "buy-button",
}

IGN_STOP_TRANSFORMS = {
    "divider",
    "author-sign-off",
}

IGN_SKIP_REGEXES = [
    re.compile(r"^for\s+more\s+(?:on\s+)?.{1,60},\s*(?:make\s+sure\s+to\s+)?check\s+out\s+our\b", re.I),
    re.compile(r"^for\s+more\s+(?:on\s+)?.{1,60},\s*be\s+sure\s+to\s+check\s+out\b", re.I),
    re.compile(r"^read\s+more\s*:", re.I),
    re.compile(r"^sign\s+up\s+for\b", re.I),
    re.compile(r"^subscribe\s+to\b", re.I),
    re.compile(r"^ign\s+recommends\b", re.I),
    re.compile(r"^if\s+you\s+buy\s+something\s+through\s+this\s+post,\s*ign\s+may\s+get\b", re.I),
]

IGN_NOISE_PHRASES = (
    "ign may get a share of the sale",
    "sign up for our newsletter",
    "subscribe to our newsletter",
    "delivered to your inbox",
    "all rights reserved",
    "sponsored content",
    "advertisement",
    "use ign's interactive map",
    "check out our comprehensive wiki",
)

AUDIO_ONLY_IFRAME_DOMAINS = (
    "simplecast.com",
    "open.spotify.com",
    "megaphone.fm",
    "omny.fm",
    "podcasts.apple.com",
    "soundcloud.com",
)

BAD_IMAGE_TOKENS = (
    "/avatars/",
    "ign-logo",
    "site-logo",
    "brand-logo",
    "wordmark",
    "lockup",
    "avatar",
    "gravatar",
    "headshot",
    "/icon",
    "-icon.",
    "_icon.",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "doubleclick",
    "googlesyndication",
    "placeholder",
    "ad-banner",
    "/ads/",
    "1x1",
    "_next/static/media/",
    "bluesky.",
)


def is_ign_url(url: str) -> bool:
    """Returns True if URL belongs to IGN (`ign.com` or `*.ign.com`)."""
    if not url or not isinstance(url, str):
        return False
    try:
        host = (urlparse(url).netloc or "").lower().split(":")[0]
    except Exception:
        return False
    return host == "ign.com" or host.endswith(".ign.com")


def _canonical_ign_key(url: str) -> str:
    return (url or "").split("?")[0].split("#")[0].strip().rstrip("/").lower()


def _get_proxies() -> Optional[Dict[str, str]]:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return None
    for env_key in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        val = os.environ.get(env_key)
        if val:
            return {"http": val, "https": val}
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
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "").replace("\u2060", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?%)\]}])", r"\1", t)
    t = re.sub(r"([(\[{“‘\$£€])\s+", r"\1", t)
    t = re.sub(r"\s+([’'](?:s|t|re|ve|ll|d|m)\b)", r"\1", t, flags=re.I)
    t = re.sub(r"\s+([”’])", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def _clean_ign_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*IGN(?:\s+(?:US|UK|AU|India|Africa|Nordic|Middle East))?\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_ign_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("ign", "ign staff", "ign editorial", "staff", "editors"):
        return ""
    return t


def _format_authors(names: List[str]) -> str:
    cleaned: List[str] = []
    seen = set()
    for n in names:
        c = _clean_ign_author(n)
        if c and c.lower() not in seen:
            seen.add(c.lower())
            cleaned.append(c)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _ign_media_stem(url: str) -> str:
    u = html.unescape((url or "").strip()).split("?")[0].split("#")[0].strip().lower()
    return u


def _is_valid_ign_image(url: str) -> bool:
    u = html.unescape((url or "").strip())
    if u.startswith("//"):
        u = "https:" + u
    if not u or not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if low.startswith("data:"):
        return False
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    clean_path = low.split("?")[0].split("#")[0]
    if clean_path.endswith((".svg", ".ico", ".mp4", ".webm", ".mov", ".m4v", ".m3u8")):
        return False
    return True


def _normalize_ign_img_url(url: str, width: int = 1280) -> str:
    u = html.unescape((url or "").strip())
    if u.startswith("//"):
        u = "https:" + u
    if not u:
        return ""
    if "assets-prd.ignimgs.com/" in u and "?" not in u:
        return f"{u}?width={width}&format=jpg&auto=webp&quality=80"
    return u


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 3 or len(t) > 140:
        return True
    low = t.lower()
    if any(p in low for p in IGN_NOISE_PHRASES):
        return True
    if low in ("related", "recommended", "comments", "subscribe", "share", "sign up", "in this article", "more from ign"):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 12:
        return True
    if any(rx.search(t) for rx in IGN_SKIP_REGEXES):
        return True
    low = t.lower()
    if any(phrase in low for phrase in IGN_NOISE_PHRASES):
        return True
    return False


def _decompress_from_utf16(compressed: str) -> str:
    """Pure-Python LZ-String `decompressFromUTF16` decoder for IGN's Apollo cache."""
    if not compressed or not isinstance(compressed, str):
        return ""
    length = len(compressed)
    reset_value = 16384
    dictionary: Dict[int, str] = {}
    enlarge_in = 4
    dict_size = 4
    num_bits = 3
    result: List[str] = []

    data_val = ord(compressed[0]) - 32
    data_pos = reset_value
    data_idx = 1

    def read_bits(n: int) -> int:
        nonlocal data_val, data_pos, data_idx
        bits = 0
        maxpower = 1 << n
        power = 1
        while power != maxpower:
            resb = data_val & data_pos
            data_pos >>= 1
            if data_pos == 0:
                data_pos = reset_value
                data_val = (ord(compressed[data_idx]) - 32) if data_idx < length else 0
                data_idx += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        return bits

    nxt = read_bits(2)
    if nxt == 0:
        c = chr(read_bits(8))
    elif nxt == 1:
        c = chr(read_bits(16))
    elif nxt == 2:
        return ""
    else:
        return ""

    dictionary[3] = c
    w = c
    result.append(c)

    while True:
        if data_idx > length:
            return ""
        c_code = read_bits(num_bits)
        if c_code == 0:
            dictionary[dict_size] = chr(read_bits(8))
            c_code = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif c_code == 1:
            dictionary[dict_size] = chr(read_bits(16))
            c_code = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif c_code == 2:
            return "".join(result)

        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1

        if c_code in dictionary:
            entry = dictionary[c_code]
        elif c_code == dict_size:
            entry = w + w[0]
        else:
            return ""

        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry

        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1


def _extract_apollo_state(tree) -> Optional[Dict[str, Any]]:
    """Extracts and decompresses IGN's Next.js `apolloState` dictionary."""
    nd = tree.css_first("script#__NEXT_DATA__")
    if not nd:
        return None
    try:
        data = json.loads(nd.text() or "{}")
    except Exception:
        return None
    ap_raw = (data.get("props") or {}).get("apolloState")
    if isinstance(ap_raw, dict):
        return ap_raw
    if isinstance(ap_raw, str) and ap_raw:
        # Handle either plain JSON string or LZ-String UTF16 compressed payload
        if ap_raw.lstrip().startswith("{"):
            try:
                parsed = json.loads(ap_raw)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                pass
        try:
            dec = _decompress_from_utf16(ap_raw)
            if dec:
                parsed = json.loads(dec)
                return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


def _pick_best_mp4_asset(assets: List[Dict[str, Any]]) -> Optional[str]:
    """Selects optimal HD MP4 stream (preferring 720p, then 1080p, then highest available)."""
    mp4s = [
        a for a in (assets or [])
        if isinstance(a, dict)
        and isinstance(a.get("url"), str)
        and a["url"].startswith(("http://", "https://"))
        and ".mp4" in a["url"].lower()
    ]
    if not mp4s:
        return None
    # Prefer 720p for fast web playback, then 1080p, then 540p/480p, then highest
    for target_h in (720, 1080, 540, 480):
        for a in mp4s:
            if a.get("height") == target_h:
                return a["url"]
    mp4s.sort(key=lambda x: int(x.get("height") or 0), reverse=True)
    return mp4s[0]["url"]


def _extract_video_from_apollo(
    apollo: Dict[str, Any],
    content_id: Optional[str] = None,
    slug: Optional[str] = None,
    allow_any: bool = False,
) -> Optional[Dict[str, Any]]:
    """Extracts a ModernVideo entry (direct MP4 + poster + title) from Apollo state."""
    if not isinstance(apollo, dict):
        return None

    target_vid: Optional[Dict[str, Any]] = None
    if content_id:
        key = f'ModernVideo:{{"content":{{"id":"{content_id}"}}}}'
        if isinstance(apollo.get(key), dict):
            target_vid = apollo[key]

    if target_vid is None and slug:
        rq = apollo.get("ROOT_QUERY") or {}
        for rk, rv in rq.items():
            if rk.startswith("videoBySlug(") and f'"{slug}"' in rk and isinstance(rv, dict):
                ref = rv.get("__ref")
                if ref and isinstance(apollo.get(ref), dict):
                    target_vid = apollo[ref]
                    break

    if target_vid is None and allow_any:
        for k, v in apollo.items():
            if k.startswith("ModernVideo:") and isinstance(v, dict) and v.get("assets"):
                target_vid = v
                break

    if not target_vid:
        return None

    mp4_url = _pick_best_mp4_asset(target_vid.get("assets") or [])
    if not mp4_url:
        return None

    mc_ref = (target_vid.get("content") or {}).get("__ref", "")
    mc = apollo.get(mc_ref) if mc_ref else {}
    if not isinstance(mc, dict):
        mc = {}
    v_title = _clean_text(mc.get("title") or "")
    feed_img = mc.get("feedImage") or {}
    poster = ""
    if isinstance(feed_img, dict) and feed_img.get("url"):
        poster = _normalize_ign_img_url(feed_img["url"], width=1280)

    is_short = bool(target_vid.get("isShort"))
    return {
        "url": mp4_url,
        "provider": "mp4",
        "poster": poster,
        "title": v_title or "IGN Video",
        "caption": v_title or "IGN Video",
        "aspect": "9:16" if is_short else "16:9",
    }


def _extract_slideshow_images(apollo: Dict[str, Any], slug: str, max_images: int = MAX_SLIDESHOW_IMAGES_PER_GALLERY) -> List[Dict[str, str]]:
    """Resolves HD images & captions for an inline IGN slideshow from Apollo cache."""
    if not isinstance(apollo, dict) or not slug:
        return []
    rq = apollo.get("ROOT_QUERY") or {}
    target_ss = None
    for rk, rv in rq.items():
        if rk.startswith("slideshow(") and slug in rk and isinstance(rv, dict):
            target_ss = rv
            break
    if not target_ss:
        return []

    ss_title = ""
    c_ref = (target_ss.get("content") or {}).get("__ref", "")
    if c_ref and isinstance(apollo.get(c_ref), dict):
        ss_title = _clean_text(apollo[c_ref].get("title") or "")

    si = target_ss.get("slideshowImages:{}") or target_ss.get("slideshowImages") or {}
    raw_imgs = si.get("images") if isinstance(si, dict) else []
    if not isinstance(raw_imgs, list) or not raw_imgs:
        return []

    total_count = len(raw_imgs)
    out: List[Dict[str, str]] = []
    seen_stems = set()
    for idx, im_ref in enumerate(raw_imgs):
        if len(out) >= max_images:
            break
        im_obj = apollo.get(im_ref.get("__ref", ""), {}) if isinstance(im_ref, dict) else {}
        if not isinstance(im_obj, dict):
            continue
        raw_url = (im_obj.get("url") or "").strip()
        if not _is_valid_ign_image(raw_url):
            continue
        stem = _ign_media_stem(raw_url)
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
        cap = _clean_text(im_obj.get("caption") or "")
        if not cap and ss_title:
            cap = f"{ss_title} ({idx + 1}/{total_count})"
        out.append({
            "url": _normalize_ign_img_url(raw_url, width=1280),
            "alt": cap or ss_title or "IGN Gallery",
            "caption_en": cap,
            "caption": cap,
        })
    return out


def _load_disk_cache() -> None:
    if _IGN_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _IGN_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        tmp_path = _DISK_CACHE_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(_IGN_CACHE, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _DISK_CACHE_FILE)
    except Exception:
        pass


def _fetch_ign_html(url: str, proxies: Optional[Dict[str, str]] = None, timeout: int = 20) -> Tuple[Optional[str], str]:
    """Fetches IGN HTML via curl_cffi (Chrome TLS impersonation) with requests fallback."""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.ign.com/",
    }
    if HAS_CURL_CFFI:
        for profile in ("chrome131", "chrome124"):
            try:
                r = cffi_requests.get(
                    url,
                    impersonate=profile,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout,
                    allow_redirects=True,
                )
                if r.status_code == 200 and len(r.text or "") > 10000:
                    low = (r.text or "")[:1500].lower()
                    if "just a moment" not in low and "cf-turnstile" not in low:
                        return r.text, f"ign_live_{profile}"
            except Exception:
                continue

    if HAS_REQUESTS:
        try:
            r = requests.get(
                url,
                headers={
                    **headers,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                },
                proxies=proxies,
                timeout=timeout,
            )
            if r.status_code == 200 and len(r.text or "") > 10000:
                return r.text, "ign_live_requests"
        except Exception:
            pass

    return None, "failed"


def _resolve_ign_video_by_slug(slug: str, proxies: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Fetches `https://www.ign.com/videos/<slug>` to extract official 720p MP4 + poster."""
    if not slug or not HAS_SELECTOLAX:
        return None
    vid_url = f"https://www.ign.com/videos/{slug.strip('/')}"
    raw_html, _ = _fetch_ign_html(vid_url, proxies=proxies, timeout=15)
    if not raw_html:
        return None
    try:
        vtree = LexborHTMLParser(raw_html)
        vap = _extract_apollo_state(vtree)
        if not vap:
            return None
        return _extract_video_from_apollo(vap, slug=slug, allow_any=True)
    except Exception:
        return None


def _localize_ign_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads IGN cover image locally to `public/images/ign_<hash>.jpg`."""
    if not img_url or not img_url.startswith(("http://", "https://")):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(project_root, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_ign_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"ign_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 4000:
            return public_url

        fetch_url = _normalize_ign_img_url(img_url, width=1280)
        raw_bytes = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(
                    fetch_url,
                    impersonate="chrome131",
                    headers={"Referer": "https://www.ign.com/"},
                    proxies=proxies,
                    timeout=18,
                )
                if r.status_code == 200 and len(r.content) > 4000:
                    ct = (r.headers.get("content-type") or "").lower()
                    if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P", b"RI"):
                        raw_bytes = r.content
            except Exception:
                pass
        if raw_bytes is None and HAS_REQUESTS:
            try:
                r = requests.get(
                    fetch_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        "Referer": "https://www.ign.com/",
                    },
                    proxies=proxies,
                    timeout=18,
                )
                if r.status_code == 200 and len(r.content) > 4000:
                    raw_bytes = r.content
            except Exception:
                pass

        if raw_bytes:
            # Convert WebP/PNG to clean JPEG if Pillow is available and format isn't JPEG
            if raw_bytes[:2] != b"\xff\xd8":
                try:
                    from PIL import Image
                    import io
                    im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=88, optimize=True)
                    raw_bytes = buf.getvalue()
                except Exception:
                    pass
            tmp_path = fpath + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(raw_bytes)
            os.replace(tmp_path, fpath)
            return public_url
    except Exception:
        pass
    return img_url


def _extract_jsonld_meta(tree) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"title": "", "summary": "", "author": "", "published_at": "", "cover_image": ""}
    for script in tree.css('script[type="application/ld+json"]'):
        raw = (script.text() or "").strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        nodes = obj if isinstance(obj, list) else [obj]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            atype = node.get("@type")
            types = atype if isinstance(atype, list) else [atype]
            if not any(t in ("Article", "NewsArticle", "ReportageNewsArticle", "Review", "BlogPosting") for t in types):
                continue
            if not meta["title"] and node.get("headline"):
                meta["title"] = _clean_ign_title(str(node["headline"]))
            if not meta["summary"] and node.get("description"):
                meta["summary"] = _clean_text(str(node["description"]))
            if not meta["published_at"] and node.get("datePublished"):
                meta["published_at"] = str(node["datePublished"]).strip()
            if not meta["author"] and node.get("author"):
                auth = node["author"]
                names: List[str] = []
                if isinstance(auth, dict) and auth.get("name"):
                    names.append(str(auth["name"]))
                elif isinstance(auth, list):
                    for a in auth:
                        if isinstance(a, dict) and a.get("name"):
                            names.append(str(a["name"]))
                        elif isinstance(a, str):
                            names.append(a)
                elif isinstance(auth, str):
                    names.append(auth)
                meta["author"] = _format_authors(names)
            if not meta["cover_image"] and node.get("image"):
                im = node["image"]
                if isinstance(im, str):
                    meta["cover_image"] = im
                elif isinstance(im, dict) and im.get("url"):
                    meta["cover_image"] = str(im["url"])
                elif isinstance(im, list) and im:
                    first = im[0]
                    meta["cover_image"] = str(first.get("url") if isinstance(first, dict) else first)
    return meta


def _extract_youtube_embed(src: str) -> Optional[Tuple[str, str]]:
    s = html.unescape((src or "").strip())
    if not s:
        return None
    m = re.search(r"(?:youtube\.com/embed/|youtube-nocookie\.com/embed/|youtu\.be/|youtube\.com/watch\?v=)([A-Za-z0-9_-]{11})", s)
    if m:
        vid = m.group(1)
        return f"https://www.youtube.com/embed/{vid}", vid
    return None


def _parse_ign_html(
    html_text: str,
    resolve_inline_videos: bool = True,
    proxies: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    if not html_text or not HAS_SELECTOLAX:
        return None

    tree = LexborHTMLParser(html_text)
    apollo = _extract_apollo_state(tree) or {}
    ld_meta = _extract_jsonld_meta(tree)

    title = ""
    summary = ""
    author = ""
    published_at = ""
    cover_image = ""
    processed_html = ""
    hero_video_id = ""
    hero_video_slug = ""

    # 1. Primary metadata from Apollo GraphQL ModernArticle + ModernContent
    main_article = None
    for k, v in apollo.items():
        if k.startswith("ModernArticle:") and isinstance(v, dict) and isinstance(v.get("article"), dict):
            main_article = v
            break

    if main_article:
        art = main_article.get("article") or {}
        processed_html = str(art.get("processedHtml") or "")
        hero_video_id = str(art.get("heroVideoContentId") or "").strip()
        hero_video_slug = str(art.get("heroVideoContentSlug") or "").strip()

        mc_ref = (main_article.get("content") or {}).get("__ref", "")
        mc = apollo.get(mc_ref) if mc_ref else {}
        if isinstance(mc, dict):
            if mc.get("title"):
                title = _clean_ign_title(str(mc["title"]))
            if mc.get("subtitle"):
                summary = _clean_text(str(mc["subtitle"]))
            if mc.get("publishDate"):
                published_at = str(mc["publishDate"]).strip()
            feed_img = mc.get("feedImage")
            if isinstance(feed_img, dict) and feed_img.get("url"):
                cover_image = str(feed_img["url"]).strip()

            contrib_names: List[str] = []
            for cb in (mc.get("contributorsOrBylines") or []):
                if isinstance(cb, dict):
                    ref = cb.get("__ref")
                    if ref and isinstance(apollo.get(ref), dict) and apollo[ref].get("name"):
                        contrib_names.append(str(apollo[ref]["name"]))
                    elif cb.get("name"):
                        contrib_names.append(str(cb["name"]))
            if contrib_names:
                author = _format_authors(contrib_names)

    # 2. Fallbacks from JSON-LD and HTML meta tags
    if not title:
        h1 = tree.css_first("h1")
        title = _clean_ign_title(h1.text() if h1 else "") or ld_meta["title"]
    if not title:
        m_ogt = tree.css_first('meta[property="og:title"]')
        if m_ogt and m_ogt.attributes.get("content"):
            title = _clean_ign_title(m_ogt.attributes["content"])

    if not summary or len(summary) < 60:
        og_desc = ""
        m_ogd = tree.css_first('meta[property="og:description"]') or tree.css_first('meta[name="description"]')
        if m_ogd and m_ogd.attributes.get("content"):
            og_desc = _clean_text(m_ogd.attributes["content"])
        best_desc = og_desc if len(og_desc) >= len(ld_meta["summary"]) else ld_meta["summary"]
        if len(best_desc) > len(summary):
            summary = best_desc

    if not author:
        author = ld_meta["author"]
    if not author:
        dom_names = [n.text() for n in tree.css("[data-cy='byline'] a, .article-byline a[href*='/person/']")]
        author = _format_authors(dom_names)

    if not published_at:
        published_at = ld_meta["published_at"]
    if not published_at:
        m_pub = tree.css_first('meta[property="article:published_time"]')
        if m_pub and m_pub.attributes.get("content"):
            published_at = m_pub.attributes["content"].strip()

    if not cover_image:
        m_ogi = tree.css_first('meta[property="og:image"]')
        if m_ogi and m_ogi.attributes.get("content"):
            cover_image = m_ogi.attributes["content"].strip()
    if not cover_image:
        cover_image = ld_meta["cover_image"]
    if cover_image:
        cover_image = _normalize_ign_img_url(cover_image, width=1280)

    # 3. Single-pass DOM walk over `processedHtml` (fallback: rendered `section.article-page`)
    body_root = None
    if processed_html:
        ptree = LexborHTMLParser(processed_html)
        body_root = ptree.css_first("section.article-page") or ptree.body
    if body_root is None:
        body_root = tree.css_first("section.article-page") or tree.css_first(".article-content")
    if body_root is None:
        return None

    # Remove nested promo/ad containers without ever decomposing body_root itself
    for sel in ("script", "style", "noscript", "aside", "nav", "form", "[data-cy='poll-view-trigger']"):
        for n in body_root.css(sel):
            if n != body_root:
                n.decompose()

    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[Dict[str, Any]] = []
    inline_videos: List[Dict[str, Any]] = []
    seen_img_stems = set()
    if cover_image:
        seen_img_stems.add(_ign_media_stem(cover_image))
    seen_vid_urls = set()
    dom_order = 0
    ign_vid_fetches = 0
    last_was_h2 = False

    # 3a. Hero video at after_para=-1 (renders cleanly at top of Full Coverage)
    if hero_video_id or hero_video_slug:
        hv = _extract_video_from_apollo(apollo, content_id=hero_video_id or None, slug=hero_video_slug or None)
        if hv and hv["url"] not in seen_vid_urls:
            seen_vid_urls.add(hv["url"])
            hv["after_para"] = -1
            hv["dom_order"] = dom_order
            dom_order += 1
            inline_videos.append(hv)

    def _add_inline_img(img_entry: Dict[str, Any], after_para: int) -> None:
        nonlocal dom_order
        if len(inline_images) >= MAX_TOTAL_INLINE_IMAGES:
            return
        u = img_entry.get("url") or ""
        if not _is_valid_ign_image(u):
            return
        stem = _ign_media_stem(u)
        if stem in seen_img_stems:
            return
        seen_img_stems.add(stem)
        entry = dict(img_entry)
        entry["url"] = _normalize_ign_img_url(u, width=1280)
        entry["after_para"] = after_para
        entry["dom_order"] = dom_order
        dom_order += 1
        inline_images.append(entry)

    def _add_inline_vid(vid_entry: Dict[str, Any], after_para: int) -> None:
        nonlocal dom_order
        u = vid_entry.get("url") or ""
        if not u or u in seen_vid_urls:
            return
        seen_vid_urls.add(u)
        entry = dict(vid_entry)
        entry["after_para"] = after_para
        entry["dom_order"] = dom_order
        dom_order += 1
        inline_videos.append(entry)

    for node in body_root.iter(include_text=False):
        tag = (node.tag or "").lower()
        dt = (node.attributes.get("data-transform") or "").lower().strip()
        dcy = (node.attributes.get("data-cy") or "").lower().strip()

        # Hard-stop markers before author sign-off & footer widgets
        if dt in IGN_STOP_TRANSFORMS or dcy in ("accent-divider", "author-sign-off"):
            break

        # Skip ad / poll / commerce / aside widgets
        if tag == "aside" or dt in IGN_SKIP_TRANSFORMS or dcy in ("poll-view-trigger", "aside"):
            continue

        cur_after = len(paragraphs) - 1

        # Inline IGN slideshow gallery
        if dt == "slideshow" or dcy == "article-slideshow":
            ss_slug = (node.attributes.get("data-slug") or node.attributes.get("data-value") or "").strip()
            if ss_slug and apollo:
                for ss_img in _extract_slideshow_images(apollo, ss_slug):
                    _add_inline_img(ss_img, after_para=cur_after)
            last_was_h2 = False
            continue

        # Inline IGN video player
        if dt == "ignvideo" or dcy == "article-video":
            v_slug = (node.attributes.get("data-slug") or node.attributes.get("data-value") or "").strip()
            if v_slug:
                v_obj = _extract_video_from_apollo(apollo, slug=v_slug)
                if v_obj is None and resolve_inline_videos and ign_vid_fetches < MAX_INLINE_VIDEO_FETCHES:
                    ign_vid_fetches += 1
                    v_obj = _resolve_ign_video_by_slug(v_slug, proxies=proxies)
                if v_obj:
                    _add_inline_vid(v_obj, after_para=cur_after)
            last_was_h2 = False
            continue

        # Standard YouTube / iframe embeds inside section/div/figure/iframe
        if tag == "iframe" or dt in ("youtube", "video", "embed"):
            ifr = node if tag == "iframe" else node.css_first("iframe")
            src = (ifr.attributes.get("src") or ifr.attributes.get("data-src") or "") if ifr else (node.attributes.get("data-url") or "")
            low_src = src.lower()
            if src and not any(d in low_src for d in AUDIO_ONLY_IFRAME_DOMAINS):
                yt = _extract_youtube_embed(src)
                if yt:
                    emb_url, vid_id = yt
                    _add_inline_vid({
                        "url": emb_url,
                        "provider": "iframe",
                        "video_id": vid_id,
                        "title": _clean_text(ifr.attributes.get("title") or "YouTube Video") if ifr else "YouTube Video",
                        "caption": _clean_text(ifr.attributes.get("title") or "YouTube Video") if ifr else "YouTube Video",
                        "aspect": "16:9",
                    }, after_para=cur_after)
            last_was_h2 = False
            continue

        # Headings
        if tag in ("h2", "h3", "h4"):
            htext = _clean_text(node.text())
            if htext and not _is_noise_heading(htext):
                if tag == "h2":
                    paragraphs.append(f"### {htext}")
                    subheadings.append(htext)
                    last_was_h2 = True
                elif last_was_h2 and len(htext) <= 80:
                    # Concise sub-label immediately under an h2 (e.g., "Completion Time: 70 hours")
                    paragraphs.append(htext)
                    last_was_h2 = False
                else:
                    paragraphs.append(f"### {htext}")
                    subheadings.append(htext)
                    last_was_h2 = False
            continue

        # Bullet / numbered lists
        if tag in ("ul", "ol"):
            added_li = False
            for li in node.css("li"):
                ltxt = _clean_text(li.text())
                if ltxt and not _is_noise_paragraph(ltxt):
                    paragraphs.append(f"• {ltxt}")
                    added_li = True
            if added_li:
                last_was_h2 = False
            continue

        # Blockquotes
        if tag == "blockquote":
            btxt = _clean_text(node.text())
            if btxt and len(btxt) >= 15 and not _is_noise_paragraph(btxt):
                if not (btxt.startswith(("“", '"')) and btxt.endswith(("”", '"'))):
                    btxt = f"“{btxt}”"
                paragraphs.append(btxt)
                last_was_h2 = False
            continue

        # Paragraphs (may occasionally contain an inline <img>)
        if tag == "p":
            for im in node.css("img"):
                iu = im.attributes.get("src") or im.attributes.get("data-src") or ""
                if _is_valid_ign_image(iu):
                    ialt = _clean_text(im.attributes.get("alt") or "")
                    _add_inline_img({"url": iu, "alt": ialt, "caption_en": ialt, "caption": ialt}, after_para=cur_after)
            ptxt = _clean_text(node.text())
            if ptxt and not _is_noise_paragraph(ptxt):
                paragraphs.append(ptxt)
                last_was_h2 = False
            continue

        # Standard figures / inline images
        if tag in ("figure", "div", "section"):
            # Check for non-slideshow direct images inside figure/section
            if tag == "figure" or dt in ("image", "inline-image"):
                im = node.css_first("img")
                if im:
                    iu = im.attributes.get("src") or im.attributes.get("data-src") or ""
                    if _is_valid_ign_image(iu):
                        fc = node.css_first("figcaption")
                        cap = _clean_text((fc.text() if fc else "") or im.attributes.get("alt") or "")
                        _add_inline_img({"url": iu, "alt": cap, "caption_en": cap, "caption": cap}, after_para=cur_after)
            continue

    # Deduplicate consecutive identical paragraphs
    deduped_paras: List[str] = []
    for p in paragraphs:
        if not deduped_paras or deduped_paras[-1] != p:
            deduped_paras.append(p)

    # Set top-level primary video metadata if we have any inline video
    has_video = bool(inline_videos)
    first_vid = inline_videos[0] if inline_videos else None

    return {
        "title": title,
        "summary": summary,
        "author": author,
        "published_at": published_at,
        "cover_image": cover_image,
        "paragraphs": deduped_paras,
        "subheadings": subheadings,
        "raw_content_text": "\n\n".join(deduped_paras),
        "inline_images": inline_images,
        "inline_videos": inline_videos,
        "has_video": has_video,
        "video_url": first_vid.get("url") if first_vid else None,
        "video_id": first_vid.get("video_id") if first_vid else None,
        "video_provider": first_vid.get("provider") if first_vid else None,
        "video_aspect": first_vid.get("aspect") if first_vid else None,
        "video_poster": first_vid.get("poster") if first_vid else None,
        "video_title": first_vid.get("title") if first_vid else None,
    }


def extract_ign_article(
    url: str,
    title: str = "",
    use_cache: bool = True,
    localize_cover: bool = True,
    html_text: Optional[str] = None,
    resolve_inline_videos: bool = True,
) -> Dict[str, Any]:
    """
    Dedicated IGN article extractor.
    Returns a standardized dict compatible with article_extractor.py / processor.py / main.py.
    """
    result: Dict[str, Any] = {
        "url": url,
        "source": "IGN",
        "title": _clean_ign_title(title) if title else "",
        "summary": "",
        "author": "",
        "published_at": "",
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "inline_videos": [],
        "subheadings": [],
        "paragraphs": [],
        "paras_count": 0,
        "lead_paragraph": "",
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "status": "failed",
        "is_substantive": False,
        "is_paywalled": False,
        "is_filtered_out": False,
        "filter_reason": "",
        "extraction_tier": "none",
    }

    if not is_ign_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_ign_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _IGN_CACHE.get(cache_key)
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

    proxies = _get_proxies() if html_text is None else None
    raw_html = html_text
    tier = "ign_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_ign_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_ign_html(
        raw_html,
        resolve_inline_videos=(resolve_inline_videos and html_text is None),
        proxies=proxies,
    )
    if not parsed:
        return result

    post_flagged, post_reason = detect_low_value_roundup_or_promo(
        title=parsed.get("title") or title,
        url=url,
        body=parsed.get("raw_content_text") or "",
        summary=parsed.get("summary") or "",
    )
    if post_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = post_reason
        if use_cache and html_text is None:
            _load_disk_cache()
            _IGN_CACHE[cache_key] = dict(result)
            _save_disk_cache()
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_ign_image(cover):
        cover = None
    if cover:
        c_stem = _ign_media_stem(cover)
        inlines = [
            e for e in inlines
            if _ign_media_stem(e["url"] if isinstance(e, dict) else str(e)) != c_stem
        ]
        if localize_cover and html_text is None:
            cover = _localize_ign_image(cover, proxies=proxies)

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
    result["inline_videos"] = list(parsed.get("inline_videos") or [])
    if parsed.get("subheadings"):
        result["subheadings"] = parsed["subheadings"]
    if parsed.get("has_video") and parsed.get("video_url"):
        result["has_video"] = True
        result["video_url"] = parsed["video_url"]
        result["video_id"] = parsed.get("video_id")
        result["video_provider"] = parsed.get("video_provider") or "mp4"
        for vk in ("video_aspect", "video_poster", "video_title"):
            if parsed.get(vk):
                result[vk] = parsed[vk]

    result["paragraphs"] = paras
    result["paras_count"] = len(paras)
    result["lead_paragraph"] = paras[0] if paras else ""
    result["full_text"] = full_text
    result["article_content"] = full_text
    result["article_content_en"] = full_text
    result["extraction_tier"] = tier

    if len(paras) >= 2 and len(full_text) >= 400:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _IGN_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result


crawl_ign = extract_ign_article

