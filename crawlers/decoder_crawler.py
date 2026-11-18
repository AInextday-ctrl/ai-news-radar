#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
THE DECODER Dedicated Crawler & Benchmark/Article Penetration Engine
=============================================================================
Source: THE DECODER (the-decoder.com)
Scope: Handles all the-decoder.com article extraction, authentic editorial
       headline resolution (`<h1>` / WP REST), real journalist byline
       extraction (`_embedded.author` / scoped HTML `a[href*="/author/"]`),
       single-pass DOM-order `.entry-content` extraction preserving inline
       `### ` section subheadings and exact `after_para` benchmark chart
       anchors (with cleaned captions), THE DECODER subscription / ad-free /
       newsletter promo stripping, generic social banner (`Banner_The-Decoder`)
       rejection, YouTube/Vimeo video detection, `http://` -> `https://`
       normalization, site-wide editorial purity filtering, and cover photo
       localization to `public/images/decoder_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 14 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC).
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


_DECODER_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "decoder_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

DECODER_NOISE_PHRASES = [
    "subscribe to the decoder",
    "ad-free reading",
    "weekly ai newsletter",
    "support our independent journalism",
    "become a supporter",
    "sign up for our",
    "sign up for the",
    "delivered to your inbox",
    "you can unsubscribe at any time",
    "when you purchase through links",
    "we may earn a small commission",
    "affect our editorial independence",
    "all rights reserved",
    "advertisement",
    "sponsored content",
    "disclosure:",
    "read our review",
    "recommended articles",
]

AUDIO_ONLY_IFRAME_DOMAINS = (
    "simplecast.com",
    "open.spotify.com",
    "megaphone.fm",
    "omny.fm",
    "podcasts.apple.com",
    "soundcloud.com",
    "podigee.io",
)

BAD_IMAGE_TOKENS = (
    "banner_the-decoder",
    "the-decoder_some",
    "avatar",
    "headshot",
    "author",
    "profile",
    "decoder-logo",
    "site-logo",
    "brand-logo",
    "publisher-logo",
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


def is_decoder_url(url: str) -> bool:
    """Returns True if URL belongs to THE DECODER."""
    if not url or not isinstance(url, str):
        return False
    return "the-decoder.com" in url.lower()


def _canonical_decoder_key(url: str) -> str:
    return (url or "").split("?")[0].split("#")[0].strip().rstrip("/").lower()


def _extract_decoder_slug(url: str) -> Optional[str]:
    path = urlparse(url or "").path.strip("/")
    if not path:
        return None
    parts = [p for p in path.split("/") if p]
    return parts[-1] if parts else None


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


def _clean_decoder_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*THE DECODER\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*\(THE DECODER\)\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_decoder_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("the decoder", "the-decoder", "decoder", "staff", "editors"):
        return ""
    return t


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 3 or len(t) > 160:
        return True
    low = t.lower()
    if any(phrase in low for phrase in DECODER_NOISE_PHRASES):
        return True
    if low in ("key points", "summary", "in brief", "tl;dr", "related", "recommended", "comments", "subscribe"):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 22:
        return True
    low = t.lower()
    if any(phrase in low for phrase in DECODER_NOISE_PHRASES):
        return True
    return False


def _upgrade_https(url: str) -> str:
    u = html.unescape((url or "").strip())
    if u.startswith("http://the-decoder.com/"):
        u = "https://" + u[len("http://"):]
    return u


def _decoder_media_stem(url: str) -> str:
    if not url:
        return ""
    base = _upgrade_https(url).split("?")[0].split("#")[0].strip().lower()
    base = re.sub(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    base = re.sub(r"-scaled(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    return base


def _is_valid_decoder_image(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = _upgrade_https(url)
    if not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    clean_path = low.split("?")[0].split("#")[0]
    if clean_path.endswith((".svg", ".ico", ".mp4", ".webm", ".mov", ".m4v", ".m3u8")):
        return False
    return True


def _load_disk_cache() -> None:
    if _DECODER_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _DECODER_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_DECODER_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_decoder_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads THE DECODER hero cover photo to `public/images/decoder_<hash>.jpg`."""
    img_url = _upgrade_https(img_url)
    if not _is_valid_decoder_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_decoder_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"decoder_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://the-decoder.com/",
            "Accept": "image/jpeg,image/png,image/webp,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        if HAS_CURL_CFFI:
            for _ in range(2):
                try:
                    r = cffi_requests.get(img_url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
                    if r.status_code == 200 and len(r.content) > 5000:
                        ct = r.headers.get("content-type", "").lower()
                        if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P") or r.content[:4] == b"RIFF":
                            content = r.content
                            break
                except Exception:
                    pass
        if content is None and HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.content) > 5000:
                    ct = r.headers.get("content-type", "").lower()
                    if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P") or r.content[:4] == b"RIFF":
                        content = r.content
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


def _parse_content_dom(content_html: str, cover_image: Optional[str] = None) -> Tuple[List[str], List[str], List[Any], Dict[str, Any]]:
    """Single-pass DOM-order parser preserving inline `### ` subheadings and exact `after_para` chart anchors."""
    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[Any] = []
    seen_p = set()
    seen_stems = set()
    if cover_image:
        seen_stems.add(_decoder_media_stem(cover_image))

    vmeta = _extract_video_from_html(content_html)
    if not content_html:
        return paragraphs, subheadings, inline_images, vmeta

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(content_html)
        for sel in (
            "script", "style", "noscript", "form", "svg", "aside",
            "[class*='newsletter']", "[class*='subscribe']", "[class*='promo']",
            "[class*='related']", "[class*='advert']", "[class*='sponsor']",
            "[class*='key-points']", "[class*='keypoints']",
            ".screen-reader-text",
        ):
            for n in tree.css(sel):
                n.decompose()

        for node in tree.css("h2, h3, h4, figure, p, blockquote, li"):
            tag = (node.tag or "").lower()
            if tag in ("p", "li", "blockquote"):
                p_anc = node.parent
                in_fig = False
                while p_anc is not None:
                    if (p_anc.tag or "").lower() in ("figure", "figcaption"):
                        in_fig = True
                        break
                    p_anc = p_anc.parent
                if in_fig:
                    continue

            if tag == "figure":
                img_el = node.css_first("img")
                if img_el:
                    src = _upgrade_https(img_el.attributes.get("data-src") or img_el.attributes.get("src") or "")
                    if _is_valid_decoder_image(src):
                        stem = _decoder_media_stem(src)
                        if stem and stem not in seen_stems:
                            seen_stems.add(stem)
                            cap_el = node.css_first("figcaption")
                            cap_txt = _clean_text(cap_el.text(separator=" ") if cap_el else img_el.attributes.get("alt") or "")
                            img_obj: Dict[str, Any] = {
                                "url": src,
                                "after_para": max(0, len(paragraphs) - 1),
                            }
                            if cap_txt and len(cap_txt) >= 5:
                                img_obj["caption"] = cap_txt[:240]
                                img_obj["caption_en"] = cap_txt[:240]
                            inline_images.append(img_obj)
                continue

            txt = _clean_text(node.text(separator=" "))
            if not txt:
                continue
            if tag in ("h2", "h3", "h4"):
                if not _is_noise_heading(txt):
                    subheadings.append(txt)
                    h_key = f"h:{txt.lower()}"
                    if h_key not in seen_p:
                        seen_p.add(h_key)
                        paragraphs.append(f"### {txt}")
                continue
            if tag == "li" and len(txt) < 35:
                continue
            if _is_noise_paragraph(txt):
                continue
            key = txt.lower()[:120]
            if key not in seen_p:
                seen_p.add(key)
                paragraphs.append(txt)

    return paragraphs, subheadings, inline_images[:6], vmeta


