#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
OpenAI Official Blog & Research Dedicated Crawler (`openai.com`)
=============================================================================
Source: OpenAI (`openai.com/index/...`, `openai.com/business/...`, etc.)
Scope: Handles all openai.com official announcements, product launches,
       research posts, and customer stories across both Contentful CMS pages
       and Next.js MDX interactive launch pages:
       - Authentic headline (`<h1>` / `og:title`), clean English `author`
         (`OpenAI` — preventing Chinese `OpenAI 官方动态` leakage on EN pages),
         and ISO publication timestamp.
       - Single-pass `<article>` DOM traversal preserving inline `### `
         subheadings and exact `after_para` + `dom_order` chart/image anchors,
         with a hard stop at `Author` / `Footnotes` / `Keep reading` / `Related`
         sections so related-article cards never pollute `inline_images`.
       - Strips OpenAI UI artifacts (`(opens in a new window)`, `Share`, etc.)
         and small customer quote logos (`-quote-logo`).
       - Next.js RSC (`self.__next_f.push`) Vimeo/MP4 demo video extraction
         with automatic portrait (`9x16`) vs landscape (`16x9`) detection and
         exact `after_para` anchoring against extracted paragraphs/headings.
       - Cover photo localization to `public/images/openai_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 15 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC, THE DECODER).
=============================================================================
"""

import os
import re
import html
import json
import time
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


_OPENAI_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "openai_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

STOP_SECTION_HEADINGS = {
    "author",
    "authors",
    "footnotes",
    "footnote",
    "keep reading",
    "related",
    "related articles",
    "related stories",
    "more from openai",
    "acknowledgments",
    "acknowledgements",
    "share",
}

NOISE_HEADING_EXACT = {
    "astra sol",
    "table of contents",
    "share",
    "copy link",
    "listen to article",
    "back to index",
    "loading",
    "loading...",
}

OPENAI_NOISE_PHRASES = [
    "keep reading",
    "all rights reserved",
    "sign up for",
    "subscribe to our",
    "copy link",
    "listen to article",
    "view all articles",
    "view all research",
    "cookies policy",
    "privacy policy",
    "terms of use",
]

BAD_IMAGE_TOKENS = (
    "-quote-logo",
    "quote-logo",
    "openai-logo",
    "site-logo",
    "brand-logo",
    "wordmark",
    "lockup",
    "avatar",
    "headshot",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "1x1",
    "placeholder",
    "doubleclick",
    "googlesyndication",
)

AUDIO_ONLY_IFRAME_DOMAINS = (
    "simplecast.com",
    "open.spotify.com",
    "megaphone.fm",
    "omny.fm",
    "podcasts.apple.com",
    "soundcloud.com",
)


def is_openai_url(url: str) -> bool:
    """Returns True if URL belongs to OpenAI official site (`openai.com`)."""
    if not url or not isinstance(url, str):
        return False
    low = url.lower()
    return "://openai.com/" in low or "://www.openai.com/" in low


def _canonical_openai_key(url: str) -> str:
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
    # Strip OpenAI link accessibility suffix: `(opens in a new window)`
    t = re.sub(r"\s*\(opens in a new window\)", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([(“\"])\s+", r"\1", t)
    t = re.sub(r"\s+([)”])", r"\1", t)
    return t.strip()


def _clean_openai_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*OpenAI\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_openai_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or any("\u4e00" <= c <= "\u9fff" for c in t):
        return "OpenAI"
    if t.lower() in ("openai", "openai team", "openai staff", "staff", "editors"):
        return "OpenAI"
    return t


def _is_stop_heading(h: str) -> bool:
    return _clean_text(h).lower().strip(": ") in STOP_SECTION_HEADINGS


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 4 or len(t) > 160:
        return True
    low = t.lower().strip(": ")
    if low in NOISE_HEADING_EXACT or low in STOP_SECTION_HEADINGS:
        return True
    if any(phrase in low for phrase in OPENAI_NOISE_PHRASES):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 22:
        return True
    low = t.lower()
    if any(phrase in low for phrase in OPENAI_NOISE_PHRASES):
        return True
    return False


def _media_stem(url: str) -> str:
    if not url:
        return ""
    return html.unescape(url).split("?")[0].split("#")[0].strip().lower()


def _is_valid_openai_image(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = html.unescape(url.strip())
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
    if _OPENAI_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _OPENAI_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        tmp = _DISK_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_OPENAI_CACHE, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _DISK_CACHE_FILE)
    except Exception:
        pass


def _localize_openai_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads OpenAI cover image to `public/images/openai_<hash>.jpg`."""
    img_url = html.unescape((img_url or "").strip())
    if not _is_valid_openai_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"openai_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://openai.com/",
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


def _extract_rsc_inline_videos(html_text: str, paragraphs: List[str], base_dom_seq: int = 500) -> List[Dict[str, Any]]:
    """
    Extracts Vimeo / MP4 demo videos embedded in OpenAI Next.js App Router RSC
    payloads (`self.__next_f.push([1,"..."])`) and maps each video to its exact
    preceding paragraph/subheading index (`after_para`).
    """
    rsc_chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html_text or "", re.S)
    if not rsc_chunks:
        return []
    joined = "".join(rsc_chunks).replace('\\"', '"').replace("\\\\", "\\")
    if "videoEmbedUrl" not in joined and "player.vimeo.com/video/" not in joined:
        return []

    # Precompute normalized anchor positions of paragraphs/subheadings inside the RSC payload
    para_offsets: List[Tuple[int, int]] = []
    for idx, p in enumerate(paragraphs):
        clean_p = p.lstrip("#").strip()
        needle = clean_p[:60] if len(clean_p) >= 24 else clean_p
        if len(needle) < 10:
            continue
        pos = joined.find(needle)
        if pos == -1 and len(needle) > 25:
            pos = joined.find(needle[:25])
        if pos != -1:
            para_offsets.append((pos, idx))
    para_offsets.sort(key=lambda x: x[0])

    out: List[Dict[str, Any]] = []
    seen = set()
    pattern = re.compile(
        r'"videoEmbedUrl":"(https://(?:player\.vimeo\.com/video/|www\.youtube\.com/embed/)[^"]+)"'
        r'(?:,"posterImageUrl":"([^"]*)")?'
        r'(?:,"altText":"([^"]*)")?',
        re.I,
    )
    for k, m in enumerate(pattern.finditer(joined)):
        v_url = html.unescape(m.group(1).strip())
        poster = html.unescape((m.group(2) or "").strip())
        alt_txt = _clean_text(m.group(3) or "")
        m_vid = re.search(r"(?:vimeo\.com/video/|youtube\.com/embed/)([A-Za-z0-9_-]+)", v_url)
        vid_id = m_vid.group(1) if m_vid else None
        dedup_k = vid_id or v_url.split("?")[0].lower()
        if dedup_k in seen:
            continue
        seen.add(dedup_k)

        ctx_before = joined[max(0, m.start() - 500):m.start()]
        is_portrait = ("aspect-9/16" in ctx_before) or ("portrait-video" in ctx_before)
        aspect = "9x16" if is_portrait else "16x9"

        # Find nearest preceding paragraph/heading in RSC stream
        after_para = 0
        for p_pos, p_idx in para_offsets:
            if p_pos < m.start():
                after_para = p_idx
            else:
                break

        vid_obj: Dict[str, Any] = {
            "url": v_url,
            "provider": "iframe",
            "after_para": after_para,
            "aspect": aspect,
            "dom_order": base_dom_seq + k,
        }
        if vid_id:
            vid_obj["video_id"] = vid_id
        if alt_txt:
            vid_obj["title"] = alt_txt[:200]
            vid_obj["caption"] = alt_txt[:240]
        if poster and _is_valid_openai_image(poster):
            vid_obj["poster"] = poster
        out.append(vid_obj)

    return out[:12]


def _parse_openai_html(html_text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "OpenAI",
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

    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t:
        out["title"] = _clean_openai_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if not m_og_d:
        m_og_d = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d:
        out["summary"] = _clean_text(m_og_d.group(1))
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if not m_og_i:
        m_og_i = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i:
        cand = html.unescape(m_og_i.group(1).strip())
        if _is_valid_openai_image(cand):
            out["cover_image"] = cand
    m_pub = re.search(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_pub:
        out["published_at"] = m_pub.group(1).strip()

    # Check JSON-LD for published date / headline if present
    for m_ld in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.S | re.I):
        try:
            ld = json.loads(m_ld.group(1).strip())
            if isinstance(ld, list):
                ld = next((x for x in ld if isinstance(x, dict)), None)
            if isinstance(ld, dict):
                if not out["published_at"] and ld.get("datePublished"):
                    out["published_at"] = str(ld["datePublished"]).strip()
                if not out["title"] and ld.get("headline"):
                    out["title"] = _clean_openai_title(str(ld["headline"]))
        except Exception:
            pass

    if not (HAS_SELECTOLAX and LexborHTMLParser is not None):
        return out

    tree = LexborHTMLParser(html_text)
    h1 = tree.css_first("article h1") or tree.css_first("main h1") or tree.css_first("h1")
    if h1:
        h1_txt = _clean_openai_title(h1.text(separator=" "))
        if len(h1_txt) >= 6:
            out["title"] = h1_txt

    if not out["published_at"]:
        t_el = tree.css_first("article time[datetime]") or tree.css_first("time[datetime]")
        if t_el and t_el.attributes.get("datetime"):
            out["published_at"] = t_el.attributes["datetime"].strip()

    body = tree.css_first("article") or tree.css_first("main")
    if not body:
        return out

    # Decompose UI chrome, navigation, and hidden accessibility widgets inside body
    for sel in (
        "script", "style", "noscript", "nav", "footer", "aside", "button", "svg",
        "[aria-label*='Share']", "[class*='keep-reading']", "[class*='related']",
        ".sr-only", ".screen-reader-text",
    ):
        for n in body.css(sel):
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
        seen_stems.add(_media_stem(out["cover_image"]))

    def _add_img(img_el, cap_txt: str = "") -> None:
        nonlocal dom_seq
        src = html.unescape((img_el.attributes.get("data-src") or img_el.attributes.get("src") or "").strip())
        if src.startswith("//"):
            src = "https:" + src
        if not _is_valid_openai_image(src):
            return
        stem = _media_stem(src)
        if not stem or stem in seen_stems:
            return
        seen_stems.add(stem)
        dom_seq += 1
        final_cap = _clean_text(cap_txt or img_el.attributes.get("alt") or "")
        obj: Dict[str, Any] = {
            "url": src,
            "after_para": max(-1, len(paragraphs) - 1),
            "dom_order": dom_seq,
        }
        if final_cap and len(final_cap) >= 5:
            obj["caption"] = final_cap[:240]
            obj["caption_en"] = final_cap[:240]
        inline_images.append(obj)

    def _add_vid(v_url: str, provider: str, vid_id: Optional[str] = None, v_title: str = "", aspect: str = "16x9", poster: str = "") -> None:
        nonlocal dom_seq
        u = html.unescape((v_url or "").strip())
        if not u.startswith(("http://", "https://")):
            return
        low = u.lower()
        if any(aud in low for aud in AUDIO_ONLY_IFRAME_DOMAINS):
            return
        dedup_k = (provider, vid_id or u.split("?")[0].lower())
        if dedup_k in seen_vids:
            return
        seen_vids.add(dedup_k)
        dom_seq += 1
        v_obj: Dict[str, Any] = {
            "url": u,
            "provider": provider,
            "after_para": max(-1, len(paragraphs) - 1),
            "aspect": aspect or "16x9",
            "dom_order": dom_seq,
        }
        if vid_id:
            v_obj["video_id"] = vid_id
        ct = _clean_text(v_title)
        if ct:
            v_obj["title"] = ct[:200]
            v_obj["caption"] = ct[:240]
        if poster and _is_valid_openai_image(poster):
            v_obj["poster"] = poster
        inline_videos.append(v_obj)

    # Single-pass DOM walk with hard stop at Author / Footnotes / Keep reading
    for node in body.css("h2, h3, figure, img, video, iframe, p, blockquote, li"):
        tag = (node.tag or "").lower()

        if tag in ("h2", "h3"):
            h_txt = _clean_text(node.text(separator=" "))
            if _is_stop_heading(h_txt):
                break
            if not _is_noise_heading(h_txt):
                subheadings.append(h_txt)
                h_key = f"h:{h_txt.lower()}"
                if h_key not in seen_p:
                    seen_p.add(h_key)
                    paragraphs.append(f"### {h_txt}")
            continue

        if tag == "figure":
            cap_el = node.css_first("figcaption")
            cap_txt = _clean_text(cap_el.text(separator=" ") if cap_el else "")
            vid_el = node.css_first("video")
            if vid_el:
                v_src = (vid_el.attributes.get("src") or "").strip()
                if not v_src:
                    s_el = vid_el.css_first("source")
                    if s_el:
                        v_src = (s_el.attributes.get("src") or "").strip()
                if v_src:
                    _add_vid(v_src, "mp4", v_title=cap_txt, poster=(vid_el.attributes.get("poster") or "").strip())
                    continue
            img_el = node.css_first("img")
            if img_el:
                _add_img(img_el, cap_txt=cap_txt)
            continue

        if tag == "img":
            # Avoid duplicating images already handled via parent <figure>
            p_anc = node.parent
            in_fig = False
            while p_anc is not None and p_anc != body:
                if (p_anc.tag or "").lower() == "figure":
                    in_fig = True
                    break
                p_anc = p_anc.parent
            if not in_fig:
                _add_img(node)
            continue

        if tag == "video":
            v_src = (node.attributes.get("src") or "").strip()
            if not v_src:
                s_el = node.css_first("source")
                if s_el:
                    v_src = (s_el.attributes.get("src") or "").strip()
            if v_src:
                _add_vid(v_src, "mp4", poster=(node.attributes.get("poster") or "").strip())
            continue

        if tag == "iframe":
            src = html.unescape((node.attributes.get("src") or node.attributes.get("data-src") or "").strip())
            low = src.lower()
            v_title = (node.attributes.get("title") or "").strip()
            if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
                m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
                _add_vid(src, "iframe", vid_id=(m_yt.group(1) if m_yt else None), v_title=v_title)
            elif "player.vimeo.com/video/" in low:
                m_vm = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
                _add_vid(src, "iframe", vid_id=(m_vm.group(1) if m_vm else None), v_title=v_title)
            continue

        if tag in ("p", "li", "blockquote"):
            # Skip paragraphs nested inside <figure> / <figcaption>
            p_anc = node.parent
            in_fig = False
            while p_anc is not None and p_anc != body:
                if (p_anc.tag or "").lower() in ("figure", "figcaption"):
                    in_fig = True
                    break
                p_anc = p_anc.parent
            if in_fig:
                continue
            txt = _clean_text(node.text(separator=" "))
            if not txt:
                continue
            if tag == "li" and len(txt) < 35:
                continue
            if _is_noise_paragraph(txt):
                continue
            key = txt.lower()[:120]
            if key not in seen_p:
                seen_p.add(key)
                paragraphs.append(txt)

    # Supplement with Next.js RSC embedded Vimeo demo videos if DOM didn't directly expose them
    rsc_vids = _extract_rsc_inline_videos(html_text, paragraphs, base_dom_seq=dom_seq + 10)
    for rv in rsc_vids:
        dk = (rv.get("provider", "iframe"), rv.get("video_id") or rv["url"].split("?")[0].lower())
        if dk not in seen_vids:
            seen_vids.add(dk)
            inline_videos.append(rv)

    out["paragraphs"] = paragraphs
    out["subheadings"] = subheadings
    out["inline_images"] = inline_images[:30]
    out["inline_videos"] = inline_videos[:12]
    out["raw_content_text"] = "\n\n".join(paragraphs)

    if inline_videos:
        first_v = inline_videos[0]
        out["has_video"] = True
        out["video_url"] = first_v["url"]
        out["video_id"] = first_v.get("video_id")
        out["video_provider"] = first_v.get("provider") or "iframe"
        out["video_aspect"] = first_v.get("aspect") or "16x9"
        out["video_poster"] = first_v.get("poster")
        out["video_title"] = first_v.get("title") or first_v.get("caption") or ""

    return out


def _fetch_openai_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for imp in ("chrome124", "safari17_2_ios"):
            try:
                r = cffi_requests.get(url, impersonate=imp, headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.text) > 12000 and ("<article" in r.text or "<h1" in r.text):
                    return r.text, f"openai_html_{imp}"
            except Exception:
                pass
            time.sleep(0.5)
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 12000:
                return r.text, "openai_html_requests"
        except Exception:
            pass
    return None, "failed"


def crawl_openai(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for OpenAI official blog (`openai.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "openai.com",
        "source": "OpenAI",
        "title": _clean_openai_title(title) if title else "",
        "summary": "",
        "author": "OpenAI",
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

    if not url or not is_openai_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_openai_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _OPENAI_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if html_text is None else None
    raw_html = html_text
    tier = "openai_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_openai_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_openai_html(raw_html)
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
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_openai_image(cover):
        cover = None
    if not cover and inlines:
        first_cand = inlines[0]["url"] if isinstance(inlines[0], dict) else str(inlines[0])
        if _is_valid_openai_image(first_cand):
            cover = first_cand
    if cover:
        c_stem = _media_stem(cover)
        inlines = [
            e for e in inlines
            if _media_stem(e["url"] if isinstance(e, dict) else str(e)) != c_stem
        ]
        if localize_cover and html_text is None:
            cover = _localize_openai_image(cover, proxies=proxies)

    paras = parsed.get("paragraphs") or []
    full_text = "\n\n".join(paras).strip()

    if parsed.get("title"):
        result["title"] = parsed["title"]
    if parsed.get("summary"):
        result["summary"] = parsed["summary"]
    result["author"] = _clean_openai_author(parsed.get("author") or "OpenAI")
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
            _OPENAI_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
