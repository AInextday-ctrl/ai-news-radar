#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
iFixit News Dedicated Crawler (`ifixit.com`)
=============================================================================
Source: iFixit News (`www.ifixit.com/News/...`)
Scope: Handles all ifixit.com hardware teardown reports and repairability analyses:
       - Authentic headline resolution (JSON-LD `NewsArticle.headline` / `<h1>`),
         real author/co-author extraction from JSON-LD `author` and byline
         `/User/` links, and exact ISO `datePublished`.
       - Dedicated WordPress `.entry-content` single-pass DOM extraction:
         * Strictly decomposes all `.ifixit-promo-wrap` store/tool/T-shirt
           promotional cards before parsing.
         * Handles both standalone `figure.wp-block-image` and nested
           `figure.wp-block-gallery` image sets in exact `(after_para, dom_order)`
           sequence, preferring HD `srcset` renditions and preserving both
           per-image and gallery captions.
         * Normalizes WordPress size suffixes (`-1200x800`, `-600x400`) when
           deduplicating `inline_images` against `cover_image`.
         * Extracts inline YouTube (`youtube-nocookie.com/embed/...`), Vimeo,
           and direct `.mp4` teardown videos into `inline_videos` at exact DOM
           positions while safely ignoring non-video WebGL embeds (e.g. Lumafield).
         * Preserves all `### ` section subheadings and clean full-text paragraphs.
       - Hero cover localization to `public/images/ifixit_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 20 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC, THE DECODER, OpenAI,
  SiliconANGLE, Semafor, CoinDesk, CBS News).
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


_IFIXIT_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "ifixit_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

WP_SIZE_SUFFIX_RE = re.compile(r"-\d{2,4}x\d{2,4}(?=\.[a-z0-9]+$)", re.I)

IFIXIT_NOISE_PHRASES = (
    "sign up for our newsletter",
    "subscribe to our newsletter",
    "delivered to your inbox",
    "you can unsubscribe at any time",
    "legalize repair t-shirt",
    "never have insufficient tools again",
    "all rights reserved",
    "sponsored content",
    "advertisement",
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
    "ifixit-logo",
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
    "placeholder",
    "ad-banner",
    "/ads/",
    "1x1",
)


def is_ifixit_url(url: str) -> bool:
    """Returns True if URL belongs to iFixit (`ifixit.com`)."""
    if not url or not isinstance(url, str):
        return False
    return "ifixit.com" in url.lower()


def _canonical_ifixit_key(url: str) -> str:
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
    t = re.sub(r"([(\[{“‘\$])\s+", r"\1", t)
    t = re.sub(r"\s+([’'](?:s|t|re|ve|ll|d|m)\b)", r"\1", t, flags=re.I)
    t = re.sub(r"\s+([”’])", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def _clean_ifixit_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*iFixit(?:\s+News)?\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_ifixit_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^(?:article\s+)?by\s*:?\s*", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("ifixit", "ifixit news", "ifixit staff", "staff", "editors"):
        return ""
    return t


def _ifixit_media_stem(url: str) -> str:
    """Normalizes WordPress resize suffixes (-1200x800, -600x400) for clean deduplication."""
    u = html.unescape((url or "").strip()).split("?")[0].split("#")[0].strip().lower()
    if not u:
        return ""
    return WP_SIZE_SUFFIX_RE.sub("", u)


def _is_valid_ifixit_image(url: str) -> bool:
    u = html.unescape((url or "").strip())
    if u.startswith("//"):
        u = "https:" + u
    if not u or not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    clean_path = low.split("?")[0].split("#")[0]
    if clean_path.endswith((".svg", ".ico", ".mp4", ".webm", ".mov", ".m4v", ".m3u8")):
        return False
    return True


def _pick_best_srcset_url(srcset: str, fallback: str) -> str:
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
            if not _is_valid_ifixit_image(cand):
                continue
            w = 0
            if len(toks) > 1:
                m = re.match(r"(\d+)w", toks[1], re.I)
                if m:
                    w = int(m.group(1))
            if w > best_w and w <= 1800:
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
    if any(p in low for p in IFIXIT_NOISE_PHRASES):
        return True
    if low in ("related", "recommended", "comments", "subscribe", "share", "sign up", "related stories"):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 20:
        return True
    low = t.lower()
    if any(phrase in low for phrase in IFIXIT_NOISE_PHRASES):
        return True
    return False


def _load_disk_cache() -> None:
    if _IFIXIT_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _IFIXIT_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        tmp = _DISK_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_IFIXIT_CACHE, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _DISK_CACHE_FILE)
    except Exception:
        pass


def _localize_ifixit_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads iFixit cover image to `public/images/ifixit_<hash>.jpg`."""
    img_url = html.unescape((img_url or "").strip())
    if not _is_valid_ifixit_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_ifixit_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"ifixit_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.ifixit.com/",
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


def _parse_ifixit_html(html_text: str) -> Dict[str, Any]:
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

    # 1. JSON-LD NewsArticle / BlogPosting metadata
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.S | re.I):
        try:
            ld = json.loads(m_ld.group(1).strip())
            if isinstance(ld, dict) and "@graph" in ld and isinstance(ld["@graph"], list):
                objs = ld["@graph"]
            elif isinstance(ld, list):
                objs = ld
            else:
                objs = [ld]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                t = obj.get("@type")
                is_art = (t in ("NewsArticle", "Article", "BlogPosting")) or (
                    isinstance(t, list) and any(x in ("NewsArticle", "Article", "BlogPosting") for x in t)
                )
                if not is_art:
                    continue
                if obj.get("headline") and not out["title"]:
                    out["title"] = _clean_ifixit_title(str(obj["headline"]))
                desc = obj.get("description") or obj.get("abstract")
                if desc and not out["summary"]:
                    out["summary"] = _clean_text(str(desc))
                if obj.get("datePublished") and not out["published_at"]:
                    out["published_at"] = str(obj["datePublished"]).strip()
                raw_auth = obj.get("author")
                names: List[str] = []
                if isinstance(raw_auth, list):
                    for a in raw_auth:
                        nm = _clean_ifixit_author(a.get("name") if isinstance(a, dict) else str(a))
                        if nm and nm not in names:
                            names.append(nm)
                elif isinstance(raw_auth, dict):
                    nm = _clean_ifixit_author(raw_auth.get("name") or "")
                    if nm:
                        names.append(nm)
                elif isinstance(raw_auth, str):
                    nm = _clean_ifixit_author(raw_auth)
                    if nm:
                        names.append(nm)
                if names and not out["author"]:
                    out["author"] = " and ".join(names) if len(names) <= 2 else ", ".join(names[:-1]) + f", and {names[-1]}"
                img_ld = obj.get("image") or obj.get("thumbnailUrl")
                if isinstance(img_ld, list) and img_ld:
                    img_ld = img_ld[0]
                if isinstance(img_ld, dict):
                    img_ld = img_ld.get("url")
                if isinstance(img_ld, str) and _is_valid_ifixit_image(img_ld) and not out["cover_image"]:
                    out["cover_image"] = html.unescape(img_ld.strip())
        except Exception:
            pass

    # OG / meta fallbacks
    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t and not out["title"]:
        out["title"] = _clean_ifixit_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d and not out["summary"]:
        out["summary"] = _clean_text(m_og_d.group(1))
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i and not out["cover_image"]:
        u = html.unescape(m_og_i.group(1).strip())
        if _is_valid_ifixit_image(u):
            out["cover_image"] = u
    m_pub = re.search(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_pub and not out["published_at"]:
        out["published_at"] = m_pub.group(1).strip()

    if not (HAS_SELECTOLAX and LexborHTMLParser is not None):
        return out

    tree = LexborHTMLParser(html_text)
    if not out["title"]:
        h1 = tree.css_first("h1")
        if h1:
            t = _clean_ifixit_title(h1.text(separator=" "))
            if len(t) >= 8:
                out["title"] = t

    # Extract full co-author list from DOM byline if richer than single JSON-LD author
    byline_names: List[str] = []
    for a_el in tree.css("header a[href*='/User/'], .author-byline a[href*='/User/'], [class*='author'] a[href*='/User/']"):
        nm = _clean_ifixit_author(a_el.text(separator=" "))
        if nm and 3 <= len(nm) <= 50 and "@" not in nm and nm not in byline_names:
            byline_names.append(nm)
    if len(byline_names) >= 2:
        out["author"] = " and ".join(byline_names) if len(byline_names) == 2 else ", ".join(byline_names[:-1]) + f", and {byline_names[-1]}"
    elif len(byline_names) == 1 and not out["author"]:
        out["author"] = byline_names[0]

    body = tree.css_first(".entry-content") or tree.css_first("article") or tree.css_first("main")
    if not body:
        return out

    # Strictly strip iFixit Store / product promo cards and non-editorial chrome
    for sel in (
        "script", "style", "noscript", "nav", "footer", "aside", "form", "svg",
        ".ifixit-promo-wrap", "[class*='promo-wrap']", "[class*='product-card']",
        "[class*='newsletter']", "[class*='subscribe']", "[class*='signup']",
        "[class*='related']", "[class*='advert']", "[class*='share']",
        ".sr-only", ".screen-reader-text",
    ):
        for n in body.css(sel):
            if n != body:
                n.decompose()

    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[Dict[str, Any]] = []
    inline_videos: List[Dict[str, Any]] = []
    seen_p = set()
    seen_stems = set()
    seen_vids = set()
    dom_seq = 0
    if out["cover_image"]:
        seen_stems.add(_ifixit_media_stem(out["cover_image"]))

    def _record_image(img_el, cap_txt: str = "") -> None:
        nonlocal dom_seq
        if img_el is None:
            return
        raw_src = img_el.attributes.get("data-src") or img_el.attributes.get("src") or ""
        src = _pick_best_srcset_url(img_el.attributes.get("srcset") or "", raw_src)
        if not _is_valid_ifixit_image(src):
            return
        stem = _ifixit_media_stem(src)
        if not stem or stem in seen_stems:
            return
        seen_stems.add(stem)
        dom_seq += 1
        alt_txt = _clean_text(img_el.attributes.get("alt") or "")
        final_cap = _clean_text(cap_txt) or alt_txt
        im_obj: Dict[str, Any] = {
            "url": src,
            "after_para": max(-1, len(paragraphs) - 1),
            "dom_order": dom_seq,
        }
        if final_cap and len(final_cap) >= 5:
            im_obj["caption"] = final_cap[:240]
            im_obj["caption_en"] = final_cap[:240]
        inline_images.append(im_obj)

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
        if poster and _is_valid_ifixit_image(poster):
            obj["poster"] = poster
        inline_videos.append(obj)

    for node in body.css("h2, h3, h4, figure, video, iframe, p, blockquote, li"):
        tag = (node.tag or "").lower()
        # Skip elements nested inside figure/figcaption (handled by figure branch)
        p_anc = node.parent
        in_fig = False
        while p_anc is not None and p_anc != body:
            if (p_anc.tag or "").lower() in ("figure", "figcaption"):
                in_fig = True
                break
            p_anc = p_anc.parent
        if in_fig:
            continue

        if tag == "figure":
            fcls = (node.attributes.get("class") or "").lower()

            # 1. Gallery block with nested figures
            if "wp-block-gallery" in fcls:
                gal_cap_el = node.css_first("figcaption.blocks-gallery-caption")
                gal_cap = _clean_text(gal_cap_el.text(separator=" ") if gal_cap_el else "")
                nested_figs = node.css("figure")
                if nested_figs:
                    for idx_nf, nf in enumerate(nested_figs):
                        im_el = nf.css_first("img")
                        nf_cap_el = nf.css_first("figcaption")
                        nf_cap = _clean_text(nf_cap_el.text(separator=" ") if nf_cap_el else "")
                        if not nf_cap and gal_cap and idx_nf == len(nested_figs) - 1:
                            nf_cap = gal_cap
                        _record_image(im_el, nf_cap)
                else:
                    imgs = node.css("img")
                    for idx_im, im_el in enumerate(imgs):
                        _record_image(im_el, gal_cap if idx_im == len(imgs) - 1 else "")
                continue

            cap_el = node.css_first("figcaption")
            cap_txt = _clean_text(cap_el.text(separator=" ") if cap_el else "")

            # 2. Video embed figure (YouTube / Vimeo / direct MP4)
            vid_el = node.css_first("video")
            if vid_el:
                v_src = (vid_el.attributes.get("src") or "").strip()
                if not v_src:
                    s_el = vid_el.css_first("source")
                    if s_el:
                        v_src = (s_el.attributes.get("src") or "").strip()
                if v_src:
                    _record_video(v_src, "mp4", v_title=cap_txt, poster=(vid_el.attributes.get("poster") or "").strip())
                    continue

            ifr = node.css_first("iframe")
            if ifr:
                src = html.unescape((ifr.attributes.get("src") or ifr.attributes.get("data-src") or "").strip())
                low = src.lower()
                v_title = _clean_text(ifr.attributes.get("title") or cap_txt)
                if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
                    m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
                    _record_video(src, "iframe", vid_id=(m_yt.group(1) if m_yt else None), v_title=v_title)
                elif "player.vimeo.com/video/" in low:
                    m_vm = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
                    _record_video(src, "iframe", vid_id=(m_vm.group(1) if m_vm else None), v_title=v_title)
                continue

            # 3. Single editorial image figure
            img_el = node.css_first("img")
            if img_el:
                _record_image(img_el, cap_txt)
            continue

        if tag == "video":
            v_src = (node.attributes.get("src") or "").strip()
            if not v_src:
                s_el = node.css_first("source")
                if s_el:
                    v_src = (s_el.attributes.get("src") or "").strip()
            if v_src:
                _record_video(v_src, "mp4", poster=(node.attributes.get("poster") or "").strip())
            continue

        if tag == "iframe":
            src = html.unescape((node.attributes.get("src") or node.attributes.get("data-src") or "").strip())
            low = src.lower()
            v_title = (node.attributes.get("title") or "").strip()
            if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
                m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
                _record_video(src, "iframe", vid_id=(m_yt.group(1) if m_yt else None), v_title=v_title)
            elif "player.vimeo.com/video/" in low:
                m_vm = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
                _record_video(src, "iframe", vid_id=(m_vm.group(1) if m_vm else None), v_title=v_title)
            continue

        txt = _clean_text(node.text(separator=" "))
        if not txt:
            continue

        if tag in ("h2", "h3", "h4"):
            if not _is_noise_heading(txt):
                subheadings.append(txt)
                hk = f"h:{txt.lower()}"
                if hk not in seen_p:
                    seen_p.add(hk)
                    paragraphs.append(f"### {txt}")
            continue

        if tag == "li" and len(txt) < 28:
            continue
        if _is_noise_paragraph(txt):
            continue
        key = txt.lower()[:120]
        if key not in seen_p:
            seen_p.add(key)
            paragraphs.append(txt)

    out["paragraphs"] = paragraphs
    out["subheadings"] = subheadings
    out["inline_images"] = inline_images[:24]
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


def _fetch_ifixit_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for imp in ("chrome124", "safari17_2_ios"):
            try:
                r = cffi_requests.get(url, impersonate=imp, headers=headers, proxies=proxies, timeout=18)
                if r.status_code == 200 and len(r.text) > 10000:
                    return r.text, f"ifixit_html_{imp}"
            except Exception:
                pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=18)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "ifixit_html_requests"
        except Exception:
            pass
    return None, "failed"


def crawl_ifixit(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for iFixit News (`ifixit.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "ifixit.com",
        "source": "iFixit News",
        "title": _clean_ifixit_title(title) if title else "",
        "summary": "",
        "author": "iFixit News",
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

    if not url or not is_ifixit_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_ifixit_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _IFIXIT_CACHE.get(cache_key)
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
    tier = "ifixit_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_ifixit_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_ifixit_html(raw_html)
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
            _IFIXIT_CACHE[cache_key] = dict(result)
            _save_disk_cache()
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_ifixit_image(cover):
        cover = None
    if cover:
        c_stem = _ifixit_media_stem(cover)
        inlines = [
            e for e in inlines
            if _ifixit_media_stem(e["url"] if isinstance(e, dict) else str(e)) != c_stem
        ]
        if localize_cover and html_text is None:
            cover = _localize_ifixit_image(cover, proxies=proxies)

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
            _IFIXIT_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
