#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CNBC Dedicated Crawler & Broadcast Video + ArticleBody Penetration Engine
=============================================================================
Source: CNBC (cnbc.com)
Scope: Handles all cnbc.com article extraction, authentic editorial headline
       resolution (`<h1>` / JSON-LD `headline`, replacing Techmeme summary
       headlines), multi-author journalist byline extraction (JSON-LD `author`
       + scoped `.Author-authorName`), `.ArticleBody-articleBody` full-text
       extraction in exact DOM order with inline `### ` subheadings and
       `after_para` figure anchors, CNBC PRO / Investing Club / Related Quotes
       / "Read more CNBC" promo stripping, direct ad-free Akamai HD MP4 video
       extraction from JSON-LD `NewsArticle.video` (`VideoObject`), CNBC
       asset-ID (`/api/v1/image/<id>`) image deduplication, site-wide editorial
       purity filtering, and cover localization to `public/images/cnbc_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 13 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import quote
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


_CNBC_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "cnbc_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

CNBC_NOISE_PHRASES = [
    "subscribe to cnbc pro",
    "cnbc investing club",
    "don't miss these insights from cnbc pro",
    "don’t miss these insights from cnbc pro",
    "read more cnbc",
    "sign up for our",
    "sign up for the",
    "delivered to your inbox",
    "you can unsubscribe at any time",
    "watch the full interview",
    "watch live on cnbc",
    "when you purchase through links",
    "we may earn a small commission",
    "affect our editorial independence",
    "all rights reserved",
    "advertisement",
    "sponsored content",
    "get this delivered to your inbox",
    "make it newsletter",
    "cnbc select",
    "disclosure:",
]

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


def is_cnbc_url(url: str) -> bool:
    """Returns True if URL belongs to CNBC."""
    if not url or not isinstance(url, str):
        return False
    return "cnbc.com" in url.lower()


def _canonical_cnbc_key(url: str) -> str:
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


def _clean_cnbc_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*CNBC\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*\(CNBC\)\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_cnbc_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("cnbc", "cnbc.com", "cnbc staff", "staff", "editors"):
        return ""
    return t


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 3 or len(t) > 140:
        return True
    low = t.lower()
    if any(phrase in low for phrase in CNBC_NOISE_PHRASES):
        return True
    if low.startswith(("read more", "watch:", "watch ", "more from", "related", "key points")):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 22:
        return True
    low = t.lower()
    if any(phrase in low for phrase in CNBC_NOISE_PHRASES):
        return True
    if re.match(r"^(watch:|read more:|related:|correction:)\s*", low) and len(t) < 160:
        return True
    return False


def _cnbc_media_stem(url: str) -> str:
    """
    Canonicalizes CNBC image URLs via numeric asset ID (`/api/v1/image/<id>`)
    so different crops/sizes of the same Getty/CNBC photo deduplicate cleanly.
    """
    if not url:
        return ""
    m_id = re.search(r"/api/v1/image/(\d{7,12})", url)
    if m_id:
        return f"cnbc_asset_{m_id.group(1)}"
    return url.split("?")[0].split("#")[0].strip().lower()


def _is_valid_cnbc_image(url: str) -> bool:
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


def _upgrade_cnbc_image_url(url: str) -> str:
    if not url:
        return ""
    u = html.unescape(url.strip())
    if "image.cnbcfm.com/api/v1/image/" in u.lower():
        base = u.split("?")[0]
        return f"{base}?w=1440&q=85"
    return u


def _load_disk_cache() -> None:
    if _CNBC_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _CNBC_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_CNBC_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_cnbc_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads CNBC hero cover photo to `public/images/cnbc_<hash>.jpg`."""
    if not _is_valid_cnbc_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        hi_u = _upgrade_cnbc_image_url(img_url)
        h = hashlib.md5(_cnbc_media_stem(hi_u).encode("utf-8")).hexdigest()[:16]
        fname = f"cnbc_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.cnbc.com/",
            "Accept": "image/jpeg,image/png,image/webp,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        for cand_u in (hi_u, img_url):
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


def _parse_cnbc_html(html_text: str) -> Dict[str, Any]:
    """
    Parses CNBC HTML page:
    - Extracts JSON-LD `NewsArticle` headline, multi-author byline, cover image,
      and official Akamai HD MP4 `video` (`VideoObject.contentUrl`).
    - Extracts `.ArticleBody-articleBody` paragraphs, inline `### ` subheadings,
      and anchored `after_para` editorial figures while stripping CNBC promo/quote widgets.
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
        "raw_content_text": "",
    }
    if not html_text:
        return out

    # 1. JSON-LD NewsArticle (headline, multi-author, high-res image, direct HD MP4 VideoObject)
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            obj = json.loads(m_ld.group(1).strip())
            if isinstance(obj, list):
                obj = next((x for x in obj if isinstance(x, dict) and "Article" in str(x.get("@type", ""))), None)
            if not isinstance(obj, dict) or "Article" not in str(obj.get("@type", "")):
                continue
            if obj.get("headline") and not out["title"]:
                out["title"] = _clean_cnbc_title(obj["headline"])
            if obj.get("description") and not out["summary"]:
                out["summary"] = _clean_text(obj["description"])
            if obj.get("datePublished") and not out["published_at"]:
                out["published_at"] = obj["datePublished"]
            auth = obj.get("author")
            if auth and not out["author"]:
                names: List[str] = []
                if isinstance(auth, list):
                    for a in auth:
                        nm = _clean_cnbc_author(a.get("name") if isinstance(a, dict) else str(a))
                        if nm and nm not in names:
                            names.append(nm)
                elif isinstance(auth, dict) and auth.get("name"):
                    nm = _clean_cnbc_author(str(auth["name"]))
                    if nm:
                        names.append(nm)
                elif isinstance(auth, str):
                    nm = _clean_cnbc_author(auth)
                    if nm:
                        names.append(nm)
                if names:
                    out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"
            img = obj.get("image")
            if img and not out["cover_image"]:
                # Prefer landscape 16:9 image over 1:1 square if image is a list of ImageObjects
                cand = ""
                if isinstance(img, list) and img:
                    landscape = next((x for x in img if isinstance(x, dict) and int(x.get("width") or 0) > int(x.get("height") or 0)), None)
                    picked = landscape or img[0]
                    cand = picked.get("url") if isinstance(picked, dict) else str(picked)
                elif isinstance(img, dict):
                    cand = img.get("url") or ""
                else:
                    cand = str(img)
                if _is_valid_cnbc_image(cand):
                    out["cover_image"] = html.unescape(cand.strip())
            # Official CNBC TV Broadcast HD MP4 (`VideoObject`)
            vid = obj.get("video")
            if isinstance(vid, list) and vid:
                vid = vid[0]
            if isinstance(vid, dict) and not out["video_url"]:
                v_mp4 = str(vid.get("contentUrl") or "").strip()
                if v_mp4.startswith("http") and ".mp4" in v_mp4.lower():
                    out["has_video"] = True
                    out["video_url"] = html.unescape(v_mp4)
                    out["video_provider"] = "mp4"
                    out["video_aspect"] = "16x9"
                    m_vid_id = re.search(r"/(\d{8,12})/", v_mp4)
                    if m_vid_id:
                        out["video_id"] = m_vid_id.group(1)
                    if vid.get("name"):
                        out["video_title"] = _clean_text(str(vid["name"]))
                    t_url = vid.get("thumbnailUrl")
                    if isinstance(t_url, list) and t_url:
                        t_url = t_url[0]
                    if isinstance(t_url, str) and t_url.startswith("http"):
                        out["video_poster"] = html.unescape(t_url.strip())
        except Exception:
            continue

    # 2. og:image / og:title / og:description fallbacks
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i and not out["cover_image"]:
        cand = html.unescape(m_og_i.group(1).strip())
        if _is_valid_cnbc_image(cand):
            out["cover_image"] = cand
    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t and not out["title"]:
        out["title"] = _clean_cnbc_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d and not out["summary"]:
        out["summary"] = _clean_text(m_og_d.group(1))

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        h1 = tree.css_first("h1.ArticleHeader-headline") or tree.css_first("h1")
        if h1:
            h1_txt = _clean_cnbc_title(h1.text(separator=" "))
            if len(h1_txt) >= 12:
                out["title"] = h1_txt

        if not out["author"]:
            names = []
            for a in tree.css(".Author-authorName, [class*='Author-authorName']"):
                nm = _clean_cnbc_author(a.text(separator=" "))
                if nm and nm not in names:
                    names.append(nm)
            if names:
                out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"

        body = tree.css_first(".ArticleBody-articleBody") or tree.css_first("article")
        if body:
            # Strip CNBC promo, quote ticker, adhesion ad, inline video thumbnail, and related-stories widgets
            for sel in (
                "script", "style", "noscript", "form", "svg", "aside",
                "[class*='RelatedQuotes']", "[class*='RelatedContent']",
                "[class*='MobileAdhesion']", "[class*='googlePreferredSource']",
                "[class*='InlinePromo']", "[class*='InlineVideo']",
                "[class*='MakeItPromo']", "[class*='Wildcard']",
                "[class*='Newsletter']", "[class*='WatchLive']",
                "[class*='HighlightShare']", ".screen-reader-text",
            ):
                for n in body.css(sel):
                    n.decompose()

            out["raw_content_text"] = _clean_text(body.text(separator=" "))
            seen_p = set()
            seen_stems = set()
            if out["cover_image"]:
                seen_stems.add(_cnbc_media_stem(out["cover_image"]))
            if out["video_poster"]:
                seen_stems.add(_cnbc_media_stem(out["video_poster"]))

            for node in body.css("h2, h3, h4, figure, p, blockquote, li"):
                tag = (node.tag or "").lower()
                if tag in ("p", "li", "blockquote"):
                    p_anc = node.parent
                    in_fig = False
                    while p_anc is not None:
                        ptag = (p_anc.tag or "").lower()
                        if ptag in ("figure", "figcaption"):
                            in_fig = True
                            break
                        if "ArticleBody-articleBody" in (p_anc.attributes.get("class") or ""):
                            break
                        p_anc = p_anc.parent
                    if in_fig:
                        continue

                if tag == "figure":
                    img_el = node.css_first("img")
                    if img_el:
                        src = html.unescape((img_el.attributes.get("data-src") or img_el.attributes.get("src") or "").strip())
                        if _is_valid_cnbc_image(src):
                            stem = _cnbc_media_stem(src)
                            if stem and stem not in seen_stems:
                                seen_stems.add(stem)
                                cap_el = node.css_first("figcaption")
                                cap_txt = _clean_text(cap_el.text(separator=" ") if cap_el else img_el.attributes.get("alt") or "")
                                img_obj: Dict[str, Any] = {
                                    "url": _upgrade_cnbc_image_url(src),
                                    "after_para": max(0, len(out["paragraphs"]) - 1),
                                }
                                if cap_txt and len(cap_txt) >= 6 and cap_txt.lower() != out["title"].lower():
                                    img_obj["caption"] = cap_txt[:220]
                                    img_obj["caption_en"] = cap_txt[:220]
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

            out["inline_images"] = out["inline_images"][:6]

    return out


def _fetch_cnbc_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        try:
            r = cffi_requests.get(url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "cnbc_html_cffi"
        except Exception:
            pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "cnbc_html_requests"
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
                        return wr.text, "cnbc_wayback"
        except Exception:
            pass
    return None, "failed"


def crawl_cnbc(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for CNBC (`cnbc.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "cnbc.com",
        "source": "CNBC",
        "title": _clean_cnbc_title(title) if title else "",
        "summary": "",
        "author": "CNBC",
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

    if not url or not is_cnbc_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_cnbc_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _CNBC_CACHE.get(cache_key)
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
    tier = "cnbc_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_cnbc_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_cnbc_html(raw_html)

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
            _CNBC_CACHE[cache_key] = dict(result)
            _save_disk_cache()
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover:
        cover_stem = _cnbc_media_stem(cover)
        inlines = [
            e for e in inlines
            if _cnbc_media_stem(e["url"] if isinstance(e, dict) else str(e)) != cover_stem
        ]
        if localize_cover and html_text is None:
            cover = _localize_cnbc_image(cover, proxies=proxies)

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
        result["video_provider"] = parsed.get("video_provider") or "mp4"
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

    if len(paras) >= 3 and len(full_text) >= 400:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _CNBC_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
