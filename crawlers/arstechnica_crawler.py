#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Ars Technica Dedicated Crawler & Multi-Block Content Penetration Engine
=============================================================================
Source: Ars Technica (arstechnica.com)
Scope: Handles all arstechnica.com article extraction, authentic editorial
       headline resolution (`<h1>` / JSON-LD `headline`, replacing Techmeme
       summary headlines), real journalist byline extraction (JSON-LD `author`
       + scoped `a[rel="author"]`), multi-block `.post-content` aggregation
       across mid-article ad splits (plus multi-page `/2/` pagination support),
       Ars / Condé Nast subscription & affiliate noise stripping, WP-size-
       suffix-aware cover & inline image deduplication (preserving authentic
       editorial figures/screenshots with cleaned captions), YouTube/Vimeo/CNE
       video detection, site-wide editorial purity filtering, and cover photo
       localization to `public/images/ars_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 12 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import quote, urljoin
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


_ARS_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "arstechnica_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

ARS_NOISE_PHRASES = [
    "join the ars orbital transmission",
    "subscribe to ars technica",
    "sign up for our",
    "sign up for the",
    "delivered to your inbox",
    "you can unsubscribe at any time",
    "condé nast",
    "conde nast",
    "all rights reserved",
    "ars technica may earn compensation",
    "when you purchase through links",
    "we may earn a small commission",
    "affect our editorial independence",
    "reader comments",
    "view comments",
    "promote comments",
    "advertisement",
    "sponsored content",
    "listing image by",
    "further reading",
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
)

BAD_IMAGE_TOKENS = (
    "avatar",
    "headshot",
    "author",
    "profile",
    "logo",
    "wordmark",
    "lockup",
    "icon",
    "badge",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "doubleclick",
    "googlesyndication",
    "taboola",
    "outbrain",
    "unsplash.com",
    "placeholder",
    "newsletter",
    "ad-banner",
    "/ads/",
    "1x1",
)


def is_arstechnica_url(url: str) -> bool:
    """Returns True if URL belongs to Ars Technica."""
    if not url or not isinstance(url, str):
        return False
    return "arstechnica.com" in url.lower()


def _canonical_ars_key(url: str) -> str:
    return (url or "").split("?")[0].split("#")[0].strip().rstrip("/").lower()


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
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([(“\"])\s+", r"\1", t)
    t = re.sub(r"\s+([)”])", r"\1", t)
    return t.strip()


def _clean_ars_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*Ars Technica\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*\(Ars Technica\)\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_ars_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("ars technica", "ars staff", "staff", "editors"):
        return ""
    return t


def _clean_ars_caption(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^enlarge\s*/\s*", "", t, flags=re.I).strip()
    t = re.sub(r"\s*\|\s*enlarge\s*$", "", t, flags=re.I).strip()
    if t.lower().startswith("listing image by") or len(t) < 4:
        return ""
    return t[:220]


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 3 or len(t) > 140:
        return True
    low = t.lower()
    if any(phrase in low for phrase in ARS_NOISE_PHRASES):
        return True
    if low in ("related", "further reading", "comments", "reader comments", "more stories", "advertisement"):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 22:
        return True
    low = t.lower()
    if any(phrase in low for phrase in ARS_NOISE_PHRASES):
        return True
    if re.match(r"^(enlarge\s*/|further reading|related|read more|image credit)\b", low) and len(t) < 140:
        return True
    return False


def _ars_media_stem(url: str) -> str:
    """Canonicalizes cdn.arstechnica.net WordPress image URLs (strips `?resize=...` and `-1152x648`)."""
    if not url:
        return ""
    base = url.split("?")[0].split("#")[0].strip().lower()
    base = re.sub(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    base = re.sub(r"-scaled(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    return base


def _is_valid_ars_image(url: str) -> bool:
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


def _clean_ars_image_url(url: str) -> str:
    if not url:
        return ""
    u = html.unescape(url.strip())
    if "cdn.arstechnica.net/wp-content/uploads/" in u.lower():
        return u.split("?")[0]
    return u


def _load_disk_cache() -> None:
    if _ARS_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _ARS_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_ARS_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_ars_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads Ars Technica hero cover photo to `public/images/ars_<hash>.jpg`."""
    if not _is_valid_ars_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        clean_u = _clean_ars_image_url(img_url)
        h = hashlib.md5(_ars_media_stem(clean_u).encode("utf-8")).hexdigest()[:16]
        fname = f"ars_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://arstechnica.com/",
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


def _extract_video_from_html(fragment: str) -> Dict[str, Any]:
    """Extracts genuine embedded YouTube/Vimeo/MP4 videos while ignoring ads and audio podcasts."""
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

    m_mp4 = re.search(r'<source[^>]+src=["\']([^"\']+\.(?:mp4|webm)(?:\?[^"\']*)?)["\']', fragment, re.I)
    if not m_mp4:
        m_mp4 = re.search(r'<video[^>]+src=["\']([^"\']+\.(?:mp4|webm)(?:\?[^"\']*)?)["\']', fragment, re.I)
    if m_mp4:
        out["has_video"] = True
        out["video_url"] = html.unescape(m_mp4.group(1).strip())
        out["video_provider"] = "mp4"
        return out

    for m_ifr in re.finditer(r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]*>', fragment, re.I):
        src = html.unescape(m_ifr.group(1).strip())
        low = src.lower()
        if any(aud in low for aud in AUDIO_ONLY_IFRAME_DOMAINS):
            continue
        if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
            m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
            out["has_video"] = True
            out["video_url"] = src
            out["video_id"] = m_yt.group(1) if m_yt else None
            out["video_provider"] = "iframe"
            out["video_aspect"] = "16x9"
            return out
        if "player.vimeo.com/video/" in low:
            m_vid = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
            out["has_video"] = True
            out["video_url"] = src
            out["video_id"] = m_vid.group(1) if m_vid else None
            out["video_provider"] = "iframe"
            out["video_aspect"] = "16x9"
            return out

    return out


def _parse_ars_html(html_text: str) -> Dict[str, Any]:
    """
    Parses Ars Technica HTML page:
    - Extracts JSON-LD NewsArticle headline, author(s), datePublished, image.
    - Aggregates ALL `.post-content` blocks across mid-article ad splits.
    - Strips ad slots, related-story boxes, and newsletter/comment widgets.
    - Deduplicates inline images against cover stem & cleans `Enlarge /` captions.
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
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
        "next_pages": [],
        "raw_content_text": "",
    }
    if not html_text:
        return out

    # 1. JSON-LD NewsArticle metadata
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            obj = json.loads(m_ld.group(1).strip())
            if isinstance(obj, list):
                obj = next((x for x in obj if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if isinstance(obj, dict) and "@graph" in obj and isinstance(obj["@graph"], list):
                obj = next((x for x in obj["@graph"] if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if not isinstance(obj, dict) or "Article" not in str(obj.get("@type", "")):
                continue
            if obj.get("headline") and not out["title"]:
                out["title"] = _clean_ars_title(obj["headline"])
            if obj.get("description") and not out["summary"]:
                out["summary"] = _clean_text(obj["description"])
            if obj.get("datePublished") and not out["published_at"]:
                out["published_at"] = obj["datePublished"]
            auth = obj.get("author")
            if auth and not out["author"]:
                names: List[str] = []
                if isinstance(auth, list):
                    for a in auth:
                        nm = _clean_ars_author(a.get("name") if isinstance(a, dict) else str(a))
                        if nm and nm not in names:
                            names.append(nm)
                elif isinstance(auth, dict) and auth.get("name"):
                    nm = _clean_ars_author(str(auth["name"]))
                    if nm:
                        names.append(nm)
                elif isinstance(auth, str):
                    nm = _clean_ars_author(auth)
                    if nm:
                        names.append(nm)
                if names:
                    out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"
            img = obj.get("image")
            if img and not out["cover_image"]:
                if isinstance(img, list) and img:
                    cand = img[0].get("url") if isinstance(img[0], dict) else str(img[0])
                elif isinstance(img, dict):
                    cand = img.get("url")
                else:
                    cand = str(img)
                cand = _clean_ars_image_url(cand)
                if _is_valid_ars_image(cand):
                    out["cover_image"] = cand
        except Exception:
            continue

    # 2. og:image / og:title / og:description
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i and not out["cover_image"]:
        cand = _clean_ars_image_url(m_og_i.group(1))
        if _is_valid_ars_image(cand):
            out["cover_image"] = cand
    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t and not out["title"]:
        out["title"] = _clean_ars_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d and not out["summary"]:
        out["summary"] = _clean_text(m_og_d.group(1))

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        # Prefer authentic <h1> headline over og:title when present
        h1 = tree.css_first("h1")
        if h1:
            h1_txt = _clean_ars_title(h1.text(separator=" "))
            if len(h1_txt) >= 12:
                out["title"] = h1_txt

        # Scoped author fallback
        if not out["author"]:
            byline_box = tree.css_first('[class*="byline"]') or tree.css_first("header")
            if byline_box:
                names = []
                for a in byline_box.css('a[rel="author"], a[href*="/author/"]'):
                    nm = _clean_ars_author(a.text(separator=" "))
                    if nm and nm not in names:
                        names.append(nm)
                if names:
                    out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"

        # Multi-block `.post-content` extraction (spans all ad-split sections cleanly!)
        blocks = tree.css(".post-content")
        if not blocks:
            fallback_node = tree.css_first(".article-content") or tree.css_first("article")
            blocks = [fallback_node] if fallback_node else []

        seen_p = set()
        seen_stems = set()
        if out["cover_image"]:
            seen_stems.add(_ars_media_stem(out["cover_image"]))

        raw_frags: List[str] = []
        for blk in blocks:
            # Strip non-editorial widgets inside each block
            for sel in (
                "script", "style", "noscript", "form", "svg", "aside",
                "[class*='ad-']", "[class*='advert']", "[class*='newsletter']",
                "[class*='promo']", "[class*='related']", "[class*='sidebar']",
                "[class*='story-sidebar']", "[class*='comments']", ".screen-reader-text",
            ):
                for n in blk.css(sel):
                    n.decompose()

            blk_html = blk.html or ""
            raw_frags.append(blk_html)

            # Single-pass DOM-order traversal preserves exact positions of subheadings (`### `) and figure anchors (`after_para`)
            for node in blk.css("h2, h3, h4, figure, p, blockquote, li"):
                tag = (node.tag or "").lower()
                # Skip <p>/<li> nested inside <figure> or <figcaption> (already handled by <figure>)
                if tag in ("p", "li", "blockquote"):
                    p_anc = node.parent
                    in_fig = False
                    while p_anc is not None:
                        ptag = (p_anc.tag or "").lower()
                        if ptag in ("figure", "figcaption"):
                            in_fig = True
                            break
                        if ptag == "div" and "post-content" in (p_anc.attributes.get("class") or ""):
                            break
                        p_anc = p_anc.parent
                    if in_fig:
                        continue

                if tag == "figure":
                    img_el = node.css_first("img")
                    if img_el:
                        src = _clean_ars_image_url(img_el.attributes.get("data-src") or img_el.attributes.get("src") or "")
                        if _is_valid_ars_image(src):
                            stem = _ars_media_stem(src)
                            if stem and stem not in seen_stems:
                                seen_stems.add(stem)
                                cap_el = node.css_first("figcaption")
                                cap_txt = _clean_ars_caption(cap_el.text(separator=" ") if cap_el else img_el.attributes.get("alt") or "")
                                after_idx = max(0, len(out["paragraphs"]) - 1)
                                img_obj: Dict[str, Any] = {"url": src, "after_para": after_idx}
                                if cap_txt:
                                    img_obj["caption"] = cap_txt
                                    img_obj["caption_en"] = cap_txt
                                out["inline_images"].append(img_obj)
                    continue

                txt = _clean_text(node.text(separator=" "))
                if not txt:
                    continue
                if tag in ("h2", "h3", "h4"):
                    if not _is_noise_heading(txt):
                        out["subheadings"].append(txt)
                        h_key = f"h:{txt.lower()}"
                        if h_key not in seen_p:
                            seen_p.add(h_key)
                            out["paragraphs"].append(f"### {txt}")
                    continue
                if tag == "li" and len(txt) < 35:
                    continue
                if _is_noise_paragraph(txt):
                    continue
                key = txt.lower()[:120]
                if key not in seen_p:
                    seen_p.add(key)
                    out["paragraphs"].append(txt)

            # Fallback for standalone inline <img> outside <figure>
            for img_el in blk.css("img"):
                p_anc = img_el.parent
                in_fig = False
                while p_anc is not None:
                    if (p_anc.tag or "").lower() == "figure":
                        in_fig = True
                        break
                    p_anc = p_anc.parent
                if in_fig:
                    continue
                src = _clean_ars_image_url(img_el.attributes.get("data-src") or img_el.attributes.get("src") or "")
                if _is_valid_ars_image(src):
                    stem = _ars_media_stem(src)
                    if stem and stem not in seen_stems:
                        seen_stems.add(stem)
                        out["inline_images"].append({"url": src, "after_para": max(0, len(out["paragraphs"]) - 1)})

        joined_frags = "\n".join(raw_frags)
        out["raw_content_text"] = _clean_text(re.sub(r"<[^>]+>", " ", joined_frags))
        out["inline_images"] = out["inline_images"][:6]
        vmeta = _extract_video_from_html(joined_frags)
        if vmeta.get("has_video"):
            out.update(vmeta)

        # Detect multi-page pagination links (`/2/`, `/3/`)
        for a in tree.css('nav[aria-label*="page"] a, .page-numbers a, a[rel="next"]'):
            href = (a.attributes.get("href") or "").strip()
            if re.search(r"/[2-5]/?$", href) and href not in out["next_pages"]:
                out["next_pages"].append(href)

    return out


