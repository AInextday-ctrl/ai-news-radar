#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
WIRED Dedicated Crawler & Condé Nast Content Penetration Engine
=============================================================================
Source: WIRED (wired.com)
Scope: Handles all wired.com article extraction, authentic editorial headline
       resolution, multi-author attribution, `.body__inner-container` /
       JSON-LD `articleBody` full-text extraction, Condé Nast subscription &
       newsletter noise stripping, 24-hex photo-ID stem deduplication (zero
       cover repeat & zero author avatars), and high-resolution
       `media.wired.com` cover photography localization to
       `public/images/wired_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 9 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import quote
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


_WIRED_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "wired_cache.json"
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

WIRED_NOISE_PHRASES = [
    "subscribe to wired",
    "get unlimited digital access",
    "sign up for our",
    "sign up for the",
    "more great wired stories",
    "this story originally appeared on",
    "already a subscriber",
    "save this story",
    "you can unsubscribe at any time",
    "by signing up you agree to our user agreement",
    "condé nast",
    "conde nast",
    "all rights reserved",
    "subscribe now",
    "wired may earn a portion of sales",
    "if you buy something using links in our stories",
    "delivered to your inbox",
]

AVATAR_BAD_TOKENS = (
    "unsplash.com", "placeholder", "icon", "pixel", "avatar",
    "favicon", "og-default", "1x1", "spacer", "wired-logo",
    "blurple", "author_profile_images", "headshot", "byline",
    "gravatar", "profile_image", "profile-pic", "-portrait-",
    "-mug-", "staff-", "/1:1/", "w_120,", "w_160,", "w_200,",
)


def is_wired_url(url: str) -> bool:
    """Checks whether the given URL belongs to WIRED."""
    if not url:
        return False
    return "wired.com/" in url.lower()


def _canonical_wired_key(url: str) -> str:
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


def _is_valid_wired_image(img_url: Optional[str]) -> bool:
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


def _wired_media_stem(img_url: Optional[str]) -> str:
    """Extracts Condé Nast 24-hex photo ID from `media.wired.com/photos/<id>/...`."""
    if not img_url:
        return ""
    m = re.search(r'/photos/([0-9a-f]{24})/', img_url.lower())
    if m:
        return m.group(1)
    return img_url.split("?")[0].lower()


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


def _clean_wired_title(raw_title: str) -> str:
    if not raw_title:
        return ""
    t = _clean_text(raw_title)
    t = re.sub(r'\s*[|—–-]\s*WIRED\s*$', '', t, flags=re.I).strip()
    return t


def _is_wired_noise(text: str) -> bool:
    if not text:
        return True
    t = text.strip()
    if len(t) < 20:
        return True
    low = t.lower()
    for phrase in WIRED_NOISE_PHRASES:
        if phrase in low:
            return True
    if re.match(r'^(?:Photograph|Illustration|Photo|Courtesy|Image)\s*:', t, re.I) and len(t) < 140:
        return True
    return False


def _load_disk_cache() -> None:
    global _WIRED_CACHE
    if _WIRED_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _WIRED_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_WIRED_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_wired_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads `media.wired.com` hero cover photo to `public/images/wired_<hash>.jpg`."""
    if not _is_valid_wired_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_wired_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"wired_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.wired.com/",
            "Accept": "image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        if HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.content) > 5000:
                    ct = r.headers.get("content-type", "").lower()
                    if "image/" in ct or r.content[:2] in (b'\xff\xd8', b'\x89P'):
                        content = r.content
            except Exception:
                pass
        if content is None and HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(img_url, impersonate="safari17_2_ios", headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.content) > 5000:
                    content = r.content
            except Exception:
                pass
        if content:
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
                except Exception:
                    pass
            with open(fpath, "wb") as f:
                f.write(content)
            return public_url
    except Exception:
        pass
    return img_url


def _parse_wired_html(html_text: str) -> Dict[str, Any]:
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

    # 1. JSON-LD NewsArticle metadata + articleBody backup
    ld_body = ""
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            obj = json.loads(m_ld.group(1).strip())
            if isinstance(obj, list):
                obj = next((x for x in obj if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if not isinstance(obj, dict) or "Article" not in str(obj.get("@type", "")):
                continue
            if obj.get("headline") and not out["title"]:
                out["title"] = _clean_wired_title(obj["headline"])
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
                if _is_valid_wired_image(cand):
                    out["cover_image"] = html.unescape(cand.strip())
            if obj.get("articleBody") and len(str(obj["articleBody"])) > len(ld_body):
                ld_body = str(obj["articleBody"])
        except Exception:
            continue

    # 2. og:image (prefer landscape 191:100 w_1280 og:image over portrait/square)
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i:
        cand = html.unescape(m_og_i.group(1).strip())
        if _is_valid_wired_image(cand):
            out["cover_image"] = cand
    if not out["title"]:
        m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_og_t:
            out["title"] = _clean_wired_title(m_og_t.group(1))

    cover_stem = _wired_media_stem(out["cover_image"])
    seen_stems = {cover_stem} if cover_stem else set()

    # 3. DOM extraction from `.body__inner-container` / `[data-testid="BodyWrapper"]`
    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        if not out["title"]:
            h1 = tree.css_first('h1[data-testid="ContentHeaderHed"]') or tree.css_first("h1")
            if h1:
                out["title"] = _clean_wired_title(h1.text(strip=True))
        containers = tree.css('.body__inner-container')
        if not containers:
            bw = tree.css_first('[data-testid="BodyWrapper"]') or tree.css_first("article")
            containers = [bw] if bw else []

        for body in containers:
            for el in body.css("h2, h3, p, blockquote"):
                tag = (el.tag or "").lower()
                parent = el.parent
                if parent and (parent.tag or "").lower() == "figcaption":
                    continue
                txt = _clean_text(el.html or "")
                if not txt or _is_wired_noise(txt):
                    continue
                if tag in ("h2", "h3") and len(txt) < 180:
                    if txt not in out["subheadings"]:
                        out["subheadings"].append(txt)
                elif tag == "blockquote":
                    q = f'“{txt}”' if not txt.startswith(('"', '“')) else txt
                    if q not in out["paragraphs"]:
                        out["paragraphs"].append(q)
                elif tag == "p":
                    if txt not in out["paragraphs"]:
                        out["paragraphs"].append(txt)

            for fg in body.css("figure"):
                im = fg.css_first("img")
                if not im:
                    continue
                src = html.unescape(str(im.attributes.get("src") or im.attributes.get("data-src") or "").strip())
                if not _is_valid_wired_image(src):
                    continue
                stem = _wired_media_stem(src)
                if stem and stem in seen_stems:
                    continue
                if stem:
                    seen_stems.add(stem)
                cap_el = fg.css_first("figcaption")
                cap = _clean_text(cap_el.html or "") if cap_el else _clean_text(im.attributes.get("alt") or "")
                out["inline_images"].append({"url": src, "caption": cap, "alt": cap or out["title"]})

    # 4. JSON-LD articleBody backup if DOM extraction was sparse
    if len(out["paragraphs"]) < 3 and len(ld_body) > 300:
        chunks = [c.strip() for c in re.split(r'\n{2,}|\r\n\r\n', ld_body) if c.strip()]
        if len(chunks) <= 2:
            chunks = [c.strip() for c in ld_body.splitlines() if c.strip()]
        cleaned = []
        for ch in chunks:
            t = _clean_text(ch)
            if t and not _is_wired_noise(t) and t not in cleaned:
                cleaned.append(t)
        if len(cleaned) > len(out["paragraphs"]):
            out["paragraphs"] = cleaned

    return out


def _fetch_wired_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for imp in ("safari17_2_ios", "safari17_0", "chrome124"):
            try:
                r = cffi_requests.get(url, impersonate=imp, headers=headers, proxies=proxies, timeout=18, allow_redirects=True)
                if r.status_code == 200 and len(r.text) > 15000:
                    return r.text, f"wired_direct_{imp}"
            except Exception:
                continue

    if HAS_REQUESTS:
        clean_u = url.split("?")[0]
        try:
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={quote(clean_u, safe='')}&output=json&limit=3&filter=statuscode:200&collapse=digest"
            cr = requests.get(cdx_url, proxies=proxies, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if cr.status_code == 200:
                rows = cr.json()
                if isinstance(rows, list) and len(rows) > 1:
                    ts, orig = rows[-1][1], rows[-1][2]
                    wr = requests.get(f"https://web.archive.org/web/{ts}id_/{orig}", proxies=proxies, timeout=18, headers={"User-Agent": "Mozilla/5.0"})
                    if wr.status_code == 200 and len(wr.text) > 15000:
                        return wr.text, "wired_wayback"
        except Exception:
            pass
    return None, "failed"


def crawl_wired(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for WIRED (`wired.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "wired.com",
        "source": "WIRED",
        "title": _clean_wired_title(title) if title else "",
        "summary": "",
        "author": "WIRED",
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

    if not url or not is_wired_url(url):
        return result

    cache_key = _canonical_wired_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _WIRED_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if html_text is None else None
    tier = "wired_injected_html"
    raw_html = html_text
    if raw_html is None:
        raw_html, tier = _fetch_wired_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_wired_html(raw_html)
    cover = parsed.get("cover_image")
    if cover and localize_cover and html_text is None:
        cover = _localize_wired_image(cover, proxies=proxies)

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
    result["extraction_tier"] = tier

    if len(paras) >= 3 and len(full_text) >= 400:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _WIRED_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