def _parse_decoder_wp_post(post: Dict[str, Any]) -> Dict[str, Any]:
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
        out["title"] = _clean_decoder_title(str(raw_title))

    raw_excerpt = (post.get("excerpt") or {}).get("rendered") if isinstance(post.get("excerpt"), dict) else ""
    if raw_excerpt:
        out["summary"] = _clean_text(re.sub(r"<[^>]+>", " ", raw_excerpt))

    emb = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    authors: List[str] = []
    for a in (emb.get("author") or []):
        if isinstance(a, dict) and a.get("name"):
            nm = _clean_decoder_author(str(a["name"]))
            if nm and nm not in authors:
                authors.append(nm)
    if authors:
        out["author"] = " and ".join(authors) if len(authors) <= 2 else ", ".join(authors[:-1]) + f", and {authors[-1]}"

    cand_cover = post.get("jetpack_featured_media_url") or ""
    if not cand_cover and emb.get("wp:featuredmedia"):
        fm = emb["wp:featuredmedia"][0]
        if isinstance(fm, dict):
            cand_cover = fm.get("source_url") or ""
    if cand_cover:
        cand_cover = _upgrade_https(str(cand_cover))
        if _is_valid_decoder_image(cand_cover):
            out["cover_image"] = cand_cover

    content_html = (post.get("content") or {}).get("rendered") if isinstance(post.get("content"), dict) else ""
    out["raw_content_text"] = _clean_text(re.sub(r"<[^>]+>", " ", content_html))
    paras, subs, inls, vmeta = _parse_content_dom(content_html, cover_image=out["cover_image"])
    out["paragraphs"] = paras
    out["subheadings"] = subs
    out["inline_images"] = inls
    if vmeta.get("has_video"):
        out.update(vmeta)

    return out


