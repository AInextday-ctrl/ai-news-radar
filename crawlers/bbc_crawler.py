#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BBC News Dedicated Crawler (`bbc.com` / `bbc.co.uk`)
=============================================================================
Source: BBC News (`www.bbc.com` / `www.bbc.co.uk`)
Scope: Handles all BBC News technology, business, and global reports:
       - Authentic headline resolution (JSON-LD `ReportageNewsArticle` /
         `NewsArticle` headline / `<h1>`), real journalist bylines from JSON-LD
         `author`, and exact ISO `datePublished`.
       - Dedicated BBC `[data-component]` block-ordered `<article>` extraction:
         * Walks `text-block`, `subheadline-block` (`### `), `image-block`,
           `unordered-list-block`, `ordered-list-block`, and `media-block` in
           exact DOM order.
         * Strictly hard-stops at `links-block` and `tag-list-block` so BBC's
           trailing `Tech Decoded` newsletter banner images and signup copy
           never leak into the article.
         * Filters out BBC `grey-placeholder.png` lazy placeholders and
           promotional banners (`promotional banner` alt text), picks HD
           `srcset` renditions from `ichef.bbci.co.uk`, and deduplicates
           `inline_images` against `cover_image` by BBC asset UUID across
           `branded_news` vs `cpsprodpb` and `.jpg` vs `.jpg.webp`.
         * Strips BBC newsletter / podcast / `Get in touch` / `Sign up for`
           housekeeping prompts.
       - Hero cover localization to `public/images/bbc_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 23 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC, THE DECODER, OpenAI,
  SiliconANGLE, Semafor, CoinDesk, CBS News, iFixit News, 9to5Mac, Tom's Hardware).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
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


_BBC_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "bbc_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)

BBC_STOP_COMPONENTS = {
    "links-block",
    "tag-list-block",
    "related-internet-links",
    "topic-list",
    "recommendations",
}

BBC_SKIP_REGEXES = [
    re.compile(r"^sign\s+up\s+for\s+our\b", re.I),
    re.compile(r"^subscribe\s+to\s+(?:our|the\s+bbc)\b", re.I),
    re.compile(r"^get\s+in\s+touch\b", re.I),
    re.compile(r"^listen\s+to\s+the\s+best\s+of\s+bbc\b", re.I),
    re.compile(r"^follow\s+bbc\b", re.I),
    re.compile(r"^watch\s*:\s*", re.I),
    re.compile(r"^additional\s+reporting\s+by\b", re.I),
]

BBC_NOISE_PHRASES = (
    "sign up for our tech decoded newsletter",
    "sign up for our",
    "follow the world's top tech stories",
    "outside the uk? sign up here",
    "download the bbc news app",
    "delivered to your inbox",
    "you can unsubscribe at any time",
    "all rights reserved",
    "sponsored content",
    "advertisement",
    "bbc is not responsible for the content of external sites",
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
    "grey-placeholder",
    "gray-placeholder",
    "placeholder",
    "bbc-logo",
    "bbc_news_logo",
    "site-logo",
    "brand-logo",
    "wordmark",
    "lockup",
    "avatar",
    "gravatar",
    "/icon",
    "-icon.",
    "_icon.",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "doubleclick",
    "googlesyndication",
    "ad-banner",
    "/ads/",
    "1x1",
)

BAD_IMAGE_ALT_PHRASES = (
    "promotional banner",
    "tech decoded newsletter",
    "bbc news newsletter",
    "sign up for",
)


def is_bbc_url(url: str) -> bool:
    """Returns True if URL belongs to BBC (`bbc.com` or `bbc.co.uk`)."""
    if not url or not isinstance(url, str):
        return False
    low = url.lower()
    return "bbc.com/" in low or "bbc.co.uk/" in low


def _canonical_bbc_key(url: str) -> str:
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
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?%)\]}])", r"\1", t)
    t = re.sub(r"([(\[{“‘\$£€])\s+", r"\1", t)
    t = re.sub(r"\s+([’'](?:s|t|re|ve|ll|d|m)\b)", r"\1", t, flags=re.I)
    t = re.sub(r"\s+([”’])", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def _clean_bbc_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*BBC(?:\s+News)?\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_bbc_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("bbc", "bbc news", "bbc staff", "staff", "editors"):
        return ""
    return t


def _bbc_media_key(url: str) -> str:
    """Stable deduplication key using BBC asset UUID across branded_news/cpsprodpb & jpg/webp."""
    u = html.unescape((url or "").strip())
    if not u:
        return ""
    m = UUID_RE.search(u)
    if m:
        return f"uuid:{m.group(0).lower()}"
    return u.split("?")[0].split("#")[0].strip().lower()


def _is_valid_bbc_image(url: str, alt: str = "") -> bool:
    u = html.unescape((url or "").strip())
    if u.startswith("//"):
        u = "https:" + u
    if not u or not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    low_alt = (alt or "").lower()
    if any(ph in low_alt for ph in BAD_IMAGE_ALT_PHRASES):
        return False
    clean_path = low.split("?")[0].split("#")[0]
    if clean_path.endswith((".svg", ".ico", ".mp4", ".webm", ".mov", ".m4v", ".m3u8")):
        return False
    return True


def _pick_best_srcset_url(srcset: str, fallback: str, alt: str = "") -> str:
    best_url = html.unescape((fallback or "").strip())
    if best_url.startswith("//"):
        best_url = "https:" + best_url
    best_w = 0
    if srcset:
        for part in srcset.split(","):
            toks = part.strip().split()
            if not toks:
                continue
            cand = html.unescape(toks[0].strip())
            if cand.startswith("//"):
                cand = "https:" + cand
            if not _is_valid_bbc_image(cand, alt=alt):
                continue
            w = 0
            if len(toks) > 1:
                m = re.match(r"(\d+)w", toks[1], re.I)
                if m:
                    w = int(m.group(1))
            if w > best_w and w <= 1600:
                best_w = w
                best_url = cand
    return best_url


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 3 or len(t) > 140:
        return True
    low = t.lower()
    if any(p in low for p in BBC_NOISE_PHRASES):
        return True
    if low in ("related", "related topics", "more on this story", "top stories", "features", "elsewhere on the bbc"):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 20:
        return True
    if any(rx.search(t) for rx in BBC_SKIP_REGEXES):
        return True
    low = t.lower()
    if any(phrase in low for phrase in BBC_NOISE_PHRASES):
        return True
    return False


def _load_disk_cache() -> None:
    if _BBC_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _BBC_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        tmp = _DISK_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_BBC_CACHE, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _DISK_CACHE_FILE)
    except Exception:
        pass


def _localize_bbc_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads BBC News cover image to `public/images/bbc_<hash>.jpg`."""
    img_url = html.unescape((img_url or "").strip())
    if not _is_valid_bbc_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_bbc_media_key(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"bbc_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.bbc.com/",
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


def _parse_bbc_html(html_text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "",
        "published_at": None,
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
        "inline_images": [],
        "inline_videos": [],
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

    # 1. JSON-LD ReportageNewsArticle / NewsArticle metadata
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.S | re.I):
        try:
            ld = json.loads(m_ld.group(1).strip())
            objs = ld if isinstance(ld, list) else [ld]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                t = obj.get("@type")
                is_art = (isinstance(t, str) and "Article" in t) or (
                    isinstance(t, list) and any("Article" in str(x) for x in t)
                )
                if not is_art:
                    continue
                if obj.get("headline") and not out["title"]:
                    out["title"] = _clean_bbc_title(str(obj["headline"]))
                desc = obj.get("description") or obj.get("abstract")
                if desc and not out["summary"]:
                    out["summary"] = _clean_text(str(desc))
                if obj.get("datePublished") and not out["published_at"]:
                    out["published_at"] = str(obj["datePublished"]).strip()
                raw_auth = obj.get("author")
                names: List[str] = []
                if isinstance(raw_auth, list):
                    for a in raw_auth:
                        nm = _clean_bbc_author(a.get("name") if isinstance(a, dict) else str(a))
                        if nm and nm not in names:
                            names.append(nm)
                elif isinstance(raw_auth, dict):
                    nm = _clean_bbc_author(raw_auth.get("name") or "")
                    if nm:
                        names.append(nm)
                elif isinstance(raw_auth, str):
                    nm = _clean_bbc_author(raw_auth)
                    if nm:
                        names.append(nm)
                if names and not out["author"]:
                    out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"
                img_ld = obj.get("image") or obj.get("thumbnailUrl")
                if isinstance(img_ld, list) and img_ld:
                    img_ld = img_ld[0]
                if isinstance(img_ld, dict):
                    img_ld = img_ld.get("url")
                if isinstance(img_ld, str) and _is_valid_bbc_image(img_ld) and not out["cover_image"]:
                    out["cover_image"] = html.unescape(img_ld.strip())
        except Exception:
            pass

    # OG / meta fallbacks
    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t and not out["title"]:
        out["title"] = _clean_bbc_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d and not out["summary"]:
        out["summary"] = _clean_text(m_og_d.group(1))
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i and not out["cover_image"]:
        u = html.unescape(m_og_i.group(1).strip())
        if _is_valid_bbc_image(u):
            out["cover_image"] = u

    if not (HAS_SELECTOLAX and LexborHTMLParser is not None):
        return out

    tree = LexborHTMLParser(html_text)
    if not out["title"]:
        h1 = tree.css_first("h1")
        if h1:
            t = _clean_bbc_title(h1.text(separator=" "))
            if len(t) >= 8:
                out["title"] = t

    art = tree.css_first("article") or tree.css_first("main")
    if not art:
        return out

    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[Dict[str, Any]] = []
    inline_videos: List[Dict[str, Any]] = []
    seen_p = set()
    seen_keys = set()
    seen_vids = set()
    dom_seq = 0
    if out["cover_image"]:
        seen_keys.add(_bbc_media_key(out["cover_image"]))

    def _record_video(v_url: str, provider: str, vid_id: Optional[str] = None, v_title: str = "", aspect: str = "16x9", poster: str = "") -> None:
        nonlocal dom_seq
        u = html.unescape((v_url or "").strip())
        if not u.startswith(("http://", "https://")):
            return
        low = u.lower()
        if any(aud in low for aud in AUDIO_ONLY_IFRAME_DOMAINS):
            return
        dk = (provider, vid_id or u.split("?")[0].lower())
        if dk in seen_vids:
            return
        seen_vids.add(dk)
        dom_seq += 1
        obj: Dict[str, Any] = {
            "url": u,
            "provider": provider,
            "after_para": max(-1, len(paragraphs) - 1),
            "aspect": aspect or "16x9",
            "dom_order": dom_seq,
        }
        if vid_id:
            obj["video_id"] = vid_id
        ct = _clean_text(v_title)
        if ct:
            obj["title"] = ct[:200]
            obj["caption"] = ct[:240]
        if poster and _is_valid_bbc_image(poster):
            obj["poster"] = poster
        inline_videos.append(obj)

    blocks = art.css("[data-component]")
    if blocks:
        for blk in blocks:
            dc = (blk.attributes.get("data-component") or "").strip().lower()
            # Hard-stop at related links / tag lists so trailing newsletter banners never leak
            if dc in BBC_STOP_COMPONENTS:
                break
            if dc in ("headline-block", "byline-block", "timestamp-block", "ad-slot", "advertisement"):
                continue

            if dc == "subheadline-block":
                h_txt = _clean_text(blk.text(separator=" "))
                if h_txt and not _is_noise_heading(h_txt):
                    subheadings.append(h_txt)
                    hk = f"h:{h_txt.lower()}"
                    if hk not in seen_p:
                        seen_p.add(hk)
                        paragraphs.append(f"### {h_txt}")
                continue

            if dc == "image-block":
                cap_el = blk.css_first("figcaption")
                cap_txt = _clean_text(cap_el.text(separator=" ") if cap_el else "")
                for im in blk.css("img"):
                    alt_txt = _clean_text(im.attributes.get("alt") or "")
                    raw_src = im.attributes.get("data-src") or im.attributes.get("src") or ""
                    src = _pick_best_srcset_url(im.attributes.get("srcset") or "", raw_src, alt=alt_txt)
                    if not _is_valid_bbc_image(src, alt=alt_txt):
                        continue
                    mk = _bbc_media_key(src)
                    if not mk or mk in seen_keys:
                        continue
                    seen_keys.add(mk)
                    dom_seq += 1
                    final_cap = cap_txt or alt_txt
                    im_obj: Dict[str, Any] = {
                        "url": src,
                        "after_para": max(-1, len(paragraphs) - 1),
                        "dom_order": dom_seq,
                    }
                    if final_cap and len(final_cap) >= 5:
                        im_obj["caption"] = final_cap[:240]
                        im_obj["caption_en"] = final_cap[:240]
                    inline_images.append(im_obj)
                    break
                continue

            if dc in ("text-block", "unordered-list-block", "ordered-list-block", "quote-block"):
                for el in blk.css("p, li, blockquote"):
                    if (el.tag or "").lower() == "p" and el.parent and (el.parent.tag or "").lower() == "blockquote":
                        continue
                    txt = _clean_text(el.text(separator=" "))
                    if not txt or _is_noise_paragraph(txt):
                        continue
                    if (el.tag or "").lower() == "li":
                        txt = f"• {txt}"
                    k = txt.lower()[:120]
                    if k not in seen_p:
                        seen_p.add(k)
                        paragraphs.append(txt)
                continue

            if "video" in dc or "media" in dc:
                for ifr in blk.css("iframe"):
                    src = html.unescape((ifr.attributes.get("src") or ifr.attributes.get("data-src") or "").strip())
                    low = src.lower()
                    v_title = (ifr.attributes.get("title") or "").strip()
                    if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
                        m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
                        _record_video(src, "iframe", vid_id=(m_yt.group(1) if m_yt else None), v_title=v_title)
                    elif "player.vimeo.com/video/" in low:
                        m_vm = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
                        _record_video(src, "iframe", vid_id=(m_vm.group(1) if m_vm else None), v_title=v_title)
    else:
        # Generic fallback if a legacy BBC page lacks data-component attributes
        for node in art.css("h2, h3, p"):
            tag = (node.tag or "").lower()
            txt = _clean_text(node.text(separator=" "))
            if not txt:
                continue
            if tag in ("h2", "h3"):
                if not _is_noise_heading(txt):
                    subheadings.append(txt)
                    paragraphs.append(f"### {txt}")
            elif not _is_noise_paragraph(txt):
                k = txt.lower()[:120]
                if k not in seen_p:
                    seen_p.add(k)
                    paragraphs.append(txt)

    out["paragraphs"] = paragraphs
    out["subheadings"] = subheadings
    out["inline_images"] = inline_images[:20]
    out["inline_videos"] = inline_videos[:8]
    out["raw_content_text"] = "\n\n".join(paragraphs)

    if inline_videos:
        fv = inline_videos[0]
        out["has_video"] = True
        out["video_url"] = fv["url"]
        out["video_id"] = fv.get("video_id")
        out["video_provider"] = fv.get("provider") or "iframe"
        out["video_aspect"] = fv.get("aspect") or "16x9"
        out["video_poster"] = fv.get("poster")
        out["video_title"] = fv.get("title") or fv.get("caption") or ""

    return out


def _fetch_bbc_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    }
    if HAS_CURL_CFFI:
        for imp in ("chrome124", "safari17_2_ios"):
            try:
                r = cffi_requests.get(url, impersonate=imp, headers=headers, proxies=proxies, timeout=18)
                if r.status_code == 200 and len(r.text) > 10000:
                    return r.text, f"bbc_html_{imp}"
            except Exception:
                pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=18)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "bbc_html_requests"
        except Exception:
            pass
    return None, "failed"


def crawl_bbc(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for BBC News (`bbc.com` / `bbc.co.uk`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "bbc.com",
        "source": "BBC News",
        "title": _clean_bbc_title(title) if title else "",
        "summary": "",
        "author": "BBC News",
        "published_at": None,
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "inline_videos": [],
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

    if not url or not is_bbc_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_bbc_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _BBC_CACHE.get(cache_key)
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
    tier = "bbc_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_bbc_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_bbc_html(raw_html)
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
            _BBC_CACHE[cache_key] = dict(result)
            _save_disk_cache()
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_bbc_image(cover):
        cover = None
    if cover:
        c_key = _bbc_media_key(cover)
        inlines = [
            e for e in inlines
            if _bbc_media_key(e["url"] if isinstance(e, dict) else str(e)) != c_key
        ]
        if localize_cover and html_text is None:
            cover = _localize_bbc_image(cover, proxies=proxies)

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
        result["video_provider"] = parsed.get("video_provider") or "iframe"
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
            _BBC_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