def _fetch_ars_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        try:
            r = cffi_requests.get(url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "ars_html_cffi"
        except Exception:
            pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "ars_html_requests"
        except Exception:
            pass
        try:
            cdx = f"https://web.archive.org/cdx/search/cdx?url={quote(url, safe='')}&output=json&filter=statuscode:200&limit=1"
            cr = requests.get(cdx, proxies=proxies, timeout=12)
            if cr.status_code == 200:
                rows = cr.json()
                if isinstance(rows, list) and len(rows) > 1:
                    ts, orig = rows[-1][1], rows[-1][2]
                    wr = requests.get(f"https://web.archive.org/web/{ts}id_/{orig}", proxies=proxies, timeout=18, headers={"User-Agent": "Mozilla/5.0"})
                    if wr.status_code == 200 and len(wr.text) > 10000:
                        return wr.text, "ars_wayback"
        except Exception:
            pass
    return None, "failed"


def crawl_arstechnica(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for Ars Technica (`arstechnica.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "arstechnica.com",
        "source": "Ars Technica",
        "title": _clean_ars_title(title) if title else "",
        "summary": "",
        "author": "Ars Technica",
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

    if not url or not is_arstechnica_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_ars_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _ARS_CACHE.get(cache_key)
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
    tier = "ars_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_ars_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_ars_html(raw_html)

    # Multi-page article aggregation (e.g. `/2/`, `/3/` on long Ars deep dives)
    if html_text is None and parsed.get("next_pages"):
        seen_p = {p.lower()[:120] for p in parsed["paragraphs"]}
        for rel_u in parsed["next_pages"][:2]:
            abs_u = urljoin(url, rel_u)
            if abs_u.rstrip("/") == url.rstrip("/"):
                continue
            p_html, _ = _fetch_ars_html(abs_u, proxies=proxies)
            if p_html:
                p2 = _parse_ars_html(p_html)
                for para in p2.get("paragraphs") or []:
                    k = para.lower()[:120]
                    if k not in seen_p:
                        seen_p.add(k)
                        parsed["paragraphs"].append(para)

    post_flagged, post_reason = detect_low_value_roundup_or_promo(
        title=parsed.get("title") or title,
        url=url,
        body=parsed.get("raw_content_text") or "\n\n".join(parsed.get("paragraphs") or []),
        summary=parsed.get("summary") or "",
    )
    if post_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = post_reason
        if use_cache and html_text is None:
            _load_disk_cache()
            _ARS_CACHE[cache_key] = dict(result)
            _save_disk_cache()
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover:
        cover_stem = _ars_media_stem(cover)
        cleaned_inls = []
        for entry in inlines:
            eu = entry["url"] if isinstance(entry, dict) else str(entry)
            if _ars_media_stem(eu) != cover_stem:
                cleaned_inls.append(entry)
        inlines = cleaned_inls
        if localize_cover and html_text is None:
            cover = _localize_ars_image(cover, proxies=proxies)

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
            _ARS_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