def _parse_decoder_html(html_text: str) -> Dict[str, Any]:
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
        "class_list": [],
        "raw_content_text": "",
    }
    if not html_text:
        return out

    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t:
        out["title"] = _clean_decoder_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d:
        out["summary"] = _clean_text(m_og_d.group(1))
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i:
        cand = _upgrade_https(m_og_i.group(1))
        if _is_valid_decoder_image(cand):
            out["cover_image"] = cand
    m_pub = re.search(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_pub:
        out["published_at"] = m_pub.group(1).strip()

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        h1 = tree.css_first("h1")
        if h1:
            h1_txt = _clean_decoder_title(h1.text(separator=" "))
            if len(h1_txt) >= 12:
                out["title"] = h1_txt

        # Scoped author from header / first author link
        header = tree.css_first("article header") or tree.css_first("header") or tree.css_first("article")
        if header:
            names = []
            for a in header.css('a[rel="author"], a[href*="/author/"]'):
                nm = _clean_decoder_author(a.text(separator=" "))
                if nm and nm not in names:
                    names.append(nm)
                    break
            if names:
                out["author"] = names[0]

        body = tree.css_first(".entry-content") or tree.css_first(".article-content") or tree.css_first("article")
        if body:
            frag = body.html or ""
            out["raw_content_text"] = _clean_text(body.text(separator=" "))
            paras, subs, inls, vmeta = _parse_content_dom(frag, cover_image=out["cover_image"])
            out["paragraphs"] = paras
            out["subheadings"] = subs
            out["inline_images"] = inls
            if vmeta.get("has_video"):
                out.update(vmeta)

    return out


def _fetch_decoder_wp_post(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
    slug = _extract_decoder_slug(url)
    if not slug:
        return None, "failed"
    api_url = f"https://the-decoder.com/wp-json/wp/v2/posts?slug={quote(slug)}&_embed=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }
    data = None
    if HAS_CURL_CFFI:
        for _ in range(2):
            try:
                r = cffi_requests.get(api_url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    break
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
        return data[0], "decoder_wp_slug"
    return None, "failed"


def _fetch_decoder_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for _ in range(2):
            try:
                r = cffi_requests.get(url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.text) > 10000:
                    return r.text, "decoder_html_cffi"
            except Exception:
                pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "decoder_html_requests"
        except Exception:
            pass
    return None, "failed"


def crawl_decoder(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    wp_post: Optional[Dict[str, Any]] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for THE DECODER (`the-decoder.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "the-decoder.com",
        "source": "THE DECODER",
        "title": _clean_decoder_title(title) if title else "",
        "summary": "",
        "author": "THE DECODER",
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

    if not url or not is_decoder_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_decoder_key(url)
    if use_cache and html_text is None and wp_post is None:
        _load_disk_cache()
        cached = _DECODER_CACHE.get(cache_key)
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

    # 1. WordPress REST API primary
    if wp_post is not None:
        parsed = _parse_decoder_wp_post(wp_post)
        tier = "decoder_injected_wp"
    elif html_text is None:
        post_obj, wp_tier = _fetch_decoder_wp_post(url, proxies=proxies)
        if post_obj:
            parsed = _parse_decoder_wp_post(post_obj)
            tier = wp_tier

    # 2. Editorial purity check
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
                _DECODER_CACHE[cache_key] = dict(result)
                _save_disk_cache()
            return result

    # 3. HTML enrichment / fallback
    need_html = (
        html_text is not None
        or (
            wp_post is None
            and (
                not parsed
                or not parsed.get("cover_image")
                or not parsed.get("author")
                or len("\n\n".join(parsed.get("paragraphs") or [])) < 400
            )
        )
    )
    if need_html:
        raw_html = html_text
        html_tier = "decoder_injected_html"
        if raw_html is None:
            raw_html, html_tier = _fetch_decoder_html(url, proxies=proxies)
        if raw_html:
            hp = _parse_decoder_html(raw_html)
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
                wp_len = len("\n\n".join(parsed.get("paragraphs") or []))
                hp_len = len("\n\n".join(hp.get("paragraphs") or []))
                if wp_len < 400 and hp_len > wp_len:
                    parsed["paragraphs"] = hp["paragraphs"]
                    parsed["subheadings"] = hp.get("subheadings") or parsed.get("subheadings") or []
                    parsed["inline_images"] = hp.get("inline_images") or parsed.get("inline_images") or []
                    tier = f"{tier}+{html_tier}"

    if not parsed:
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_decoder_image(cover):
        cover = None
    if not cover and inlines:
        first_cand = inlines[0]["url"] if isinstance(inlines[0], dict) else str(inlines[0])
        if _is_valid_decoder_image(first_cand):
            cover = first_cand
    if cover:
        cover_stem = _decoder_media_stem(cover)
        inlines = [
            e for e in inlines
            if _decoder_media_stem(e["url"] if isinstance(e, dict) else str(e)) != cover_stem
        ]
        if localize_cover and html_text is None and wp_post is None:
            cover = _localize_decoder_image(cover, proxies=proxies)

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

    if len(paras) >= 2 and len(full_text) >= 400:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None and wp_post is None:
            _load_disk_cache()
            _DECODER_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
